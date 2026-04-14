# Terminal Orchestrator

Per-user container orchestrator that sits between Open WebUI and Open Terminal. It implements the `server_type: "orchestrator"` contract that Open WebUI already understands, so no changes to Open WebUI are required.

## Architecture

```
Open WebUI  ──HTTPS──▶  Terminal Orchestrator  ──Docker SDK──▶  terminal_{user_id}
            X-User-Id                          (ensures + proxies)
            Bearer <shared-key>
```

- **HTTP**: `*  /p/{policy_id}/{path}` — validates `Authorization: Bearer <ORCHESTRATOR_SHARED_KEY>`, reads `X-User-Id`, ensures the user's container is running, forwards the request to `http://<ip>:<port>/<path>`.
- **WebSocket**: `WSS /p/{policy_id}/api/terminals/{session_id}?user_id=<id>` — first-message auth envelope consumed for the shared-key check, then a bidirectional bridge to the upstream container is opened.
- **Policies API**: `GET /api/v1/policies`, `PUT /api/v1/policies/{id}` — used by Open WebUI's verify endpoint and policy editor ([`configs.py`](../../backend/open_webui/routers/configs.py)).

## Trust boundaries

- `ORCHESTRATOR_SHARED_KEY` is the only trust boundary. Treat it like a database password.
- The orchestrator does **not** cryptographically verify `X-User-Id`. It trusts Open WebUI to set it. Therefore the orchestrator port must never be exposed to the host or the public internet — only to the internal compose network shared with `open-webui`.
- `/var/run/docker.sock` grants root-on-host. The orchestrator container is itself `read_only: true`, runs as UID 1000, and has no other host mounts.

## Container hardening (baseline)

Every spawned container gets:

| Flag           | Value                                              |
| -------------- | -------------------------------------------------- |
| `cap_drop`     | `ALL`                                              |
| `security_opt` | `no-new-privileges:true` + docker default seccomp  |
| `read_only`    | `True`                                             |
| `tmpfs`        | `/tmp` 64 MiB, `/run` 16 MiB                       |
| `user`         | `1000:1000`                                        |
| `mem_limit`    | policy-driven (default 1 GiB)                      |
| `nano_cpus`    | policy-driven (default 1.0)                        |
| `pids_limit`   | policy-driven (default 256)                        |
| `network`      | `terminal-internal` (internal bridge, no outbound) |
| `volumes`      | `terminal-data-{user_id}` → `/workspace`           |

Policies with `allow_internet: true` additionally attach to `terminal-egress` (a regular bridge). gVisor is accepted via the `runtime:` policy field but not installed by default.

## Environment variables

See [`config.py`](src/terminal_orchestrator/config.py) for the full list. Required:

- `ORCHESTRATOR_SHARED_KEY` — must equal the `key` field on the Open WebUI terminal connection.

Commonly tuned:

- `TERMINAL_IMAGE`, `TERMINAL_INTERNAL_PORT`
- `IDLE_TIMEOUT_SECONDS` (default 1800)
- `MEM_LIMIT`, `CPU_LIMIT`, `PIDS_LIMIT`
- `SPAWN_RATE_PER_MIN` (default 3)

## Policies

Bundled in [`policies.yaml`](policies.yaml): `default`, `heavy`, `internet`. Admin edits via Open WebUI's policy editor go through `PUT /api/v1/policies/{id}` and are persisted to `/etc/orchestrator/policies-overrides.json`. Policy changes apply on the next container spawn — existing containers are not restarted.

## Running

From the repository root:

```bash
export TERMINAL_ORCHESTRATOR_KEY=$(openssl rand -hex 32)
docker compose -f docker-compose.yaml -f docker-compose.terminal-orchestrator.yaml up --build
```

Then in Open WebUI → Admin → Integrations → Terminal Servers → Add:

- **URL**: `http://terminal-orchestrator:8000`
- **Key**: value of `TERMINAL_ORCHESTRATOR_KEY`
- **Policy ID**: `default`
- Click **Verify** — the orchestrator's `GET /api/v1/policies` should respond 200 and Open WebUI will classify the server as `orchestrator`.

## Verification checklist

1. `docker ps` shows the orchestrator container running.
2. Admin UI → Verify — green.
3. Open a terminal in chat — a container named `terminal_<user_id>` appears within 10 s.
4. Inside the terminal: `whoami` → `1000` or `user`; `touch /etc/hello` → read-only error; `touch /workspace/hello` → succeeds.
5. `curl https://example.com` fails for `default`, succeeds for `internet`.
6. Sign in as a second user, run `ls /workspace` — empty, cross-user isolation confirmed.
7. Set `IDLE_TIMEOUT_SECONDS=120`, wait 3 minutes — containers are reaped.
8. Restart the orchestrator — surviving containers are adopted back into the state map on startup (label-based recovery).

## Scope (v1)

Out of scope: multi-host scheduling, Redis/SQLite persistence, Prometheus metrics, disk quotas on the user volume, gVisor installation/testing, per-user quotas beyond "one container at a time". The in-memory state map plus `managed-by=terminal-orchestrator` label recovery is the entire persistence layer.
