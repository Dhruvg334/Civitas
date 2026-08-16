"""Resolution submission + reviewer close action.

Two endpoints:

1. POST /incidents/{id}/resolution-submissions
   Stores Pavit's resolution-verification model output and advances the
   incident to ``verification_pending``.

2. POST /incidents/{id}/resolve
   Reviewer close action. ``payload.action`` is one of
   ``resolved | partially_resolved | reopened``. Advances the incident
   accordingly and writes an audit row.

See ref/04 §14 + ref/08 §9.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from civitas_api.core.database import get_connection
from civitas_api.operations import reports as reports_ops
from civitas_api.operations.state_machine import assert_incident_transition


def _now() -> datetime:
    return datetime.now(UTC)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{_uuid.uuid4().hex}"


def submit_resolution(
    incident_id: str,
    classification: str,
    resolved_evidence: list[str],
    remaining_evidence: list[str],
    uncertainties: list[str],
    model_version: str | None,
    submitted_by: str,
) -> dict[str, Any]:
    target = reports_ops.get_incident(incident_id)
    if target is None:
        raise HTTPException(status_code=404, detail="incident not found")

    valid_classes = {"resolved", "partially_resolved", "unverifiable", "conflicting_evidence"}
    if classification not in valid_classes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"classification must be one of {sorted(valid_classes)}",
                "retryable": False,
            },
        )

    # The incident must be in a state where resolution is being submitted.
    # Per contract §13, the WO advances resolution_submitted -> verification_pending.
    # The incident must therefore be at in_progress or resolution_submitted.
    current_status = target.get("status") or "submitted"
    if current_status not in {"in_progress", "resolution_submitted"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_STATE",
                "message": f"resolution submissions only valid while in_progress or resolution_submitted; current={current_status!r}",
                "retryable": False,
            },
        )

    resolution_id = _gen_id("rsl")
    now = _now()

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO resolution_submissions "
            "(resolution_id, incident_id, classification, "
            "resolved_evidence, remaining_evidence, uncertainties, "
            "model_version, submitted_at, submitted_by) "
            "VALUES (%(id)s, %(i)s, %(c)s, %(re)s, %(rr)s, %(u)s, "
            "%(mv)s, %(now)s, %(by)s)",
            {
                "id": resolution_id,
                "i": incident_id,
                "c": classification,
                "re": reports_ops.to_json(resolved_evidence),
                "rr": reports_ops.to_json(remaining_evidence),
                "u": reports_ops.to_json(uncertainties),
                "mv": model_version,
                "now": now,
                "by": submitted_by,
            },
        )

        # Advance incident.
        if current_status == "in_progress":
            assert_incident_transition("in_progress", "resolution_submitted")
        assert_incident_transition("resolution_submitted", "verification_pending")
        cur.execute(
            "UPDATE incidents SET status = 'verification_pending', "
            "resolution_class = %(c)s, status_updated_at = %(now)s "
            "WHERE incident_id = %(i)s",
            {"c": classification, "now": now, "i": incident_id},
        )

        cur.execute(
            "INSERT INTO agent_traces "
            "(trace_id, incident_id, node, model_version, "
            "input, output, validation_outcome, created_at) "
            "VALUES (%(t)s, %(i)s, 'resolution_submit', %(mv)s, "
            "%(input)s, %(output)s, 'ok', %(now)s)",
            {
                "t": _gen_id("trc"),
                "i": incident_id,
                "mv": model_version,
                "input": reports_ops.to_json({"incident_id": incident_id}),
                "output": reports_ops.to_json({
                    "resolution_id": resolution_id,
                    "classification": classification,
                }),
                "now": now,
            },
        )
        conn.commit()

    return get_resolution_submission(resolution_id) or {}


def reviewer_resolve(
    incident_id: str,
    action: str,
    reviewer_id: str,
) -> dict[str, Any]:
    """Final reviewer close. `action` is one of
    resolved | partially_resolved | reopened."""
    target = reports_ops.get_incident(incident_id)
    if target is None:
        raise HTTPException(status_code=404, detail="incident not found")

    valid_actions = {"resolved", "partially_resolved", "reopened"}
    if action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"action must be one of {sorted(valid_actions)}",
                "retryable": False,
            },
        )

    current_status = target.get("status") or "submitted"
    assert_incident_transition(current_status, action)

    now = _now()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE incidents SET status = %(st)s, "
            "status_updated_at = %(now)s "
            "WHERE incident_id = %(i)s",
            {"st": action, "now": now, "i": incident_id},
        )
        cur.execute(
            "INSERT INTO agent_traces "
            "(trace_id, incident_id, node, "
            "input, output, validation_outcome, created_at) "
            "VALUES (%(t)s, %(i)s, 'reviewer_action', "
            "%(input)s, %(output)s, 'ok', %(now)s)",
            {
                "t": _gen_id("trc"),
                "i": incident_id,
                "input": reports_ops.to_json({"incident_id": incident_id}),
                "output": reports_ops.to_json({"action": action}),
                "now": now,
            },
        )
        conn.commit()

    return reports_ops.get_incident(incident_id) or {}


def get_resolution_submission(resolution_id: str) -> dict[str, Any] | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM resolution_submissions WHERE resolution_id = %(id)s",
            {"id": resolution_id},
        )
        row = cur.fetchone()
    if row is None:
        return None
    d = dict(row)
    for key in ("resolved_evidence", "remaining_evidence", "uncertainties"):
        v = d.get(key)
        if isinstance(v, str):
            import json as _json
            try:
                d[key] = _json.loads(v)
            except (ValueError, TypeError):
                pass
    return d


def list_resolution_submissions(incident_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM resolution_submissions WHERE incident_id = %(i)s "
            "ORDER BY submitted_at DESC",
            {"i": incident_id},
        )
        rows = list(cur.fetchall())
    out = []
    for r in rows:
        d = dict(r)
        for key in ("resolved_evidence", "remaining_evidence", "uncertainties"):
            v = d.get(key)
            if isinstance(v, str):
                import json as _json
                try:
                    d[key] = _json.loads(v)
                except (ValueError, TypeError):
                    pass
        out.append(d)
    return out