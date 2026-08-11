"""Routing routes:

    POST /api/v1/incidents/{incident_id}/route           (SUPERVISOR)
    GET  /api/v1/incidents/{incident_id}/route           (TRIAGE)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import success_envelope
from civitas_api.operations import routing as rt_ops

router = APIRouter(prefix="/api/v1/incidents", tags=["routing"])


@router.post("/{incident_id}/route", status_code=status.HTTP_201_CREATED)
def route_incident(
    incident_id: str,
    payload: dict[str, Any],
    principal: Annotated[Principal, Depends(require_role(Role.SUPERVISOR))],
) -> dict[str, Any]:
    primary = (payload or {}).get("primary_department")
    if not primary or not isinstance(primary, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "payload.primary_department (string) required",
                "retryable": False,
            },
        )
    row = rt_ops.create_routing_decision(
        incident_id=incident_id,
        primary_department=primary,
        secondary_departments=payload.get("secondary_departments") or [],
        escalation_required=bool(payload.get("escalation_required", False)),
        policy_references=payload.get("policy_references") or [],
        decision_basis=payload.get("decision_basis") or [],
        review_required=bool(payload.get("review_required", True)),
        workflow_version=payload.get("workflow_version") or "routing-v1",
        routed_by=principal.user_id,
    )
    return success_envelope(row)


@router.get("/{incident_id}/route")
def list_routings(
    incident_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    rows = rt_ops.list_routings_for_incident(incident_id)
    return success_envelope({
        "incident_id": incident_id,
        "routings": rows,
        "count": len(rows),
    })