import asyncio
import json

import aiohttp
from fastapi import WebSocket, WebSocketDisconnect, status

from .auth import verify_ws_shared_key
from .config import Settings
from .container_manager import ContainerManager, ContainerState
from .logging_config import get_logger
from .policies import Policy

log = get_logger(__name__)


async def proxy_ws(
    ws: WebSocket,
    session_id: str,
    policy: Policy,
    settings: Settings,
    manager: ContainerManager,
    session: aiohttp.ClientSession,
) -> None:
    await ws.accept()

    # First-message auth from Open WebUI.
    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=10.0)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        await _safe_close(ws, 4001, "Auth timeout")
        return
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        await _safe_close(ws, 4001, "Invalid auth payload")
        return
    if payload.get("type") != "auth":
        await _safe_close(ws, 4001, "Expected auth message")
        return
    if not verify_ws_shared_key(payload.get("token", ""), settings):
        await _safe_close(ws, 4001, "Invalid token")
        return

    user_id = ws.query_params.get("user_id", "")
    import re

    if not user_id or not re.match(settings.user_id_pattern, user_id):
        await _safe_close(ws, 4001, "Missing or malformed user_id")
        return

    try:
        state: ContainerState = await manager.ensure(user_id, policy)
    except Exception as exc:
        log.warning("ws_ensure_failed", user_id=user_id, error=str(exc))
        await _safe_close(ws, 4500, "Failed to start container")
        return

    manager.mark_active(user_id)

    upstream_url = f"ws://{state.ip}:{state.port}/api/terminals/{session_id}"

    try:
        async with session.ws_connect(
            upstream_url,
            heartbeat=20.0,
            max_msg_size=0,
        ) as upstream:
            await upstream.send_str(
                json.dumps({"type": "auth", "token": state.internal_token})
            )

            stop = asyncio.Event()

            async def client_to_upstream() -> None:
                try:
                    while not stop.is_set():
                        msg = await ws.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        data_bytes = msg.get("bytes")
                        data_text = msg.get("text")
                        if data_bytes:
                            manager.mark_active(user_id)
                            await upstream.send_bytes(data_bytes)
                        elif data_text is not None:
                            manager.mark_active(user_id)
                            await upstream.send_str(data_text)
                except Exception as exc:
                    log.debug("ws_client_to_upstream_exit", error=str(exc))
                finally:
                    stop.set()

            async def upstream_to_client() -> None:
                try:
                    async for msg in upstream:
                        if msg.type == aiohttp.WSMsgType.BINARY:
                            manager.mark_active(user_id)
                            await ws.send_bytes(msg.data)
                        elif msg.type == aiohttp.WSMsgType.TEXT:
                            manager.mark_active(user_id)
                            await ws.send_text(msg.data)
                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            break
                        if stop.is_set():
                            break
                except Exception as exc:
                    log.debug("ws_upstream_to_client_exit", error=str(exc))
                finally:
                    stop.set()

            await asyncio.gather(
                client_to_upstream(),
                upstream_to_client(),
                return_exceptions=True,
            )
    except aiohttp.ClientError as exc:
        log.warning("ws_upstream_connect_failed", user_id=user_id, error=str(exc))
        await _safe_close(ws, 4502, "Upstream unreachable")
        return
    finally:
        await _safe_close(ws)


async def _safe_close(ws: WebSocket, code: int = status.WS_1000_NORMAL_CLOSURE, reason: str = "") -> None:
    try:
        await ws.close(code=code, reason=reason)
    except Exception:
        pass
