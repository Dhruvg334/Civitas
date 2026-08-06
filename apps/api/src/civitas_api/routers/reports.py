from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CreateReportRequest(BaseModel):
    description: str = Field(min_length=3, max_length=2000)
    location: Location
    citizen_selected_category: str | None = None


class ReportResponse(BaseModel):
    report_id: UUID
    description: str
    location: Location
    citizen_selected_category: str | None
    status: str
    submitted_at: datetime


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(payload: CreateReportRequest) -> ReportResponse:
    """Skeleton endpoint. Persistence is added by the operations module."""
    return ReportResponse(
        report_id=uuid4(),
        description=payload.description,
        location=payload.location,
        citizen_selected_category=payload.citizen_selected_category,
        status="submitted",
        submitted_at=datetime.now(timezone.utc),
    )
