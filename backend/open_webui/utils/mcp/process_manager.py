"""Manage stdio MCP server subprocess lifecycles.

The registry is keyed by ``(user_id, app_id)`` to ensure per-user process
isolation.  Each entry holds the :class:`MCPClient` (already connected via
stdio transport), creation/last-used timestamps, and a configurable TTL.

A periodic cleanup task evicts expired entries.  The registry is also
consulted on server startup to detect orphaned processes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 1800  # 30 minutes
CLEANUP_INTERVAL_SECONDS = 60  # check every minute


@dataclass
class ProcessEntry:
    client: object  # MCPClient instance
    app_id: str
    user_id: str
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    ttl: float = DEFAULT_TTL_SECONDS

    def is_expired(self) -> bool:
        return (time.time() - self.last_used) > self.ttl

    def touch(self):
        self.last_used = time.time()


class ProcessRegistry:
    """Manages stdio MCP subprocess lifecycles per (user_id, app_id)."""

    def __init__(self):
        self._entries: dict[tuple[str, str], ProcessEntry] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def get(self, user_id: str, app_id: str) -> Optional[ProcessEntry]:
        key = (user_id, app_id)
        entry = self._entries.get(key)
        if entry is None:
            return None

        # Check if the client session is still alive
        client = entry.client
        if client.session is None:
            log.warning('stdio process for (%s, %s) has no active session — removing', user_id, app_id)
            self._entries.pop(key, None)
            return None

        entry.touch()
        return entry

    async def spawn(
        self,
        user_id: str,
        app_id: str,
        command: str,
        args: list[str],
        env: Optional[dict[str, str]] = None,
        ttl: float = DEFAULT_TTL_SECONDS,
    ) -> ProcessEntry:
        """Spawn a new stdio MCP process and connect.

        If an entry already exists for this (user_id, app_id), it is killed
        first to avoid orphans.
        """
        from open_webui.utils.mcp.client import MCPClient

        existing = self._entries.get((user_id, app_id))
        if existing:
            await self._kill_entry(user_id, app_id, existing)

        client = MCPClient()
        await client.connect(
            transport='stdio',
            command=command,
            args=args,
            env=env,
        )

        entry = ProcessEntry(
            client=client,
            app_id=app_id,
            user_id=user_id,
            ttl=ttl,
        )
        self._entries[(user_id, app_id)] = entry
        log.info('Spawned stdio MCP process for (%s, %s)', user_id, app_id)
        return entry

    async def kill(self, user_id: str, app_id: str):
        """Kill and remove a specific process."""
        key = (user_id, app_id)
        entry = self._entries.pop(key, None)
        if entry:
            await self._kill_entry(user_id, app_id, entry)

    async def _kill_entry(self, user_id: str, app_id: str, entry: ProcessEntry):
        """Disconnect the MCP client, terminating the subprocess."""
        try:
            await entry.client.disconnect()
            log.info('Killed stdio MCP process for (%s, %s)', user_id, app_id)
        except Exception:
            log.exception('Error killing stdio MCP process for (%s, %s)', user_id, app_id)

    async def cleanup_expired(self):
        """Remove all expired entries."""
        expired_keys = [key for key, entry in self._entries.items() if entry.is_expired()]
        for key in expired_keys:
            entry = self._entries.pop(key, None)
            if entry:
                log.info(
                    'TTL expired for stdio MCP process (%s, %s) — killing',
                    entry.user_id,
                    entry.app_id,
                )
                await self._kill_entry(entry.user_id, entry.app_id, entry)

    async def cleanup_all(self):
        """Kill all managed processes (e.g. on shutdown)."""
        keys = list(self._entries.keys())
        for key in keys:
            entry = self._entries.pop(key, None)
            if entry:
                await self._kill_entry(entry.user_id, entry.app_id, entry)

    def start_cleanup_loop(self):
        """Start the periodic cleanup background task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            log.info('Started MCP stdio process cleanup loop')

    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                log.exception('Error in MCP stdio process cleanup loop')

    def stop_cleanup_loop(self):
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            self._cleanup_task = None

    @property
    def active_count(self) -> int:
        return len(self._entries)


# Singleton instance
mcp_process_registry = ProcessRegistry()
