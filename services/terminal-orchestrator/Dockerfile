FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install .

RUN mkdir -p /etc/orchestrator

# Runs as root because /var/run/docker.sock access is mandatory and group-GID
# matching across hosts is brittle. Hardening for this container is done via
# read_only rootfs, tmpfs, no published ports, and attachment to an internal
# network only (see docker-compose.terminal-orchestrator.yaml).

EXPOSE 8000

ENTRYPOINT ["python", "-m", "terminal_orchestrator"]
