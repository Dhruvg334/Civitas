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

## Map-link extraction (utility)

| Method | Path | Role |
|---|---|---|
| `POST` | `/api/v1/map-extract` | open |

Accepts a Google Maps or OpenStreetMap share URL and returns the
embedded `(latitude, longitude)`. Pure string-parsing utility — no DB,
no private state. The intended flow is:

```
map URL  →  POST /api/v1/map-extract  →  (lat, lon)
                                         ↓
                              POST /api/v1/reports (with that location)
```

**Request:**

```json
{ "url": "https://www.google.com/maps/@28.6139,77.2090,15z" }
```

**Success (200):**

```json
{
  "success": true,
  "data": { "latitude": 28.6139, "longitude": 77.2090, "url": "..." },
  "trace_id": "...",
  "timestamp": "..."
}
```

**Errors (all 422):**

| Code | When |
|---|---|
| `VALIDATION_ERROR` | `payload.url` missing or empty |
| `MAP_LINK_INVALID` | URL did not match a supported pattern |
| `MAP_LINK_OUT_OF_RANGE` | Extracted coords outside [-90,90] / [-180,180] |

**Supported formats:**

- Google Maps `/@lat,lon,zoom` — `https://www.google.com/maps/@28.6139,77.2090,15z`
- Google Maps `/place/.../@lat,lon,zoom` — `https://www.google.com/maps/place/Sunrise+School/@28.6139,77.2090,17z`
- Google Maps `?q=lat,lon` — `https://maps.google.com/?q=28.6139,77.2090`
- Google Maps `?ll=lat,lon` — `https://maps.google.com/?ll=28.6139,77.2090`
- Google Maps `?center=lat,lon` — same shape
- Google Maps URL-encoded — `?q=28.6139%2C77.2090`
- OpenStreetMap `?mlat=lat&mlon=lon` — `https://www.openstreetmap.org/?mlat=28.6139&mlon=77.2090#map=15/28.6139/77.2090`
- OpenStreetMap `?lat=lat&lon=lon` — bare form
- Plain `lat,lon` string (no scheme) — `28.6139,77.2090`

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