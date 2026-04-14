import hmac
import re

from fastapi import Header, HTTPException, Request, status

from .config import Settings, get_settings

_USER_ID_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _user_id_re(pattern: str) -> re.Pattern[str]:
    cached = _USER_ID_RE_CACHE.get(pattern)
    if cached is None:
        cached = re.compile(pattern)
        _USER_ID_RE_CACHE[pattern] = cached
    return cached


def verify_bearer(request: Request) -> None:
    settings: Settings = request.app.state.settings
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expected = settings.orchestrator_shared_key.get_secret_value()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_user_id(
    request: Request,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str:
    settings: Settings = request.app.state.settings
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    if not _user_id_re(settings.user_id_pattern).match(x_user_id):
        raise HTTPException(status_code=400, detail="Malformed X-User-Id")
    return x_user_id


def verify_ws_shared_key(token: str, settings: Settings) -> bool:
    expected = settings.orchestrator_shared_key.get_secret_value()
    return hmac.compare_digest(token or "", expected)
