# ManicTime API Wrapper

A read-only Flask API wrapper around a [ManicTime Server](https://www.manictime.com/server) instance. Its sole purpose is to expose ManicTime timeline data to a downstream AI agent that analyses it and produces detailed timesheets — including tasks, which ManicTime itself does not track.

## Architecture

```
Downstream AI agent → [API key auth] → This wrapper → [Squid] → ManicTime Server
```

- **Stateless** — no database. All data comes from ManicTime; responses are cached in-memory.
- **Read-only** — only GET operations against the ManicTime REST API are exposed.
- **Network isolation** — a Squid forward proxy (internal Docker network) ensures outgoing traffic is restricted to the configured ManicTime server. The Flask container has no direct internet access.
- **Two independent auth layers:**
  - Clients authenticate to this wrapper via a static API key (`X-API-Key` header, validated with constant-time comparison).
  - This wrapper authenticates to ManicTime via HATEOAS-discovered token endpoint (`MT_USERNAME` / `MT_PASSWORD`), with automatic re-authentication on 401.

## Stack

- **Python 3.14**, managed with [uv](https://github.com/astral-sh/uv)
- **Flask 3** — web framework
- **httpx** — HTTP client for ManicTime API calls (routed through Squid)
- **Flask-Caching** (`SimpleCache`) — in-memory cache for MT responses
- **Flask-Limiter** — rate limiting (60 requests/minute default)
- **Gunicorn** — WSGI server
- **Squid** — forward proxy / egress firewall

## Project context

This wrapper is intentionally a separate project from the AI agent that consumes it. The separation provides a security boundary between the AI agent and the ManicTime instance — the agent can only access what this wrapper explicitly exposes.

The downstream agent is responsible for task analysis and timesheet generation. This wrapper only fetches and (where useful) aggregates raw ManicTime data.

## API endpoints

| Endpoint | Auth | Cached | Purpose |
|---|---|---|---|
| `GET /health` | No | No | Shallow health check; `?deep=true` verifies ManicTime connectivity (503 if unreachable) |
| `GET /api/openapi.yaml` | No | No | OpenAPI 3.1 specification |
| `GET /api/timelines` | Yes | Yes | List all timelines |
| `GET /api/timelines/{key}/activities` | Yes | Yes | Activities in a date range (`fromTime`, `toTime` required, ISO 8601) |
| `GET /api/tags` | Yes | Yes | Tag combinations; `?all=true` for all |
| `GET /api/screenshots` | Yes | Yes | Screenshots |

Timeline keys are validated against `^[\w-]{1,128}$`. Date parameters are validated as ISO 8601. All authenticated endpoints require the `X-API-Key` header.

## Project layout

```
app/                        # Flask application package
  __init__.py               # App factory, cache/limiter init, error handlers, request logging
  auth.py                   # @require_api_key decorator
  mt_client.py              # ManicTimeClient (HATEOAS discovery, token auth, auto-retry)
  routes.py                 # API endpoints (blueprint)
  openapi.yaml              # OpenAPI 3.1 spec
docker/                     # Docker configuration
  Dockerfile                # Multi-stage: builder → production → development, plus squid
  claude.sh                 # Lazy Claude Code installer/launcher
  entrypoint.sh             # Gunicorn startup
  squid/                    # Squid proxy configs
    squid-prod.conf.template
    squid-dev.conf.template
    squid-entrypoint.sh
tests/                      # Pytest suite
  conftest.py               # Fixtures (app, mock client, test client)
  test_auth.py              # Auth decorator tests
  test_mt_client.py         # ManicTimeClient unit tests
  test_routes.py            # Endpoint tests (validation, error handling, caching)
  test_rate_limit.py        # Rate limiting (429 after 60 req/min)
  test_smoke.py             # Smoke test
wsgi.py                     # WSGI entry point (gunicorn wsgi:app)
Makefile                    # Dev commands (up, down, build, test, lint, fix, typecheck, claude)
docker-compose.yml          # Production compose (web + squid)
docker-compose.override.yml # Dev overrides (volume mounts, dev squid config)
```

## Key configuration (`.env`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask secret key |
| `MT_SERVER_URL` | Base URL of the ManicTime server |
| `MT_USERNAME` | ManicTime login username |
| `MT_PASSWORD` | ManicTime login password |
| `API_KEY` | Shared secret for clients of this wrapper |
| `MT_HOSTNAME` | ManicTime server hostname (used by Squid allowlist) |
| `CACHE_DEFAULT_TIMEOUT` | Cache TTL in seconds (default: 300) |

## Squid allowlist

The production Squid config is generated from `docker/squid/squid-prod.conf.template` using `MT_HOSTNAME`:

- **Build time**: pass `--build-arg MT_HOSTNAME=<hostname>` — bakes the hostname into the image. The CI pipeline does not set this, so published images default to `example.invalid` (blocks all traffic until overridden at runtime).
- **Runtime**: set `MT_HOSTNAME` in the environment (e.g. via `.env`) — the Squid entrypoint re-renders the config on startup.

The dev config (`docker/squid/squid-dev.conf.template`) works the same way as production — `MT_HOSTNAME` from `.env` is substituted at container startup. The dev template also includes extra allowlist entries for package registries and Claude Code.

## CI/CD

GitHub Actions (`.github/workflows/ci-cd.yml`):

1. **code-quality** — ruff check, ruff format, pylint, ty type checker, pytest
2. **docker-publish** (on main push / release) — builds and pushes app and squid images to `ghcr.io`

## Development

```bash
cp .env.example .env        # fill in values
docker compose up --build
curl http://localhost:8000/health
```

The dev image mounts the project root into the container, so code changes are reflected without rebuilding.

**Claude Code runs inside the dev container.** Claude Code is not baked into the Docker image — it is installed lazily on first run into a named volume (`claude_local`) mounted at `/home/appuser/.local`. Run `make claude` to install (if needed) and open a Claude Code session. The installation persists across container restarts; delete the volume to force a reinstall. The dev Squid allowlist includes Anthropic domains so Claude Code can reach its backend.

### Makefile targets

| Target | Purpose |
|---|---|
| `make up` | Start services |
| `make down` | Stop services |
| `make build` | Rebuild and start |
| `make reset` | Full reset with volume cleanup |
| `make logs` | Follow logs (filter with `s=web`) |
| `make shell` | Bash in web container |
| `make claude` | Claude Code in web container |
| `make test` | Run pytest (pass args with `args=...`) |
| `make lint` | Ruff check (no fixes) |
| `make fix` | Ruff check + format with fixes |
| `make typecheck` | ty type checker |
