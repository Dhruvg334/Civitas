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
- [x] Verified user identity and role endpoint `GET /api/v1/me` implemented and tested.

## Evaluation & Benchmarking

- [x] Offline 25-case deterministic contract corpus and runner exist.
- [x] Real Baseline A (one-call unstructured) exists.
- [x] Real Baseline B (one-call structured JSON-Schema) exists.
- [x] Multi-agent Civitas graph evaluator exists.
- [x] Deterministic offline evaluation outputs and metrics recorded.
- [ ] Live Groq external provider evaluation (manual future execution path; requires live production API key).

## Frontend & Integration Layer

- [x] Real Supabase authentication abstraction with `@supabase/supabase-js` without fabricated browser tokens.
- [x] Verified user role derived from backend `GET /api/v1/me` and trusted session claims.
- [x] Explicit demo mode isolation (`NEXT_PUBLIC_CIVITAS_DEMO_MODE=true`) with visible persona switcher disclaimers.
- [x] Real citizen report submission (`POST /api/v1/reports`) wired with LangGraph workflow initiation (`POST /api/v1/reports/{id}/workflow`).
- [x] Real multipart media upload (`POST /api/v1/reports/{id}/media`) with client validation (MIME allowlist, max 50MB limit) and object URL cleanup.
- [x] Geolocation integrity: browser geolocation failure does not inject silent fake coordinates in production.
- [x] Citizen clarification UI wired to `POST /api/v1/workflows/{id}/clarification` with retry on failure.
- [x] Municipal supervisor review UI wired to `POST /api/v1/workflows/{id}/review` with all 5 review operations (`approve`, `edit`, `reroute`, `reject`, `request_more_evidence`).
- [x] Centralized incident taxonomy (`apps/web/src/lib/taxonomy.ts`) reconciled against `civitas_vision.contracts`.
- [x] Fabricated precise percentages and fake telemetry removed/relabelled as illustrative traces.
- [x] Production Next.js 16 build, TypeScript typecheck, ESLint, Vitest, and Pytest passing.
