"""Operational metadata for checkpointed workflow executions."""

from __future__ import annotations

from typing import Any

from civitas_api.operations.reports import get_connection

ACTIVE = ("RUNNING", "WAITING_FOR_CLARIFICATION", "WAITING_FOR_REVIEW")


def get(workflow_id: str) -> dict[str, Any] | None:
    return _one("SELECT * FROM workflow_runs WHERE workflow_id = %(id)s", {"id": workflow_id})


def find_active(report_id: str) -> dict[str, Any] | None:
    return _one(
        "SELECT * FROM workflow_runs WHERE report_id = %(id)s "
        "AND status IN ('RUNNING','WAITING_FOR_CLARIFICATION','WAITING_FOR_REVIEW') "
        "ORDER BY created_at DESC LIMIT 1",
        {"id": report_id},
    )


def create(workflow_id: str, thread_id: str, report_id: str, trace_id: str) -> dict[str, Any]:
    _execute(
        "INSERT INTO workflow_runs (workflow_id, thread_id, report_id, incident_id, trace_id, status) "
        "VALUES (%(workflow_id)s, %(thread_id)s, %(report_id)s, %(report_id)s, %(trace_id)s, 'RUNNING')",
        {
            "workflow_id": workflow_id,
            "thread_id": thread_id,
            "report_id": report_id,
            "trace_id": trace_id,
        },
    )
    return get(workflow_id) or _missing(workflow_id)


def update(workflow_id: str, status: str, interrupt_type: str | None = None) -> None:
    _execute(
        "UPDATE workflow_runs SET status=%(status)s, interrupt_type=%(interrupt)s, "
        "updated_at=CURRENT_TIMESTAMP, completed_at=CASE WHEN %(status)s IN ('COMPLETED','REJECTED','FAILED') "
        "THEN CURRENT_TIMESTAMP ELSE NULL END WHERE workflow_id=%(workflow_id)s",
        {"workflow_id": workflow_id, "status": status, "interrupt": interrupt_type},
    )


def _one(sql: str, params: dict[str, object]) -> dict[str, Any] | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return dict(row) if row else None


def _execute(sql: str, params: dict[str, object]) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        conn.commit()


def _missing(workflow_id: str) -> dict[str, Any]:
    raise LookupError(f"workflow {workflow_id} not found")
