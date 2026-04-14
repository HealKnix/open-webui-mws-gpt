import time
import logging
import sys

from aiocache import cached
from typing import Any, Optional
import random
import json
import re

import uuid
import asyncio

from fastapi import Request, status
from starlette.responses import Response, StreamingResponse, JSONResponse


from open_webui.models.users import UserModel

from open_webui.socket.main import (
    sio,
    get_event_call,
    get_event_emitter,
)
from open_webui.functions import generate_function_chat_completion

from open_webui.routers.openai import (
    generate_chat_completion as generate_openai_chat_completion,
)

from open_webui.routers.ollama import (
    generate_chat_completion as generate_ollama_chat_completion,
)
from open_webui.orchestration.executor import execute_orchestrated_chat_completion

from open_webui.routers.pipelines import (
    process_pipeline_inlet_filter,
    process_pipeline_outlet_filter,
)

from open_webui.models.functions import Functions
from open_webui.models.models import Models

from open_webui.utils.models import get_all_models, check_model_access
from open_webui.utils.payload import convert_payload_openai_to_ollama
from open_webui.utils.response import (
    convert_response_ollama_to_openai,
    convert_streaming_response_ollama_to_openai,
)
from open_webui.utils.filter import (
    get_sorted_filter_ids,
    process_filter_functions,
)

from open_webui.env import GLOBAL_LOG_LEVEL, BYPASS_MODEL_ACCESS_CONTROL

logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)


ORCHESTRATOR_SIMPLE_SKIP_HINTS = (
    'исслед',
    'research',
    'deep research',
    'пошаг',
    'архитект',
    'документ',
    'источник',
    'citation',
    'review',
    'проверь',
    'код',
    'code',
    'debug',
    'ошиб',
    'bug',
    'traceback',
    'stacktrace',
    'refactor',
    'сравни',
    'compare',
)

ORCHESTRATOR_PASSTHROUGH_MODEL_PRIORITY = (
    'mws-gpt-alpha',
    'qwen3-32b',
    'T-pro-it-1.0',
    'qwen2.5-72b-instruct',
    'llama-3.1-8b-instruct',
)

PRESENTATION_REQUEST_HINTS = (
    'презентац',
    'слайд',
    'ppt',
    'pptx',
    'slides',
    'pitch deck',
    'deck',
)


def _is_orchestrator_model(model: dict[str, Any]) -> bool:
    return bool(model.get('orchestrator') or model.get('owned_by') == 'orchestrator')


def _extract_last_user_content(messages: list[dict[str, Any]] | None) -> tuple[str, bool]:
    if not messages:
        return '', False

    for message in reversed(messages):
        if message.get('role') != 'user':
            continue

        content = message.get('content', '')
        if isinstance(content, str):
            return content.strip(), False

        if isinstance(content, list):
            text_blocks: list[str] = []
            has_non_text_blocks = False
            for item in content:
                if not isinstance(item, dict):
                    continue
                block_type = item.get('type')
                if block_type == 'text':
                    text_blocks.append(str(item.get('text') or '').strip())
                else:
                    has_non_text_blocks = True
            return '\n'.join([block for block in text_blocks if block]).strip(), has_non_text_blocks

        return str(content or '').strip(), False

    return '', False


def _is_presentation_intent(form_data: dict[str, Any]) -> bool:
    prompt, has_non_text_blocks = _extract_last_user_content(form_data.get('messages') or [])
    if has_non_text_blocks:
        return False
    lowered = (prompt or '').strip().lower()
    if not lowered:
        return False
    return any(hint in lowered for hint in PRESENTATION_REQUEST_HINTS)


def _is_simple_orchestrator_request(form_data: dict[str, Any]) -> bool:
    messages = form_data.get('messages') or []
    prompt, has_non_text_blocks = _extract_last_user_content(messages)
    if not prompt:
        return False
    if has_non_text_blocks:
        return False

    files = form_data.get('files') or (form_data.get('metadata') or {}).get('files') or []
    if files:
        return False

    lowered = prompt.lower()
    if any(hint in lowered for hint in ORCHESTRATOR_SIMPLE_SKIP_HINTS):
        return False

    word_count = len([token for token in re.split(r'\s+', prompt) if token])
    if word_count > 20:
        return False

    return True


def _select_orchestrator_passthrough_model(models: dict[str, dict[str, Any]]) -> str | None:
    for model_id in ORCHESTRATOR_PASSTHROUGH_MODEL_PRIORITY:
        model = models.get(model_id)
        if not model:
            continue
        if model.get('owned_by') != 'openai':
            continue
        if model.get('orchestrator'):
            continue
        return model_id

    for model_id, model in models.items():
        if model.get('owned_by') != 'openai':
            continue
        if model.get('orchestrator'):
            continue
        lowered = str(model_id).lower()
        if any(token in lowered for token in ['embedding', 'bge', 'whisper']):
            continue
        if 'image' in lowered and 'instruct' not in lowered:
            continue
        if '-vl' in lowered:
            continue
        return model_id

    return None


def _is_forced_deep_research(form_data: dict[str, Any]) -> bool:
    metadata = form_data.get('metadata') or {}
    metadata_features = metadata.get('features') or {}
    request_features = form_data.get('features') or {}

    metadata_params = metadata.get('params') or {}
    request_params = form_data.get('params') or {}

    return bool(
        metadata_features.get('deep_research')
        or request_features.get('deep_research')
        or metadata_params.get('deep_research')
        or request_params.get('deep_research')
    )


def _is_forced_presentation_generation(form_data: dict[str, Any]) -> bool:
    metadata = form_data.get('metadata') or {}
    metadata_features = metadata.get('features') or {}
    request_features = form_data.get('features') or {}

    metadata_params = metadata.get('params') or {}
    request_params = form_data.get('params') or {}

    return bool(
        metadata_features.get('presentation_generation')
        or request_features.get('presentation_generation')
        or metadata_params.get('presentation_generation')
        or request_params.get('presentation_generation')
        or metadata_params.get('presentation')
        or request_params.get('presentation')
    )


def _should_passthrough_orchestrator(form_data: dict[str, Any], model: dict[str, Any]) -> tuple[bool, str | None]:
    metadata = form_data.get('metadata') or {}
    if metadata.get('task'):
        return True, 'internal_task'

    if _is_forced_deep_research(form_data):
        return False, None
    if _is_forced_presentation_generation(form_data):
        return False, None
    if _is_presentation_intent(form_data):
        return False, None

    metadata_features = metadata.get('features') or {}
    request_features = form_data.get('features') or {}
    model_skill_ids = model.get('info', {}).get('meta', {}).get('skillIds', []) or []
    has_model_skills = len(model_skill_ids) > 0
    has_explicit_tooling = bool(
        form_data.get('tool_ids')
        or form_data.get('terminal_id')
        or form_data.get('tools')
        or request_features.get('web_search')
        or metadata_features.get('web_search')
    )

    if has_model_skills or has_explicit_tooling:
        if _is_simple_orchestrator_request(form_data):
            return True, 'skills_or_tools_simple'
        return False, None

    if _is_simple_orchestrator_request(form_data):
        return True, 'simple_prompt'

    return False, None


# When the question has been asked, let silence not be the
# answer. But if the answer must wait, let it come honest.
async def generate_direct_chat_completion(
    request: Request,
    form_data: dict,
    user: Any,
    models: dict,
):
    log.info('generate_direct_chat_completion')

    metadata = form_data.pop('metadata', {})

    user_id = metadata.get('user_id')
    session_id = metadata.get('session_id')
    request_id = str(uuid.uuid4())  # Generate a unique request ID

    event_caller = get_event_call(metadata)

    channel = f'{user_id}:{session_id}:{request_id}'
    logging.info(f'WebSocket channel: {channel}')

    if form_data.get('stream'):
        q = asyncio.Queue()

        async def message_listener(sid, data):
            """
            Handle received socket messages and push them into the queue.
            """
            await q.put(data)

        # Register the listener
        sio.on(channel, message_listener)

        # Start processing chat completion in background
        res = await event_caller(
            {
                'type': 'request:chat:completion',
                'data': {
                    'form_data': form_data,
                    'model': models[form_data['model']],
                    'channel': channel,
                    'session_id': session_id,
                },
            }
        )

        log.info(f'res: {res}')

        if res.get('status', False):
            # Define a generator to stream responses
            async def event_generator():
                nonlocal q
                try:
                    while True:
                        data = await q.get()  # Wait for new messages
                        if isinstance(data, dict):
                            if 'done' in data and data['done']:
                                break  # Stop streaming when 'done' is received

                            yield f'data: {json.dumps(data)}\n\n'
                        elif isinstance(data, str):
                            if 'data:' in data:
                                yield f'{data}\n\n'
                            else:
                                yield f'data: {data}\n\n'
                except Exception as e:
                    log.debug(f'Error in event generator: {e}')
                    pass

            # Define a background task to run the event generator
            async def background():
                try:
                    del sio.handlers['/'][channel]
                except Exception as e:
                    pass

            # Return the streaming response
            return StreamingResponse(event_generator(), media_type='text/event-stream', background=background)
        else:
            raise Exception(str(res))
    else:
        res = await event_caller(
            {
                'type': 'request:chat:completion',
                'data': {
                    'form_data': form_data,
                    'model': models[form_data['model']],
                    'channel': channel,
                    'session_id': session_id,
                },
            }
        )

        if 'error' in res and res['error']:
            raise Exception(res['error'])

        return res


async def generate_chat_completion(
    request: Request,
    form_data: dict,
    user: Any,
    bypass_filter: bool = False,
    bypass_system_prompt: bool = False,
):
    log.debug(f'generate_chat_completion: {form_data}')
    if BYPASS_MODEL_ACCESS_CONTROL:
        bypass_filter = True

    # Propagate bypass_filter via request.state so that downstream route
    # handlers (openai/ollama) can read it without exposing it as a query param.
    request.state.bypass_filter = bypass_filter

    if hasattr(request.state, 'metadata'):
        if 'metadata' not in form_data:
            form_data['metadata'] = request.state.metadata
        else:
            form_data['metadata'] = {
                **form_data['metadata'],
                **request.state.metadata,
            }

    # Apply context compression if enabled
    try:
        from open_webui.utils.context_builder import build_chat_context
        from open_webui.models.chat_context_state import ChatContextStates

        metadata = form_data.get('metadata', {})
        chat_id = metadata.get('chat_id')

        if chat_id and user and hasattr(user, 'id'):
            state = ChatContextStates.get_state_by_chat_id(chat_id)
            if state and state.enabled and state.active_segment_id:
                # Build compressed context
                compressed_context = build_chat_context(
                    chat_id=chat_id,
                    user_id=user.id,
                    system_prompt=None,  # Will handle separately
                    include_summary=True,
                    include_tool_digest=state.include_tool_data,
                )

                if compressed_context:
                    # Get original messages
                    original_messages = form_data.get('messages', [])

                    # Find system prompt if any
                    system_prompt = None
                    other_messages = []
                    for msg in original_messages:
                        if msg.get('role') == 'system':
                            system_prompt = msg.get('content', '')
                        else:
                            other_messages.append(msg)

                    # Keep only last N messages based on state.keep_last_messages
                    keep_last = state.keep_last_messages or 5
                    recent_messages = other_messages[-keep_last:] if len(other_messages) > keep_last else other_messages

                    # Build new message list: system prompt + compressed summary + recent messages
                    new_messages = []

                    # Add system prompt if exists
                    if system_prompt:
                        new_messages.append({
                            'role': 'system',
                            'content': system_prompt,
                        })

                    # Add compressed context (which includes its own system message)
                    new_messages.extend(compressed_context)

                    # Add recent messages
                    new_messages.extend(recent_messages)

                    # Replace messages in form_data
                    form_data['messages'] = new_messages

                    log.info(f"Applied context compression for chat {chat_id}: {len(original_messages)} -> {len(new_messages)} messages")
    except Exception as e:
        log.warning(f"Failed to apply context compression: {e}")

    if getattr(request.state, 'direct', False) and hasattr(request.state, 'model'):
        models = {
            request.state.model['id']: request.state.model,
        }
        log.debug(f'direct connection to model: {models}')
    else:
        models = request.app.state.MODELS

    model_id = form_data['model']
    if model_id not in models:
        raise Exception('Model not found')

    model = models[model_id]

    if getattr(request.state, 'direct', False):
        return await generate_direct_chat_completion(request, form_data, user=user, models=models)
    else:
        # Check if user has access to the model
        if not bypass_filter and user.role == 'user':
            try:
                check_model_access(user, model)
            except Exception as e:
                raise e

        # Arena model — sub-model was already resolved by process_chat_payload.
        # Inject selected_model_id into the response for the frontend.
        metadata = form_data.get('metadata', {})
        selected_model_id = metadata.pop('selected_model_id', None)
        # Also clear from request.state.metadata to prevent the merge at
        # lines 177-179 from re-adding it on the recursive call.
        if hasattr(request.state, 'metadata'):
            request.state.metadata.pop('selected_model_id', None)

        # Fallback: if generate_chat_completion is called with an arena model
        # from a path that did NOT go through process_chat_payload (e.g.,
        # background tasks for title/follow-up/tags generation), resolve now.
        if not selected_model_id and model.get('owned_by') == 'arena':
            model_ids = model.get('info', {}).get('meta', {}).get('model_ids')
            filter_mode = model.get('info', {}).get('meta', {}).get('filter_mode')
            if model_ids and filter_mode == 'exclude':
                model_ids = [
                    available_model['id']
                    for available_model in list(request.app.state.MODELS.values())
                    if available_model.get('owned_by') != 'arena' and available_model['id'] not in model_ids
                ]

            if isinstance(model_ids, list) and model_ids:
                selected_model_id = random.choice(model_ids)
            else:
                model_ids = [
                    available_model['id']
                    for available_model in list(request.app.state.MODELS.values())
                    if available_model.get('owned_by') != 'arena'
                ]
                selected_model_id = random.choice(model_ids)

            form_data['model'] = selected_model_id

        if selected_model_id:
            if form_data.get('stream') == True:

                async def stream_wrapper(stream):
                    yield f'data: {json.dumps({"selected_model_id": selected_model_id})}\n\n'
                    async for chunk in stream:
                        yield chunk

                response = await generate_chat_completion(
                    request,
                    form_data,
                    user,
                    bypass_filter=True,
                    bypass_system_prompt=bypass_system_prompt,
                )
                return StreamingResponse(
                    stream_wrapper(response.body_iterator),
                    media_type='text/event-stream',
                    background=response.background,
                )
            else:
                return {
                    **(
                        await generate_chat_completion(
                            request,
                            form_data,
                            user,
                            bypass_filter=True,
                            bypass_system_prompt=bypass_system_prompt,
                        )
                    ),
                    'selected_model_id': selected_model_id,
                }

        if model.get('pipe'):
            # Below does not require bypass_filter because this is the only route the uses this function and it is already bypassing the filter
            return await generate_function_chat_completion(request, form_data, user=user, models=models)
        if _is_orchestrator_model(model):
            should_passthrough, passthrough_reason = _should_passthrough_orchestrator(form_data, model)
            if should_passthrough:
                passthrough_model_id = _select_orchestrator_passthrough_model(models)
                if passthrough_model_id:
                    log.info(
                        f'Bypassing orchestrator for model {model.get("id")} '
                        f'({passthrough_reason}) -> {passthrough_model_id}'
                    )
                    form_data['model'] = passthrough_model_id
                    return await generate_openai_chat_completion(
                        request=request,
                        form_data=form_data,
                        user=user,
                        bypass_system_prompt=bypass_system_prompt,
                    )
                log.warning(
                    f'Bypass requested for orchestrator model {model.get("id")} '
                    f'({passthrough_reason}), but no passthrough model is available.'
                )
            return await execute_orchestrated_chat_completion(request, form_data, user=user)
        if model.get('owned_by') == 'ollama':
            # Using /ollama/api/chat endpoint
            form_data = convert_payload_openai_to_ollama(form_data)
            response = await generate_ollama_chat_completion(
                request=request,
                form_data=form_data,
                user=user,
                bypass_system_prompt=bypass_system_prompt,
            )
            if form_data.get('stream'):
                response.headers['content-type'] = 'text/event-stream'
                return StreamingResponse(
                    convert_streaming_response_ollama_to_openai(response),
                    headers=dict(response.headers),
                    background=response.background,
                )
            else:
                return convert_response_ollama_to_openai(response)
        else:
            return await generate_openai_chat_completion(
                request=request,
                form_data=form_data,
                user=user,
                bypass_system_prompt=bypass_system_prompt,
            )


chat_completion = generate_chat_completion


async def chat_completed(request: Request, form_data: dict, user: Any):
    if not request.app.state.MODELS:
        await get_all_models(request, user=user)

    if getattr(request.state, 'direct', False) and hasattr(request.state, 'model'):
        models = {
            request.state.model['id']: request.state.model,
        }
    else:
        models = request.app.state.MODELS

    data = form_data
    model_id = data['model']
    if model_id not in models:
        raise Exception('Model not found')

    model = models[model_id]

    try:
        data = await process_pipeline_outlet_filter(request, data, user, models)
    except Exception as e:
        raise Exception(f'Error: {e}')

    metadata = {
        'chat_id': data['chat_id'],
        'message_id': data['id'],
        'filter_ids': data.get('filter_ids', []),
        'session_id': data['session_id'],
        'user_id': user.id,
    }

    extra_params = {
        '__event_emitter__': get_event_emitter(metadata),
        '__event_call__': get_event_call(metadata),
        '__user__': user.model_dump() if isinstance(user, UserModel) else {},
        '__metadata__': metadata,
        '__request__': request,
        '__model__': model,
    }

    try:
        filter_ids = get_sorted_filter_ids(request, model, metadata.get('filter_ids', []))
        filter_functions = Functions.get_functions_by_ids(filter_ids)

        result, _ = await process_filter_functions(
            request=request,
            filter_functions=filter_functions,
            filter_type='outlet',
            form_data=data,
            extra_params=extra_params,
        )

        # Trigger context compression after successful chat completion
        # This runs in the background and doesn't block the response
        try:
            chat_id = data.get('chat_id')
            if chat_id and not chat_id.startswith('local:'):
                from open_webui.utils.context_compactor import get_context_compactor

                # Run compaction in background task with user object
                compactor = get_context_compactor()
                asyncio.create_task(
                    compactor.compact_chat_context(
                        request=request,
                        chat_id=chat_id,
                        user_id=user.id,
                        force=False,  # Only compact if thresholds are met
                        user=user,  # Pass user object for background task
                    )
                )
        except Exception as e:
            # Log but don't fail the chat completion
            log.warning(f'Error triggering context compression: {e}')

        return result
    except Exception as e:
        raise Exception(f'Error: {e}')
