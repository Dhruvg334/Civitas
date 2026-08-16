# Runtime Integration

The Civitas runtime connects FastAPI, LangGraph, the unified ML pipeline, policy grounding, persistence, and review APIs into one resumable workflow service.

## WorkflowRuntimeService

`WorkflowRuntimeService` owns workflow execution rather than placing orchestration logic inside route handlers. It creates or reuses workflow metadata, invokes the graph, maps interrupts to API-safe statuses, reads checkpointed state, resumes clarification/review commands, updates terminal metadata, and preserves idempotency.

## Workflow metadata

`workflow_runs` maps the operational workflow identifier to report/incident IDs, trace ID, LangGraph `thread_id`, status, interrupt type, and timestamps. It does not store graph state.

## Checkpoint lifecycle

Production composition uses LangGraph's PostgreSQL saver. The saver is initialized once through application lifespan, its schema setup is run in controlled startup, and the resource is reused for workflow execution. Test composition uses an in-memory saver while retaining the same graph and runtime behavior.

## Runtime API

- `POST /api/v1/reports/{report_id}/workflow` starts or reuses report processing.
- `GET /api/v1/workflows/{workflow_id}` returns safe workflow metadata/status.
- `POST /api/v1/workflows/{workflow_id}/clarification` persists an answer and resumes the same thread.
- `POST /api/v1/workflows/{workflow_id}/review` validates the review action and resumes the same thread.

## Status model

The API exposes application-level workflow states such as running, waiting for clarification, waiting for review, completed, rejected, and failed. Internal LangGraph checkpoint details are not part of the public API.

## Persistence adapters

The runtime uses backend operations for report context, ML analysis, knowledge retrieval, clarification, routing, work orders, review actions, citizen communication state, and traces. Real business records are persisted through canonical backend tables instead of being duplicated inside graph checkpoints.

## Golden runtime verification

The golden FastAPI integration slice executes the real test database, stored report context, local ML pipeline, knowledge service, LangGraph graph, WorkflowRuntimeService, routing/work-order persistence, and trace persistence. It reaches human review, resumes the same thread after approval, completes citizen communication, and verifies repeated start calls do not duplicate operational records. The external LLM is replaced with a deterministic test provider.
