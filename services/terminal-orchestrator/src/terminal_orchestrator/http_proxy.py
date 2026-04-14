import posixpath
from urllib.parse import unquote

import aiohttp
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from .container_manager import ContainerManager, ContainerState
from .logging_config import get_logger
from .policies import Policy

log = get_logger(__name__)

STREAMING_CONTENT_TYPES = (
    "application/octet-stream",
    "image/",
    "application/pdf",
    "text/event-stream",
)

STRIPPED_REQUEST_HEADERS = frozenset(
    (
        "host",
        "content-length",
        "connection",
        "transfer-encoding",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "upgrade",
        "authorization",
        "x-user-id",
    )
)

STRIPPED_RESPONSE_HEADERS = frozenset(
    (
        "transfer-encoding",
        "connection",
        "content-encoding",
        "content-length",
    )
)


def sanitize_path(path: str) -> str | None:
    decoded = unquote(path)
    had_trailing_slash = decoded.endswith("/")
    normalized = posixpath.normpath(decoded)
    cleaned = normalized.lstrip("/")
    if cleaned.startswith("..") or cleaned == ".":
        return None
    if had_trailing_slash and cleaned and not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned


async def proxy_http(
    request: Request,
    user_id: str,
    policy: Policy,
    raw_path: str,
    manager: ContainerManager,
    session: aiohttp.ClientSession,
) -> Response:
    safe_path = sanitize_path(raw_path)
    if safe_path is None:
        raise HTTPException(status_code=400, detail="Invalid path")

    state: ContainerState = await manager.ensure(user_id, policy)
    manager.mark_active(user_id)

    target = f"http://{state.ip}:{state.port}/{safe_path}"
    if request.url.query:
        target += f"?{request.url.query}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in STRIPPED_REQUEST_HEADERS
    }
    headers["Authorization"] = f"Bearer {state.internal_token}"

    async def body_iter():
        async for chunk in request.stream():
            if chunk:
                yield chunk

    method = request.method.upper()
    data = None
    if method not in ("GET", "HEAD", "OPTIONS"):
        data = body_iter()

    try:
        upstream = await session.request(
            method=method,
            url=target,
            headers=headers,
            data=data,
        )
    except aiohttp.ClientError as exc:
        log.warning("upstream_http_error", user_id=user_id, error=str(exc))
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}") from exc

    filtered_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in STRIPPED_RESPONSE_HEADERS
    }

    async def cleanup() -> None:
        manager.mark_active(user_id)
        await upstream.release()

    return StreamingResponse(
        content=upstream.content.iter_any(),
        status_code=upstream.status,
        headers=filtered_headers,
        background=BackgroundTask(cleanup),
    )
