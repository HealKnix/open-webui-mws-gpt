from contextlib import asynccontextmanager

import aiohttp
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse

from .api_policies import router as policies_router
from .auth import require_user_id, verify_bearer
from .config import get_settings
from .container_manager import (
    ContainerManager,
    ContainerSpawnError,
    ContainerSpawnTimeout,
    SpawnRateLimited,
)
from .docker_client import build_client
from .http_proxy import proxy_http
from .logging_config import configure_logging, get_logger
from .openapi_synthetic import build_openapi_document
from .policies import PolicyRegistry
from .ratelimit import SpawnRateLimiter
from .ws_proxy import proxy_ws

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    registry = PolicyRegistry(settings.policies_file, settings.policies_overrides_file)
    registry.load()

    rate_limiter = SpawnRateLimiter(settings.spawn_rate_per_min)

    docker_client = build_client()
    manager = ContainerManager(docker_client, settings, rate_limiter)
    await manager.start()

    http_session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=None, sock_connect=10, sock_read=300),
        trust_env=True,
    )

    app.state.settings = settings
    app.state.policies = registry
    app.state.manager = manager
    app.state.http_session = http_session
    app.state.rate_limiter = rate_limiter

    log.info("orchestrator_started", host=settings.listen_host, port=settings.listen_port)

    try:
        yield
    finally:
        log.info("orchestrator_stopping")
        await http_session.close()
        await manager.stop()
        try:
            docker_client.close()
        except Exception:
            pass


app = FastAPI(title="Terminal Orchestrator", version="0.1.0", lifespan=lifespan)
app.include_router(policies_router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/openapi.json")
async def openapi_document() -> dict:
    return build_openapi_document()


def _resolve_policy(request: Request, policy_id: str):
    registry: PolicyRegistry = request.app.state.policies
    policy = registry.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found")
    return policy


@app.api_route(
    "/p/{policy_id}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    dependencies=[Depends(verify_bearer)],
    operation_id="proxy_entry",
    include_in_schema=False,
)
async def proxy_entry(
    policy_id: str,
    path: str,
    request: Request,
    user_id: str = Depends(require_user_id),
):
    policy = _resolve_policy(request, policy_id)
    manager: ContainerManager = request.app.state.manager
    session: aiohttp.ClientSession = request.app.state.http_session

    try:
        return await proxy_http(request, user_id, policy, path, manager, session)
    except SpawnRateLimited:
        return JSONResponse({"error": "Spawn rate limit exceeded"}, status_code=429)
    except ContainerSpawnTimeout as exc:
        log.warning("spawn_timeout", user_id=user_id, error=str(exc))
        raise HTTPException(status_code=504, detail=f"Container spawn timeout: {exc}")
    except ContainerSpawnError as exc:
        log.warning("spawn_error", user_id=user_id, error=str(exc))
        raise HTTPException(status_code=503, detail=f"Container spawn failed: {exc}")


@app.websocket("/p/{policy_id}/api/terminals/{session_id}")
async def proxy_websocket(ws: WebSocket, policy_id: str, session_id: str) -> None:
    registry: PolicyRegistry = ws.app.state.policies
    policy = registry.get(policy_id)
    if policy is None:
        await ws.close(code=4004, reason="Policy not found")
        return

    settings = ws.app.state.settings
    manager: ContainerManager = ws.app.state.manager
    session: aiohttp.ClientSession = ws.app.state.http_session

    await proxy_ws(ws, session_id, policy, settings, manager, session)
