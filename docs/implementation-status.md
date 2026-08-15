# Civitas Implementation Status

## Runtime Composition

- [x] Production workflow composition factory exists (`create_production_workflow`).
- [x] Reusable test runtime fixture is available for offline deterministic testing.
- [x] PostgreSQL saver lifecycle is owned by FastAPI lifespan when configured.
- [x] SQLite execution cleanly skips PostgreSQL saver initialization for offline runs.
- [x] Workflow metadata supplies a stable thread identifier.

## Workflow API, Persistence, and Golden Slice

- [x] Start, status, clarification, and review routes exist and are tested.
- [x] Narrow edit (`EditableWorkOrder`) and reroute (`RoutingOverride`) schemas are implemented and schema-validated.
- [x] Backend persistence adapters and operational state management are complete.
- [x] Golden FastAPI start-to-review-to-approval integration test passes.
- [x] Same-thread LangGraph resume from human review and clarification gates verified.

## Evaluation & Benchmarking

- [x] Offline 25-case deterministic contract corpus and runner exist.
- [x] Real Baseline A (one-call unstructured) exists.
- [x] Real Baseline B (one-call structured JSON-Schema) exists.
- [x] Multi-agent Civitas graph evaluator exists.
- [x] Deterministic offline evaluation outputs and metrics recorded.
- [ ] Live Groq external provider evaluation (manual future execution path; not claimed as completed).

## Frontend & Integration Layer

- [x] Frontend connected to canonical FastAPI backend endpoints.
- [x] Zero hardcoded/fabricated bearer tokens in browser client.
- [x] Explicit demo mode toggle (`NEXT_PUBLIC_CIVITAS_DEMO_MODE=true`).
- [x] Real citizen report submission wired with LangGraph workflow initiation.
- [x] Supervisor review UI wired to `POST /api/v1/workflows/{id}/review`.
- [x] Citizen clarification UI wired to `POST /api/v1/workflows/{id}/clarification`.
- [x] Fabricated precise percentages and fake telemetry removed/relabelled.
- [x] Production Next.js 16 build passing.
