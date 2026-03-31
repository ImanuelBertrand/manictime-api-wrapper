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
  - Clients authenticate to this wrapper via a static API key (`API_KEY` env var).
  - This wrapper authenticates to ManicTime via credentials (`MT_USERNAME` / `MT_PASSWORD`) configured in the `.env` file.

## Stack

- **Python 3.14**, managed with [uv](https://github.com/astral-sh/uv)
- **Flask 3** — web framework
- **httpx** — HTTP client for ManicTime API calls (routed through Squid)
- **Flask-Caching** (`SimpleCache`) — in-memory cache for MT responses
- **Gunicorn** — WSGI server
- **Squid** — forward proxy / egress firewall

## Project context

This wrapper is intentionally a separate project from the AI agent that consumes it. The separation provides a security boundary between the AI agent and the ManicTime instance — the agent can only access what this wrapper explicitly exposes.

The downstream agent is responsible for task analysis and timesheet generation. This wrapper only fetches and (where useful) aggregates raw ManicTime data.

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

## Development

```bash
cp .env.example .env        # fill in values
docker compose up --build
curl http://localhost:8000/health
```

The dev image mounts the project root into the container, so code changes are reflected without rebuilding.
