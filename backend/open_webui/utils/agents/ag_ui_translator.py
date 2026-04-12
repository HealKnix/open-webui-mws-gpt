"""Translate LangGraph ``astream_events(version='v2')`` → AG UI events.

The translator is stateful: it holds the current run id, the open
assistant message id, and open tool-call ids so that consecutive
``on_chat_model_stream`` / ``on_tool_*`` events map onto correctly
scoped AG UI events.

Only a subset of the AG UI protocol is emitted here — the events needed
to drive the Open WebUI frontend. Additional events (SNAPSHOT, STATE_*)
can be added as consumers start relying on them.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Iterable

log = logging.getLogger(__name__)

# The ag-ui-protocol SDK exports typed pydantic events. We import them
# lazily so the module stays import-safe when the package is absent
# (e.g. during partial installs / dev checks).
try:
    from ag_ui.core import (
        EventType,
        RunStartedEvent,
        RunFinishedEvent,
        RunErrorEvent,
        TextMessageStartEvent,
        TextMessageContentEvent,
        TextMessageEndEvent,
        ToolCallStartEvent,
        ToolCallArgsEvent,
        ToolCallEndEvent,
        StateSnapshotEvent,
        StateDeltaEvent,
    )

    _HAS_AG_UI = True
except Exception:  # pragma: no cover - optional dep
    _HAS_AG_UI = False
    log.warning(
        'ag-ui-protocol not installed — falling back to dict-based AG UI events'
    )


def _new_id(prefix: str) -> str:
    return f'{prefix}_{uuid.uuid4().hex[:12]}'


class AGUITranslator:
    """Stateful LangGraph → AG UI translator.

    Usage::

        translator = AGUITranslator(thread_id=chat_id)
        async for lg_event in app.astream_events(..., version='v2'):
            for ag_ui_event in translator.translate(lg_event):
                await emit_ag_ui(event_emitter, ag_ui_event)
        for ag_ui_event in translator.finish():
            await emit_ag_ui(event_emitter, ag_ui_event)
    """

    def __init__(self, thread_id: str, run_id: str | None = None):
        self.thread_id = thread_id
        self.run_id = run_id or _new_id('run')
        self._run_started = False
        self._current_message_id: str | None = None
        self._open_tool_calls: dict[str, str] = {}  # lg_run_id -> tool_call_id

    # ---- helpers -------------------------------------------------------

    def _mk(self, cls_name: str, **fields) -> Any:
        """Return an AG UI event — pydantic instance if SDK is present,
        otherwise a plain dict shaped like one."""
        if _HAS_AG_UI:
            cls = globals()[cls_name]
            return cls(**fields)
        # Fallback: dict with a ``type`` field matching the SDK's EventType.
        type_map = {
            'RunStartedEvent': 'RUN_STARTED',
            'RunFinishedEvent': 'RUN_FINISHED',
            'RunErrorEvent': 'RUN_ERROR',
            'TextMessageStartEvent': 'TEXT_MESSAGE_START',
            'TextMessageContentEvent': 'TEXT_MESSAGE_CONTENT',
            'TextMessageEndEvent': 'TEXT_MESSAGE_END',
            'ToolCallStartEvent': 'TOOL_CALL_START',
            'ToolCallArgsEvent': 'TOOL_CALL_ARGS',
            'ToolCallEndEvent': 'TOOL_CALL_END',
            'StateSnapshotEvent': 'STATE_SNAPSHOT',
            'StateDeltaEvent': 'STATE_DELTA',
        }
        return {'type': type_map[cls_name], **fields}

    def _ensure_run_started(self) -> Iterable[Any]:
        if self._run_started:
            return []
        self._run_started = True
        return [
            self._mk(
                'RunStartedEvent',
                threadId=self.thread_id,
                runId=self.run_id,
            )
        ]

    # ---- main dispatch -------------------------------------------------

    def translate(self, lg_event: dict) -> list[Any]:
        """Map a single LangGraph event to 0+ AG UI events."""
        kind = lg_event.get('event')
        data = lg_event.get('data') or {}
        out: list[Any] = list(self._ensure_run_started())

        if kind == 'on_chat_model_start':
            msg_id = _new_id('msg')
            self._current_message_id = msg_id
            out.append(
                self._mk(
                    'TextMessageStartEvent',
                    messageId=msg_id,
                    role='assistant',
                )
            )

        elif kind == 'on_chat_model_stream':
            chunk = data.get('chunk')
            delta = _extract_text_delta(chunk)
            if delta and self._current_message_id:
                out.append(
                    self._mk(
                        'TextMessageContentEvent',
                        messageId=self._current_message_id,
                        delta=delta,
                    )
                )
            # Tool call fragments inside the stream (OpenAI-style)
            for tc in _extract_tool_call_chunks(chunk):
                lg_call_id = tc.get('id') or tc.get('index')
                name = tc.get('name')
                args_delta = tc.get('args') or ''
                if lg_call_id is None:
                    continue
                key = str(lg_call_id)
                if key not in self._open_tool_calls and name:
                    tc_id = tc.get('id') or _new_id('tc')
                    self._open_tool_calls[key] = tc_id
                    out.append(
                        self._mk(
                            'ToolCallStartEvent',
                            toolCallId=tc_id,
                            toolCallName=name,
                            parentMessageId=self._current_message_id,
                        )
                    )
                if args_delta and key in self._open_tool_calls:
                    out.append(
                        self._mk(
                            'ToolCallArgsEvent',
                            toolCallId=self._open_tool_calls[key],
                            delta=args_delta,
                        )
                    )

        elif kind == 'on_chat_model_end':
            if self._current_message_id:
                out.append(
                    self._mk(
                        'TextMessageEndEvent',
                        messageId=self._current_message_id,
                    )
                )
                self._current_message_id = None

        elif kind == 'on_tool_start':
            run_id = lg_event.get('run_id') or _new_id('tc')
            name = lg_event.get('name', '')
            args_in = data.get('input')
            tc_id = self._open_tool_calls.get(str(run_id)) or _new_id('tc')
            self._open_tool_calls[str(run_id)] = tc_id
            out.append(
                self._mk(
                    'ToolCallStartEvent',
                    toolCallId=tc_id,
                    toolCallName=name,
                )
            )
            if args_in is not None:
                try:
                    delta = json.dumps(args_in) if not isinstance(args_in, str) else args_in
                except Exception:
                    delta = str(args_in)
                out.append(
                    self._mk(
                        'ToolCallArgsEvent',
                        toolCallId=tc_id,
                        delta=delta,
                    )
                )

        elif kind == 'on_tool_end':
            run_id = lg_event.get('run_id')
            tc_id = self._open_tool_calls.pop(str(run_id), None)
            if tc_id:
                out.append(
                    self._mk(
                        'ToolCallEndEvent',
                        toolCallId=tc_id,
                    )
                )

        elif kind == 'on_chain_end' and lg_event.get('name') == 'LangGraph':
            # Root graph finished — emit after the caller's `finish()`.
            pass

        return out

    def finish(self) -> list[Any]:
        out: list[Any] = []
        if not self._run_started:
            return out
        out.append(
            self._mk(
                'RunFinishedEvent',
                threadId=self.thread_id,
                runId=self.run_id,
            )
        )
        return out

    def error(self, message: str, code: str = 'agent_error') -> list[Any]:
        out: list[Any] = list(self._ensure_run_started())
        out.append(
            self._mk(
                'RunErrorEvent',
                message=message,
                code=code,
            )
        )
        return out


# ---- extraction helpers ------------------------------------------------


def _extract_text_delta(chunk: Any) -> str:
    if chunk is None:
        return ''
    content = getattr(chunk, 'content', None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text' and isinstance(item.get('text'), str):
                    parts.append(item['text'])
            elif isinstance(item, str):
                parts.append(item)
        return ''.join(parts)
    return ''


def _extract_tool_call_chunks(chunk: Any) -> list[dict]:
    if chunk is None:
        return []
    # LangChain AIMessageChunk exposes ``tool_call_chunks`` for streamed
    # tool calls. Each entry has name/args/id/index.
    tc_chunks = getattr(chunk, 'tool_call_chunks', None)
    if not tc_chunks:
        return []
    out = []
    for tc in tc_chunks:
        out.append(
            {
                'id': tc.get('id'),
                'index': tc.get('index'),
                'name': tc.get('name'),
                'args': tc.get('args'),
            }
        )
    return out
