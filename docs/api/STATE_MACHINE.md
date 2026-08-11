# Civitas API — State Machine

> **Looking for the integration playbook?** See [`INTEGRATION.md`](INTEGRATION.md)
> for the 8-step recipe to walk the golden scenario end-to-end. This doc is
> the state-machine reference.

Two parallel state machines: incident-level and work-order-level.
All transitions go through `civitas_api.operations.state_machine` and
return HTTP 409 with `code: INVALID_STATE` on illegal edges.

## Incident lifecycle

```
submitted ─┬─▶ awaiting_clarification ─▶ under_analysis ─┬─▶ awaiting_review
           │     ▲                                       │      │
           ├─▶ under_analysis ◀──────────────────────────┘      │
           │     ▲                                              ▼
           ├─▶ clustered ──────────────────────────────────▶ approved ─▶ assigned ─▶ in_progress
           │                                                     ▲                       │
           └─▶ awaiting_review ──────────────────────────────────┘                       ▼
                                            │                                       resolution_submitted
                                            ▼                                          │
                                         rejected                                     ▼
                                                                          verification_pending ─┬─▶ resolved
                                                                                                ├─▶ partially_resolved ─▶ in_progress
                                                                                                └─▶ reopened ─▶ under_analysis / awaiting_clarification
```

## Work-order lifecycle

```
awaiting_review ─▶ approved ─▶ assigned ─▶ in_progress
                                          └─▶ resolution_submitted ─▶ verification_pending ─┬─▶ resolved
                                                                                            ├─▶ partially_resolved ─▶ in_progress
                                                                                            └─▶ reopened ─▶ in_progress
```

Note: `rejected` is NOT a work-order status. When a reviewer rejects a WO,
the WO row stays in `awaiting_review` (closed-but-not-approved) and the
parent incident moves to `rejected`.

## Application-level invariants

### `incidents.assigned_work_order_id` has no DB foreign key

A single incident can have multiple work orders over its lifecycle
(initial, follow-up drainage after golden §12 partial resolution,
re-assignment after reopen). The `assigned_work_order_id` column points
to the *currently active* WO, not a hard 1:1.

The application enforces:
1. the target WO must exist
2. the target WO must belong to this incident
3. the target WO must be in a non-terminal status

Violating this invariant returns 409 INVALID_STATE.

### Clarification re-asking after reopen

`(incident_id, question_id)` is intentionally NOT a unique constraint
in the database. The same question may be re-asked after an incident is
reopened (ref/04 §3 lists `reopened` as a valid status).

Application layer enforces "at most one OPEN clarification per
(incident, question)" — re-asking the same unanswered question is a
silent no-op rather than a duplicate row. Re-asking after the question
has been answered creates a fresh row, which is the intended behavior.

### Reviewer gates

The reviewer role (REVIEWER) is the gate for:
- `POST /work-orders/{id}/approve` — advances WO + incident
- `POST /work-orders/{id}/reject` — leaves WO, moves incident to rejected
- `POST /incidents/{id}/resolve` — final close action

The reviewer is *not* required for normal citizen or triage work; it
exists so that critical or uncertain incidents (per ref/08 §10) require
human sign-off before high-impact action.

## What is NOT a state

- `incident_id` deletion: not supported. Use `resolved` / `rejected` to close.
- `reopened` is the way to "unresolve" an incident. It transitions back to
  `under_analysis` (or `awaiting_clarification` if more Q's are needed).
- `partially_resolved` incidents can transition back to `in_progress`
  (continuation) or `reopened` (reviewer disagrees with the model).

## Trace + audit

Every state transition writes one row to `agent_traces` with a
descriptive `node` value:
- `work_order_create`, `work_order_approve`, `work_order_reject`
- `route` (routing decision)
- `resolution_submit` (resolution classification persisted)
- `reviewer_action` (final close)
- `duplicate_detector`, `risk` (used by agents; out of backend scope)

Plus any custom nodes added by the agent workflow.