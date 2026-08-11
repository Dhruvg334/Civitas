# Civitas Backend Integration Guide

This is the **start-here doc** for integrating the Civitas backend with the
agent workflow, frontend, and ML services. If you only have time to read
one backend doc, read this one.

The other docs in `docs/api/` and `apps/api/` cover specific concerns:

| Doc | When to read |
|---|---|
| [`docs/api/INTEGRATION.md`](INTEGRATION.md) | Always — start here |
| [`apps/api/README.md`](../../apps/api/README.md) | Backend dev setup, env vars, pytest |
| [`apps/api/OPENAPI.md`](../../apps/api/OPENAPI.md) | Full route reference with curl examples |
| [`docs/api/STATE_MACHINE.md`](STATE_MACHINE.md) | Incident + work-order transition graphs |
| [`docs/api/HANDOFF_NOTES.md`](HANDOFF_NOTES.md) | Known limitations, secrets, adapter choices |

---

## TL;DR for the 14 Aug integration

The backend is ready. Production data is seeded. You can run the golden
scenario against `inc-golden-A` immediately — no need to apply migrations
or create fixtures.

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Hit the seeded incident
curl -H "Authorization: Bearer $JWT" \
     http://localhost:8000/api/v1/incidents/inc-golden-A

# 3. Approve the seeded work order (your agent workflow drives the rest)
curl -X POST -H "Authorization: Bearer $REVIEWER_JWT" \
     http://localhost:8000/api/v1/work-orders/wo-golden-A-01/approve
```

---

## What the backend does for you

```
┌──────────────┐    POST /reports           ┌──────────────┐
│   Citizen    │ ─────────────────────────▶ │              │
└──────────────┘                            │              │
                                            │   Backend    │
┌──────────────┐    POST /reports/{id}/media │              │
│   Citizen    │ ─────────────────────────▶ │   (this)     │
└──────────────┘                            │              │
                                            │              │
┌──────────────┐    POST /incidents/{id}/   │              │
│   Agent      │     merge | assess | route │              │
│   workflow   │ ─────────────────────────▶ │              │
└──────────────┘                            │              │
                                            │              │
┌──────────────┐    POST /incidents/{id}/   │              │
│   Reviewer   │     resolve                │              │
│   (human)    │ ─────────────────────────▶ │              │
└──────────────┘                            └──────────────┘
```

The backend **does not**:

- Generate clarification questions (that's your job, Dhruv)
- Decide routing (your job — we just persist)
- Run ML models (Pavit's job — we just persist the output)
- Build a UI (your job, frontend)

The backend **does**:

- Persist every state change with audit trail
- Enforce the state machine (return 409 INVALID_STATE on illegal moves)
- Authenticate every request with role-based gates
- Store all media with signed URLs
- Expose the policies + playbooks for grounding

---

## The golden scenario, step by step

The seeded data: `inc-golden-A` is the main incident, with `inc-golden-B`
and `inc-golden-C` already linked as duplicates. A work order
`wo-golden-A-01` is at `awaiting_review`. A routing decision is logged.
A clarification answer is recorded.

Here's how an agent workflow walks the rest of the loop:

### Step 1 — read the current incident

```bash
curl -H "Authorization: Bearer $TRIAGE_JWT" \
     http://localhost:8000/api/v1/incidents/inc-golden-A
```

Returns:

```json
{
  "success": true,
  "data": {
    "incident_id": "inc-golden-A",
    "status": "awaiting_review",
    "duplicates_seen": 3,
    "assigned_department": "water_supply",
    "latest_assessment": { ... risk-v1 severity=78, priority=91 ... },
    "media_count": 0,
    "linked_reports_count": 2
  }
}
```

### Step 2 — read the routing decision (if you generated one)

```bash
curl -H "Authorization: Bearer $TRIAGE_JWT" \
     http://localhost:8000/api/v1/incidents/inc-golden-A/route
```

### Step 3 — read the work order

```bash
curl -H "Authorization: Bearer $TRIAGE_JWT" \
     http://localhost:8000/api/v1/work-orders/wo-golden-A-01
```

### Step 4 — read the audit trail (full timeline)

```bash
curl -H "Authorization: Bearer $TRIAGE_JWT" \
     http://localhost:8000/api/v1/incidents/inc-golden-A/trace
```

Returns events in `created_at` order. Each event has `node`,
`model_version`, `input`, `output`, `validation_outcome`.

### Step 5 — wait for the reviewer to approve

The reviewer (a human) hits:

```bash
curl -X POST -H "Authorization: Bearer $REVIEWER_JWT" \
     http://localhost:8000/api/v1/work-orders/wo-golden-A-01/approve
```

Side effects:
- Work order: `awaiting_review` → `approved`
- Incident: `awaiting_review` → `assigned`
- Incident: `assigned_work_order_id` set to `wo-golden-A-01`
- One row appended to `agent_traces` with `node='work_order_approve'`

### Step 6 — the field worker does the work

Out of scope for the backend. Once they're done, your agent (or Pavit's
resolution-verify ML) submits a resolution:

```bash
curl -X POST -H "Authorization: Bearer $TRIAGE_JWT" \
     -H "Content-Type: application/json" \
     -d '{
       "classification": "partially_resolved",
       "resolved_evidence": ["active flow no longer visible"],
       "remaining_evidence": ["standing water remains near footpath"],
       "uncertainties": ["drainage outside frame"],
       "model_version": "resolution-verify-v1"
     }' \
     http://localhost:8000/api/v1/incidents/inc-golden-A/resolution-submissions
```

Side effects:
- One row in `resolution_submissions`
- Incident: `in_progress` → `resolution_submitted` → `verification_pending`
- Incident: `resolution_class` set to `partially_resolved`

### Step 7 — reviewer closes the loop

```bash
curl -X POST -H "Authorization: Bearer $REVIEWER_JWT" \
     -H "Content-Type: application/json" \
     -d '{"action": "partially_resolved"}' \
     http://localhost:8000/api/v1/incidents/inc-golden-A/resolve
```

Side effects:
- Incident: `verification_pending` → `partially_resolved`
- One row in `agent_traces` with `node='reviewer_action'`

### Step 8 — list everything for the citizen update

```bash
curl -H "Authorization: Bearer $TRIAGE_JWT" \
     "http://localhost:8000/api/v1/incidents?status=partially_resolved"
```

Note: `partially_resolved` is what golden §12 expects ("active flow has
stopped but standing water remains"). See STATE_MACHINE.md for the
re-open path.

---

## Creating a new incident from scratch

If you want to test the full pipeline (not just consume the seeded data):

```bash
# Submit a report
curl -X POST -H "Authorization: Bearer $CITIZEN_JWT" \
     -H "Content-Type: application/json" \
     -d '{
       "description": "pothole near the school gate",
       "location": {"latitude": 20.2961, "longitude": 85.8245},
       "citizen_selected_category": "pothole"
     }' \
     http://localhost:8000/api/v1/reports
# Returns { "data": { "report_id": "inc-..." } }

# Attach an image
curl -X POST -H "Authorization: Bearer $CITIZEN_JWT" \
     -F "file=@photo.jpg;type=image/jpeg" \
     http://localhost:8000/api/v1/reports/inc-.../media
# Returns { "data": { "media_id": "med-...", "signed_url": "https://..." } }
```

The `signed_url` is what you hand to Pavit's ML service for vision
analysis. It's a 1-hour URL.

---

## Common envelope

Every response is one of:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "trace_id": "uuid",
  "timestamp": "2026-08-12T00:00:00Z"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATE",
    "message": "incident cannot transition 'resolved' -> 'assigned'",
    "retryable": false
  },
  "trace_id": "uuid",
  "timestamp": "2026-08-12T00:00:00Z"
}
```

Error codes you'll see:

| Code | HTTP | When |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Payload missing a required field |
| `INVALID_STATE` | 409 | State machine rejects the transition |
| `UNSUPPORTED_MEDIA` | 415 | MIME type not in allowlist |
| `EMPTY_FILE` | 400 | Uploaded file is 0 bytes |
| `FILE_TOO_LARGE` | 413 | Upload exceeds 50 MB |
| `PERSISTENCE_ERROR` | 500 | DB write failed |
| `STORAGE_ERROR` | 500 | Storage adapter failed |
| `LOCATION_PLACEHOLDER` | 400 | (0,0) coordinates — sentinel value |

---

## Auth in dev mode

Without `SUPABASE_JWT_SECRET` set, the backend accepts any HS256 JWT
without checking the signature. The token must still decode to a dict
with `sub` and `role`. For production, set the secret.

Roles (lowest to highest):

```
citizen < triage < supervisor < reviewer < admin
```

Required role for each operation is documented in [`apps/api/OPENAPI.md`](../../apps/api/OPENAPI.md).

To mint a dev token from claim dict:

```python
import jwt
tok = jwt.encode(
    {"sub": "u-1", "role": "supervisor"},
    "any-string-at-least-one-char",
    algorithm="HS256",
)
```

Use the token in the `Authorization: Bearer <token>` header.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| 401 on every request | JWT missing `sub` or wrong header | `Authorization: Bearer <token>` |
| 403 on a write | Role too low | Mint a token with the role that matches the route |
| 409 with `INVALID_STATE` | Lifecycle edge blocked | Check STATE_MACHINE.md; the incident or WO is past the target state |
| 422 with `VALIDATION_ERROR` | Payload missing a required field | See `OPENAPI.md` for the required payload per route |
| 415 on media upload | MIME not in allowlist | Allowlist: png, jpeg, jpg, webp, mp4, webm, mov, mkv |
| Server boots but `psycopg.OperationalError` | DB not reachable | Check `DATABASE_URL`; for local dev use `sqlite:///./test.db` |
| `/api/v1/incidents/inc-golden-A` 404 | Seed not applied | Apply `database/seed/0002_golden_scenario.sql` |
| `signed_url` is `local://` not `https://` | LocalDisk adapter in use | Set `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` envs |

---

## What lives where

- **Code**: `apps/api/src/civitas_api/{core,operations,routers}`
- **Routes**: `apps/api/src/civitas_api/routers/{reports,incidents,incidents_ops,media,work_orders,clarifications,routing,resolutions,policies}.py`
- **State machine**: `apps/api/src/civitas_api/operations/state_machine.py`
- **Schema**: `database/migrations/0001–0005.sql`
- **Seeds**: `database/seed/0001_demo_landmarks.sql`, `0002_golden_scenario.sql`
- **Tests**: `apps/api/tests/test_*.py`

---

## What is NOT in this backend

- Frontend (`apps/web` — Dhruv)
- Agent orchestration (`services/workflow` — Dhruv)
- Knowledge grounding (`services/knowledge` — Dhruv)
- ML models (`services/spatial`, `services/ml` — Pavit)
- LAZ/TIFF/map ingestion (deferred)
- Rate limiting (use edge proxy)

See [`docs/api/HANDOFF_NOTES.md`](HANDOFF_NOTES.md) for the full
limitations list.
