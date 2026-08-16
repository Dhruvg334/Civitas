"""Centralised state-machine guards for incidents + work-orders.

Two transitions tables live here, both enforced by application code rather
than by DB constraints (the DB only knows the legal *values*, not the legal
*edges*). Every route that mutates `incidents.status` or `work_orders.status`
imports ``assert_incident_transition`` / ``assert_work_order_transition``
and raises ``HTTPException(409, INVALID_STATE)`` on an illegal edge.

The `rejected` state is intentional: a rejected work order keeps its row in
``awaiting_review`` (closed-but-not-approved); the rejection is recorded by
moving the parent incident to ``rejected`` and stamping ``reviewed_by`` /
``reviewed_at`` on the WO. See ``docs/api/STATE_MACHINE.md``.
"""

from __future__ import annotations

from fastapi import HTTPException, status

# Incident lifecycle edges (ref/04 §3 + state machine).
INCIDENT_TRANSITIONS: dict[str, set[str]] = {
    "submitted": {"awaiting_clarification", "under_analysis", "clustered", "awaiting_review", "approved"},
    "awaiting_clarification": {"under_analysis", "clustered", "awaiting_review"},
    "under_analysis": {"awaiting_clarification", "clustered", "awaiting_review", "approved"},
    "clustered": {"awaiting_review", "approved"},
    "awaiting_review": {"approved", "rejected"},
    "approved": {"assigned"},
    "assigned": {"in_progress"},
    "in_progress": {"resolution_submitted"},
    "resolution_submitted": {"verification_pending"},
    "verification_pending": {"resolved", "partially_resolved", "reopened"},
    "resolved": set(),
    "partially_resolved": {"in_progress", "reopened"},
    "reopened": {"under_analysis", "awaiting_clarification", "awaiting_review", "approved"},
    "rejected": set(),
}


# Work-order lifecycle edges.
WORK_ORDER_TRANSITIONS: dict[str, set[str]] = {
    "awaiting_review": {"approved"},
    "approved": {"assigned"},
    "assigned": {"in_progress"},
    "in_progress": {"resolution_submitted"},
    "resolution_submitted": {"verification_pending"},
    "verification_pending": {"resolved", "partially_resolved", "reopened"},
    "resolved": set(),
    "partially_resolved": {"in_progress"},
    "reopened": {"in_progress"},
}


def assert_incident_transition(current: str, target: str) -> None:
    """Raise 409 INVALID_STATE if `current -> target` is not allowed."""
    if current == target:
        return
    if target not in INCIDENT_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_STATE",
                "message": f"incident cannot transition {current!r} -> {target!r}",
                "retryable": False,
            },
        )


def assert_work_order_transition(current: str, target: str) -> None:
    """Raise 409 INVALID_STATE if `current -> target` is not allowed."""
    if current == target:
        return
    if target not in WORK_ORDER_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_STATE",
                "message": f"work_order cannot transition {current!r} -> {target!r}",
                "retryable": False,
            },
        )


def is_terminal(state: str) -> bool:
    """A state with no outgoing edges."""
    return len(INCIDENT_TRANSITIONS.get(state, set())) == 0