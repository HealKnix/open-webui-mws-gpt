import docker
from docker.errors import APIError, DockerException, NotFound
from docker.models.networks import Network

from .logging_config import get_logger

log = get_logger(__name__)


class DockerSocketUnavailable(RuntimeError):
    pass


def build_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except (DockerException, PermissionError, FileNotFoundError) as exc:
        raise DockerSocketUnavailable(
            "Failed to connect to Docker daemon via /var/run/docker.sock. "
            "Check that the socket is mounted into this container and that "
            "the orchestrator process can read it. Underlying error: "
            f"{exc!s}"
        ) from exc


def ensure_network(client: docker.DockerClient, name: str, *, internal: bool) -> Network:
    try:
        return client.networks.get(name)
    except NotFound:
        pass
    try:
        return client.networks.create(name, driver="bridge", internal=internal, check_duplicate=True)
    except APIError as exc:
        if "already exists" in str(exc).lower():
            return client.networks.get(name)
        raise


def ensure_volume(client: docker.DockerClient, name: str) -> None:
    try:
        client.volumes.get(name)
    except NotFound:
        client.volumes.create(
            name=name,
            labels={"managed-by": "terminal-orchestrator"},
        )
