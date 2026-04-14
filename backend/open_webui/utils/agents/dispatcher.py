"""Dispatcher for per-model agent backends.

Reads ``model.params.agent_backend`` and routes to the concrete
implementation. Keeping the dispatch layer separate from the LangGraph
adapter lets us add other backends later without touching middleware.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def is_agent_backend_enabled(
    model: dict | None,
    metadata: dict | None = None,
) -> str | None:
    """Return the configured agent backend id or None.

    Checks (in order):
    1. ``metadata['params']['agent_backend']`` — populated in
       ``main.chat_completion`` from ``Models.get_model_by_id().params``.
       This is the most reliable source because the runtime
       ``request.app.state.MODELS[...]`` dict strips ``params`` for
       privacy reasons.
    2. ``model['params']['agent_backend']`` — in case a caller passes the
       un-stripped model dict directly.
    3. ``model['info']['params']['agent_backend']`` — the admin-configured
       variant, when ``info`` still carries params.
    4. DB fallback via ``Models.get_model_by_id(model_id).params`` so
       that late-stage callers can still discover the setting even if
       it wasn't propagated through metadata.
    """
    if metadata:
        meta_params = metadata.get('params') or {}
        backend = meta_params.get('agent_backend')
        if backend:
            return backend

    if not model:
        return None

    params = model.get('params') or {}
    backend = params.get('agent_backend')
    if backend:
        return backend

    info = model.get('info') or {}
    info_params = (info.get('params') if isinstance(info, dict) else None) or {}
    backend = info_params.get('agent_backend')
    if backend:
        return backend

    # Last-resort DB lookup — avoids a stale strip in MODELS state.
    model_id = model.get('id') if isinstance(model, dict) else None
    if model_id:
        try:
            from open_webui.models.models import Models

            record = Models.get_model_by_id(model_id)
            if record and record.params:
                db_params = record.params.model_dump()
                return db_params.get('agent_backend')
        except Exception:
            return None

    return None


async def run_agent_backend(
    backend: str,
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
    """Run the configured agent backend to completion.

    The backend is responsible for streaming AG UI events via
    ``event_emitter``. It must not return until the run is finished (or
    errored), because the caller uses the completion of this coroutine to
    flip ``message.done`` server-side.
    """
    if backend == 'langgraph':
        from open_webui.utils.agents.langgraph_adapter import run_langgraph_agent

        await run_langgraph_agent(
            request=request,
            form_data=form_data,
            tools_dict=tools_dict,
            event_emitter=event_emitter,
            event_caller=event_caller,
            metadata=metadata,
            model=model,
            user=user,
        )
        return

    log.warning('Unknown agent_backend %r — falling back to built-in loop', backend)
    raise ValueError(f'Unknown agent_backend: {backend}')
