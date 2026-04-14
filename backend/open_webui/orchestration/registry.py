from __future__ import annotations

import time
from typing import Any, Iterable
from urllib.parse import urlparse


MTS_ROUTER_MODEL_ID = 'mts-router'
MWS_HOSTNAME = 'api.gpt.mws.ru'


def is_mws_base_url(url: str | None) -> bool:
    if not url:
        return False
    return (urlparse(url).hostname or '').lower() == MWS_HOSTNAME


def _get_model_url(request, model: dict[str, Any]) -> str | None:
    url_idx = model.get('urlIdx')
    if url_idx is None:
        return None

    try:
        url_idx = int(url_idx)
    except (TypeError, ValueError):
        return None

    base_urls = list(getattr(request.app.state.config, 'OPENAI_API_BASE_URLS', []) or [])
    if 0 <= url_idx < len(base_urls):
        return base_urls[url_idx]
    return None


def infer_capabilities(model_id: str, existing: dict[str, Any] | None = None) -> dict[str, bool]:
    capabilities = dict(existing or {})
    lowered = model_id.lower()

    if any(pattern in lowered for pattern in ['-vl', 'qwen2.5-vl', 'qwen3-vl', 'cotype-pro-vl']):
        capabilities['vision'] = True
        capabilities.setdefault('file_upload', True)

    if 'whisper' in lowered:
        capabilities['stt'] = True
        capabilities.setdefault('file_upload', True)

    if 'image' in lowered:
        capabilities['image_generation'] = True

    if 'embedding' in lowered or lowered.startswith('bge-') or 'bge/' in lowered or 'bge-' in lowered:
        capabilities['embedding'] = True

    if 'coder' in lowered or 'kodify' in lowered or 'gpt-oss' in lowered:
        capabilities['coding'] = True

    if not any(capabilities.get(name) for name in ['stt', 'embedding', 'image_generation']):
        capabilities.setdefault('text_reasoning', True)
        capabilities.setdefault('structured_output', True)

    return capabilities


def _iter_models(models: Iterable[dict[str, Any]] | dict[str, dict[str, Any]] | None) -> list[dict[str, Any]]:
    if models is None:
        return []
    if isinstance(models, dict):
        return list(models.values())
    return list(models)


def get_mws_models(
    request,
    models: Iterable[dict[str, Any]] | dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    discovered_models = []
    source_models = _iter_models(models if models is not None else (request.app.state.MODELS or {}))

    for model in source_models:
        if model.get('orchestrator'):
            continue

        if model.get('owned_by') != 'openai':
            continue

        provider_url = _get_model_url(request, model)
        if not is_mws_base_url(provider_url):
            continue

        capabilities = infer_capabilities(model.get('id', ''), model.get('info', {}).get('meta', {}).get('capabilities'))

        model_copy = {
            **model,
            'provider_url': provider_url,
            'capabilities': capabilities,
        }
        discovered_models.append(model_copy)

    return discovered_models


def build_registry(request) -> dict[str, Any]:
    models = get_mws_models(request)
    return {
        'provider': 'mws',
        'models': models,
        'by_id': {model['id']: model for model in models},
    }


def has_mws_models(request, models: Iterable[dict[str, Any]] | dict[str, dict[str, Any]] | None = None) -> bool:
    return len(get_mws_models(request, models=models)) > 0


def build_router_virtual_model() -> dict[str, Any]:
    return {
        'id': MTS_ROUTER_MODEL_ID,
        'name': 'MTS Router (Preview)',
        'object': 'model',
        'created': int(time.time()),
        'owned_by': 'orchestrator',
        'connection_type': 'external',
        'orchestrator': True,
        'info': {
            'meta': {
                'description': (
                    'Preview orchestration model that routes text, image, and audio inputs '
                    'across MWS GPT models with structured planning.'
                ),
                'capabilities': {
                    'vision': True,
                    'file_upload': True,
                    'file_context': True,
                    'web_search': True,
                    'deep_research': True,
                    'presentation_generation': True,
                    'builtin_tools': True,
                    'usage': True,
                    'status_updates': True,
                },
                # Keep Deep Research visible/toggled by default in current Open WebUI builds.
                'defaultFeatureIds': ['web_search', 'deep_research'],
                'tags': [{'name': 'preview'}, {'name': 'mws'}],
            }
        },
    }
