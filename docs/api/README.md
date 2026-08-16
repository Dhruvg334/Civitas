# Civitas API

The FastAPI service is the operational boundary for report intake, media, incidents, workflow execution, routing, work orders, clarification, resolution, identity, and safe execution traces.

## API principles

- All write operations are validated with typed Pydantic models.
- Role-gated actions are authorized by the backend, not by frontend presentation state.
- Public responses use a consistent Civitas success/error envelope.
- Workflow execution is exposed through stable workflow IDs while LangGraph checkpoint state remains internal.
- Internal service credentials are never required by browser clients.
- Operational records retain trace IDs so decisions can be correlated across API, workflow, knowledge, and ML layers.

## Documentation map

- [`INTEGRATION.md`](INTEGRATION.md) — end-to-end API and workflow integration
- [`STATE_MACHINE.md`](STATE_MACHINE.md) — incident and work-order lifecycle invariants
- [`apps/api/OPENAPI.md`](../../apps/api/OPENAPI.md) — route-level request/response reference
- [`apps/api/README.md`](../../apps/api/README.md) — package setup, configuration and local execution
- [`../runtime-integration.md`](../runtime-integration.md) — LangGraph runtime composition and resume semantics

## Core route groups

### Identity and health

- `GET /live`
- `GET /ready`
- `GET /api/v1/me`

### Reports and media

- report creation and retrieval
- media registration/upload
- signed media access
- report clarification records

### Incidents and municipal operations

- incident retrieval and spatial queries
- report-to-incident linkage
- assessments
- routing decisions
- work orders
- reviewer transitions
- resolution submissions

### Workflow runtime

- `POST /api/v1/reports/{report_id}/workflow`
- `GET /api/v1/workflows/{workflow_id}`
- `POST /api/v1/workflows/{workflow_id}/clarification`
- `POST /api/v1/workflows/{workflow_id}/review`

These endpoints expose the application-safe workflow surface. LangGraph's internal checkpoint representation is not returned to clients.

## Error envelope

Operational errors retain machine-readable codes and trace identifiers. Authentication errors, forbidden actions, invalid transitions, schema failures, missing resources, and dependency failures are surfaced as failures rather than converted into successful fallback responses.

## Authentication

Browser clients authenticate with real Supabase access-token JWTs. Production startup requires JWT verification configuration. Service-to-service endpoints use separate internal credentials and are not exposed through browser environment variables.

## Persistence

Application migrations define reports, incidents, media, assessments, routing, work orders, clarification, resolution, policies, traces, and workflow-run metadata. LangGraph PostgreSQL checkpoint tables are managed by the LangGraph saver and remain separate from application workflow metadata.
