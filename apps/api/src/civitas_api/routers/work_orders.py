"""Work-order lifecycle routes.

Routes
------
POST   /api/v1/incidents/{incident_id}/work-orders  (SUPERVISOR)
GET    /api/v1/work-orders/{work_order_id}           (TRIAGE)
PUT    /api/v1/work-orders/{work_order_id}           (SUPERVISOR)
POST   /api/v1/work-orders/{work_order_id}/approve   (REVIEWER)
POST   /api/v1/work-orders/{work_order_id}/reject    (REVIEWER)

Reject semantics: WO row stays in ``awaiting_review`` (closed-but-not-
approved) and the incident moves to ``rejected``. See STATE_MACHINE.md.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import success_envelope
from civitas_api.operations import work_orders as wo_ops

router = APIRouter(prefix="/api/v1", tags=["work-orders"])


@router.post(
    "/incidents/{incident_id}/work-orders",
    status_code=status.HTTP_201_CREATED,
)
def create_work_order(
    incident_id: str,
    payload: dict[str, Any],
    principal: Annotated[Principal, Depends(require_role(Role.SUPERVISOR))],
) -> dict[str, Any]:
    """Create a work order for an incident. Returns the persisted WO."""
    summary = (payload or {}).get("summary")
    if not summary or not isinstance(summary, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "payload.summary (string) required",
                "retryable": False,
            },
        )
    row = wo_ops.create_work_order(
        incident_id=incident_id,
        summary=summary,
        required_actions=payload.get("required_actions") or [],
        suggested_resources=payload.get("suggested_resources") or [],
        safety_notes=payload.get("safety_notes") or [],
        primary_department=payload.get("primary_department"),
        secondary_departments=payload.get("secondary_departments") or [],
        escalation_required=bool(payload.get("escalation_required", False)),
        policy_references=payload.get("policy_references") or [],
        estimated_window_min_hours=payload.get("estimated_window_min_hours"),
        estimated_window_max_hours=payload.get("estimated_window_max_hours"),
        created_by=principal.user_id,
    )
    return success_envelope(row)


@router.get("/work-orders/{work_order_id}")
def get_work_order(
    work_order_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    row = wo_ops.get_work_order(work_order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="work_order not found")
    return success_envelope(row)


@router.put("/work-orders/{work_order_id}")
def update_work_order(
    work_order_id: str,
    payload: dict[str, Any],
    principal: Annotated[Principal, Depends(require_role(Role.SUPERVISOR))],
) -> dict[str, Any]:
    row = wo_ops.update_work_order(
        work_order_id=work_order_id,
        summary=payload.get("summary"),
        required_actions=payload.get("required_actions"),
        suggested_resources=payload.get("suggested_resources"),
        safety_notes=payload.get("safety_notes"),
        estimated_window_min_hours=payload.get("estimated_window_min_hours"),
        estimated_window_max_hours=payload.get("estimated_window_max_hours"),
        primary_department=payload.get("primary_department"),
        secondary_departments=payload.get("secondary_departments"),
        policy_references=payload.get("policy_references"),
    )
    return success_envelope(row)


@router.post("/work-orders/{work_order_id}/approve", status_code=status.HTTP_200_OK)
def approve_work_order(
    work_order_id: str,
    principal: Annotated[Principal, Depends(require_role(Role.REVIEWER))],
    _payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = wo_ops.approve_work_order(work_order_id, reviewer_id=principal.user_id)
    return success_envelope(row)


@router.post("/work-orders/{work_order_id}/reject", status_code=status.HTTP_200_OK)
def reject_work_order(
    work_order_id: str,
    principal: Annotated[Principal, Depends(require_role(Role.REVIEWER))],
    _payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = wo_ops.reject_work_order(work_order_id, reviewer_id=principal.user_id)
    return success_envelope(row)