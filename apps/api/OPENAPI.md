# Civitas API — Route Tour

> **Integrating?** See [`docs/api/INTEGRATION.md`](../../docs/api/INTEGRATION.md)
> first for the end-to-end recipe. This doc is the per-route reference.

Base path: `/api/v1`. All requests require `Authorization: Bearer <jwt>`.
Common envelope: `{success, data, trace_id, timestamp}` on success,
`{success:false, error:{code,message,retryable}, trace_id, timestamp}` on error.

The full OpenAPI spec is served at `GET /openapi.json` (and rendered
visually at `GET /docs`).

## Reports + incidents (Tier 1, ships since 12 Aug)

| Method | Path | Role | Notes |
|---|---|---|---|
| `POST` | `/reports` | citizen | Create incident. Returns `incident_id`. |
| `GET` | `/reports/{id}` | citizen | Read one. |
| `POST` | `/reports/{id}/media` | citizen | Multipart upload. Allowlist: png, jpeg, webp, mp4, webm, mov, mkv. Max 50 MB. |
| `GET` | `/reports/{id}/media` | citizen | List media for the report with signed URLs. |
| `POST` | `/reports/{id}/clarifications` | triage | Ask a batch of questions. |
| `POST` | `/reports/{id}/clarifications/{qid}/answer` | citizen | Persist answer. |
| `GET` | `/reports/{id}/clarifications` | triage | List all clarifications. |
| `GET` | `/incidents` | triage | Paginated list with `?status=&category=&since=`. |
| `GET` | `/incidents/{id}` | triage | Detail. |
| `POST` | `/incidents/{id}/merge` | supervisor | Idempotent link to a duplicate report. |
| `POST` | `/incidents/{id}/assess` | triage | Persist severity + priority + write trace. |
| `POST` | `/incidents/{id}/route` | supervisor | Persist routing decision + write trace. |
| `POST` | `/incidents/{id}/work-orders` | supervisor | Create WO. |
| `GET` | `/incidents/{id}/route` | triage | List routing decisions. |
| `POST` | `/incidents/{id}/resolution-submissions` | triage | Store Pavit's resolution-verify output. |
| `POST` | `/incidents/{id}/resolve` | reviewer | Final close: `resolved` / `partially_resolved` / `reopened`. |
| `GET` | `/incidents/{id}/trace` | triage | Ordered agent/ML trace events. |

## Work orders

| Method | Path | Role |
|---|---|---|
| `GET` | `/work-orders/{id}` | triage |
| `PUT` | `/work-orders/{id}` | supervisor |
| `POST` | `/work-orders/{id}/approve` | reviewer |
| `POST` | `/work-orders/{id}/reject` | reviewer |

## Policies / playbooks

| Method | Path | Role | Notes |
|---|---|---|---|
| `GET` | `/policies` | triage | Filters: `?category=&department=&kind=&limit=` |
| `GET` | `/policies/{code}` | triage | One by code |

## Geospatial (Passthrough to Pavit's `civitas_geo`)

| Method | Path | Role |
|---|---|---|
| `GET` | `/incidents/nearby` | open (city-aware) |
| `GET` | `/incidents/{id}/candidates` | open |
| `GET` | `/landmarks/nearby` | open |
| `GET` | `/incidents/nearby/density` | open |

## Ops

| Method | Path | Role |
|---|---|---|
| `GET` | `/health` | open |
| `GET` | `/ready` | open |

## Sample curl

```bash
TOK="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1MSIsInJvbGUiOiJzdXBlcnZpc29yIn0.<signature>"
H="Authorization: Bearer $TOK"

# Submit a report
curl -X POST http://localhost:8000/api/v1/reports \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"description":"water on road","location":{"latitude":20.2961,"longitude":85.8245},"citizen_selected_category":"water_leakage"}'

# Attach a photo
curl -X POST http://localhost:8000/api/v1/reports/inc-xxx/media \
  -H "$H" -F "file=@photo.jpg;type=image/jpeg"

# Approve a work order (as reviewer)
curl -X POST http://localhost:8000/api/v1/work-orders/wo-xxx/approve -H "$H"
```