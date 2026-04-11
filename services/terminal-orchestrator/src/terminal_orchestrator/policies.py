import json
import re
from pathlib import Path
from threading import RLock
from typing import Any

import yaml
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from .logging_config import get_logger

log = get_logger(__name__)


_MEMORY_UNIT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([kKmMgGtT]?)([iI]?)[bB]?\s*$")


def _normalize_memory(value: Any) -> str:
    """Accept Docker ('1g', '512m'), Kubernetes ('1Gi', '512Mi'), or raw bytes and return
    a string Docker's SDK will accept."""
    if value is None:
        return "1g"
    if isinstance(value, int):
        return f"{value}b"
    text = str(value).strip()
    if not text:
        return "1g"
    match = _MEMORY_UNIT_RE.match(text)
    if not match:
        return text
    number, unit, _binary = match.groups()
    unit = (unit or "").lower()
    if not unit:
        return f"{number}b"
    return f"{number}{unit}"


class Policy(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    image: str | None = None
    port: int = 8000
    mem_limit: str = Field(
        default="1g",
        validation_alias=AliasChoices("mem_limit", "memory_limit"),
    )
    cpu_limit: float = 1.0
    pids_limit: int = 256
    allow_internet: bool = False
    runtime: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    description: str = ""

    # Fields accepted from the Open WebUI admin UI that the orchestrator does not
    # consume directly in v1; stored so round-trips don't lose information.
    idle_timeout_minutes: int | None = None
    storage: str | None = None

    @field_validator("mem_limit", mode="before")
    @classmethod
    def _coerce_mem_limit(cls, value: Any) -> str:
        return _normalize_memory(value)

    @field_validator("cpu_limit", mode="before")
    @classmethod
    def _coerce_cpu_limit(cls, value: Any) -> float:
        if value is None or value == "":
            return 1.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 1.0

    @field_validator("env", mode="before")
    @classmethod
    def _coerce_env(cls, value: Any) -> dict[str, str]:
        if not value:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        return {}


class PolicyRegistry:
    def __init__(self, base_file: Path, overrides_file: Path) -> None:
        self._base_file = base_file
        self._overrides_file = overrides_file
        self._policies: dict[str, Policy] = {}
        self._lock = RLock()

    def load(self) -> None:
        with self._lock:
            self._policies.clear()
            if self._base_file.exists():
                raw = yaml.safe_load(self._base_file.read_text(encoding="utf-8")) or {}
                for item in raw.get("policies", []):
                    policy = Policy.model_validate(item)
                    self._policies[policy.id] = policy
            else:
                log.warning("policies_file_missing", path=str(self._base_file))

            if self._overrides_file.exists():
                try:
                    raw = json.loads(self._overrides_file.read_text(encoding="utf-8"))
                    for item in raw.get("policies", []):
                        policy = Policy.model_validate(item)
                        self._policies[policy.id] = policy
                except Exception as exc:
                    log.error("policies_overrides_invalid", error=str(exc))

    def get(self, policy_id: str) -> Policy | None:
        with self._lock:
            return self._policies.get(policy_id)

    def all(self) -> list[Policy]:
        with self._lock:
            return list(self._policies.values())

    def upsert(self, policy: Policy) -> Policy:
        with self._lock:
            self._policies[policy.id] = policy
            self._persist_overrides()
            return policy

    def _persist_overrides(self) -> None:
        try:
            self._overrides_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {"policies": [p.model_dump() for p in self._policies.values()]}
            self._overrides_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            log.warning("policies_overrides_not_persisted", error=str(exc))
