"""File transfer endpoints: push/pull files between Open WebUI and the
per-user /workspace volume mounted in `terminal_{user_id}` containers.

Routes:
    POST /api/v1/files/upload?policy_id=&filename=   (multipart `file`)
    GET  /api/v1/files/download?path=/workspace/...
    GET  /api/v1/files/list?policy_id=

All routes require `Authorization: Bearer <shared key>` and `X-User-Id`.
"""

import asyncio
import io
import os
import posixpath
import tarfile
import time

from docker.errors import APIError, NotFound
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import StreamingResponse

from .auth import require_user_id, verify_bearer
from .container_manager import (
    ContainerManager,
    ContainerSpawnError,
    ContainerSpawnTimeout,
    SpawnRateLimited,
)
from .logging_config import get_logger
from .policies import Policy, PolicyRegistry

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1/files", tags=["files"])

WORKSPACE = "/workspace"


def _resolve_policy(request: Request, policy_id: str) -> Policy:
    registry: PolicyRegistry = request.app.state.policies
    policy = registry.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found")
    return policy


def _safe_basename(filename: str) -> str:
    if not filename or "\x00" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    base = os.path.basename(filename.replace("\\", "/"))
    if base in ("", ".", "..") or "/" in base:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if len(base) > 255:
        raise HTTPException(status_code=400, detail="Filename too long")
    return base


def _safe_workspace_path(path: str) -> tuple[str, str]:
    if not path or "\x00" in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    normalized = posixpath.normpath(path)
    if normalized != WORKSPACE and not normalized.startswith(WORKSPACE + "/"):
        raise HTTPException(status_code=400, detail="Path outside /workspace")
    base = posixpath.basename(normalized)
    if not base or base in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid path")
    return normalized, base


async def _ensure_container(request: Request, user_id: str, policy: Policy):
    manager: ContainerManager = request.app.state.manager
    try:
        state = await manager.ensure(user_id, policy)
    except SpawnRateLimited as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except ContainerSpawnTimeout as exc:
        raise HTTPException(status_code=504, detail=f"Container spawn timeout: {exc}")
    except ContainerSpawnError as exc:
        raise HTTPException(status_code=503, detail=f"Container spawn failed: {exc}")
    manager.mark_active(user_id)
    return state


@router.post("/upload", dependencies=[Depends(verify_bearer)])
async def upload_file(
    request: Request,
    policy_id: str = Query(..., min_length=1),
    filename: str = Query(..., min_length=1),
    file: UploadFile = File(...),
    user_id: str = Depends(require_user_id),
) -> dict:
    settings = request.app.state.settings
    max_bytes = settings.file_max_bytes
    safe_name = _safe_basename(filename)
    policy = _resolve_policy(request, policy_id)

    buf = io.BytesIO()
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="File exceeds file_max_bytes")
        buf.write(chunk)
    data = buf.getvalue()

    state = await _ensure_container(request, user_id, policy)
    manager: ContainerManager = request.app.state.manager

    def _put() -> None:
        client = manager._client
        container = client.containers.get(state.container_id)
        tar_buf = io.BytesIO()
        now = int(time.time())
        with tarfile.open(fileobj=tar_buf, mode="w") as tf:
            info = tarfile.TarInfo(name=safe_name)
            info.size = len(data)
            info.mode = 0o644
            info.uid = 1000
            info.gid = 1000
            info.uname = "user"
            info.gname = "user"
            info.mtime = now
            info.type = tarfile.REGTYPE
            tf.addfile(info, io.BytesIO(data))
        container.put_archive(WORKSPACE, tar_buf.getvalue())

    try:
        await asyncio.to_thread(_put)
    except NotFound:
        raise HTTPException(status_code=503, detail="Container not found")
    except APIError as exc:
        log.warning("put_archive_failed", user_id=user_id, error=str(exc))
        raise HTTPException(status_code=502, detail=f"Docker error: {exc}") from exc

    workspace_path = f"{WORKSPACE}/{safe_name}"
    log.info(
        "file_uploaded",
        user_id=user_id,
        path=workspace_path,
        size=len(data),
    )
    return {"path": workspace_path, "size": len(data)}


@router.get("/download", dependencies=[Depends(verify_bearer)])
async def download_file(
    request: Request,
    path: str = Query(..., min_length=1),
    user_id: str = Depends(require_user_id),
) -> StreamingResponse:
    settings = request.app.state.settings
    max_bytes = settings.file_max_bytes
    abs_path, base = _safe_workspace_path(path)

    manager: ContainerManager = request.app.state.manager
    state = manager._states.get(user_id)
    if state is None:
        raise HTTPException(status_code=404, detail="No container for user")
    manager.mark_active(user_id)

    def _fetch() -> tuple[bytes, int]:
        client = manager._client
        container = client.containers.get(state.container_id)
        try:
            gen, stat = container.get_archive(abs_path)
        except NotFound:
            raise HTTPException(status_code=404, detail="File not found")
        declared = int(stat.get("size", 0))
        if declared > max_bytes:
            raise HTTPException(status_code=413, detail="File exceeds file_max_bytes")

        tar_buf = io.BytesIO()
        total = 0
        tar_overhead = 4 * 1024 * 1024
        for chunk in gen:
            total += len(chunk)
            if total > max_bytes + tar_overhead:
                raise HTTPException(status_code=413, detail="File exceeds file_max_bytes")
            tar_buf.write(chunk)
        tar_buf.seek(0)

        with tarfile.open(fileobj=tar_buf, mode="r") as tf:
            member = None
            for candidate in tf:
                if not candidate.isfile():
                    continue
                if candidate.name == base or candidate.name.endswith("/" + base):
                    member = candidate
                    break
            if member is None:
                raise HTTPException(status_code=404, detail="File not found in archive")
            fh = tf.extractfile(member)
            if fh is None:
                raise HTTPException(status_code=404, detail="File not readable")
            return fh.read(), member.size

    try:
        content, size = await asyncio.to_thread(_fetch)
    except HTTPException:
        raise
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Docker error: {exc}") from exc

    headers = {
        "Content-Disposition": f'attachment; filename="{base}"',
        "Content-Length": str(size),
    }
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers=headers,
    )


@router.get("/list", dependencies=[Depends(verify_bearer)])
async def list_files(
    request: Request,
    policy_id: str = Query(..., min_length=1),
    user_id: str = Depends(require_user_id),
) -> dict:
    policy = _resolve_policy(request, policy_id)
    state = await _ensure_container(request, user_id, policy)
    manager: ContainerManager = request.app.state.manager

    def _list() -> list[dict]:
        client = manager._client
        container = client.containers.get(state.container_id)
        cmd = [
            "sh",
            "-lc",
            "find /workspace -maxdepth 4 -type f -exec stat -c '%n\t%s\t%Y' {} + 2>/dev/null",
        ]
        result = container.exec_run(cmd, user="1000:1000", stdout=True, stderr=False, demux=False)
        out = result.output or b""
        files: list[dict] = []
        for line in out.decode("utf-8", errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            full_name = parts[0]
            try:
                size = int(parts[1])
                mtime = float(parts[2])
            except ValueError:
                continue
            rel = full_name
            if rel.startswith("/workspace/"):
                rel = rel[len("/workspace/"):]
            elif rel == "/workspace":
                continue
            if not rel:
                continue
            files.append(
                {
                    "name": rel,
                    "path": f"/workspace/{rel}",
                    "size": size,
                    "mtime": mtime,
                }
            )
        return files

    try:
        files = await asyncio.to_thread(_list)
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Docker error: {exc}") from exc
    return {"files": files}
