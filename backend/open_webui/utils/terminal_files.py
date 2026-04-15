"""Helpers to push uploaded chat files into the per-user terminal-orchestrator
`/workspace` volume, and to fetch files back out.

The active orchestrator connection is picked from
``request.app.state.config.TERMINAL_SERVER_CONNECTIONS`` — the first entry with
``enabled`` and ``server_type == "orchestrator"``.
"""

import logging
from typing import Optional

import requests

log = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = (10, 300)  # (connect, read)


def get_active_orchestrator(request) -> Optional[dict]:
    connections = getattr(request.app.state.config, "TERMINAL_SERVER_CONNECTIONS", None) or []
    for connection in connections:
        if not connection.get("enabled", True):
            continue
        if connection.get("server_type") != "orchestrator":
            continue
        base_url = (connection.get("url") or "").rstrip("/")
        if not base_url:
            continue
        policy_id = connection.get("policy_id") or "default"
        return {
            "url": base_url,
            "key": connection.get("key") or "",
            "auth_type": connection.get("auth_type") or "bearer",
            "policy_id": policy_id,
            "name": connection.get("name") or "",
            "id": connection.get("id") or "",
        }
    return None


def _auth_headers(connection: dict) -> dict:
    if connection.get("auth_type", "bearer") == "bearer" and connection.get("key"):
        return {"Authorization": f"Bearer {connection['key']}"}
    return {}


def push_file_to_workspace(
    connection: dict,
    user_id: str,
    contents: bytes,
    filename: str,
) -> dict:
    """Upload ``contents`` to ``/workspace/<filename>`` in the user's container.

    Returns the orchestrator response dict (``{"path": ..., "size": ...}``).
    Raises ``requests.HTTPError`` on non-2xx or ``requests.RequestException`` on
    transport failure; callers should handle these and decide whether to fall
    back (e.g., to the RAG pipeline).
    """
    url = f"{connection['url']}/api/v1/files/upload"
    params = {
        "policy_id": connection.get("policy_id", "default"),
        "filename": filename,
    }
    headers = {"X-User-Id": user_id, **_auth_headers(connection)}
    files = {"file": (filename, contents, "application/octet-stream")}

    resp = requests.post(
        url,
        params=params,
        headers=headers,
        files=files,
        timeout=_DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_workspace_file(connection: dict, user_id: str, path: str) -> requests.Response:
    """Stream a file back from ``/workspace``.

    Returns the raw streaming ``requests.Response``; caller is responsible for
    closing it (e.g., via ``StreamingResponse`` with ``background=close``).
    """
    url = f"{connection['url']}/api/v1/files/download"
    headers = {"X-User-Id": user_id, **_auth_headers(connection)}
    resp = requests.get(
        url,
        params={"path": path},
        headers=headers,
        stream=True,
        timeout=_DEFAULT_TIMEOUT,
    )
    return resp


def list_workspace(connection: dict, user_id: str) -> dict:
    url = f"{connection['url']}/api/v1/files/list"
    params = {"policy_id": connection.get("policy_id", "default")}
    headers = {"X-User-Id": user_id, **_auth_headers(connection)}
    resp = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=_DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
