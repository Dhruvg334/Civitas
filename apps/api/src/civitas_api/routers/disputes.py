"""Citizen Dispute & Resolution Re-open Router."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from civitas_api.core.envelope import envelope, error_envelope
from civitas_api.operations.disputes import get_dispute_window_status, submit_citizen_dispute

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resolutions", tags=["Resolution Disputes & Re-Open"])


class CitizenDisputePayload(BaseModel):
    dispute_reason: str = Field(..., min_length=5, description="Explanation of why the issue is not resolved")
    rebuttal_photo_url: str | None = Field(default=None, description="Optional photo URL showing remaining defect")


@router.get("/{incident_id}/dispute-status")
async def check_dispute_status(incident_id: str):
    """Checks whether an incident is within the active 72-hour citizen dispute window."""
    try:
        status = get_dispute_window_status(incident_id)
        return envelope({
            "incident_id": status.incident_id,
            "status": status.status,
            "is_disputable": status.is_disputable,
            "resolved_at": status.resolved_at,
            "dispute_deadline": status.dispute_deadline,
            "hours_remaining": status.hours_remaining,
        })
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=error_envelope(
                code="INCIDENT_NOT_FOUND",
                message=str(exc),
            ),
        ) from exc


@router.post("/{incident_id}/dispute")
async def dispute_resolution(incident_id: str, payload: CitizenDisputePayload):
    """Submits a citizen dispute against a resolved case, automatically re-opening the work order."""
    try:
        res = submit_citizen_dispute(
            incident_id=incident_id,
            dispute_reason=payload.dispute_reason,
            rebuttal_photo_url=payload.rebuttal_photo_url,
        )
        return envelope(res)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=error_envelope(
                code="DISPUTE_NOT_PERMITTED",
                message=str(exc),
            ),
        ) from exc
