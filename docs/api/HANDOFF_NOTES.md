# Civitas API — Handoff Notes

> **Integrating against this backend?** Read [`INTEGRATION.md`](INTEGRATION.md)
> first — it has the golden-scenario recipe and the troubleshooting table.
> This doc covers limitations, secret handling, and the design decisions
> that aren't obvious from the code.

## Scope delivered (Tier 1 + Tier 2)

Everything in `apps/api` is ready for integration testing against the
golden scenario. Specifically:

- Auth + 5-role gating with dev-mode bypass for tests
- Common success/error envelope
- PostGIS-backed incidents (live on Supabase)
- 13 routes listed in ref/04 §15 that fall under backend ownership
- Work-order state machine + reviewer approve/reject/close actions
- 11 seeded policies/playbooks (5 playbooks + 6 general policies) per ref/08
- 3-incident golden scenario pre-seeded per ref/07

## Known limitations

### LAZ / TIFF / map-formatted files

Not implemented.

### Clarification: `decision_impact` is not enforced

The contract says clarifications have `decision_impact` ("severity",
"priority", "routing", etc.). We persist the value verbatim but do not
use it to drive any backend decision — that responsibility sits with
the agent workflow. We treat `decision_impact` as an audit-tag only.

### Routing: model_version stored, not consumed

We persist `workflow_version` on routing decisions and `model_version`
on assessments / resolutions. We do not version our responses by
model_version. If a workflow re-runs with a newer model, the new
routing is appended (no replacement of older entries).

### Resolutions: no separate `verifier` flag

The reviewer who calls `POST /incidents/{id}/resolve` is recorded in
`agent_traces.node='reviewer_action'` but the `resolution_submissions`
table does not carry the reviewer's `user_id`. If you need that link,
add a column on `resolution_submissions` in a future migration.

### Storage adapter auto-switch

`get_storage()` picks the Supabase Storage adapter when `SUPABASE_URL`
+ `SUPABASE_SERVICE_ROLE_KEY` are set; otherwise it falls back to
LocalDisk under `./storage`. There is no explicit env flag — the
switch is automatic based on env presence. If you want to force a
specific adapter, set `CIVITAS_STORAGE_ROOT` to override the
fallback path even when Supabase is configured.

### Idempotency keys

We don't yet support client-provided `Idempotency-Key` headers. Work
orders and merges are idempotent on natural keys (incident_id,
question_id), so retry safety is implicit. Other writes (assess,
route, resolve) are not retried by the API — clients should retry
the whole operation if they get a transient 5xx.

## Adapter choices

| Concern | Choice | Why |
|---|---|---|
| HTTP framework | FastAPI | Pydantic v2, async support, OpenAPI auto-gen |
| Database driver | psycopg 3 | Native async, dict-row factory, Supabase pooler compatible |
| Storage | Supabase Storage (production) / LocalDisk (dev) | One path, two backends |
| JWT | PyJWT | HS256, dev-mode skip-signature behind empty secret |
| State machine | Application-level dict | DB only enforces values; transitions are app concern |
| Idempotency | DB-level UNIQUE on `(incident_id, report_id)` for merges; app-level for everything else |

## Secrets

| Secret | Where | Notes |
|---|---|---|
| `DATABASE_URL` | .env / CI / Render env | Supabase pooler DSN |
| `SUPABASE_SERVICE_ROLE_KEY` | .env / CI / Render env | Server-side only; never sent to clients |
| `SUPABASE_JWT_SECRET` | .env / CI / Render env | Required in production |

`SUPABASE_ANON_KEY` is reserved for future client-side use; not consumed today.

## Cross-team dependencies

| From | What | Status |
|---|---|---|
| Pavit | `civitas_geo` Python package | Installed as editable via `services/spatial/pyproject.toml` |
| Pavit | Resolution-verify ML model | We persist the output; model runs out of scope |
| Dhruv | Agent workflow | We expose persistence endpoints; agent runs out of scope |

## What's deliberately NOT in this codebase

- Frontend (Dhruv's `apps/web`)
- Agent orchestration (Dhruv's `services/workflow`)
- Knowledge grounding (Dhruv's `services/knowledge`)
- Vision / duplicate / severity / resolution ML models (Pavit)
- LAZ / TIFF ingestion (deferred)
- Rate limiting (use Vercel/Render edge in front)
- WebSocket / push notifications (citizen updates batched in the next phase)

## How to bring up a fresh environment

```bash
# 1. Install Python deps
cd apps/api && python -m pip install -e .
python -m pip install -e ../spatial

# 2. Apply migrations (in order)
for f in ../../database/migrations/00*.sql; do
  psql "$DATABASE_URL" -f "$f"
done

# 3. (Optional) apply seeds
psql "$DATABASE_URL" -f ../../database/seed/0001_demo_landmarks.sql
psql "$DATABASE_URL" -f ../../database/seed/0002_golden_scenario.sql

# 4. Boot
python -m uvicorn civitas_api.main:app --host 0.0.0.0 --port 8000
```

OpenAPI: `http://localhost:8000/docs`

For the integration playbook (golden-scenario recipe, troubleshooting,
expected wire format), see [`INTEGRATION.md`](INTEGRATION.md).