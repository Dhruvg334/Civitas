# Civitas API Route Reference

Base prefix for operational APIs: `/api/v1`.

FastAPI serves the machine-readable specification at `/openapi.json` and interactive Swagger UI at `/docs`.

## Response envelope

Successful Civitas routes return an envelope containing `success`, `data`, `trace_id`, and `timestamp`. Application errors preserve a machine-readable code/message and trace identifier where the route uses the Civitas envelope; FastAPI validation/auth errors retain their HTTP semantics.

## Health and identity

| Method | Path | Access | Purpose |
|---|---|---|---|
| `GET` | `/live` | public | Process liveness |
| `GET` | `/ready` | public | Database-backed readiness |
| `GET` | `/api/v1/me` | authenticated | Backend-verified identity and role |

## Reports

| Method | Path | Minimum role | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/reports` | citizen | Create a report with description and coordinates |
| `GET` | `/api/v1/reports/{report_id}` | citizen | Read stored report context |
| `POST` | `/api/v1/reports/{report_id}/media` | citizen | Upload report media |
| `GET` | `/api/v1/reports/{report_id}/media` | citizen | List report media and access metadata |
| `POST` | `/api/v1/reports/{report_id}/clarifications` | triage | Persist clarification questions |
| `POST` | `/api/v1/reports/{report_id}/clarifications/{question_id}/answer` | citizen | Persist a clarification answer |
| `GET` | `/api/v1/reports/{report_id}/clarifications` | triage | List clarification records |

`POST /api/v1/reports` expects a non-empty description and valid latitude/longitude. The response `report_id` maps to the persisted incident identifier used across spatial/operational routes.

## Incidents and geospatial context

| Method | Path | Minimum role | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/incidents` | triage | Paginated/filterable incident list |
| `GET` | `/api/v1/incidents/{incident_id}` | triage | Incident detail |
| `GET` | `/api/v1/incidents/nearby` | route-defined | Nearby incident search |
| `GET` | `/api/v1/incidents/{incident_id}/candidates` | route-defined | Duplicate candidate context |
| `GET` | `/api/v1/incidents/nearby/density` | route-defined | Local incident density |
| `GET` | `/api/v1/landmarks/nearby` | route-defined | Nearby landmark context |
| `POST` | `/api/v1/incidents/{incident_id}/merge` | supervisor | Link a duplicate report/incident |
| `POST` | `/api/v1/incidents/{incident_id}/assess` | triage | Persist severity/priority assessment |
| `POST` | `/api/v1/incidents/{incident_id}/trace` | internal/operational | Persist safe trace event |
| `GET` | `/api/v1/incidents/{incident_id}/trace` | triage | Read ordered safe trace events |

## Routing and work orders

| Method | Path | Minimum role | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/incidents/{incident_id}/route` | supervisor | Persist routing decision |
| `GET` | `/api/v1/incidents/{incident_id}/route` | triage | Read routing history |
| `POST` | `/api/v1/incidents/{incident_id}/work-orders` | supervisor | Create work order |
| `GET` | `/api/v1/work-orders/{work_order_id}` | triage | Read work order |
| `PUT` | `/api/v1/work-orders/{work_order_id}` | supervisor | Update permitted work-order fields |
| `POST` | `/api/v1/work-orders/{work_order_id}/approve` | reviewer | Approve work order |
| `POST` | `/api/v1/work-orders/{work_order_id}/reject` | reviewer | Reject work order |

## Resolution

| Method | Path | Minimum role | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/incidents/{incident_id}/resolution-submissions` | triage | Persist structured resolution-verification result |
| `GET` | `/api/v1/incidents/{incident_id}/resolution-submissions` | triage | Read resolution submissions |
| `POST` | `/api/v1/incidents/{incident_id}/resolve` | reviewer | Resolve, partially resolve, or reopen incident |

## Policies and playbooks

| Method | Path | Minimum role | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/policies` | triage | Filter policy/playbook corpus |
| `GET` | `/api/v1/policies/{code}` | triage | Retrieve one policy/playbook |

## Workflow runtime

| Method | Path | Minimum role | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/reports/{report_id}/workflow` | citizen | Start or reuse checkpointed workflow |
| `GET` | `/api/v1/workflows/{workflow_id}` | triage | Read safe workflow metadata/status |
| `POST` | `/api/v1/workflows/{workflow_id}/clarification` | citizen | Persist answers and resume same thread |
| `POST` | `/api/v1/workflows/{workflow_id}/review` | reviewer | Validate review action and resume same thread |

Review actions are `approve`, `edit`, `reroute`, `reject`, and `request_more_evidence`. `edit` and `reroute` use narrow typed schemas and reject unknown fields.

## Internal ML bridge

Routes under `/api/v1/ml` are server/internal integration surfaces protected by the internal API-key mechanism. They expose the unified ML analysis contract and adapter endpoints required by the workflow runtime. Browser clients do not receive or send the internal key.

## Map-link extraction

`POST /api/v1/map-extract` accepts supported Google Maps/OpenStreetMap share URLs and extracts validated coordinates for report creation. It performs parsing/validation only and does not access private incident state.

## State-machine behavior

Incident and work-order transitions are validated at the application layer. Illegal transitions return HTTP conflict responses rather than silently mutating state. See [`../../docs/api/STATE_MACHINE.md`](../../docs/api/STATE_MACHINE.md).
