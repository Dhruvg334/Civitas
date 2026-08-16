# Production Deployment

Civitas uses a three-service production topology:

- **Web:** Vercel — `https://civitas-web.vercel.app`
- **API/runtime:** Render — Dockerized FastAPI service
- **Data/auth/storage:** Supabase — PostgreSQL, PostGIS, Auth, Storage

The browser communicates only with public authenticated API routes. Server-only Supabase, workflow, database, and Groq credentials remain on the API service.

## Database schema

Apply the application migrations in order:

```bash
psql "$DATABASE_URL" -f database/migrations/0001_spatial_core.sql
psql "$DATABASE_URL" -f database/migrations/0002_incident_description.sql
psql "$DATABASE_URL" -f database/migrations/0003_incident_operations.sql
psql "$DATABASE_URL" -f database/migrations/0004_workflow_core.sql
psql "$DATABASE_URL" -f database/migrations/0005_seed_policies.sql
psql "$DATABASE_URL" -f database/migrations/0006_workflow_runs.sql
```

`workflow_runs` stores application metadata only. LangGraph's PostgreSQL saver initializes and owns its checkpoint tables through `create_postgres_checkpointer().setup()` using `CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL`.

## Render API service

Render uses the repository `render.yaml` and `apps/api/Dockerfile`.

### Required server environment

| Variable | Purpose |
|---|---|
| `CIVITAS_ENV=production` | Enables production validation and fail-closed auth configuration |
| `DATABASE_URL` | PostgreSQL operational database |
| `CIVITAS_POSTGIS_DSN` | PostGIS connection used by geospatial operations |
| `CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL` | PostgreSQL connection for LangGraph checkpoints |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase project public key used by server integrations where required |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-only Storage/Admin access |
| `SUPABASE_JWT_SECRET` | Backend JWT verification |
| `CIVITAS_INTERNAL_API_KEY` | Internal ML/runtime service authentication |
| `GROQ_API_KEY` | Production LLM provider credential |
| `CIVITAS_LLM_PRIMARY_MODEL` | Primary reasoning model |
| `CIVITAS_LLM_FAST_MODEL` | Lightweight structured-output model |
| `CORS_ORIGINS=https://civitas-web.vercel.app` | Production browser origin |

The container runs Python 3.12, installs the Civitas packages from their declared `pyproject.toml` dependency graphs, binds Uvicorn to `0.0.0.0:$PORT`, and uses one worker so application lifespan owns a single workflow/checkpointer resource set.

### Health endpoints

- `GET /live` — process liveness
- `GET /ready` — database-backed readiness

Render should use `/ready` as the health-check path.

## Vercel web application

The deployed web application is `https://civitas-web.vercel.app`.

### Public browser environment

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Render API base including `/api/v1` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase browser-safe public key |
| `NEXT_PUBLIC_CIVITAS_DEMO_MODE=false` | Keeps production paths on real APIs |

No service-role key, JWT secret, database credential, internal API key, or Groq key belongs in Vercel `NEXT_PUBLIC_*` variables.

## Supabase Auth

Configure the Supabase Authentication site URL as:

```text
https://civitas-web.vercel.app
```

Redirect URLs should include the deployed origin and the local development origin when local authentication is required. The frontend authenticates through Supabase, forwards the real access-token JWT to FastAPI, and uses `/api/v1/me` as the backend-verified identity/role surface.

## Production verification

A production verification pass covers:

1. `/live` and `/ready` on the API service;
2. authenticated `/api/v1/me`;
3. report creation with real coordinates;
4. media upload and media listing;
5. workflow start and status retrieval;
6. clarification resume when requested;
7. reviewer action on `WAITING_FOR_REVIEW`;
8. same-thread completion;
9. trace and work-order persistence;
10. CORS from `https://civitas-web.vercel.app`;
11. Groq structured-output smoke through the server-side provider configuration.

The deployment topology keeps deterministic offline evaluation separate from live provider execution; production credentials do not affect the reproducible offline artifacts stored in the repository.
