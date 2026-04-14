from __future__ import annotations

import re
from typing import Any

from open_webui.orchestration.schema import ModelRoleAssignment, PolicyMode


ROLE_CAPABILITY_MAP = {
    'planner': 'text_reasoning',
    'reasoner': 'text_reasoning',
    'researcher': 'text_reasoning',
    'searcher': 'text_reasoning',
    'analyst': 'text_reasoning',
    'reporter': 'text_reasoning',
    'retriever': 'text_reasoning',
    'reviewer': 'text_reasoning',
    'vision': 'vision',
    'stt': 'stt',
    'embedding': 'embedding',
    'coder': 'coding',
    'image_generation': 'image_generation',
}


POLICY_ROLE_PRIORITIES: dict[str, dict[str, list[str]]] = {
    'fast': {
        'planner': ['mws-gpt-alpha', 'qwen3-32b', 'T-pro-it-1.0', 'qwen2.5-72b-instruct'],
        'researcher': ['mws-gpt-alpha', 'qwen2.5-72b-instruct', 'qwen3-32b', 'glm-4.6-357b'],
        'reasoner': [
            'qwen3-32b',
            'mws-gpt-alpha',
            'qwen2.5-72b-instruct',
            'QwQ-32B',
            'deepseek-r1-distill-qwen-32b',
            'llama-3.3-70b-instruct',
            'glm-4.6-357b',
        ],
        'analyst': ['qwen2.5-72b-instruct', 'mws-gpt-alpha', 'qwen3-32b', 'glm-4.6-357b'],
        'searcher': ['qwen3-32b', 'mws-gpt-alpha', 'qwen2.5-72b-instruct', 'glm-4.6-357b'],
        'reporter': ['qwen2.5-72b-instruct', 'glm-4.6-357b', 'mws-gpt-alpha', 'qwen3-32b'],
        'retriever': ['qwen3-32b', 'mws-gpt-alpha', 'qwen2.5-72b-instruct', 'glm-4.6-357b'],
        'reviewer': ['qwen2.5-72b-instruct', 'glm-4.6-357b', 'mws-gpt-alpha', 'qwen3-32b'],
        'vision': ['qwen2.5-vl', 'qwen3-vl-30b-a3b-instruct', 'cotype-pro-vl-32b', 'qwen2.5-vl-72b'],
        'stt': ['whisper-turbo-local', 'whisper-medium'],
        'embedding': ['bge-m3', 'qwen3-embedding-8b', 'BAAI/bge-multilingual-gemma2'],
        'coder': ['gpt-oss-20b', 'qwen3-coder-480b-a35b', 'gpt-oss-120b'],
        'image_generation': ['qwen-image-lightning', 'qwen-image'],
    },
    'balanced': {
        'planner': ['mws-gpt-alpha', 'qwen2.5-72b-instruct', 'glm-4.6-357b', 'qwen3-32b'],
        'researcher': ['qwen2.5-72b-instruct', 'glm-4.6-357b', 'mws-gpt-alpha', 'qwen3-32b'],
        'reasoner': [
            'qwen2.5-72b-instruct',
            'glm-4.6-357b',
            'kimi-k2-instruct',
            'QwQ-32B',
            'llama-3.3-70b-instruct',
            'mws-gpt-alpha',
            'qwen3-32b',
        ],
        'analyst': ['qwen2.5-72b-instruct', 'glm-4.6-357b', 'kimi-k2-instruct', 'mws-gpt-alpha'],
        'searcher': ['qwen2.5-72b-instruct', 'glm-4.6-357b', 'mws-gpt-alpha', 'qwen3-32b'],
        'reporter': ['glm-4.6-357b', 'qwen2.5-72b-instruct', 'kimi-k2-instruct', 'QwQ-32B'],
        'retriever': ['qwen2.5-72b-instruct', 'glm-4.6-357b', 'mws-gpt-alpha', 'qwen3-32b'],
        'reviewer': ['glm-4.6-357b', 'qwen2.5-72b-instruct', 'kimi-k2-instruct', 'QwQ-32B'],
        'vision': ['qwen2.5-vl-72b', 'qwen3-vl-30b-a3b-instruct', 'cotype-pro-vl-32b'],
        'stt': ['whisper-medium', 'whisper-turbo-local'],
        'embedding': ['bge-m3', 'qwen3-embedding-8b', 'BAAI/bge-multilingual-gemma2'],
        'coder': ['qwen3-coder-480b-a35b', 'gpt-oss-120b', 'gpt-oss-20b'],
        'image_generation': ['qwen-image', 'qwen-image-lightning'],
    },
    'quality': {
        'planner': ['glm-4.6-357b', 'qwen2.5-72b-instruct', 'mws-gpt-alpha'],
        'researcher': ['Qwen3-235B-A22B-Instruct-2507-FP8', 'glm-4.6-357b', 'qwen2.5-72b-instruct'],
        'reasoner': [
            'Qwen3-235B-A22B-Instruct-2507-FP8',
            'glm-4.6-357b',
            'kimi-k2-instruct',
            'qwen2.5-72b-instruct',
            'llama-3.3-70b-instruct',
            'QwQ-32B',
        ],
        'analyst': ['Qwen3-235B-A22B-Instruct-2507-FP8', 'glm-4.6-357b', 'kimi-k2-instruct', 'qwen2.5-72b-instruct'],
        'searcher': ['glm-4.6-357b', 'Qwen3-235B-A22B-Instruct-2507-FP8', 'qwen2.5-72b-instruct'],
        'reporter': ['Qwen3-235B-A22B-Instruct-2507-FP8', 'glm-4.6-357b', 'kimi-k2-instruct', 'qwen2.5-72b-instruct'],
        'retriever': ['glm-4.6-357b', 'Qwen3-235B-A22B-Instruct-2507-FP8', 'qwen2.5-72b-instruct'],
        'reviewer': ['Qwen3-235B-A22B-Instruct-2507-FP8', 'glm-4.6-357b', 'kimi-k2-instruct', 'QwQ-32B'],
        'vision': ['qwen2.5-vl-72b', 'qwen3-vl-30b-a3b-instruct', 'cotype-pro-vl-32b'],
        'stt': ['whisper-medium', 'whisper-turbo-local'],
        'embedding': ['bge-m3', 'qwen3-embedding-8b', 'BAAI/bge-multilingual-gemma2'],
        'coder': ['qwen3-coder-480b-a35b', 'gpt-oss-120b', 'gpt-oss-20b'],
        'image_generation': ['qwen-image', 'qwen-image-lightning'],
    },
}


OPERATION_ROLE_MAP = {
    'generate_text': 'reasoner',
    'analyze_image': 'vision',
    'transcribe_audio': 'stt',
    'retrieve_context': 'retriever',
    'critique_text': 'reviewer',
}


CODING_HINTS = (
    'код',
    'code',
    'python',
    'javascript',
    'typescript',
    'node',
    'sql',
    'bash',
    'regex',
    'stacktrace',
    'traceback',
    'bug',
    'debug',
    'refactor',
    'алгоритм',
    'программ',
)

STRUCTURED_OUTPUT_HINTS = (
    'json',
    'schema',
    'strict',
    'структур',
    'таблиц',
    'yaml',
    'xml',
)

COMPLEXITY_HINTS = (
    'step-by-step',
    'step by step',
    'пошаг',
    'деталь',
    'глубок',
    'архитект',
    'оркестр',
    'pipeline',
    'multi-step',
    'reason',
    'докажи',
    'оптимиз',
    'trade-off',
    'компромисс',
)

SPEED_HINTS = ('быстро', 'кратко', 'коротко', 'short', 'latency', 'fast')
QUALITY_HINTS = ('подробно', 'максимально', 'глубоко', 'thorough', 'quality', 'точно')


DEFAULT_MODEL_TRAITS = {
    'quality': 3,
    'speed': 3,
    'reasoning': 3,
    'coding': 1,
    'structured': 3,
    'reliability': 3,
    'context': 3,
    'vision': 3,
    'stt_quality': 3,
    'image_quality': 3,
}


MODEL_TRAIT_OVERRIDES: dict[str, dict[str, int]] = {
    'Qwen3-235B-A22B-Instruct-2507-FP8': {
        'quality': 5,
        'speed': 1,
        'reasoning': 5,
        'coding': 3,
        'structured': 5,
        'reliability': 4,
        'context': 5,
    },
    'glm-4.6-357b': {
        'quality': 5,
        'speed': 2,
        'reasoning': 5,
        'coding': 3,
        'structured': 4,
        'reliability': 4,
        'context': 5,
    },
    'kimi-k2-instruct': {
        'quality': 4,
        'speed': 2,
        'reasoning': 4,
        'coding': 3,
        'structured': 4,
        'reliability': 3,
        'context': 4,
    },
    'qwen2.5-72b-instruct': {
        'quality': 4,
        'speed': 3,
        'reasoning': 4,
        'coding': 3,
        'structured': 4,
        'reliability': 4,
        'context': 4,
    },
    'qwen3-32b': {
        'quality': 3,
        'speed': 4,
        'reasoning': 3,
        'coding': 2,
        'structured': 3,
        'reliability': 3,
        'context': 3,
    },
    'mws-gpt-alpha': {
        'quality': 3,
        'speed': 4,
        'reasoning': 3,
        'coding': 2,
        'structured': 4,
        'reliability': 4,
        'context': 3,
    },
    'T-pro-it-1.0': {
        'quality': 2,
        'speed': 5,
        'reasoning': 2,
        'coding': 1,
        'structured': 3,
        'reliability': 3,
        'context': 2,
    },
    'llama-3.1-8b-instruct': {
        'quality': 2,
        'speed': 5,
        'reasoning': 2,
        'coding': 1,
        'structured': 2,
        'reliability': 3,
        'context': 2,
    },
    'llama-3.3-70b-instruct': {
        'quality': 4,
        'speed': 3,
        'reasoning': 4,
        'coding': 3,
        'structured': 3,
        'reliability': 4,
        'context': 4,
    },
    'deepseek-r1-distill-qwen-32b': {
        'quality': 4,
        'speed': 3,
        'reasoning': 4,
        'coding': 3,
        'structured': 4,
        'reliability': 3,
        'context': 3,
    },
    'QwQ-32B': {
        'quality': 4,
        'speed': 3,
        'reasoning': 4,
        'coding': 3,
        'structured': 4,
        'reliability': 3,
        'context': 3,
    },
    'gpt-oss-20b': {
        'quality': 3,
        'speed': 4,
        'reasoning': 3,
        'coding': 4,
        'structured': 3,
        'reliability': 3,
        'context': 3,
    },
    'gpt-oss-120b': {
        'quality': 4,
        'speed': 2,
        'reasoning': 4,
        'coding': 4,
        'structured': 4,
        'reliability': 4,
        'context': 4,
    },
    'qwen3-coder-480b-a35b': {
        'quality': 5,
        'speed': 1,
        'reasoning': 4,
        'coding': 5,
        'structured': 4,
        'reliability': 4,
        'context': 5,
    },
    'gemma-3-27b-it': {
        'quality': 3,
        'speed': 4,
        'reasoning': 3,
        'coding': 2,
        'structured': 3,
        'reliability': 3,
        'context': 3,
    },
    'qwen2.5-vl': {
        'quality': 3,
        'speed': 4,
        'reasoning': 3,
        'vision': 3,
        'reliability': 3,
    },
    'qwen3-vl-30b-a3b-instruct': {
        'quality': 4,
        'speed': 3,
        'reasoning': 4,
        'vision': 4,
        'reliability': 4,
    },
    'qwen2.5-vl-72b': {
        'quality': 5,
        'speed': 2,
        'reasoning': 4,
        'vision': 5,
        'reliability': 4,
    },
    'cotype-pro-vl-32b': {
        'quality': 4,
        'speed': 3,
        'reasoning': 4,
        'vision': 4,
        'reliability': 4,
    },
    'whisper-medium': {
        'quality': 4,
        'speed': 2,
        'stt_quality': 5,
        'reliability': 4,
    },
    'whisper-turbo-local': {
        'quality': 3,
        'speed': 5,
        'stt_quality': 3,
        'reliability': 3,
    },
    'qwen-image': {
        'quality': 5,
        'speed': 2,
        'image_quality': 5,
        'reliability': 4,
    },
    'qwen-image-lightning': {
        'quality': 3,
        'speed': 5,
        'image_quality': 3,
        'reliability': 3,
    },
    'bge-m3': {
        'quality': 5,
        'speed': 3,
        'reliability': 4,
    },
    'qwen3-embedding-8b': {
        'quality': 4,
        'speed': 4,
        'reliability': 3,
    },
    'BAAI/bge-multilingual-gemma2': {
        'quality': 4,
        'speed': 3,
        'reliability': 4,
    },
}

MODEL_TRAIT_OVERRIDES_LOWER = {model_id.lower(): traits for model_id, traits in MODEL_TRAIT_OVERRIDES.items()}


def _clamp(value: int, min_value: int = 1, max_value: int = 5) -> int:
    return max(min_value, min(max_value, value))


def _is_enabled(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _infer_model_traits(model_id: str) -> dict[str, int]:
    lowered = model_id.lower()
    traits = dict(DEFAULT_MODEL_TRAITS)
    traits.update(MODEL_TRAIT_OVERRIDES_LOWER.get(lowered, {}))

    size_match = re.search(r'(\d{1,4})b', lowered)
    if size_match:
        size = int(size_match.group(1))
        if size >= 200:
            traits['quality'] += 2
            traits['reasoning'] += 2
            traits['context'] += 2
            traits['speed'] -= 2
        elif size >= 70:
            traits['quality'] += 1
            traits['reasoning'] += 1
            traits['context'] += 1
            traits['speed'] -= 1
        elif size <= 8:
            traits['speed'] += 2
            traits['quality'] -= 1
            traits['reasoning'] -= 1
            traits['context'] -= 1

    if any(tag in lowered for tag in ['turbo', 'lightning']):
        traits['speed'] += 2
        traits['quality'] -= 1

    if 'vl' in lowered:
        traits['vision'] += 1

    if 'whisper' in lowered:
        traits['stt_quality'] += 1

    if 'image' in lowered:
        traits['image_quality'] += 1

    if 'coder' in lowered or 'gpt-oss' in lowered:
        traits['coding'] += 1

    if 'bge' in lowered or 'embedding' in lowered:
        traits['quality'] += 1

    for key in ['quality', 'speed', 'reasoning', 'structured', 'reliability', 'context', 'vision', 'stt_quality', 'image_quality']:
        traits[key] = _clamp(traits[key])
    traits['coding'] = _clamp(traits['coding'], min_value=0, max_value=5)

    return traits


def _build_task_profile(plan: Any | None, operation: Any | None, operation_kind: str) -> dict[str, Any]:
    user_goal = (getattr(plan, 'user_goal', None) or '').strip()
    operation_prompt = (getattr(operation, 'prompt', None) or '').strip()
    combined = '\n'.join([part for part in [user_goal, operation_prompt] if part]).strip()
    lowered = combined.lower()

    word_count = len([token for token in re.split(r'\s+', combined) if token]) if combined else 0
    inputs = list(getattr(operation, 'inputs', []) or [])
    operation_count = len(getattr(plan, 'operations', []) or [])
    operation_options = dict(getattr(operation, 'options', {}) or {})

    has_context_artifacts = any(
        input_id.startswith('image_ctx_') or input_id.startswith('audio_ctx_') for input_id in inputs if isinstance(input_id, str)
    )
    is_multimodal_context = has_context_artifacts or len(inputs) > 1

    is_coding_task = any(token in lowered for token in CODING_HINTS)
    needs_structured_output = any(token in lowered for token in STRUCTURED_OUTPUT_HINTS)
    speed_priority = any(token in lowered for token in SPEED_HINTS)
    quality_priority = any(token in lowered for token in QUALITY_HINTS)
    has_deep_research = _is_enabled(operation_options.get('deep_research'))
    stage = str(operation_options.get('stage') or '').strip().lower()
    is_presentation_stage = stage.startswith('presentation_')
    preferred_agent_role = str(operation_options.get('agent') or '').strip().lower() or None
    if preferred_agent_role and preferred_agent_role not in ROLE_CAPABILITY_MAP:
        preferred_agent_role = None

    if is_presentation_stage:
        # Presentation pipeline benefits from higher-quality/structured models by default.
        needs_structured_output = True
        quality_priority = True
        speed_priority = False

    score = 0
    if word_count > 40:
        score += 1
    if word_count > 120:
        score += 2
    if word_count > 240:
        score += 2
    if any(token in lowered for token in COMPLEXITY_HINTS):
        score += 2
    if is_coding_task:
        score += 2
    if needs_structured_output:
        score += 1
    if operation_count > 1:
        score += 1
    if is_multimodal_context:
        score += 1
    if operation_kind in ['analyze_image', 'transcribe_audio']:
        score += 1
    if operation_kind in ['retrieve_context', 'critique_text']:
        score += 1
    if has_deep_research:
        score += 2
    if speed_priority:
        score -= 1
    if quality_priority:
        score += 1

    if score <= 2:
        complexity = 'low'
    elif score <= 5:
        complexity = 'medium'
    elif score <= 8:
        complexity = 'high'
    else:
        complexity = 'expert'

    return {
        'complexity': complexity,
        'score': score,
        'is_coding_task': is_coding_task,
        'needs_structured_output': needs_structured_output,
        'is_multimodal_context': is_multimodal_context,
        'speed_priority': speed_priority,
        'quality_priority': quality_priority,
        'has_deep_research': has_deep_research,
        'is_presentation_stage': is_presentation_stage,
        'preferred_agent_role': preferred_agent_role,
    }


def _resolve_role(operation_kind: str, profile: dict[str, Any]) -> str:
    preferred_role = profile.get('preferred_agent_role')
    if preferred_role in ROLE_CAPABILITY_MAP:
        return preferred_role

    if operation_kind == 'retrieve_context':
        return 'retriever'
    if operation_kind == 'critique_text':
        return 'coder' if profile.get('is_coding_task') else 'reviewer'
    if operation_kind == 'generate_text' and profile.get('is_coding_task'):
        return 'coder'
    return OPERATION_ROLE_MAP.get(operation_kind, 'reasoner')


def _target_quality_speed(policy_mode: PolicyMode, profile: dict[str, Any]) -> tuple[int, int]:
    if policy_mode == 'fast':
        target_quality, target_speed = 2, 5
    elif policy_mode == 'quality':
        target_quality, target_speed = 5, 2
    else:
        target_quality, target_speed = 3, 3

    complexity = profile.get('complexity')
    if complexity == 'medium':
        target_quality += 1
    elif complexity == 'high':
        target_quality += 2
        target_speed -= 1
    elif complexity == 'expert':
        target_quality += 2
        target_speed -= 2

    if profile.get('speed_priority'):
        target_speed += 1
        target_quality -= 1
    if profile.get('quality_priority'):
        target_quality += 1
    if profile.get('has_deep_research'):
        target_quality += 1
        target_speed -= 1

    return _clamp(target_quality), _clamp(target_speed)


def _candidate_ids_for_role(registry: dict[str, Any], role: str) -> list[str]:
    capability = ROLE_CAPABILITY_MAP.get(role)
    if not capability:
        return []

    candidates = [
        model['id']
        for model in registry.get('models', [])
        if (model.get('capabilities') or {}).get(capability)
    ]
    if candidates:
        return candidates

    # Last-resort fallback for text roles if capability tags are incomplete.
    if role in {'planner', 'reasoner', 'researcher', 'searcher', 'analyst', 'reporter', 'coder', 'reviewer', 'retriever'}:
        text_candidates = [
            model['id']
            for model in registry.get('models', [])
            if (model.get('capabilities') or {}).get('text_reasoning')
        ]
        if text_candidates:
            return text_candidates

    return [model['id'] for model in registry.get('models', [])]


def _score_candidate_model(
    model_id: str,
    role: str,
    policy_mode: PolicyMode,
    preferred_rank: int | None,
    profile: dict[str, Any],
) -> int:
    traits = _infer_model_traits(model_id)
    target_quality, target_speed = _target_quality_speed(policy_mode, profile)

    score = 0
    if preferred_rank is not None:
        score += max(0, 28 - preferred_rank * 4)
    else:
        score += 6

    quality_fit = 5 - abs(traits['quality'] - target_quality)
    speed_fit = 5 - abs(traits['speed'] - target_speed)
    score += quality_fit * 6
    score += speed_fit * 5
    score += traits['reliability'] * 2

    if role in {'planner', 'reasoner', 'researcher', 'searcher', 'analyst', 'reporter', 'coder', 'reviewer', 'retriever'}:
        score += traits['reasoning'] * 3
        score += traits['structured']
        if profile.get('complexity') in {'high', 'expert'}:
            score += traits['context'] * 2
        if profile.get('is_multimodal_context'):
            score += traits['reasoning']
        if profile.get('has_deep_research'):
            score += traits['context'] * 2
            score += traits['reliability'] * 2

    if role == 'coder':
        score += traits['coding'] * 7
        if traits['coding'] <= 1:
            score -= 10

    if role in {'reviewer', 'reporter'}:
        score += traits['reliability'] * 4
        score += traits['structured'] * 3

    if role in {'retriever', 'searcher'}:
        score += traits['reliability'] * 3
        score += traits['context'] * 3
        score += traits['speed'] * 2

    if role == 'researcher':
        score += traits['reasoning'] * 2
        score += traits['context'] * 3
        score += traits['reliability'] * 2

    if role == 'analyst':
        score += traits['reasoning'] * 3
        score += traits['context'] * 2
        score += traits['structured'] * 2

    if role == 'vision':
        score += traits['vision'] * 6

    if role == 'stt':
        score += traits['stt_quality'] * 6

    if role == 'image_generation':
        score += traits['image_quality'] * 6

    if profile.get('needs_structured_output'):
        score += traits['structured'] * 2

    return score


def select_role_assignment(
    registry: dict[str, Any],
    role: str,
    policy_mode: PolicyMode = 'balanced',
    profile: dict[str, Any] | None = None,
) -> ModelRoleAssignment:
    profile = profile or {}
    preferred = POLICY_ROLE_PRIORITIES.get(policy_mode, POLICY_ROLE_PRIORITIES['balanced']).get(role, [])
    available_ids = registry.get('by_id', {})

    candidates = [model_id for model_id in _candidate_ids_for_role(registry, role) if model_id in available_ids]

    # Keep explicit policy preferences in pool even if capability tagging is incomplete.
    for model_id in preferred:
        if model_id in available_ids and model_id not in candidates:
            candidates.append(model_id)

    if not candidates:
        ordered = [model_id for model_id in preferred if model_id in available_ids]
        primary = ordered[0] if ordered else None
        fallbacks = ordered[1:] if len(ordered) > 1 else []
        return ModelRoleAssignment(role=role, primary=primary, fallbacks=fallbacks)

    preferred_rank = {model_id: idx for idx, model_id in enumerate(preferred)}
    model_scores = {
        model_id: _score_candidate_model(
            model_id=model_id,
            role=role,
            policy_mode=policy_mode,
            preferred_rank=preferred_rank.get(model_id),
            profile=profile,
        )
        for model_id in candidates
    }

    ordered = sorted(
        candidates,
        key=lambda model_id: (
            model_scores[model_id],
            -preferred_rank.get(model_id, 10_000),
            model_id,
        ),
        reverse=True,
    )

    deduped_ordered = []
    seen = set()
    for model_id in ordered:
        if model_id in seen:
            continue
        deduped_ordered.append(model_id)
        seen.add(model_id)

    primary = deduped_ordered[0] if deduped_ordered else None
    fallbacks = deduped_ordered[1:] if len(deduped_ordered) > 1 else []
    return ModelRoleAssignment(role=role, primary=primary, fallbacks=fallbacks)


def select_operation_assignment(
    registry: dict[str, Any],
    operation_kind: str,
    policy_mode: PolicyMode = 'balanced',
    plan: Any | None = None,
    operation: Any | None = None,
) -> ModelRoleAssignment:
    profile = _build_task_profile(plan, operation, operation_kind)
    role = _resolve_role(operation_kind, profile)
    return select_role_assignment(registry, role, policy_mode, profile=profile)
