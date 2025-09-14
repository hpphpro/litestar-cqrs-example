# Litestar CQRS Template

Minimal, production‑ready API template on Litestar with CQRS, SQLAlchemy/Alembic, Redis, JWT auth, observability (Prometheus+Grafana+Loki via Vector), and Docker profiles.

## What's inside

- **CQRS**: separate command/query flows, buses, and middlewares
- **Database**: SQLAlchemy + Alembic, ready-to-use migrations and repositories
- **HTTP API**: Litestar with `v1` versioning
- **Authentication**: JWT (access/refresh), refresh cookie, per-endpoint rate limits
- **Cache**: Redis (keys, lists, increments)
- **Code quality**: `ruff`, strict `mypy`, `pytest`
- **Observability**: Prometheus, Grafana, Loki, Vector
- **DB backups**: periodic `pg_dump`

## Quick start (local)

1. Install `uv` (if not installed):

```bash
pip install uv
```

Docs: `https://docs.astral.sh/uv/getting-started/installation/`

1. Install dependencies:

```bash
uv sync --all-groups
```

1. Run tests:

```bash
uv run pytest
```

1. Run the API:

```bash
uv run python -m backend
```

By default the server listens on `127.0.0.1:9393` and the API root path is `/api`.

## Docker

- Start API and metrics:

```bash
docker compose --profile api --profile grafana --profile prometheus up -d
```

- Stop:

```bash
docker compose --profile api --profile grafana --profile prometheus down
```

Default addresses:

- **API**: `http://127.0.0.1:${SERVER_PORT}/api`
- **Prometheus**: `http://127.0.0.1:9090`
- **Grafana**: `http://127.0.0.1:3000`
- **Loki**: `http://127.0.0.1:3100`

The `database_backup` service periodically runs `pg_dump` and stores files in `${DB_BACKUP_DIR:-./.backups}`. Interval is controlled by `DB_BACKUP_INTERVAL` (seconds).

## Environment variables (key ones)

- **SERVER_**:
  - `SERVER_HOST` (default `127.0.0.1`)
  - `SERVER_PORT` (default `9393`)
  - `SERVER_TIMEOUT` (keep-alive, default `60`)
  - `SERVER_TYPE` — `granian` | `uvicorn` | `gunicorn` (default `granian`)
  - `SERVER_WORKERS` — number or `auto`
  - `SERVER_THREADS`, `SERVER_LOG`, `SERVER_MAX_REQUESTS`

- **APP_**:
  - `APP_ROOT_PATH` (default `/api`)
  - `APP_TITLE` (default `Example`), `APP_VERSION` (`0.0.1`)
  - `APP_DEBUG`, `APP_DEBUG_DETAILED`, `APP_METRICS`, `APP_SWAGGER`

- **DB_**:
  - `DB_DRIVER` (e.g., `postgresql+asyncpg` or `sqlite+aiosqlite`)
  - `DB_NAME`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`
  - `DB_MIN_CONNECTIONS`, `DB_MAX_CONNECTIONS`, `DB_PING_CONNECTION`
  - `DB_REPLICA_HOST`, `DB_REPLICA_USER`, `DB_REPLICA_PASSWORD`, `DB_REPLICA_MAX_CONNECTIONS`

- **REDIS_**:
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
  - `REDIS_USERNAME`, `REDIS_PASSWORD`

- **SECURITY_** (JWT):
  - `SECURITY_ALGORITHM` (e.g. `HS256`)
  - `SECURITY_SECRET_KEY`, `SECURITY_PUBLIC_KEY` (raw strings or base64)
  - `SECURITY_ACCESS_TOKEN_EXPIRE_SECONDS`, `SECURITY_REFRESH_TOKEN_EXPIRE_SECONDS`

Example for local (Postgres/Redis via Docker):

```env
DB_DRIVER=postgresql+asyncpg
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=service.database.primary
DB_PORT=5432
DB_NAME=example
DB_MIN_CONNECTIONS=10
DB_PING_CONNECTION=False
DB_MAX_CONNECTIONS=100
DB_BACKUP_DIR=
DB_BACKUP_INTERVAL=86400
REPLICA_MAX_CONNECTIONS=100
REPLICA_USER=replicator
REPLICA_PASSWORD=qwerty
REPLICA_HOST=service.database.replica


SERVER_HOST=0.0.0.0
SERVER_PORT=9393
SERVER_TIMEOUT=10
SERVER_TYPE=granian
SERVER_WORKERS=auto
SERVER_THREADS=1
SERVER_LOG=True
SERVER_MAX_REQUESTS=2000
SERVER_STRATEGY=stable

APP_ROOT_PATH=/api
APP_TITLE=ExampleAPI
APP_DEBUG=False
APP_DEBUG_DETAILED=False
APP_VERSION=0.0.1
APP_SWAGGER=True
APP_METRICS=True

REDIS_HOST=service.redis
REDIS_PORT=6379
REDIS_PASSWORD=

GRAFANA_USER=user
GRAFANA_PASSWORD=strong_password

SECURITY_ALGORITHM=HS256
SECURITY_SECRET_KEY=devsecret
SECURITY_PUBLIC_KEY=devsecret
SECURITY_ACCESS_TOKEN_EXPIRE_SECONDS=1800
SECURITY_REFRESH_TOKEN_EXPIRE_SECONDS=604800
```

## Database migrations

- Locally:

```bash
uv run alembic upgrade head
```

## Tests and code quality

```bash
uv run pytest             # tests
uv run mypy               # type checks
uv run ruff check .       # lint
uv run ruff format .      # format
```

## API (at a glance)

Base path: `/api/v1`

- **Health**: `GET /api/v1/healthcheck`
- **Auth**: `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/refresh`
- **Users (public create)**: `POST /api/v1/users`
- **Users (private, JWT)**: `GET /api/v1/users/{user_id}`, `GET /api/v1/users/me`, `GET /api/v1/users`, `PATCH /api/v1/users/{user_id}`, `DELETE /api/v1/users/{user_id}`

Swagger/Scalar are served when `APP_SWAGGER=true`.

## Authorization & RBAC

- Auth flow
- Login: `POST /api/v1/auth/login` with body:

```json
{"email": "user@example.com", "password": "secret123", "fingerprint": "client-id"}
```

- Returns `access_token` (response body) and sets `refresh` as an HTTP-only cookie.
- Refresh: `POST /api/v1/auth/refresh` with body `{"fingerprint": "client-id"}`. Uses `refresh` cookie or `Authorization: Bearer` header.
- Logout: `POST /api/v1/auth/logout` with body `{"fingerprint": "client-id"}`. Accepts `refresh` cookie or `Authorization: Bearer`.

- RBAC resources (all require Bearer JWT):
- Roles
  - `POST /api/v1/rbac/roles` — create role
  - `GET /api/v1/rbac/roles` — list roles
  - `PATCH /api/v1/rbac/roles/{role_id}` — update role
- Permissions
  - `GET /api/v1/rbac/permissions` — list permissions
  - `POST /api/v1/rbac/permissions` — grant permission to role
  - `POST /api/v1/rbac/permission-fields` — grant permission field to role
  - `PATCH /api/v1/rbac/roles/{role_id}/permissions/{permission_id}/fields/{field_id}` — update permission field effect
  - `DELETE /api/v1/rbac/roles/{role_id}/permissions/{permission_id}` — revoke permission from role
  - `DELETE /api/v1/rbac/roles/{role_id}/permissions/{permission_id}/fields/{field_id}` — revoke permission field
- User ↔ Role
  - `POST /api/v1/rbac/roles/{role_id}/users/{user_id}` — assign role to user
  - `DELETE /api/v1/rbac/roles/{role_id}/users/{user_id}` — unassign role from user
- User-centric
  - `GET /api/v1/rbac/users/{user_id}/roles` — list user roles
  - `GET /api/v1/rbac/users/{user_id}/permissions` — list user permissions

- Scopes and fields
- Scopes: `OWN` vs `ANY` determine whether a user can act on own vs any resource.
- Permission fields allow fine-grained allow/deny over request sources: `QUERY` and `JSON`.
- Controllers annotate required permissions via `PermissionSpec` and attach rules with `@add_rule(...)`.

## Architecture and project layout

```plaintext
.
├── metrics/              # Grafana, Prometheus, Loki, Vector
├── nginx/                # Nginx (reverse proxy, SSL) — optional
├── sql/                  # Scripts (init, pg_hba)
├── src/
│   ├── backend/
│   │   ├── app/          # domain: bus, use_cases, dto, contracts
│   │   ├── http/         # controllers, middlewares, HTTP DTOs
│   │   └── infra/        # database, cache, security, shared
│   └── config/           # configuration (pydantic-settings)
├── tests/                # integration tests
├── docker-compose.yml    # profiles: api, grafana, prometheus
├── Dockerfile            # service image (uv)
└── pyproject.toml        # dependencies and tools
```

## Notes

- Switch server type via `SERVER_TYPE` (`granian` | `uvicorn` | `gunicorn`).
- API base prefix is controlled by `APP_ROOT_PATH` (default `/api`).
- OpenAPI UI is available when `APP_SWAGGER=true`.
- Container logs are collected by Vector and shipped to Loki; metrics are available in Prometheus/Grafana.
