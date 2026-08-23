"""Routing-decision persistence.

The agent workflow generates the routing decision (which department, what
policy refs); this module persists it and updates incident status. The
incident advances to ``approved`` if the routing does NOT require review,
else stays at ``awaiting_review`` (typical path).
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

from civitas_api.core.database import get_connection
from civitas_api.operations import reports as reports_ops
from civitas_api.operations.state_machine import assert_incident_transition


def _now() -> datetime:
    return datetime.now(UTC)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{_uuid.uuid4().hex}"


def create_routing_decision(
    incident_id: str,
    primary_department: str,
    secondary_departments: list[str],
    escalation_required: bool,
    policy_references: list[str],
    decision_basis: list[str],
    review_required: bool,
    workflow_version: str,
    routed_by: str,
) -> dict[str, Any]:
    target = reports_ops.get_incident(incident_id)
    if target is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="incident not found")

    current_status = target.get("status") or "submitted"
    routing_id = _gen_id("rte")
    trace_id = _gen_id("trc")
    now = _now()

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO routing_decisions "
            "(routing_id, incident_id, primary_department, "
            "secondary_departments, escalation_required, policy_references, "
            "decision_basis, review_required, workflow_version, routed_at, routed_by) "
            "VALUES (%(id)s, %(i)s, %(pd)s, %(sd)s, %(esc)s, %(pr)s, "
            "%(db)s, %(rr)s, %(wv)s, %(now)s, %(by)s)",
            {
                "id": routing_id,
                "i": incident_id,
                "pd": primary_department,
                "sd": reports_ops.to_json(secondary_departments),
                "esc": escalation_required,
                "pr": reports_ops.to_json(policy_references),
                "db": reports_ops.to_json(decision_basis),
                "rr": review_required,
                "wv": workflow_version,
                "now": now,
                "by": routed_by,
            },
        )

        # Side-effects:
        # - If we're at awaiting_review and routing does NOT require
        #   review, advance to approved (skipping the reviewer gate).
        # - Update assigned_department to mirror the routing choice.
        new_status = current_status
        if current_status == "awaiting_review" and not review_required:
            assert_incident_transition("awaiting_review", "approved")
            new_status = "approved"
        elif current_status in {"submitted", "under_analysis", "clustered"}:
            # Routing in early lifecycle -> move to awaiting_review
            # (or approved if no review needed).
            if not review_required:
                assert_incident_transition(current_status, "approved")
                new_status = "approved"
            else:
                assert_incident_transition(current_status, "awaiting_review")
                new_status = "awaiting_review"

        cur.execute(
            "UPDATE incidents SET assigned_department = %(pd)s, "
            "status = %(st)s, status_updated_at = %(now)s "
            "WHERE incident_id = %(i)s",
            {"pd": primary_department, "st": new_status, "now": now, "i": incident_id},
        )

        cur.execute(
            "INSERT INTO agent_traces "
            "(trace_id, incident_id, node, model_version, "
            "input, output, validation_outcome, created_at) "
            "VALUES (%(t)s, %(i)s, 'route', %(wv)s, "
            "%(input)s, %(output)s, 'ok', %(now)s)",
            {
                "t": trace_id,
                "i": incident_id,
                "wv": workflow_version,
                "input": reports_ops.to_json({"incident_id": incident_id}),
                "output": reports_ops.to_json({
                    "routing_id": routing_id,
                    "primary_department": primary_department,
                }),
                "now": now,
            },
        )
        conn.commit()

    return get_routing_decision(routing_id) or {}


def get_routing_decision(routing_id: str) -> dict[str, Any] | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM routing_decisions WHERE routing_id = %(id)s",
            {"id": routing_id},
        )
        row = cur.fetchone()
    if row is None:
        return None
    d = dict(row)
    for key in ("secondary_departments", "policy_references", "decision_basis"):
        v = d.get(key)
        if isinstance(v, str):
            import json as _json
            try:
                d[key] = _json.loads(v)
            except (ValueError, TypeError):
                pass
    return d


def list_routings_for_incident(incident_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM routing_decisions WHERE incident_id = %(i)s "
            "ORDER BY routed_at DESC",
            {"i": incident_id},
        )
        rows = list(cur.fetchall())
    out = []
    for r in rows:
        d = dict(r)
        for key in ("secondary_departments", "policy_references", "decision_basis"):
            v = d.get(key)
            if isinstance(v, str):
                import json as _json
                try:
                    d[key] = _json.loads(v)
                except (ValueError, TypeError):
                    pass
        out.append(d)
    return out