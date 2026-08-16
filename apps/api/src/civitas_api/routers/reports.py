from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import error_envelope, success_envelope
from civitas_api.operations import reports as reports_ops

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CreateReportRequest(BaseModel):
    description: str = Field(min_length=3, max_length=2000)
    location: Location
    citizen_selected_category: str | None = None


class ReportData(BaseModel):
    report_id: str
    description: str
    location: Location
    citizen_selected_category: str | None
    category: str | None
    status: str
    submitted_at: datetime
    latitude: float
    longitude: float


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report(
    payload: CreateReportRequest,
    principal: Annotated[Principal, Depends(require_role(Role.CITIZEN))],
) -> dict:
    """Persist a citizen report as a new incident in PostGIS.

    The `incident_id` returned in the response is the same identifier used by
    the spatial endpoints; the legacy `report_id` field is preserved for
    backward-compatible clients.
    """
    try:
        row = reports_ops.create_incident(
            description=payload.description,
            latitude=payload.location.latitude,
            longitude=payload.location.longitude,
            citizen_selected_category=payload.citizen_selected_category,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_envelope(
                code="PERSISTENCE_ERROR",
                message=f"failed to persist report: {exc}",
                retryable=True,
            ),
        ) from exc

    data = ReportData(
        report_id=row["incident_id"],
        description=row["description"],
        location=Location(latitude=float(row["latitude"]), longitude=float(row["longitude"])),
        citizen_selected_category=payload.citizen_selected_category,
        category=row.get("category"),
        status="submitted",
        submitted_at=row["reported_at"],
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
    )
    return success_envelope(data.model_dump(mode="json"))


@router.get("/{report_id}")
def get_report(
    report_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.CITIZEN))],
) -> dict:
    row = reports_ops.get_incident(report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="report not found")
    reported_at = row.get("reported_at")
    if hasattr(reported_at, "isoformat"):
        reported_at_str = reported_at.isoformat()
    else:
        reported_at_str = str(reported_at) if reported_at else None
    return success_envelope({
        "report_id": row["incident_id"],
        "category": row.get("category"),
        "reported_at": reported_at_str,
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "description": row.get("description"),
        "duplicates_seen": int(row.get("duplicates_seen") or 1),
    })