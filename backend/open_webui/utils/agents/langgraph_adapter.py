"""LangGraph implementation of the agent backend.

The adapter:

1. Wraps each entry of Open WebUI's ``tools_dict`` (as returned by
   ``open_webui.utils.tools.get_tools``) into a LangChain
   ``StructuredTool``. The underlying callable already has
   ``__event_emitter__``, ``__user__``, ``__metadata__`` etc. bound via
   closure, so tool execution keeps emitting citations / status events
   through the standard Open WebUI path.

2. Builds a minimal ``StateGraph`` with an LLM node (``ChatOpenAI`` bound
   to those tools) and a local tool-execution node. This avoids relying on
   ``langgraph.prebuilt`` at runtime while keeping ``astream_events`` tool
   traces intact. A ``MemorySaver`` checkpointer is attached so the graph
   can be interrupted or resumed later for HITL.

3. Streams LangGraph ``astream_events(version='v2')`` through the
   :class:`AGUITranslator` and emits the resulting AG UI events via the
   Open WebUI Socket.IO transport.

Caveats / follow-ups:

- ``ChatOpenAI`` is pointed at the first configured OpenAI-compatible
  backend (``OPENAI_API_BASE_URLS[0]``). A richer integration should call
  back into ``open_webui.utils.chat.generate_chat_completion`` so that
  Ollama / per-user routing / pipelines stay in effect. For now this is
  good enough for MVP validation against OpenAI-compatible models.
- ``StateDelta`` / HITL emission is wired at the translator level but not
  yet fed from graph state. That is a follow-up.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Callable, Literal

from fastapi.responses import HTMLResponse
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from open_webui.utils.agents.ag_ui_translator import AGUITranslator
from open_webui.utils.agents.transport import emit_ag_ui

log = logging.getLogger(__name__)

TOOL_APPROVAL_EVENT_NAME = 'tool_approval_requested'
TOOL_APPROVAL_REJECTED_MESSAGE = 'Execution rejected by user.'
TOOL_APPROVAL_TIMED_OUT_MESSAGE = 'Tool approval timed out.'
DEFAULT_TOOL_APPROVAL_TIMEOUT = 300.0
TOOL_APPROVAL_TITLE = 'Approve Tool Execution'
TOOL_APPROVAL_CONFIRM_LABEL = 'Approve'
TOOL_APPROVAL_CANCEL_LABEL = 'Reject'
MAX_TOOL_APPROVAL_ARG_PREVIEW_LENGTH = 1800


# ---- tool wrapping -----------------------------------------------------

_JSON_TYPE_TO_PY = {
    'string': (str, ...),
    'number': (float, ...),
    'integer': (int, ...),
    'boolean': (bool, ...),
    'array': (list, ...),
    'object': (dict, ...),
}


def _jsonschema_to_pydantic(name: str, schema: dict) -> type[BaseModel]:
    """Build a tiny pydantic model from an OpenAI function ``parameters`` schema."""
    properties = (schema or {}).get('properties') or {}
    required = set((schema or {}).get('required') or [])
    fields: dict[str, tuple[Any, Any]] = {}

    for prop_name, prop_schema in properties.items():
        json_type = prop_schema.get('type') if isinstance(prop_schema, dict) else None
        py_type, _default = _JSON_TYPE_TO_PY.get(json_type, (Any, ...))
        description = prop_schema.get('description') if isinstance(prop_schema, dict) else None
        default = ... if prop_name in required else None
        fields[prop_name] = (
            py_type if prop_name in required else (py_type | None),
            Field(default=default, description=description),
        )

    if not fields:
        return create_model(f'{name}Args')  # type: ignore[return-value]

    return create_model(f'{name}Args', **fields)  # type: ignore[call-overload]


def wrap_owui_tool_as_structured_tool(
    tool_name: str, entry: dict, event_emitter=None,
) -> dict[str, Any]:
    """Wrap an Open WebUI tool as a LangChain ``StructuredTool``."""
    spec = entry['spec']
    owui_callable: Callable = entry['callable']
    description = spec.get('description') or tool_name
    args_schema = _jsonschema_to_pydantic(tool_name, spec.get('parameters') or {})

    async def _invoke(**kwargs: Any) -> Any:
        # Drop None values: the pydantic args model fills optional fields with
        # None by default, but MCP servers typically reject `null` for optional
        # string/number parameters ("None is not of type 'string'"). Absence
        # and None are equivalent from the LLM's perspective.
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        result = await owui_callable(**kwargs)

        # Handle (HTMLResponse, result_context) tuples returned by tools
        # like Inline Visualizer.  Extract the HTML content, emit it as
        # an 'embeds' event so the frontend renders the iframe, and
        # return the context string for the LLM.
        result_context = None
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], HTMLResponse):
            result, result_context = result

        if isinstance(result, HTMLResponse):
            content_disposition = result.headers.get('Content-Disposition', '')
            if 'inline' in content_disposition and event_emitter:
                html_content = result.body.decode('utf-8', 'replace')
                await event_emitter({
                    'type': 'embeds',
                    'data': {'embeds': [html_content]},
                })

            if result_context is not None and isinstance(result_context, str):
                return result_context
            if result_context is not None and isinstance(result_context, (dict, list)):
                return json.dumps(result_context, ensure_ascii=False)
            return json.dumps({
                'status': 'success',
                'code': 'ui_component',
                'message': f'{tool_name}: Embedded UI result is active and visible to the user.',
            })

        if isinstance(result, (dict, list)):
            return result
        return str(result)

    structured_tool = StructuredTool.from_function(
        coroutine=_invoke,
        name=spec.get('name') or tool_name,
        description=description,
        args_schema=args_schema,
    )

    return {
        'structured_tool': structured_tool,
        'tool_id': entry.get('tool_id'),
    }


def _normalize_tool_call(tool_call: dict[str, Any], index: int) -> dict[str, Any]:
    tool_name = str(tool_call.get('name') or '')
    tool_args = tool_call.get('args')

    return {
        'name': tool_name,
        'args': tool_args if isinstance(tool_args, dict) else {},
        'id': str(tool_call.get('id') or f'tool_call_{index}'),
        'type': tool_call.get('type') or 'tool_call',
    }


def _tool_error_message(tool_call: dict[str, Any], content: str):
    from langchain_core.messages import ToolMessage

    return ToolMessage(
        content=content,
        name=tool_call.get('name') or None,
        tool_call_id=str(tool_call.get('id') or ''),
        status='error',
    )


def _get_tool_runtime(tool_entry: StructuredTool | dict[str, Any]) -> dict[str, Any]:
    if isinstance(tool_entry, StructuredTool):
        return {
            'structured_tool': tool_entry,
            'tool_id': tool_entry.name,
        }

    return tool_entry


def _get_model_tool_approval_ids(form_data: dict, model: dict | None) -> set[str]:
    from open_webui.models.models import Models

    model_id = form_data.get('model') or (model or {}).get('id')
    approval_ids: list[str] = []

    if model_id:
        try:
            model_record = Models.get_model_by_id(model_id)
            if model_record and model_record.meta and model_record.meta.toolApprovalIds:
                approval_ids = model_record.meta.toolApprovalIds
        except Exception:
            approval_ids = []

    if not approval_ids and model:
        model_meta = model.get('meta') or {}
        info = model.get('info') or {}
        info_meta = info.get('meta') if isinstance(info, dict) else {}
        approval_ids = model_meta.get('toolApprovalIds') or info_meta.get('toolApprovalIds') or []

    return {tool_id for tool_id in approval_ids if isinstance(tool_id, str) and tool_id}


def _build_tool_approval_event(
    *,
    run_id: str,
    tool_call: dict[str, Any],
    tool_id: str,
    parent_message_id: str | None,
    confirmation_widget_id: str | None = None,
) -> dict[str, Any]:
    value = {
        'requestId': f'tool_approval_{uuid.uuid4().hex[:12]}',
        'runId': run_id,
        'toolId': tool_id,
        'toolName': tool_call.get('name') or tool_id,
        'args': tool_call.get('args') or {},
        'parentMessageId': parent_message_id,
    }
    if confirmation_widget_id:
        value['confirmationWidgetId'] = confirmation_widget_id

    return {
        'type': 'CUSTOM',
        'name': TOOL_APPROVAL_EVENT_NAME,
        'value': value,
    }


def _format_tool_approval_args(args: Any) -> str:
    if isinstance(args, str):
        text = args.strip() or '{}'
    else:
        try:
            text = json.dumps(args or {}, ensure_ascii=False, indent=2)
        except Exception:
            text = '{}'

    if len(text) <= MAX_TOOL_APPROVAL_ARG_PREVIEW_LENGTH:
        return text

    remaining = len(text) - MAX_TOOL_APPROVAL_ARG_PREVIEW_LENGTH
    return (
        text[:MAX_TOOL_APPROVAL_ARG_PREVIEW_LENGTH].rstrip()
        + f'\n... [truncated {remaining} chars]'
    )


def _build_tool_approval_confirmation(tool_call: dict[str, Any], tool_id: str) -> dict[str, Any]:
    tool_name = tool_call.get('name') or tool_id
    args_preview = _format_tool_approval_args(tool_call.get('args'))

    return {
        'type': 'confirmation',
        'data': {
            'title': TOOL_APPROVAL_TITLE,
            'message': '\n'.join(
                [
                    f'Approve running `{tool_name}`?',
                    '',
                    'Arguments:',
                    '```json',
                    args_preview,
                    '```',
                ]
            ),
            'confirmLabel': TOOL_APPROVAL_CONFIRM_LABEL,
            'cancelLabel': TOOL_APPROVAL_CANCEL_LABEL,
        },
    }


async def _request_tool_approval(
    *,
    event_caller,
    event_emitter=None,
    run_id: str,
    tool_call: dict[str, Any],
    tool_id: str,
    parent_message_id: str | None,
    timeout: float | None = DEFAULT_TOOL_APPROVAL_TIMEOUT,
    confirmation_widget_id: str | None = None,
) -> tuple[bool, str | None]:
    if event_caller is None:
        return False, TOOL_APPROVAL_TIMED_OUT_MESSAGE

    if event_emitter is not None:
        try:
            await emit_ag_ui(
                event_emitter,
                _build_tool_approval_event(
                    run_id=run_id,
                    tool_call=tool_call,
                    tool_id=tool_id,
                    parent_message_id=parent_message_id,
                    confirmation_widget_id=confirmation_widget_id,
                ),
            )
        except Exception:
            log.exception("Tool approval event emit failed for '%s'", tool_call.get('name'))

    try:
        response = await event_caller(
            _build_tool_approval_confirmation(tool_call, tool_id),
            timeout=timeout,
        )
    except Exception:
        log.exception("Tool approval request failed for '%s'", tool_call.get('name'))
        return False, TOOL_APPROVAL_TIMED_OUT_MESSAGE

    if response is True:
        return True, None

    if isinstance(response, dict) and response.get('approved') is True:
        return True, None

    return False, TOOL_APPROVAL_REJECTED_MESSAGE


def _route_after_llm(
    state: list[Any] | dict[str, Any] | BaseModel,
    messages_key: str = 'messages',
) -> Literal['tools', '__end__']:
    """Route to the tool node when the last AI message includes tool calls."""
    if isinstance(state, list):
        messages = state
    elif isinstance(state, dict):
        messages = state.get(messages_key, [])
    else:
        messages = getattr(state, messages_key, [])

    if not messages:
        raise ValueError(f'No messages found in input state to tool edge: {state}')

    ai_message = messages[-1]
    tool_calls = getattr(ai_message, 'tool_calls', None) or []
    if tool_calls:
        return 'tools'
    return '__end__'


def _stringify_tool_output(output: Any) -> str | list[str | dict]:
    if isinstance(output, list):
        if all(isinstance(item, (str, dict)) for item in output):
            return output
        return json.dumps(output, ensure_ascii=False)
    if isinstance(output, dict):
        return json.dumps(output, ensure_ascii=False)
    return str(output)


async def _tools_node(
    state: dict[str, Any],
    tools_by_name: dict[str, StructuredTool | dict[str, Any]],
    *,
    tool_approval_ids: set[str] | None = None,
    mcp_app_tool_configs: dict[str, dict] | None = None,
    event_caller=None,
    event_emitter=None,
    run_id: str = 'run',
    approval_timeout: float | None = DEFAULT_TOOL_APPROVAL_TIMEOUT,
) -> dict[str, list[Any]]:
    """Execute tool calls from the latest AI message in order."""
    from langchain_core.messages import ToolMessage

    messages = state.get('messages', [])
    if not messages:
        raise ValueError(f'No messages found in input state to tool node: {state}')

    ai_message = messages[-1]
    raw_tool_calls = getattr(ai_message, 'tool_calls', None) or []
    parent_message_id = getattr(ai_message, 'id', None)

    outputs = []
    for index, raw_tool_call in enumerate(raw_tool_calls):
        tool_call = _normalize_tool_call(raw_tool_call, index)
        tool_name = tool_call['name']
        tool_runtime = tools_by_name.get(tool_name)

        if tool_runtime is None:
            available_tools = ', '.join(sorted(tools_by_name)) or 'none'
            outputs.append(
                _tool_error_message(
                    tool_call,
                    f'Error: {tool_name} is not a valid tool, try one of [{available_tools}].',
                )
            )
            continue

        tool_runtime = _get_tool_runtime(tool_runtime)
        tool = tool_runtime['structured_tool']
        tool_id = tool_runtime.get('tool_id') or tool_name

        if tool_approval_ids and tool_id in tool_approval_ids:
            # Look up confirmation widget ID from MCP App tool configs
            confirmation_widget_id = None
            if mcp_app_tool_configs:
                # tool_id format: mcp_app:{app_id}_{tool_name}
                # tool_configs key: tool_name
                for tc_name, tc in mcp_app_tool_configs.items():
                    if tool_id.endswith(f'_{tc_name}') and tc.get('confirmation_widget_id'):
                        confirmation_widget_id = tc['confirmation_widget_id']
                        break

            approved, approval_error = await _request_tool_approval(
                event_caller=event_caller,
                event_emitter=event_emitter,
                run_id=run_id,
                tool_call=tool_call,
                tool_id=tool_id,
                parent_message_id=parent_message_id,
                timeout=approval_timeout,
                confirmation_widget_id=confirmation_widget_id,
            )
            if not approved:
                if event_emitter is not None:
                    await emit_ag_ui(
                        event_emitter,
                        {
                            'type': 'TOOL_CALL_END',
                            'toolCallId': tool_call['id'],
                        },
                    )
                outputs.append(
                    _tool_error_message(
                        tool_call,
                        approval_error or TOOL_APPROVAL_REJECTED_MESSAGE,
                    )
                )
                continue

        try:
            result = await tool.ainvoke(tool_call)
        except Exception as exc:
            log.exception("LangGraph tool '%s' failed: %s", tool_name, exc)
            outputs.append(
                _tool_error_message(
                    tool_call,
                    f"Error executing tool '{tool_name}' with error: {exc}",
                )
            )
            continue

        if isinstance(result, ToolMessage):
            outputs.append(result)
            continue

        outputs.append(
            ToolMessage(
                content=_stringify_tool_output(result),
                name=tool_name,
                tool_call_id=tool_call['id'],
            )
        )

    return {'messages': outputs}


# ---- graph construction ------------------------------------------------


def _resolve_upstream(request: Any, model: dict, form_data: dict) -> tuple[str, str | None, str]:
    """Resolve a model to the upstream OpenAI-compatible connection."""
    from open_webui.models.models import Models

    model_id = form_data.get('model') or model.get('id')

    visited: set[str] = set()
    current = Models.get_model_by_id(model_id)
    while current and current.base_model_id and current.id not in visited:
        visited.add(current.id)
        model_id = current.base_model_id
        current = Models.get_model_by_id(model_id)

    openai_models = getattr(request.app.state, 'OPENAI_MODELS', None) or {}
    resolved = openai_models.get(model_id) or {}
    idx = resolved.get('urlIdx', 0)

    app_config = request.app.state.config
    base_urls = getattr(app_config, 'OPENAI_API_BASE_URLS', None) or []
    api_keys = getattr(app_config, 'OPENAI_API_KEYS', None) or []
    base_url = base_urls[idx] if 0 <= idx < len(base_urls) else (base_urls[0] if base_urls else None)
    api_key = api_keys[idx] if 0 <= idx < len(api_keys) else (api_keys[0] if api_keys else 'EMPTY')

    api_configs = getattr(app_config, 'OPENAI_API_CONFIGS', None) or {}
    api_config = api_configs.get(str(idx)) or (
        api_configs.get(base_urls[idx]) if 0 <= idx < len(base_urls) else {}
    ) or {}
    prefix_id = api_config.get('prefix_id')
    if prefix_id and isinstance(model_id, str):
        model_id = model_id.replace(f'{prefix_id}.', '')

    return model_id, base_url, api_key


def _build_llm(request: Any, model: dict, form_data: dict):
    """Instantiate a LangChain chat model for the agent node."""
    from langchain_openai import ChatOpenAI

    upstream_model, base_url, api_key = _resolve_upstream(request, model, form_data)

    return ChatOpenAI(
        model=upstream_model or 'gpt-4o-mini',
        base_url=base_url,
        api_key=api_key,
        streaming=True,
        temperature=form_data.get('temperature', 0.7),
    )


def _build_graph(
    llm,
    lc_tool_runtimes: list[dict[str, Any]],
    *,
    event_caller=None,
    event_emitter=None,
    tool_approval_ids: set[str] | None = None,
    mcp_app_tool_configs: dict[str, dict] | None = None,
    run_id: str = 'run',
):
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph, MessagesState

    lc_tools = [tool_runtime['structured_tool'] for tool_runtime in lc_tool_runtimes]
    llm_with_tools = llm.bind_tools(lc_tools) if lc_tools else llm
    tools_by_name = {tool_runtime['structured_tool'].name: tool_runtime for tool_runtime in lc_tool_runtimes}

    async def llm_node(state: MessagesState) -> dict:
        response = await llm_with_tools.ainvoke(state['messages'])
        return {'messages': [response]}

    async def tools_node(state: MessagesState) -> dict:
        return await _tools_node(
            state,
            tools_by_name,
            tool_approval_ids=tool_approval_ids,
            mcp_app_tool_configs=mcp_app_tool_configs,
            event_caller=event_caller,
            event_emitter=event_emitter,
            run_id=run_id,
        )

    graph = StateGraph(MessagesState)
    graph.add_node('llm', llm_node)

    if lc_tools:
        graph.add_node('tools', tools_node)
        graph.add_edge(START, 'llm')
        graph.add_conditional_edges('llm', _route_after_llm)
        graph.add_edge('tools', 'llm')
    else:
        graph.add_edge(START, 'llm')
        graph.add_edge('llm', END)

    return graph.compile(checkpointer=MemorySaver())


def _messages_from_form_data(form_data: dict) -> list:
    """Convert OpenAI-format chat messages into LangChain message objects."""
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

    out = []
    for message in form_data.get('messages', []) or []:
        role = message.get('role')
        content = message.get('content', '')

        if role == 'system':
            out.append(SystemMessage(content=content))
        elif role == 'assistant':
            out.append(AIMessage(content=content))
        elif role == 'tool':
            out.append(
                ToolMessage(
                    content=content,
                    tool_call_id=message.get('tool_call_id', ''),
                )
            )
        else:
            out.append(HumanMessage(content=content))
    return out


# ---- main entrypoint ---------------------------------------------------


async def run_langgraph_agent(
    *,
    request: Any,
    form_data: dict,
    tools_dict: dict,
    event_emitter,
    event_caller,
    metadata: dict,
    model: dict,
    user,
) -> None:
    """Run a LangGraph agent for this chat turn."""
    chat_id = metadata.get('chat_id') or 'default'
    translator = AGUITranslator(thread_id=chat_id)

    try:
        lc_tool_runtimes = [
            wrap_owui_tool_as_structured_tool(name, entry, event_emitter=event_emitter)
            for name, entry in (tools_dict or {}).items()
        ]
        tool_approval_ids = _get_model_tool_approval_ids(form_data, model)

        # Merge MCP App confirmation IDs
        mcp_app_confirmation_ids = metadata.get('mcp_app_confirmation_ids')
        if mcp_app_confirmation_ids:
            tool_approval_ids = tool_approval_ids | mcp_app_confirmation_ids

        mcp_app_tool_configs = metadata.get('mcp_app_tool_configs')

        llm = _build_llm(request, model, form_data)
        app = _build_graph(
            llm,
            lc_tool_runtimes,
            event_caller=event_caller,
            event_emitter=event_emitter,
            tool_approval_ids=tool_approval_ids,
            mcp_app_tool_configs=mcp_app_tool_configs,
            run_id=translator.run_id,
        )

        messages = _messages_from_form_data(form_data)
        config = {'configurable': {'thread_id': chat_id}}

        async for lg_event in app.astream_events(
            {'messages': messages},
            version='v2',
            config=config,
        ):
            for ag_ui_event in translator.translate(lg_event):
                await emit_ag_ui(event_emitter, ag_ui_event)

        for ag_ui_event in translator.finish():
            await emit_ag_ui(event_emitter, ag_ui_event)

    except Exception as exc:
        log.exception('LangGraph agent failed: %s', exc)
        for ag_ui_event in translator.error(str(exc)):
            await emit_ag_ui(event_emitter, ag_ui_event)
