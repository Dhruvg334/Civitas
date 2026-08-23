"""Incident detail + lifecycle routes.

Routes in this module:

    GET  /api/v1/incidents                  — paginated list with filters
    GET  /api/v1/incidents/{id}            — detail read with envelope
    POST /api/v1/incidents/{id}/merge      — link a duplicate report
    POST /api/v1/incidents/{id}/assess     — persist severity + priority
    GET  /api/v1/incidents/{id}/trace      — ordered agent trace events

All routes are role-gated. Write routes require at least TRIAGE;
assess/merge additionally require SUPERVISOR.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from civitas_api.core.auth import Principal, Role, require_role, get_optional_principal
from civitas_api.core.envelope import error_envelope, success_envelope
from civitas_api.operations import reports as reports_ops
from civitas_api.operations import routing as routing_ops
from civitas_api.operations import work_orders as work_order_ops
from civitas_api.operations import workflow_runs as workflow_run_ops

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


class WorkflowTraceWrite(BaseModel):
    """Safe node-level trace payload from the workflow service."""

    workflow_trace_id: str = Field(min_length=1, max_length=200)
    node: str = Field(min_length=1, max_length=100)
    status: str = Field(min_length=1, max_length=50)
    latency_ms: int = Field(ge=0)
    tool_or_model: str | None = Field(default=None, max_length=200)
    validation_outcome: str = Field(default="valid", max_length=50)
    knowledge_reference_ids: list[str] = Field(default_factory=list, max_length=100)
    warnings: list[str] = Field(default_factory=list, max_length=100)
    error_code: str | None = Field(default=None, max_length=200)


def _iso(v):
    if v is None:
        return None
    return v.isoformat() if hasattr(v, "isoformat") else v


def _now() -> datetime:
    return datetime.now(UTC)


@router.get("")
def list_incidents(
    _principal: Annotated[Principal | None, Depends(get_optional_principal)] = None,
    status: str | None = Query(None),
    category: str | None = Query(None),
    since: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    rows = reports_ops.list_incidents(status=status, category=category, since=since, limit=limit)
    out = []
    for r in rows:
        reported_at = r.get("reported_at")
        out.append(
            {
                "incident_id": r["incident_id"],
                "category": r.get("category"),
                "status": r.get("status") or "submitted",
                "duplicates_seen": int(r.get("duplicates_seen") or 1),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "reported_at": _iso(reported_at),
                "assigned_department": r.get("assigned_department"),
                "resolution_class": r.get("resolution_class"),
            }
        )
    return success_envelope({"incidents": out, "count": len(out)})


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{_uuid.uuid4().hex}"


# ---------------------------------------------------------------------------
# GET /api/v1/incidents/{id}
# ---------------------------------------------------------------------------


@router.get("/{incident_id}")
def get_incident(
    incident_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    """Incident detail: row + latest assessment + media count + trace count."""
    row = reports_ops.get_incident(incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="incident not found")

    with reports_ops.get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS c FROM media WHERE incident_id = %(i)s",
            {"i": incident_id},
        )
        media_count = int(cur.fetchone()["c"])
        cur.execute(
            "SELECT COUNT(*) AS c FROM incident_links WHERE incident_id = %(i)s",
            {"i": incident_id},
        )
        linked_count = int(cur.fetchone()["c"])
        cur.execute(
            "SELECT assessment_id, severity_score, severity_level, priority_score, "
            "priority_level, review_required, model_version, assessed_at "
            "FROM incident_assessments WHERE incident_id = %(i)s "
            "ORDER BY assessed_at DESC LIMIT 1",
            {"i": incident_id},
        )
        latest = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) AS c FROM incident_assessments WHERE incident_id = %(i)s",
            {"i": incident_id},
        )
        assessment_count = int(cur.fetchone()["c"])

    reported_at = row.get("reported_at")
    status_updated_at = row.get("status_updated_at")
    workflow = workflow_run_ops.find_latest(incident_id)
    routings = routing_ops.list_routings_for_incident(incident_id)
    work_orders = work_order_ops.list_work_orders_for_incident(incident_id)

    return success_envelope(
        {
            "incident_id": row["incident_id"],
            "category": row.get("category"),
            "description": row.get("description"),
            "status": row.get("status") or "submitted",
            "source": row.get("source") or "citizen",
            "duplicates_seen": int(row.get("duplicates_seen") or 1),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "reported_at": _iso(reported_at),
            "status_updated_at": _iso(status_updated_at),
            "last_assessment_model": row.get("last_assessment_model"),
            "assigned_department": row.get("assigned_department"),
            "assigned_work_order_id": row.get("assigned_work_order_id"),
            "resolution_class": row.get("resolution_class"),
            "media_count": media_count,
            "linked_reports_count": linked_count,
            "assessment_count": assessment_count,
            "latest_assessment": dict(latest) if latest else None,
            "routing_decisions": routings,
            "work_orders": work_orders,
            "workflow_id": workflow.get("workflow_id") if workflow else None,
            "workflow_status": workflow.get("status") if workflow else None,
            "workflow_trace_id": workflow.get("trace_id") if workflow else None,
        }
    )


# ---------------------------------------------------------------------------
# POST /api/v1/incidents/{id}/merge
# ---------------------------------------------------------------------------


@router.post("/{incident_id}/merge", status_code=status.HTTP_201_CREATED)
def merge_incident(
    incident_id: str,
    payload: dict[str, Any],
    principal: Annotated[Principal, Depends(require_role(Role.SUPERVISOR))],
) -> dict[str, Any]:
    """Link a duplicate report (payload['report_id']) into this incident.

    Persists one incident_links row, increments duplicates_seen, and
    writes an agent_traces entry. Idempotent: re-merging the same pair
    returns the existing link.
    """
    report_id = (payload or {}).get("report_id")
    if not report_id or not isinstance(report_id, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_envelope(
                code="VALIDATION_ERROR",
                message="payload.report_id (string) required",
                retryable=False,
            ),
        )
    confidence = (payload or {}).get("confidence")
    basis = (payload or {}).get("basis")
    source = (payload or {}).get("source") or "duplicate_detector"

    target = reports_ops.get_incident(incident_id)
    if target is None:
        raise HTTPException(status_code=404, detail="target incident not found")
    if (target.get("status") or "") in {"resolved", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_envelope(
                code="INVALID_STATE",
                message=f"cannot merge into incident in terminal state '{target['status']}'",
                retryable=False,
            ),
        )
    report = reports_ops.get_incident(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report incident not found")

    link_id = _gen_id("lnk")
    trace_id = _gen_id("trc")
    now = _now()

    try:
        with reports_ops.get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO incident_links "
                "(link_id, incident_id, report_id, source, confidence, basis, "
                "created_at, created_by) "
                "VALUES (%(link_id)s, %(incident_id)s, %(report_id)s, %(source)s, "
                "%(confidence)s, %(basis)s, %(now)s, %(created_by)s) "
                "ON CONFLICT (incident_id, report_id) DO NOTHING "
                "RETURNING link_id, created_at",
                {
                    "link_id": link_id,
                    "incident_id": incident_id,
                    "report_id": report_id,
                    "source": source,
                    "confidence": confidence,
                    "basis": reports_ops.to_json(basis) if basis is not None else None,
                    "now": now,
                    "created_by": principal.user_id,
                },
            )
            inserted = cur.fetchone()
            if inserted is None:
                # Already linked; fetch the existing row.
                cur.execute(
                    "SELECT link_id, created_at FROM incident_links "
                    "WHERE incident_id = %(i)s AND report_id = %(r)s",
                    {"i": incident_id, "r": report_id},
                )
                inserted = cur.fetchone()
            else:
                cur.execute(
                    "UPDATE incidents SET duplicates_seen = duplicates_seen + 1, "
                    "status_updated_at = %(now)s WHERE incident_id = %(i)s",
                    {"now": now, "i": incident_id},
                )
            cur.execute(
                "UPDATE incidents SET status = 'clustered', "
                "status_updated_at = %(now)s WHERE incident_id = %(r)s "
                "AND status IN ('submitted', 'under_analysis')",
                {"now": now, "r": report_id},
            )
            cur.execute(
                "INSERT INTO agent_traces "
                "(trace_id, incident_id, node, model_version, input, output, "
                "validation_outcome, created_at) "
                "VALUES (%(t)s, %(i)s, 'merge', NULL, %(input)s, %(output)s, "
                "'ok', %(now)s)",
                {
                    "t": trace_id,
                    "i": incident_id,
                    "input": reports_ops.to_json({"report_id": report_id, "source": source}),
                    "output": reports_ops.to_json({"link_id": inserted["link_id"]}),
                    "now": now,
                },
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        return error_envelope(
            code="PERSISTENCE_ERROR",
            message=f"merge failed: {exc}",
            retryable=True,
        )

    return success_envelope(
        {
            "link_id": inserted["link_id"],
            "incident_id": incident_id,
            "report_id": report_id,
            "source": source,
            "confidence": confidence,
            "created_at": inserted["created_at"].isoformat()
            if hasattr(inserted["created_at"], "isoformat")
            else str(inserted["created_at"]),
            "trace_id": trace_id,
            "merged_by": principal.user_id,
        }
    )


# ---------------------------------------------------------------------------
# POST /api/v1/incidents/{id}/assess
# ---------------------------------------------------------------------------


@router.post("/{incident_id}/assess", status_code=status.HTTP_201_CREATED)
def assess_incident(
    incident_id: str,
    principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a severity + priority verdict for this incident.

    The caller supplies the verdicts (produced by Pavit's risk model).
    We persist + trace + update `incidents.last_assessment_model`.
    """
    payload = payload or {}
    target = reports_ops.get_incident(incident_id)
    if target is None:
        raise HTTPException(status_code=404, detail="incident not found")

    severity = payload.get("severity") or {}
    priority = payload.get("priority") or {}
    uncertainties = payload.get("uncertainties")
    review_required = bool(payload.get("review_required", False))
    model_version = payload.get("model_version") or "risk-v1"

    assessment_id = _gen_id("ase")
    trace_id = _gen_id("trc")
    now = _now()

    try:
        with reports_ops.get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO incident_assessments "
                "(assessment_id, incident_id, severity_score, severity_level, "
                "severity_factors, priority_score, priority_level, priority_factors, "
                "uncertainties, review_required, model_version, assessed_at, assessed_by) "
                "VALUES (%(id)s, %(i)s, %(ss)s, %(sl)s, %(sf)s, %(ps)s, %(pl)s, "
                "%(pf)s, %(u)s, %(rr)s, %(mv)s, %(now)s, %(by)s)",
                {
                    "id": assessment_id,
                    "i": incident_id,
                    "ss": severity.get("score"),
                    "sl": severity.get("level"),
                    "sf": reports_ops.to_json(severity.get("factors")),
                    "ps": priority.get("score"),
                    "pl": priority.get("level"),
                    "pf": reports_ops.to_json(priority.get("factors")),
                    "u": reports_ops.to_json(uncertainties),
                    "rr": review_required,
                    "mv": model_version,
                    "now": now,
                    "by": principal.user_id,
                },
            )
            cur.execute(
                "UPDATE incidents SET last_assessment_model = %(mv)s, "
                "status_updated_at = %(now)s, "
                "status = CASE WHEN status IN ('submitted', 'under_analysis', 'clustered') "
                "THEN 'awaiting_review' ELSE status END "
                "WHERE incident_id = %(i)s",
                {"mv": model_version, "now": now, "i": incident_id},
            )
            cur.execute(
                "INSERT INTO agent_traces "
                "(trace_id, incident_id, node, model_version, input, output, "
                "validation_outcome, created_at) "
                "VALUES (%(t)s, %(i)s, 'assess', %(mv)s, %(input)s, %(output)s, "
                "'ok', %(now)s)",
                {
                    "t": trace_id,
                    "i": incident_id,
                    "mv": model_version,
                    "input": reports_ops.to_json({"incident_id": incident_id}),
                    "output": reports_ops.to_json(
                        {
                            "assessment_id": assessment_id,
                            "severity": severity,
                            "priority": priority,
                            "review_required": review_required,
                        }
                    ),
                    "now": now,
                },
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        return error_envelope(
            code="PERSISTENCE_ERROR",
            message=f"assess failed: {exc}",
            retryable=True,
        )

    return success_envelope(
        {
            "assessment_id": assessment_id,
            "incident_id": incident_id,
            "severity": severity,
            "priority": priority,
            "uncertainties": uncertainties,
            "review_required": review_required,
            "model_version": model_version,
            "trace_id": trace_id,
            "assessed_at": now.isoformat(),
            "assessed_by": principal.user_id,
        }
    )


# ---------------------------------------------------------------------------
# GET /api/v1/incidents/{id}/trace
# ---------------------------------------------------------------------------


@router.post("/{incident_id}/trace", status_code=status.HTTP_201_CREATED)
def record_workflow_trace(
    incident_id: str,
    payload: WorkflowTraceWrite,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    """Persist a safe workflow-node trace in the existing trace table.

    `workflow_trace_id` is retained inside the trace input as a correlation
    value. The table's primary `trace_id` remains one unique event ID.
    """
    if reports_ops.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail="incident not found")
    trace_id = _gen_id("trc")
    now = _now()
    safe_input = {"workflow_trace_id": payload.workflow_trace_id}
    safe_output = {
        "status": payload.status,
        "knowledge_reference_ids": payload.knowledge_reference_ids,
        "warnings": payload.warnings,
        "error_code": payload.error_code,
    }
    with reports_ops.get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO agent_traces "
            "(trace_id, incident_id, node, model_version, input, output, latency_ms, "
            "validation_outcome, created_at) "
            "VALUES (%(t)s, %(i)s, %(n)s, %(m)s, %(input)s, %(output)s, %(lat)s, %(v)s, %(now)s)",
            {
                "t": trace_id,
                "i": incident_id,
                "n": payload.node,
                "m": payload.tool_or_model,
                "input": reports_ops.to_json(safe_input),
                "output": reports_ops.to_json(safe_output),
                "lat": payload.latency_ms,
                "v": payload.validation_outcome,
                "now": now,
            },
        )
        conn.commit()
    return success_envelope({"trace_id": trace_id, "workflow_trace_id": payload.workflow_trace_id})


@router.get("/{incident_id}/trace")
def incident_trace(
    incident_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
    node: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    """Ordered agent/ML trace events for the incident."""
    target = reports_ops.get_incident(incident_id)
    if target is None:
        raise HTTPException(status_code=404, detail="incident not found")

    sql = (
        "SELECT trace_id, incident_id, node, model_version, prompt_version, "
        "input, output, latency_ms, tokens_in, tokens_out, validation_outcome, created_at "
        "FROM agent_traces WHERE incident_id = %(i)s "
    )
    params: dict[str, Any] = {"i": incident_id, "limit": limit}
    if node:
        sql += "AND node = %(node)s "
        params["node"] = node
    sql += "ORDER BY created_at ASC LIMIT %(limit)s"

    with reports_ops.get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = list(cur.fetchall())

    events = []
    for r in rows:
        created = r.get("created_at")
        events.append(
            {
                "trace_id": r["trace_id"],
                "node": r["node"],
                "model_version": r.get("model_version"),
                "prompt_version": r.get("prompt_version"),
                "input": r.get("input"),
                "output": r.get("output"),
                "latency_ms": r.get("latency_ms"),
                "tokens_in": r.get("tokens_in"),
                "tokens_out": r.get("tokens_out"),
                "validation_outcome": r.get("validation_outcome"),
                "created_at": created.isoformat()
                if hasattr(created, "isoformat")
                else str(created),
            }
        )

    return success_envelope({"incident_id": incident_id, "events": events, "count": len(events)})
