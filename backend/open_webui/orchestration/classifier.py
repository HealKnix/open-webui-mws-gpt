from __future__ import annotations

import os
import re
import uuid
from typing import Any

from open_webui.models.files import Files
from open_webui.orchestration.schema import Artifact
from open_webui.storage.provider import Storage
from open_webui.utils.files import get_image_base64_from_file_id, get_image_base64_from_url
from open_webui.utils.misc import get_content_from_message, get_last_assistant_message, get_last_user_message


TRANSCRIPTION_HINTS = (
    'расшифр',
    'транскриб',
    'transcrib',
    'transcript',
    'transcription',
    'speech-to-text',
    'распознай',
    'распознать',
    'переведи в текст',
)

FOLLOWUP_REFERENCE_HINTS = (
    'на эту тему',
    'по этой теме',
    'на основе этого',
    'по этому',
    'по нему',
    'из этого',
    'на эту',
    'на это',
    'это',
    'эту',
    'данную тему',
    'ту же тему',
    'продолжи',
    'дополни',
    'раскрой',
    'теперь',
)

FOLLOWUP_ACTION_HINTS = (
    'презентац',
    'слайд',
    'ppt',
    'pptx',
    'deck',
    'отчет',
    'отчёт',
    'summary',
    'резюме',
    'план',
)


def _normalize_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text or '').strip()


def _truncate_text(text: str, max_chars: int) -> str:
    normalized = _normalize_ws(text)
    if len(normalized) <= max_chars:
        return normalized
    return f'{normalized[: max_chars - 3]}...'


def _extract_user_text_messages(messages: list[dict[str, Any]]) -> list[str]:
    user_messages: list[str] = []
    for message in messages:
        if message.get('role') != 'user':
            continue
        text = (get_content_from_message(message) or '').strip()
        if text:
            user_messages.append(text)
    return user_messages


def _is_contextual_followup(user_text: str) -> bool:
    lowered = _normalize_ws(user_text).lower()
    if not lowered:
        return False

    if any(hint in lowered for hint in FOLLOWUP_REFERENCE_HINTS):
        return True

    word_count = len(lowered.split())
    if word_count <= 16 and any(action in lowered for action in FOLLOWUP_ACTION_HINTS):
        if lowered.startswith(('теперь ', 'а теперь', 'давай ', 'сделай ', 'оформи ', 'продолжи ', 'дополни ')):
            return True

    return False


def resolve_user_goal(messages: list[dict[str, Any]]) -> str:
    """
    Resolve short follow-up prompts (e.g. "сделай презентацию на эту тему")
    against recent dialog context, so planner/classifier keep the original topic.
    """
    current_goal = (get_last_user_message(messages) or '').strip()
    if not current_goal:
        return ''

    user_messages = _extract_user_text_messages(messages)
    previous_user_goal = user_messages[-2].strip() if len(user_messages) >= 2 else ''

    if not previous_user_goal or not _is_contextual_followup(current_goal):
        return current_goal

    assistant_context = _truncate_text(get_last_assistant_message(messages) or '', 1800)
    previous_user_goal = _truncate_text(previous_user_goal, 1400)

    sections = [
        f'Текущий запрос пользователя:\n{current_goal}',
        f'Связанный предыдущий запрос пользователя:\n{previous_user_goal}',
    ]
    if assistant_context:
        sections.append(
            'Краткий контекст из предыдущего ответа ассистента '
            '(используй как фон, но приоритет у запроса пользователя):\n'
            f'{assistant_context}'
        )
    sections.append('Инструкция: выполни текущий запрос строго по теме предыдущего запроса.')
    return '\n\n'.join(sections)


def _content_type(file_item: dict[str, Any]) -> str:
    return (
        file_item.get('content_type')
        or file_item.get('meta', {}).get('content_type')
        or file_item.get('file', {}).get('meta', {}).get('content_type')
        or ''
    )


def _resolve_file_path(file_id: str | None) -> str | None:
    if not file_id:
        return None

    file = Files.get_file_by_id(file_id)
    if not file or not file.path:
        return None

    path = Storage.get_file(file.path)
    if path and os.path.isfile(path):
        return path
    return None


def _extract_file_artifacts(files: list[dict[str, Any]]) -> list[Artifact]:
    artifacts: list[Artifact] = []
    seen_images = set()
    seen_audio = set()

    for file_item in files:
        file_id = file_item.get('id')
        file_type = file_item.get('type', '')
        content_type = _content_type(file_item).lower()

        if file_type == 'image' or content_type.startswith('image/'):
            if file_id and file_id in seen_images:
                continue

            image_data = None
            if file_id:
                image_data = get_image_base64_from_file_id(file_id)
            if not image_data and file_item.get('url'):
                image_data = get_image_base64_from_url(file_item.get('url'))
            if image_data:
                artifacts.append(
                    Artifact(
                        id=f'inp_img_{uuid.uuid4().hex[:8]}',
                        type='image',
                        source='file',
                        file_id=file_id,
                        url=file_item.get('url'),
                        data=image_data,
                        mime_type=content_type or 'image/png',
                        metadata={'name': file_item.get('name') or file_item.get('filename')},
                    )
                )
                if file_id:
                    seen_images.add(file_id)

        elif file_type == 'audio' or content_type.startswith('audio/') or content_type.startswith('video/'):
            path = _resolve_file_path(file_id)
            if not path:
                continue
            if file_id and file_id in seen_audio:
                continue

            artifacts.append(
                Artifact(
                    id=f'inp_audio_{uuid.uuid4().hex[:8]}',
                    type='audio',
                    source='file',
                    file_id=file_id,
                    path=path,
                    mime_type=content_type or 'audio/wav',
                    metadata={'name': file_item.get('name') or file_item.get('filename')},
                )
            )
            if file_id:
                seen_audio.add(file_id)

    return artifacts


def _extract_message_image_artifacts(messages: list[dict[str, Any]]) -> list[Artifact]:
    artifacts: list[Artifact] = []
    seen_urls = set()

    for message in messages:
        if message.get('role') != 'user':
            continue

        content = message.get('content')
        if not isinstance(content, list):
            continue

        for item in content:
            if item.get('type') != 'image_url':
                continue

            image_url = item.get('image_url', {}).get('url')
            if not image_url or image_url in seen_urls:
                continue

            image_data = image_url if image_url.startswith('data:image/') else get_image_base64_from_url(image_url)
            if not image_data:
                continue

            artifacts.append(
                Artifact(
                    id=f'inp_img_{uuid.uuid4().hex[:8]}',
                    type='image',
                    source='message',
                    url=image_url,
                    data=image_data,
                    mime_type='image/png',
                )
            )
            seen_urls.add(image_url)

    return artifacts


def extract_input_artifacts(form_data: dict[str, Any]) -> list[Artifact]:
    messages = form_data.get('messages', []) or []
    metadata = form_data.get('metadata', {}) or {}
    files = metadata.get('files') or form_data.get('files') or []

    artifacts: list[Artifact] = []

    raw_user_goal = get_last_user_message(messages)
    user_goal = resolve_user_goal(messages)
    if user_goal:
        artifacts.append(
            Artifact(
                id='inp_text_1',
                type='text',
                source='user',
                text=user_goal,
                metadata={'resolved_from_history': bool(raw_user_goal and raw_user_goal.strip() != user_goal.strip())},
            )
        )

    artifacts.extend(_extract_file_artifacts(files))
    artifacts.extend(_extract_message_image_artifacts(messages))

    deduped: list[Artifact] = []
    seen_keys = set()
    for artifact in artifacts:
        key = (artifact.type, artifact.file_id, artifact.url, artifact.text)
        if key in seen_keys:
            continue
        deduped.append(artifact)
        seen_keys.add(key)

    return deduped


def detect_requested_output_modalities(user_goal: str) -> list[str]:
    goal = (user_goal or '').lower()
    output_modalities = ['text']

    if any(token in goal for token in ['изображен', 'картин', 'баннер', 'нарис', 'render', 'image']):
        output_modalities.append('image')

    if any(token in goal for token in ['озвуч', 'голос', 'audio', 'speech', 'tts']):
        output_modalities.append('audio')

    return list(dict.fromkeys(output_modalities))


def wants_transcription_only(user_goal: str) -> bool:
    goal = (user_goal or '').lower().strip()
    if goal == '':
        return True
    return any(token in goal for token in TRANSCRIPTION_HINTS)


def classify_intent(artifacts: list[Artifact], user_goal: str) -> str:
    has_image = any(artifact.type == 'image' for artifact in artifacts)
    has_audio = any(artifact.type == 'audio' for artifact in artifacts)

    if has_audio:
        return 'transcribe_audio' if wants_transcription_only(user_goal) else 'compose_text_with_audio_context'
    if has_image:
        return 'compose_text_with_image_context' if (user_goal or '').strip() else 'analyze_image'
    return 'analyze_text'


def build_preparse_summary(artifacts: list[Artifact], user_goal: str) -> dict[str, Any]:
    input_modalities = list(dict.fromkeys(artifact.type for artifact in artifacts))
    return {
        'input_modalities': input_modalities,
        'requested_output_modalities': detect_requested_output_modalities(user_goal),
        'hints': {
            'has_image': 'image' in input_modalities,
            'has_audio': 'audio' in input_modalities,
            'has_text': 'text' in input_modalities,
            'transcription_only': wants_transcription_only(user_goal),
        },
    }
