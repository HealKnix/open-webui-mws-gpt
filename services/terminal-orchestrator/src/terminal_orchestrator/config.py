from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    orchestrator_shared_key: SecretStr = Field(..., description="Bearer key validating Open WebUI.")

    terminal_image: str = "ghcr.io/open-webui/open-terminal:latest"
    terminal_internal_port: int = 8000

    internal_network_name: str = "terminal-internal"
    egress_network_name: str = "terminal-egress"

    idle_timeout_seconds: int = 1800
    gc_interval_seconds: int = 60

    mem_limit: str = "1g"
    cpu_limit: float = 1.0
    pids_limit: int = 256
    allow_internet_default: bool = False
    gvisor_runtime: str | None = None
    container_user: str = "1000:1000"
    workspace_mount: str = "/workspace"

    stop_on_shutdown: bool = True

    spawn_rate_per_min: int = 3
    spawn_readiness_timeout: float = 30.0

    policies_file: Path = Path("/etc/orchestrator/policies.yaml")
    policies_overrides_file: Path = Path("/etc/orchestrator/state/policies-overrides.json")

    listen_host: str = "0.0.0.0"
    listen_port: int = 8000
    log_level: str = "INFO"

    user_id_pattern: str = r"^[A-Za-z0-9._-]{1,64}$"

    file_max_bytes: int = 256 * 1024 * 1024

    skills_source_dir: Path = Path("/opt/skills")
    skills_mount: str = "/skills"
    skills_volume_name: str = "terminal-skills"
    skills_volume_target: Path = Path("/var/lib/terminal-skills")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
