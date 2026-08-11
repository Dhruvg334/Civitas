# Civitas API

FastAPI backend for the Civitas civic incident intelligence platform.

> **Integrating?** See [`docs/api/INTEGRATION.md`](../../docs/api/INTEGRATION.md)
> first — it has the 8-step golden-scenario recipe and the troubleshooting table.

## Setup

```bash
# Python 3.11+ (uses StrEnum from stdlib)
python -m pip install -e .
python -m pip install -e ../spatial  # if working from apps/api
```

Required environment variables — see `.env.example`:

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection (Supabase pooler). SQLite (`sqlite:///./test.db`) works for local dev without PostGIS. |
| `CIVITAS_POSTGIS_DSN` | Same value as DATABASE_URL; consumed by `services/spatial`. |
| `SUPABASE_URL` | Optional. If set with `SUPABASE_SERVICE_ROLE_KEY`, media uploads go to Supabase Storage. |
| `SUPABASE_SERVICE_ROLE_KEY` | Storage admin. |
| `SUPABASE_JWT_SECRET` | If empty, dev mode accepts any HS256 token without signature verification. Required in production. |
| `SUPABASE_ANON_KEY` | Future use. |
| `STORAGE_BUCKET` | Default `report-media`. |
| `CIVITAS_STORAGE_ROOT` | Where local-disk adapter writes. Default `./storage`. |
| `CIVITAS_ENV` | `development` \| `production` |
| `LOG_LEVEL` | Python log level. |
| `API_HOST` / `API_PORT` | `0.0.0.0` / `8000` |

## Running

```bash
# Local
python -m uvicorn civitas_api.main:app --reload

# Production-like
python -m uvicorn civitas_api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

OpenAPI spec is auto-served at `/openapi.json` and Swagger UI at `/docs`.

## Testing

```bash
python -m pytest -q
```

71 tests. Uses an isolated SQLite profile (per-test fresh DB) by default. To run against the real Supabase DB, set `DATABASE_URL=postgresql://…` before pytest.

## Migrations

```bash
# Schema
psql "$DATABASE_URL" -f ../../database/migrations/0001_spatial_core.sql
psql "$DATABASE_URL" -f ../../database/migrations/0002_incident_description.sql
psql "$DATABASE_URL" -f ../../database/migrations/0003_incident_operations.sql
psql "$DATABASE_URL" -f ../../database/migrations/0004_workflow_core.sql
psql "$DATABASE_URL" -f ../../database/migrations/0005_seed_policies.sql

# Demo data
psql "$DATABASE_URL" -f ../../database/seed/0001_demo_landmarks.sql
psql "$DATABASE_URL" -f ../../database/seed/0002_golden_scenario.sql
```

## Folder layout

```
apps/api/
├── src/civitas_api/
│   ├── core/           # auth, config, database, envelope, spatial, storage
│   ├── operations/     # state_machine, reports, work_orders,
│   │                   # clarifications, routing, resolutions, policies
│   ├── routers/        # one FastAPI router per resource
│   └── main.py         # FastAPI app entrypoint
└── tests/              # pytest suite (one file per resource)
```

## Roles

Five-tier hierarchy: `citizen < triage < supervisor < reviewer < admin`.

| Role | Can |
|---|---|
| citizen | submit reports, attach media, answer clarifications, list own media |
| triage | read all incidents, run assess, ask clarifications, list policies |
| supervisor | merge, route, create/edit work orders |
| reviewer | approve / reject / close / reopen |
| admin | unrestricted |

Every authenticated route resolves the caller via `Authorization: Bearer <jwt>`.
In dev mode (`SUPABASE_JWT_SECRET=""`) any token is accepted as long as it
decodes to a dict with `sub`. In production the secret is required.

See `docs/api/STATE_MACHINE.md` for the state-machine details.