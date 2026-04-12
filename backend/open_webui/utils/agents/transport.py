"""AG UI event transport over Open WebUI's Socket.IO channel.

Reuses the existing ``__event_emitter__`` callable produced by
``open_webui.socket.main.get_event_emitter`` — we only introduce a new
event ``type`` (``chat:ag_ui``) whose ``data`` payload carries a single
AG UI event serialised to a dict.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

AG_UI_EVENT_TYPE = 'chat:ag_ui'


def _serialize_event(event: Any) -> dict:
    """Convert a pydantic AG UI event to a plain dict.

    Supports both ``ag_ui.core.events`` pydantic models (``model_dump``)
    and already-serialised dicts. Uses ``by_alias=True`` so we emit the
    camelCase field names defined by the AG UI spec.
    """
    if isinstance(event, dict):
        return event
    if hasattr(event, 'model_dump'):
        return event.model_dump(by_alias=True, exclude_none=True)
    raise TypeError(f'Unsupported AG UI event type: {type(event)!r}')


async def emit_ag_ui(event_emitter, event: Any) -> None:
    """Emit a single AG UI event via the Open WebUI event emitter."""
    try:
        payload = _serialize_event(event)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception('Failed to serialize AG UI event: %s', exc)
        return

    await event_emitter(
        {
            'type': AG_UI_EVENT_TYPE,
            'data': payload,
        }
    )


async def request_ag_ui_input(event_caller, event: Any, timeout: float | None = None):
    """RPC-style human-in-the-loop request.

    Sends an AG UI event to the client using ``event_caller`` (which maps
    to ``sio.call`` in ``socket/main.py``) and returns the client reply.
    """
    payload = _serialize_event(event)
    call = {'type': AG_UI_EVENT_TYPE, 'data': payload}
    if timeout is not None:
        return await event_caller(call, timeout=timeout)  # type: ignore[call-arg]
    return await event_caller(call)
