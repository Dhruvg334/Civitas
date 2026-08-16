# Civitas API Service

FastAPI operational service for Civitas. The API owns authenticated report/media intake, incident state, routing/work orders, clarification, resolution, workflow runtime endpoints, safe traces, and the backend-verified user identity surface.

## Runtime

- Python 3.12
- FastAPI + Pydantic
- PostgreSQL/Supabase
- PostGIS through the geospatial package
- Supabase Storage for production media
- LangGraph PostgreSQL saver for workflow checkpoints

## Configuration

Server configuration is read from environment variables. See `.env.example` and [`../../docs/DEPLOYMENT_GUIDE.md`](../../docs/DEPLOYMENT_GUIDE.md) for the production topology.

Key variables include:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Operational PostgreSQL connection |
| `CIVITAS_POSTGIS_DSN` | PostGIS connection used by geospatial operations |
| `CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL` | LangGraph checkpoint database |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-only Storage/Admin access |
| `SUPABASE_JWT_SECRET` | Production JWT verification |
| `CIVITAS_INTERNAL_API_KEY` | Internal ML/runtime authentication |
| `GROQ_API_KEY` | Server-side LLM provider credential |
| `CORS_ORIGINS` | Allowed browser origins |
| `CIVITAS_ENV` | Runtime environment |

Production startup validates required security configuration and keeps internal/server credentials out of browser code.

## Local execution

```bash
python -m pip install -e .
python -m uvicorn civitas_api.main:app --reload
```

Swagger UI is served at `/docs`; the OpenAPI document is served at `/openapi.json`.

## Database migrations

Apply application migrations in order:

```bash
psql "$DATABASE_URL" -f ../../database/migrations/0001_spatial_core.sql
psql "$DATABASE_URL" -f ../../database/migrations/0002_incident_description.sql
psql "$DATABASE_URL" -f ../../database/migrations/0003_incident_operations.sql
psql "$DATABASE_URL" -f ../../database/migrations/0004_workflow_core.sql
psql "$DATABASE_URL" -f ../../database/migrations/0005_seed_policies.sql
psql "$DATABASE_URL" -f ../../database/migrations/0006_workflow_runs.sql
```

Deterministic policy/demo seed data is stored under `database/seed/`. LangGraph checkpoint tables are managed independently by the PostgreSQL saver.

## Roles

Backend authorization follows the hierarchy:

`citizen < triage < supervisor < reviewer < admin`

| Role | Operational scope |
|---|---|
| `citizen` | report creation, media, workflow start, clarification |
| `triage` | incident visibility, assessments, policies, workflow status |
| `supervisor` | merge, routing, work-order creation/update |
| `reviewer` | workflow review, work-order approval/rejection, resolution decisions |
| `admin` | full operational scope |

Frontend role presentation is not an authorization boundary; every protected mutation is validated again by FastAPI.

## Package layout

```text
apps/api/src/civitas_api/
├── core/          auth, config, DB, envelopes, spatial/storage adapters
├── operations/    report, incident, routing, work-order, workflow metadata logic
├── routers/       public/internal HTTP surfaces
├── services/      workflow runtime/composition
└── main.py        FastAPI application and lifespan
```

## Testing

```bash
python -m pytest apps/api/tests
```

The API test profile uses SQLite where PostGIS behavior is not required and injects deterministic runtime dependencies for workflow tests. The golden integration slice exercises the real FastAPI application, local ML pipeline, knowledge service, LangGraph graph, workflow runtime, persisted routing/work-order data, human-review resume, trace persistence, and idempotency.

## References

- [`OPENAPI.md`](OPENAPI.md) — route inventory and request/response shapes
- [`../../docs/api/INTEGRATION.md`](../../docs/api/INTEGRATION.md) — end-to-end runtime integration
- [`../../docs/api/STATE_MACHINE.md`](../../docs/api/STATE_MACHINE.md) — incident/work-order transitions
- [`../../docs/runtime-integration.md`](../../docs/runtime-integration.md) — checkpoint/resume architecture
