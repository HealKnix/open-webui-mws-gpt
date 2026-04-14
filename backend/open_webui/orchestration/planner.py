from __future__ import annotations

import uuid
from typing import Any

from open_webui.orchestration.classifier import (
    build_preparse_summary,
    classify_intent,
    extract_input_artifacts,
    resolve_user_goal,
)
from open_webui.orchestration.schema import Operation, OrchestrationPlan, PolicyMode
from open_webui.orchestration.validator import validate_plan
from open_webui.utils.misc import get_last_user_message


CRITIQUE_HINTS = (
    'проверь',
    'review',
    'крити',
    'точно',
    'quality',
    'надеж',
    'структур',
)

PRESENTATION_HINTS = (
    'презентац',
    'слайд',
    'ppt',
    'pptx',
    'deck',
    'pitch',
    'slides',
)


def _artifact_id(artifacts, artifact_type: str) -> str | None:
    for artifact in artifacts:
        if artifact.type == artifact_type:
            return artifact.id
    return None


def _goal_complexity_score(user_goal: str) -> int:
    goal = (user_goal or '').strip().lower()
    if not goal:
        return 0

    score = 0
    words = [token for token in goal.split() if token]
    if len(words) > 30:
        score += 1
    if len(words) > 90:
        score += 2
    if any(token in goal for token in CRITIQUE_HINTS):
        score += 1
    return score


def _to_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _is_presentation_goal(user_goal: str) -> bool:
    lowered = (user_goal or '').strip().lower()
    if not lowered:
        return False
    return any(hint in lowered for hint in PRESENTATION_HINTS)


def _should_enable_deep_research(form_data: dict[str, Any], metadata: dict[str, Any]) -> bool:
    features = metadata.get('features') or {}
    params = metadata.get('params') or {}
    request_features = form_data.get('features') or {}
    request_params = form_data.get('params') or {}

    if any(
        _to_bool(flag)
        for flag in (
            features.get('deep_research'),
            params.get('deep_research'),
            request_features.get('deep_research'),
            request_params.get('deep_research'),
        )
    ):
        return True

    files = metadata.get('files') or form_data.get('files') or []
    sources = metadata.get('sources') or []
    return bool(files or sources)


def _should_enable_presentation_generation(
    form_data: dict[str, Any],
    metadata: dict[str, Any],
    user_goal: str,
) -> bool:
    features = metadata.get('features') or {}
    params = metadata.get('params') or {}
    request_features = form_data.get('features') or {}
    request_params = form_data.get('params') or {}

    if any(
        _to_bool(flag)
        for flag in (
            features.get('presentation_generation'),
            params.get('presentation_generation'),
            request_features.get('presentation_generation'),
            request_params.get('presentation_generation'),
            params.get('presentation'),
            request_params.get('presentation'),
        )
    ):
        return True

    mode_candidates = [
        str(params.get('response_mode') or '').strip().lower(),
        str(request_params.get('response_mode') or '').strip().lower(),
        str(params.get('output_mode') or '').strip().lower(),
        str(request_params.get('output_mode') or '').strip().lower(),
    ]
    if any(mode in {'presentation', 'pptx', 'slides'} for mode in mode_candidates if mode):
        return True

    return _is_presentation_goal(user_goal)


def _should_enable_critic(user_goal: str) -> bool:
    return _goal_complexity_score(user_goal) >= 2


def build_plan(form_data: dict[str, Any], policy_mode: PolicyMode = 'balanced') -> OrchestrationPlan:
    artifacts = extract_input_artifacts(form_data)
    messages = form_data.get('messages', []) or []
    raw_user_goal = get_last_user_message(messages) or ''
    user_goal = resolve_user_goal(messages)
    metadata = dict(form_data.get('metadata', {}) or {})
    intent_mode = classify_intent(artifacts, user_goal)
    preparse = build_preparse_summary(artifacts, user_goal)
    deep_research = _should_enable_deep_research(form_data, metadata)
    presentation_generation = _should_enable_presentation_generation(form_data, metadata, user_goal)
    effective_policy_mode: PolicyMode = policy_mode
    if presentation_generation and policy_mode == 'balanced':
        effective_policy_mode = 'quality'
    use_critic = _should_enable_critic(raw_user_goal)

    operations: list[Operation] = []
    output_artifact_ids: list[str] = []

    text_input_id = _artifact_id(artifacts, 'text')
    image_input_id = _artifact_id(artifacts, 'image')
    audio_input_id = _artifact_id(artifacts, 'audio')

    if intent_mode == 'analyze_text':
        if presentation_generation:
            operations.extend(
                [
                    Operation(
                        id='op_1',
                        kind='generate_text',
                        inputs=[text_input_id] if text_input_id else [],
                        output_id='presentation_plan_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Presentation planner: define presentation objective, audience and target deck structure.',
                        options={'stage': 'presentation_plan', 'agent': 'researcher', 'deep_research': True},
                    ),
                    Operation(
                        id='op_2',
                        kind='generate_text',
                        inputs=[artifact_id for artifact_id in [text_input_id, 'presentation_plan_1'] if artifact_id],
                        output_id='source_routing_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Source router: split evidence between internet and uploaded files by presentation components.',
                        options={'stage': 'source_routing', 'agent': 'researcher', 'deep_research': True},
                    ),
                    Operation(
                        id='op_3',
                        kind='retrieve_context',
                        inputs=[artifact_id for artifact_id in [text_input_id, 'presentation_plan_1', 'source_routing_1'] if artifact_id],
                        output_id='presentation_ctx_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Searcher: collect evidence for presentation components from files and web.',
                        options={'stage': 'presentation_search_primary', 'agent': 'searcher', 'deep_research': True, 'top_k_chunks': 20},
                    ),
                    Operation(
                        id='op_4',
                        kind='generate_text',
                        inputs=[
                            artifact_id
                            for artifact_id in [text_input_id, 'presentation_plan_1', 'source_routing_1', 'presentation_ctx_1']
                            if artifact_id
                        ],
                        output_id='presentation_outline_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Analyst: create a slide-by-slide outline grounded in retrieved evidence.',
                        options={'stage': 'presentation_outline', 'agent': 'analyst', 'deep_research': True},
                    ),
                    Operation(
                        id='op_5',
                        kind='generate_text',
                        inputs=[
                            artifact_id
                            for artifact_id in [text_input_id, 'presentation_outline_1', 'presentation_ctx_1']
                            if artifact_id
                        ],
                        output_id='presentation_content_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Reporter: generate full slide content JSON for the draft deck.',
                        options={'stage': 'presentation_content', 'agent': 'reporter', 'deep_research': True},
                    ),
                    Operation(
                        id='op_6',
                        kind='critique_text',
                        inputs=['presentation_content_1', 'presentation_ctx_1', 'source_routing_1'],
                        output_id='presentation_validation_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Validator: check factual quality and structure, then produce targeted follow-up queries.',
                        options={'stage': 'presentation_validation', 'agent': 'reviewer', 'deep_research': True},
                    ),
                    Operation(
                        id='op_7',
                        kind='retrieve_context',
                        inputs=[
                            artifact_id
                            for artifact_id in [text_input_id, 'source_routing_1', 'presentation_validation_1']
                            if artifact_id
                        ],
                        output_id='presentation_ctx_gap_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Searcher: close evidence gaps discovered by presentation validator.',
                        options={'stage': 'presentation_gap_fill', 'agent': 'searcher', 'deep_research': True, 'top_k_chunks': 20},
                    ),
                    Operation(
                        id='op_8',
                        kind='generate_text',
                        inputs=[
                            artifact_id
                            for artifact_id in [
                                text_input_id,
                                'presentation_outline_1',
                                'presentation_content_1',
                                'presentation_validation_1',
                                'presentation_ctx_gap_1',
                            ]
                            if artifact_id
                        ],
                        output_id='presentation_content_2',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Reporter: refine slide deck content using validation feedback and gap-fill evidence.',
                        max_rounds=2,
                        stop_on_no_change=1,
                        options={'stage': 'presentation_content_refined', 'agent': 'reporter', 'deep_research': True},
                    ),
                    Operation(
                        id='op_9',
                        kind='generate_text',
                        inputs=[
                            artifact_id
                            for artifact_id in [
                                text_input_id,
                                'presentation_plan_1',
                                'source_routing_1',
                                'presentation_ctx_1',
                                'presentation_outline_1',
                                'presentation_content_2',
                                'presentation_validation_1',
                                'presentation_ctx_gap_1',
                            ]
                            if artifact_id
                        ],
                        output_id='out_text_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Reporter: assemble final presentation package, narrative and implementation notes.',
                        max_rounds=2,
                        stop_on_no_change=1,
                        options={'stage': 'presentation_finalize', 'agent': 'reporter', 'deep_research': True},
                    ),
                ]
            )
        elif deep_research:
            operations.extend(
                [
                    Operation(
                        id='op_1',
                        kind='generate_text',
                        inputs=[text_input_id] if text_input_id else [],
                        output_id='research_plan_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Researcher agent: decompose request and define evidence-oriented investigation plan.',
                        options={'stage': 'research_plan', 'agent': 'researcher', 'deep_research': True},
                    ),
                    Operation(
                        id='op_2',
                        kind='generate_text',
                        inputs=[artifact_id for artifact_id in [text_input_id, 'research_plan_1'] if artifact_id],
                        output_id='source_routing_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Researcher agent: route research components between internet and attached documents.',
                        options={'stage': 'source_routing', 'agent': 'researcher', 'deep_research': True},
                    ),
                    Operation(
                        id='op_3',
                        kind='retrieve_context',
                        inputs=[artifact_id for artifact_id in [text_input_id, 'research_plan_1', 'source_routing_1'] if artifact_id],
                        output_id='research_ctx_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Searcher agent: collect, deduplicate and normalize primary evidence from files and web.',
                        options={'stage': 'search_primary', 'agent': 'searcher', 'deep_research': True, 'top_k_chunks': 20},
                    ),
                    Operation(
                        id='op_4',
                        kind='generate_text',
                        inputs=[
                            artifact_id
                            for artifact_id in [text_input_id, 'research_plan_1', 'source_routing_1', 'research_ctx_1']
                            if artifact_id
                        ],
                        output_id='analysis_text_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Analyst agent: synthesize evidence by components and produce grounded findings.',
                        options={'stage': 'analysis', 'agent': 'analyst', 'deep_research': True},
                    ),
                    Operation(
                        id='op_5',
                        kind='critique_text',
                        inputs=['analysis_text_1', 'research_ctx_1', 'source_routing_1'],
                        output_id='validation_text_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Validator agent: score coverage and factual consistency, detect gaps and generate follow-up queries.',
                        options={'stage': 'validation', 'agent': 'reviewer', 'deep_research': True},
                    ),
                    Operation(
                        id='op_6',
                        kind='retrieve_context',
                        inputs=[
                            artifact_id
                            for artifact_id in [text_input_id, 'source_routing_1', 'validation_text_1']
                            if artifact_id
                        ],
                        output_id='research_ctx_gap_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Searcher agent: perform targeted gap-fill retrieval using validator feedback.',
                        options={'stage': 'gap_fill', 'agent': 'searcher', 'deep_research': True, 'top_k_chunks': 20},
                    ),
                    Operation(
                        id='op_7',
                        kind='generate_text',
                        inputs=[
                            artifact_id
                            for artifact_id in [text_input_id, 'analysis_text_1', 'validation_text_1', 'research_ctx_gap_1']
                            if artifact_id
                        ],
                        output_id='analysis_text_2',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Analyst agent: update component analysis after targeted gap-fill retrieval.',
                        options={'stage': 'analysis_refined', 'agent': 'analyst', 'deep_research': True},
                    ),
                    Operation(
                        id='op_8',
                        kind='generate_text',
                        inputs=[
                            artifact_id
                            for artifact_id in [
                                text_input_id,
                                'research_plan_1',
                                'source_routing_1',
                                'research_ctx_1',
                                'analysis_text_1',
                                'validation_text_1',
                                'research_ctx_gap_1',
                                'analysis_text_2',
                            ]
                            if artifact_id
                        ],
                        output_id='out_text_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Reporter agent: assemble the final evidence-bound answer with explicit limits.',
                        max_rounds=2,
                        stop_on_no_change=1,
                        options={'stage': 'report', 'agent': 'reporter', 'deep_research': True},
                    ),
                ]
            )
        elif use_critic:
            operations.extend(
                [
                    Operation(
                        id='op_1',
                        kind='generate_text',
                        inputs=[text_input_id] if text_input_id else [],
                        output_id='draft_text_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Create the initial draft response.',
                        options={'stage': 'draft'},
                    ),
                    Operation(
                        id='op_2',
                        kind='critique_text',
                        inputs=['draft_text_1'],
                        output_id='critique_text_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Critique the draft and list concrete improvements.',
                    ),
                    Operation(
                        id='op_3',
                        kind='generate_text',
                        inputs=[artifact_id for artifact_id in [text_input_id, 'draft_text_1', 'critique_text_1'] if artifact_id],
                        output_id='out_text_1',
                        required_capabilities=['text_reasoning'],
                        prompt=user_goal,
                        description='Apply critique and produce the final answer.',
                        max_rounds=2,
                        stop_on_no_change=1,
                        options={'stage': 'final'},
                    ),
                ]
            )
        else:
            operations.append(
                Operation(
                    id='op_1',
                    kind='generate_text',
                    inputs=[text_input_id] if text_input_id else [],
                    output_id='out_text_1',
                    required_capabilities=['text_reasoning'],
                    prompt=user_goal,
                    description='Respond to the user using the text context only.',
                )
            )
        output_artifact_ids = ['out_text_1']

    elif intent_mode == 'analyze_image':
        operations.append(
            Operation(
                id='op_1',
                kind='analyze_image',
                inputs=[image_input_id] if image_input_id else [],
                output_id='out_text_1',
                required_capabilities=['vision'],
                prompt=user_goal or 'Опиши содержимое изображения кратко и по существу.',
                description='Analyze the image and produce a textual summary.',
            )
        )
        output_artifact_ids = ['out_text_1']

    elif intent_mode == 'transcribe_audio':
        operations.append(
            Operation(
                id='op_1',
                kind='transcribe_audio',
                inputs=[audio_input_id] if audio_input_id else [],
                output_id='out_text_1',
                required_capabilities=['stt'],
                prompt=user_goal,
                description='Transcribe the audio into plain text.',
            )
        )
        output_artifact_ids = ['out_text_1']

    elif intent_mode == 'compose_text_with_audio_context':
        operations.extend(
            [
                Operation(
                    id='op_1',
                    kind='transcribe_audio',
                    inputs=[audio_input_id] if audio_input_id else [],
                    output_id='audio_ctx_1',
                    required_capabilities=['stt'],
                    prompt=user_goal,
                    description='Transcribe the audio before answering.',
                ),
                Operation(
                    id='op_2',
                    kind='generate_text',
                    inputs=[artifact_id for artifact_id in [text_input_id, 'audio_ctx_1'] if artifact_id],
                    output_id='out_text_1',
                    required_capabilities=['text_reasoning'],
                    prompt=user_goal,
                    description='Answer the user using both the request text and audio transcript.',
                ),
            ]
        )
        output_artifact_ids = ['out_text_1']

    else:
        operations.extend(
            [
                Operation(
                    id='op_1',
                    kind='analyze_image',
                    inputs=[image_input_id] if image_input_id else [],
                    output_id='image_ctx_1',
                    required_capabilities=['vision'],
                    prompt=user_goal or 'Опиши содержимое изображения кратко и по существу.',
                    description='Analyze the image and prepare a textual context block.',
                ),
                Operation(
                    id='op_2',
                    kind='generate_text',
                    inputs=[artifact_id for artifact_id in [text_input_id, 'image_ctx_1'] if artifact_id],
                    output_id='out_text_1',
                    required_capabilities=['text_reasoning'],
                    prompt=user_goal,
                    description='Answer the user using both the request text and image analysis.',
                ),
            ]
        )
        output_artifact_ids = ['out_text_1']

    plan = OrchestrationPlan(
        request_id=str(uuid.uuid4()),
        intent_mode=intent_mode,
        user_goal=user_goal,
        policy_mode=effective_policy_mode,
        input_artifacts=artifacts,
        operations=operations,
        output_artifact_ids=output_artifact_ids,
        metadata={
            'planner_mode': 'deterministic_v2',
            'preparse': preparse,
            'raw_user_goal': raw_user_goal,
            'resolved_user_goal': user_goal,
            'resolved_goal_from_history': bool(raw_user_goal and raw_user_goal.strip() != user_goal.strip()),
            'deep_research': deep_research,
            'presentation_generation': presentation_generation,
            'deep_research_pattern': 'researcher_router_searcher_analyst_validator_gapfill_reporter_v2'
            if deep_research
            else None,
            'presentation_pattern': 'planner_router_searcher_outline_writer_validator_gapfill_writer_finalize_v1'
            if presentation_generation
            else None,
            'critic_enabled': use_critic,
            'goal_complexity_score': _goal_complexity_score(raw_user_goal),
            'source_count': len(metadata.get('sources') or []),
            'file_count': len(metadata.get('files') or []),
            'policy_mode_requested': policy_mode,
            'policy_mode_effective': effective_policy_mode,
        },
    )

    return validate_plan(plan)
