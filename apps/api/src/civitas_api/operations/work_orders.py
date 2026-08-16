"""Work-order persistence + state transitions.

Pure functions over the DB connection. Every status change routes through
``assert_work_order_transition`` (or ``assert_incident_transition`` for the
incident side-effect) so illegal edges fail loudly with HTTP 409.

Application-level invariants enforced here:

- a WO always belongs to its parent incident
- a WO cannot be set on an incident that is in a terminal state
- ``incidents.assigned_work_order_id`` is application-managed, no DB FK
- writing ``assigned_work_order_id`` verifies (a) WO exists, (b) WO
  belongs to the incident, (c) WO is in a non-terminal status
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

from civitas_api.core.database import get_connection
from civitas_api.operations import reports as reports_ops
from civitas_api.operations.state_machine import (
    assert_incident_transition,
    assert_work_order_transition,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{_uuid.uuid4().hex}"


def _is_sqlite() -> bool:
    from civitas_api.core.config import get_settings
    return get_settings().database_url.startswith("sqlite:///")


def _coerce_row(row: Any) -> dict[str, Any]:
    """Cast a row to dict and normalise list/jsonb fields that sqlite returns as text."""
    d = dict(row)
    for key in ("required_actions", "suggested_resources", "safety_notes",
                "secondary_departments", "policy_references"):
        v = d.get(key)
        if isinstance(v, str):
            import json as _json
            try:
                d[key] = _json.loads(v)
            except (ValueError, TypeError):
                pass
    return d


def get_work_order(work_order_id: str) -> dict[str, Any] | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM work_orders WHERE work_order_id = %(id)s",
            {"id": work_order_id},
        )
        row = cur.fetchone()
    return _coerce_row(row) if row else None


def list_work_orders_for_incident(incident_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM work_orders WHERE incident_id = %(i)s "
            "ORDER BY created_at ASC",
            {"i": incident_id},
        )
        rows = list(cur.fetchall())
    return [_coerce_row(r) for r in rows]


def create_work_order(
    incident_id: str,
    summary: str,
    required_actions: list[str],
    suggested_resources: list[str],
    safety_notes: list[str],
    primary_department: str | None,
    secondary_departments: list[str],
    escalation_required: bool,
    policy_references: list[str],
    estimated_window_min_hours: int | None,
    estimated_window_max_hours: int | None,
    created_by: str,
) -> dict[str, Any]:
    """Create a work order in 'awaiting_review'. Incident moves to 'awaiting_review'
    unless it is already past that point in its lifecycle."""
    target = reports_ops.get_incident(incident_id)
    if target is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="incident not found")

    incident_status = target.get("status") or "submitted"
    # If incident hasn't reached awaiting_review yet, advance it.
    if incident_status in {"submitted", "under_analysis", "clustered"}:
        assert_incident_transition(incident_status, "awaiting_review")

    work_order_id = _gen_id("wo")
    trace_id = _gen_id("trc")
    now = _now()

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO work_orders "
            "(work_order_id, incident_id, summary, required_actions, "
            "suggested_resources, safety_notes, estimated_window_min_hours, "
            "estimated_window_max_hours, non_binding, status, "
            "primary_department, secondary_departments, escalation_required, "
            "policy_references, created_at, created_by) "
            "VALUES (%(id)s, %(i)s, %(s)s, %(ra)s, %(sr)s, %(sn)s, "
            "%(min)s, %(max)s, true, 'awaiting_review', "
            "%(pd)s, %(sd)s, %(esc)s, %(pr)s, %(now)s, %(by)s)",
            {
                "id": work_order_id,
                "i": incident_id,
                "s": summary,
                "ra": reports_ops.to_json(required_actions),
                "sr": reports_ops.to_json(suggested_resources),
                "sn": reports_ops.to_json(safety_notes),
                "min": estimated_window_min_hours,
                "max": estimated_window_max_hours,
                "pd": primary_department,
                "sd": reports_ops.to_json(secondary_departments),
                "esc": escalation_required,
                "pr": reports_ops.to_json(policy_references),
                "now": now,
                "by": created_by,
            },
        )
        # Side-effect: advance incident + record trace.
        if incident_status in {"submitted", "under_analysis", "clustered"}:
            cur.execute(
                "UPDATE incidents SET status = 'awaiting_review', "
                "status_updated_at = %(now)s, assigned_department = %(pd)s "
                "WHERE incident_id = %(i)s",
                {"now": now, "pd": primary_department, "i": incident_id},
            )
        cur.execute(
            "INSERT INTO agent_traces "
            "(trace_id, incident_id, node, input, output, "
            "validation_outcome, created_at) "
            "VALUES (%(t)s, %(i)s, 'work_order_create', %(input)s, %(output)s, "
            "'ok', %(now)s)",
            {
                "t": trace_id,
                "i": incident_id,
                "input": reports_ops.to_json({"incident_id": incident_id}),
                "output": reports_ops.to_json({"work_order_id": work_order_id}),
                "now": now,
            },
        )
        conn.commit()

    return get_work_order(work_order_id) or {}


def update_work_order(
    work_order_id: str,
    summary: str | None,
    required_actions: list[str] | None,
    suggested_resources: list[str] | None,
    safety_notes: list[str] | None,
    estimated_window_min_hours: int | None,
    estimated_window_max_hours: int | None,
    primary_department: str | None,
    secondary_departments: list[str] | None,
    policy_references: list[str] | None,
) -> dict[str, Any]:
    """Patch fields on a work order. Cannot change status via this route —
    status transitions go through /approve (or the resolutions module)."""
    wo = get_work_order(work_order_id)
    if wo is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="work_order not found")

    sets: list[str] = []
    params: dict[str, Any] = {"id": work_order_id}
    if summary is not None:
        sets.append("summary = %(s)s")
        params["s"] = summary
    if required_actions is not None:
        sets.append("required_actions = %(ra)s")
        params["ra"] = reports_ops.to_json(required_actions)
    if suggested_resources is not None:
        sets.append("suggested_resources = %(sr)s")
        params["sr"] = reports_ops.to_json(suggested_resources)
    if safety_notes is not None:
        sets.append("safety_notes = %(sn)s")
        params["sn"] = reports_ops.to_json(safety_notes)
    if estimated_window_min_hours is not None:
        sets.append("estimated_window_min_hours = %(min)s")
        params["min"] = estimated_window_min_hours
    if estimated_window_max_hours is not None:
        sets.append("estimated_window_max_hours = %(max)s")
        params["max"] = estimated_window_max_hours
    if primary_department is not None:
        sets.append("primary_department = %(pd)s")
        params["pd"] = primary_department
    if secondary_departments is not None:
        sets.append("secondary_departments = %(sd)s")
        params["sd"] = reports_ops.to_json(secondary_departments)
    if policy_references is not None:
        sets.append("policy_references = %(pr)s")
        params["pr"] = reports_ops.to_json(policy_references)

    if not sets:
        return wo

    sql = f"UPDATE work_orders SET {', '.join(sets)} WHERE work_order_id = %(id)s"
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        conn.commit()
    return get_work_order(work_order_id) or {}


def approve_work_order(work_order_id: str, reviewer_id: str) -> dict[str, Any]:
    """Reviewer action: move WO from awaiting_review -> approved.

    Side effects on the incident: status -> 'approved', then to 'assigned'
    (the assignment is the supervisor's separate concern but the seed data
    assumes auto-assignment on approval for the MVP)."""
    wo = get_work_order(work_order_id)
    if wo is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="work_order not found")

    current = wo["status"]
    assert_work_order_transition(current, "approved")

    incident_id = wo["incident_id"]
    incident = reports_ops.get_incident(incident_id)
    if incident is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="incident not found")

    incident_status = incident.get("status") or "submitted"
    assert_incident_transition(incident_status, "approved")
    # Auto-progress to assigned on approval — MVP simplification. Ref/03 §3
    # assigns the assignment to the supervisor; we treat approval as
    # implicit-assignment for the 13 Aug demo.
    assert_incident_transition("approved", "assigned")

    now = _now()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE work_orders SET status = 'approved', "
            "reviewed_by = %(rb)s, reviewed_at = %(now)s "
            "WHERE work_order_id = %(id)s",
            {"rb": reviewer_id, "now": now, "id": work_order_id},
        )
        cur.execute(
            "UPDATE incidents SET status = 'assigned', "
            "status_updated_at = %(now)s, assigned_work_order_id = %(id)s "
            "WHERE incident_id = %(i)s",
            {"now": now, "id": work_order_id, "i": incident_id},
        )
        cur.execute(
            "INSERT INTO agent_traces (trace_id, incident_id, node, "
            "input, output, validation_outcome, created_at) "
            "VALUES (%(t)s, %(i)s, 'work_order_approve', "
            "%(input)s, %(output)s, 'ok', %(now)s)",
            {
                "t": _gen_id("trc"),
                "i": incident_id,
                "input": reports_ops.to_json({"work_order_id": work_order_id}),
                "output": reports_ops.to_json({"status": "approved"}),
                "now": now,
            },
        )
        conn.commit()
    return get_work_order(work_order_id) or {}


def reject_work_order(work_order_id: str, reviewer_id: str) -> dict[str, Any]:
    """Supervisor/reviewer rejection: WO stays in 'awaiting_review'
    (closed-but-not-approved) and the incident moves to 'rejected'."""
    wo = get_work_order(work_order_id)
    if wo is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="work_order not found")

    if wo["status"] != "awaiting_review":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_STATE",
                "message": f"work_order in status {wo['status']!r} cannot be rejected; only awaiting_review is rejectable",
                "retryable": False,
            },
        )

    incident_id = wo["incident_id"]
    incident = reports_ops.get_incident(incident_id)
    if incident is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="incident not found")

    incident_status = incident.get("status") or "submitted"
    assert_incident_transition(incident_status, "rejected")

    now = _now()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE work_orders SET reviewed_by = %(rb)s, reviewed_at = %(now)s "
            "WHERE work_order_id = %(id)s",
            {"rb": reviewer_id, "now": now, "id": work_order_id},
        )
        cur.execute(
            "UPDATE incidents SET status = 'rejected', "
            "status_updated_at = %(now)s WHERE incident_id = %(i)s",
            {"now": now, "i": incident_id},
        )
        cur.execute(
            "INSERT INTO agent_traces (trace_id, incident_id, node, "
            "input, output, validation_outcome, created_at) "
            "VALUES (%(t)s, %(i)s, 'work_order_reject', "
            "%(input)s, %(output)s, 'ok', %(now)s)",
            {
                "t": _gen_id("trc"),
                "i": incident_id,
                "input": reports_ops.to_json({"work_order_id": work_order_id}),
                "output": reports_ops.to_json({"status": "rejected"}),
                "now": now,
            },
        )
        conn.commit()
    return get_work_order(work_order_id) or {}