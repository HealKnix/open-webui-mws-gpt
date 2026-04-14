from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

import aiohttp
from fastapi import HTTPException, Request, status

from open_webui.orchestration.registry import MWS_HOSTNAME, is_mws_base_url


def resolve_mws_connection(request: Request) -> tuple[str, str]:
    base_urls = list(getattr(request.app.state.config, 'OPENAI_API_BASE_URLS', []) or [])
    keys = list(getattr(request.app.state.config, 'OPENAI_API_KEYS', []) or [])

    for index, base_url in enumerate(base_urls):
        if is_mws_base_url(base_url):
            key = keys[index] if index < len(keys) else ''
            if key:
                return base_url.rstrip('/'), key

    if base_urls and keys:
        return str(base_urls[0]).rstrip('/'), keys[0]

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f'MWS connection is not configured (expected provider host {MWS_HOSTNAME}).',
    )


async def _parse_json_response(response: aiohttp.ClientResponse) -> dict[str, Any]:
    try:
        return await response.json()
    except Exception:
        body = await response.text()
        raise HTTPException(
            status_code=response.status,
            detail=body or 'Unexpected response from MWS.',
        )


async def create_chat_completion(
    request: Request,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0,
    max_tokens: int | None = None,
    extra_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_url, api_key = resolve_mws_connection(request)
    payload: dict[str, Any] = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'stream': False,
    }
    if max_tokens is not None:
        payload['max_tokens'] = max_tokens
    if extra_body:
        payload.update(extra_body)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(f'{base_url}/chat/completions', json=payload, headers=headers) as response:
            data = await _parse_json_response(response)
            if response.status >= 400:
                detail = data.get('error') if isinstance(data, dict) else data
                raise HTTPException(status_code=response.status, detail=detail or 'MWS chat completion failed.')
            return data


async def create_text_response(
    request: Request,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0,
    max_tokens: int | None = None,
    extra_body: dict[str, Any] | None = None,
) -> str:
    data = await create_chat_completion(
        request=request,
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_body=extra_body,
    )

    try:
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='MWS chat completion returned an unexpected payload.',
        )


async def transcribe_audio(
    request: Request,
    model: str,
    file_path: str,
    language: str | None = None,
) -> str:
    base_url, api_key = resolve_mws_connection(request)
    headers = {
        'Authorization': f'Bearer {api_key}',
    }

    resolved = Path(file_path)
    if not resolved.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Audio file not found: {file_path}',
        )

    mime_type = mimetypes.guess_type(resolved.name)[0] or 'audio/wav'
    timeout = aiohttp.ClientTimeout(total=300)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        with resolved.open('rb') as file_handle:
            form = aiohttp.FormData()
            form.add_field('model', model)
            if language:
                form.add_field('language', language)
            form.add_field('file', file_handle, filename=resolved.name, content_type=mime_type)

            async with session.post(f'{base_url}/audio/transcriptions', data=form, headers=headers) as response:
                data = await _parse_json_response(response)
                if response.status >= 400:
                    detail = data.get('error') if isinstance(data, dict) else data
                    raise HTTPException(status_code=response.status, detail=detail or 'MWS transcription failed.')

    text = data.get('text') if isinstance(data, dict) else None
    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='MWS transcription returned an empty payload.',
        )
    return text
