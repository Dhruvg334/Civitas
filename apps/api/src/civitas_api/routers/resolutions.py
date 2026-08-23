"""Resolution routes:

    POST /api/v1/incidents/{incident_id}/resolution-submissions   (TRIAGE)
    GET  /api/v1/incidents/{incident_id}/resolution-submissions   (TRIAGE)
    POST /api/v1/incidents/{incident_id}/resolve                  (REVIEWER)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import success_envelope
from civitas_api.operations import resolutions as res_ops

router = APIRouter(prefix="/api/v1/incidents", tags=["resolutions"])


@router.post(
    "/{incident_id}/resolution-submissions",
    status_code=status.HTTP_201_CREATED,
)
def submit_resolution(
    incident_id: str,
    payload: dict[str, Any],
    principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    classification = (payload or {}).get("classification")
    if not classification:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "payload.classification required",
                "retryable": False,
            },
        )
    row = res_ops.submit_resolution(
        incident_id=incident_id,
        classification=classification,
        resolved_evidence=payload.get("resolved_evidence") or [],
        remaining_evidence=payload.get("remaining_evidence") or [],
        uncertainties=payload.get("uncertainties") or [],
        model_version=payload.get("model_version"),
        submitted_by=principal.user_id,
    )
    return success_envelope(row)


@router.get("/{incident_id}/resolution-submissions")
def list_resolution_submissions(
    incident_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    rows = res_ops.list_resolution_submissions(incident_id)
    return success_envelope({
        "incident_id": incident_id,
        "submissions": rows,
        "count": len(rows),
    })


@router.post("/{incident_id}/resolve", status_code=status.HTTP_200_OK)
def reviewer_resolve(
    incident_id: str,
    payload: dict[str, Any],
    principal: Annotated[Principal, Depends(require_role(Role.REVIEWER))],
) -> dict[str, Any]:
    action = (payload or {}).get("action")
    if not action:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "payload.action required",
                "retryable": False,
            },
        )
    row = res_ops.reviewer_resolve(
        incident_id=incident_id, action=action, reviewer_id=principal.user_id
    )
    return success_envelope(row)