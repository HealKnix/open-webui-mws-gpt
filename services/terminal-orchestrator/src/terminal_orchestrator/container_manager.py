import asyncio
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import aiohttp
import docker
from docker.errors import APIError, ImageNotFound, NotFound

from .config import Settings
from .docker_client import ensure_network, ensure_volume
from .logging_config import get_logger
from .policies import Policy
from .ratelimit import SpawnRateLimiter

log = get_logger(__name__)

MANAGED_LABEL = "managed-by"
MANAGED_VALUE = "terminal-orchestrator"


class ContainerSpawnError(RuntimeError):
    pass


class ContainerSpawnTimeout(ContainerSpawnError):
    pass


class SpawnRateLimited(ContainerSpawnError):
    pass


@dataclass
class ContainerState:
    user_id: str
    container_id: str
    ip: str
    port: int
    policy_id: str
    internal_token: str
    created_at: float
    last_active_at: float
    _status_cache: tuple[float, str] = field(default=(0.0, ""))


class ContainerManager:
    def __init__(
        self,
        client: docker.DockerClient,
        settings: Settings,
        rate_limiter: SpawnRateLimiter,
    ) -> None:
        self._client = client
        self._settings = settings
        self._rate_limiter = rate_limiter
        self._states: dict[str, ContainerState] = {}
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._pulled_images: set[str] = set()
        self._gc_task: asyncio.Task[None] | None = None

    def has_state(self, user_id: str) -> bool:
        return user_id in self._states

    async def start(self) -> None:
        await asyncio.to_thread(self._ensure_base_networks)
        await asyncio.to_thread(self._recover_existing)
        self._gc_task = asyncio.create_task(self._gc_loop(), name="orchestrator-gc")

    async def stop(self) -> None:
        if self._gc_task is not None:
            self._gc_task.cancel()
            try:
                await self._gc_task
            except (asyncio.CancelledError, Exception):
                pass
            self._gc_task = None
        if self._settings.stop_on_shutdown:
            for user_id in list(self._states.keys()):
                state = self._states.pop(user_id, None)
                if state is not None:
                    try:
                        await asyncio.to_thread(self._destroy_by_id, state.container_id)
                    except Exception as exc:
                        log.warning("shutdown_destroy_failed", user_id=user_id, error=str(exc))

    def mark_active(self, user_id: str) -> None:
        state = self._states.get(user_id)
        if state is not None:
            state.last_active_at = time.monotonic()

    async def ensure(self, user_id: str, policy: Policy) -> ContainerState:
        async with self._locks[user_id]:
            state = self._states.get(user_id)
            if state is not None and await asyncio.to_thread(self._is_running, state):
                state.last_active_at = time.monotonic()
                return state
            if state is not None:
                log.info("stale_state_discarded", user_id=user_id)
                self._states.pop(user_id, None)
                try:
                    await asyncio.to_thread(self._destroy_by_id, state.container_id)
                except Exception:
                    pass

            if not self._rate_limiter.try_consume(user_id):
                raise SpawnRateLimited(
                    f"spawn rate limit exceeded for user {user_id}"
                )

            new_state = await asyncio.to_thread(self._spawn, user_id, policy)
            try:
                await self._wait_ready(new_state)
            except Exception:
                try:
                    await asyncio.to_thread(self._destroy_by_id, new_state.container_id)
                finally:
                    raise
            self._states[user_id] = new_state
            return new_state

    def _ensure_base_networks(self) -> None:
        ensure_network(self._client, self._settings.internal_network_name, internal=True)
        ensure_network(self._client, self._settings.egress_network_name, internal=False)

    def _recover_existing(self) -> None:
        try:
            containers = self._client.containers.list(
                all=True,
                filters={"label": f"{MANAGED_LABEL}={MANAGED_VALUE}"},
            )
        except APIError as exc:
            log.warning("recover_list_failed", error=str(exc))
            return
        for container in containers:
            labels = container.labels or {}
            user_id = labels.get("user_id")
            policy_id = labels.get("policy_id", "")
            port = int(labels.get("port", self._settings.terminal_internal_port))
            token = labels.get("internal_token", "")
            if not user_id:
                continue
            if container.status != "running":
                try:
                    container.remove(force=True)
                except Exception:
                    pass
                continue
            network = (container.attrs.get("NetworkSettings", {}).get("Networks") or {}).get(
                self._settings.internal_network_name
            )
            ip = (network or {}).get("IPAddress", "")
            if not ip:
                continue
            now = time.monotonic()
            self._states[user_id] = ContainerState(
                user_id=user_id,
                container_id=container.id,
                ip=ip,
                port=port,
                policy_id=policy_id,
                internal_token=token,
                created_at=now,
                last_active_at=now,
            )
            log.info("recovered_container", user_id=user_id, container_id=container.id[:12])

    def _image_ready(self, image: str) -> None:
        if image in self._pulled_images:
            return
        try:
            self._client.images.get(image)
        except ImageNotFound:
            log.info("pulling_image", image=image)
            self._client.images.pull(image)
        self._pulled_images.add(image)

    def _spawn(self, user_id: str, policy: Policy) -> ContainerState:
        image = policy.image or self._settings.terminal_image
        self._image_ready(image)

        volume_name = f"terminal-data-{user_id}"
        ensure_volume(self._client, volume_name)

        token = secrets.token_hex(32)
        container_name = f"terminal_{user_id}"

        # Clean up any leftover with the same name.
        try:
            existing = self._client.containers.get(container_name)
            existing.remove(force=True)
        except NotFound:
            pass
        except APIError as exc:
            log.warning("cleanup_existing_failed", name=container_name, error=str(exc))

        env = dict(policy.env)
        env["OPEN_TERMINAL_API_KEY"] = token

        labels = {
            MANAGED_LABEL: MANAGED_VALUE,
            "user_id": user_id,
            "policy_id": policy.id,
            "port": str(policy.port),
            "internal_token": token,
        }

        kwargs: dict[str, Any] = dict(
            image=image,
            name=container_name,
            detach=True,
            network=self._settings.internal_network_name,
            volumes={volume_name: {"bind": self._settings.workspace_mount, "mode": "rw"}},
            mem_limit=policy.mem_limit,
            nano_cpus=int(policy.cpu_limit * 1e9),
            pids_limit=policy.pids_limit,
            cap_drop=["ALL"],
            cap_add=["SETGID"],
            security_opt=["no-new-privileges:true"],
            read_only=True,
            tmpfs={
                "/tmp": "rw,size=64m,mode=1777",
                "/run": "rw,size=16m",
                "/home/user": "rw,size=64m,mode=0755,uid=1000,gid=1000",
            },
            environment=env,
            labels=labels,
            auto_remove=False,
            restart_policy={"Name": "no"},
        )

        runtime = policy.runtime or self._settings.gvisor_runtime
        if runtime:
            kwargs["runtime"] = runtime

        try:
            container = self._client.containers.run(**kwargs)
        except APIError as exc:
            raise ContainerSpawnError(f"docker run failed: {exc}") from exc

        if policy.allow_internet:
            try:
                egress = self._client.networks.get(self._settings.egress_network_name)
                egress.connect(container)
            except APIError as exc:
                log.warning("egress_attach_failed", user_id=user_id, error=str(exc))

        container.reload()
        networks = (container.attrs.get("NetworkSettings", {}) or {}).get("Networks") or {}
        internal = networks.get(self._settings.internal_network_name) or {}
        ip = internal.get("IPAddress", "")
        if not ip:
            try:
                container.remove(force=True)
            finally:
                raise ContainerSpawnError("container has no internal IP")

        now = time.monotonic()
        log.info(
            "container_spawned",
            user_id=user_id,
            container_id=container.id[:12],
            policy=policy.id,
            ip=ip,
        )
        return ContainerState(
            user_id=user_id,
            container_id=container.id,
            ip=ip,
            port=policy.port,
            policy_id=policy.id,
            internal_token=token,
            created_at=now,
            last_active_at=now,
        )

    async def _wait_ready(self, state: ContainerState) -> None:
        deadline = time.monotonic() + self._settings.spawn_readiness_timeout
        delay = 0.2
        last_error: str = ""
        while True:
            try:
                # TCP-level probe: if we can open a socket to the container, it's
                # accepting connections and ready to serve requests. This avoids
                # coupling the readiness gate to the upstream's auth model.
                conn_reader, conn_writer = await asyncio.wait_for(
                    asyncio.open_connection(state.ip, state.port),
                    timeout=2.0,
                )
                conn_writer.close()
                try:
                    await conn_writer.wait_closed()
                except Exception:
                    pass
                return
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            if time.monotonic() >= deadline:
                log.warning(
                    "spawn_readiness_timeout",
                    container_id=state.container_id[:12],
                    ip=state.ip,
                    port=state.port,
                    last_error=last_error,
                )
                raise ContainerSpawnTimeout(
                    f"container {state.container_id[:12]} not ready on "
                    f"{state.ip}:{state.port} after "
                    f"{self._settings.spawn_readiness_timeout}s ({last_error})"
                )
            await asyncio.sleep(delay)
            delay = min(delay * 2, 0.8)

    def _is_running(self, state: ContainerState) -> bool:
        now = time.monotonic()
        cached_at, cached = state._status_cache
        if now - cached_at < 1.0 and cached:
            return cached == "running"
        try:
            container = self._client.containers.get(state.container_id)
        except NotFound:
            return False
        except APIError:
            return False
        state._status_cache = (now, container.status)
        return container.status == "running"

    def _destroy_by_id(self, container_id: str) -> None:
        try:
            container = self._client.containers.get(container_id)
        except NotFound:
            return
        try:
            container.stop(timeout=5)
        except Exception:
            pass
        try:
            container.remove(force=True)
        except Exception:
            pass

    async def _gc_loop(self) -> None:
        interval = self._settings.gc_interval_seconds
        timeout = self._settings.idle_timeout_seconds
        while True:
            try:
                await asyncio.sleep(interval)
                now = time.monotonic()
                victims = [
                    uid
                    for uid, st in list(self._states.items())
                    if now - st.last_active_at > timeout
                ]
                for user_id in victims:
                    async with self._locks[user_id]:
                        state = self._states.pop(user_id, None)
                        if state is None:
                            continue
                        log.info("idle_gc_destroy", user_id=user_id)
                        try:
                            await asyncio.to_thread(self._destroy_by_id, state.container_id)
                        except Exception as exc:
                            log.warning("idle_gc_destroy_failed", user_id=user_id, error=str(exc))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.exception("gc_tick_failed", error=str(exc))
