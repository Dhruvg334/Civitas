"""Citizen 72-Hour Resolution Dispute & Automated Re-Open Operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from civitas_api.operations.reports import get_connection, get_incident, _is_sqlite


@dataclass(frozen=True)
class DisputeWindowStatus:
    incident_id: str
    status: str
    is_disputable: bool
    resolved_at: str | None
    dispute_deadline: str | None
    hours_remaining: float
    dispute_count: int


def get_dispute_window_status(incident_id: str) -> DisputeWindowStatus:
    """Checks whether an incident is within the active 72-hour citizen dispute window."""
    inc = get_incident(incident_id)
    if not inc:
        raise ValueError(f"Incident '{incident_id}' not found")

    status = inc.get("status", "open")
    resolved_at_raw = inc.get("status_updated_at")

    if not resolved_at_raw:
        resolved_at = datetime.now(UTC)
    elif isinstance(resolved_at_raw, str):
        try:
            resolved_at = datetime.fromisoformat(resolved_at_raw)
        except ValueError:
            resolved_at = datetime.now(UTC)
    elif isinstance(resolved_at_raw, datetime):
        resolved_at = resolved_at_raw
    else:
        resolved_at = datetime.now(UTC)

    if resolved_at.tzinfo is None:
        resolved_at = resolved_at.replace(tzinfo=UTC)

    deadline = resolved_at + timedelta(hours=72)
    now = datetime.now(UTC)
    remaining_seconds = (deadline - now).total_seconds()
    hours_remaining = max(0.0, round(remaining_seconds / 3600.0, 1))

    is_disputable = status in ("resolved", "closed") and hours_remaining > 0.0

    return DisputeWindowStatus(
        incident_id=incident_id,
        status=status,
        is_disputable=is_disputable,
        resolved_at=resolved_at.isoformat(),
        dispute_deadline=deadline.isoformat(),
        hours_remaining=hours_remaining,
        dispute_count=0,
    )


def submit_citizen_dispute(
    incident_id: str,
    dispute_reason: str,
    rebuttal_photo_url: str | None = None,
) -> dict[str, Any]:
    """Submits a citizen dispute against a resolved case, automatically re-opening the incident."""
    window = get_dispute_window_status(incident_id)
    if not window.is_disputable:
        raise ValueError(
            f"Incident '{incident_id}' is not eligible for dispute. Current status: '{window.status}', hours remaining: {window.hours_remaining}h."
        )

    now = datetime.now(UTC)

    with get_connection() as conn, conn.cursor() as cur:
        if _is_sqlite():
            cur.execute(
                "UPDATE incidents SET status = 'reopened_disputed', status_updated_at = ? WHERE incident_id = ?",
                (now.isoformat(), incident_id),
            )
        else:
            cur.execute(
                "UPDATE incidents SET status = 'reopened_disputed', status_updated_at = %(now)s WHERE incident_id = %(id)s",
                {"now": now, "id": incident_id},
            )
        conn.commit()

    return {
        "incident_id": incident_id,
        "previous_status": window.status,
        "new_status": "reopened_disputed",
        "dispute_reason": dispute_reason,
        "rebuttal_photo_url": rebuttal_photo_url,
        "priority_escalation": "P1_CRITICAL_SUPERVISOR_REVIEW",
        "reopened_at": now.isoformat(),
        "dispute_ticket_id": f"DISP-{incident_id[-6:]}",
    }
