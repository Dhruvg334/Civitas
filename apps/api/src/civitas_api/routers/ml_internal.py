"""Internal API consumed by the Civitas ML service.

This is the canonical backend/ML integration boundary. It deliberately
returns the existing Civitas success envelope while keeping persistence and
PostGIS details behind the backend. In production, X-Civitas-Internal-Key is
required.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field

from civitas_api.core.config import get_settings
from civitas_api.core.envelope import success_envelope
from civitas_api.core.spatial import (
    DEFAULT_BOUNDARY,
    GeoPoint,
    get_candidate_retriever,
    get_landmark_index,
)
from civitas_api.core.storage import get_storage
from civitas_api.operations import reports as reports_ops

router = APIRouter(prefix="/api/v1/ml", tags=["internal-ml"])


class NearbyCandidatesRequest(BaseModel):
    report_id: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    submitted_at: datetime
    category: str | None = None
    radius_m: float = Field(default=2000.0, ge=0, le=50_000)
    time_window_h: float = Field(default=72.0, ge=0, le=8_760)
    limit: int = Field(default=25, ge=1, le=100)


class AnalyzeReportRequest(BaseModel):
    """Identifier-only request; the backend loads persisted report context."""

    report_id: str = Field(min_length=1, max_length=200)
    trace_id: str | None = Field(default=None, max_length=200)


def require_internal_key(x_civitas_internal_key: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    expected = settings.civitas_internal_api_key.strip()
    if not expected and not settings.is_production:
        return
    if not expected or x_civitas_internal_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid internal service key"
        )


@router.post("/analyze")
def analyze(
    body: AnalyzeReportRequest,
    _: Annotated[None, Depends(require_internal_key)],
) -> dict[str, Any]:
    """Thin internal bridge to the existing unified ReportAnalysis pipeline."""
    from civitas_api.services.ml_runtime import analyze_persisted_report

    try:
        analysis = analyze_persisted_report(body.report_id, trace_id=body.trace_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="report not found") from exc
    return success_envelope(analysis.model_dump(mode="json"))


def _media_refs(incident_id: str) -> list[dict[str, Any]]:
    refs = []
    for row in reports_ops.list_media_for_incident(incident_id):
        refs.append(
            {
                "media_id": row["media_id"],
                "kind": row["kind"],
                "mime_type": row.get("mime_type"),
                "local_path": None,
                "note": None,
            }
        )
    return refs


@router.post("/nearby-candidates")
def nearby_candidates(
    body: NearbyCandidatesRequest, _: Annotated[None, Depends(require_internal_key)]
) -> dict[str, Any]:
    from civitas_geo.models import CandidateSearchSpec

    retriever = get_candidate_retriever()
    spec = CandidateSearchSpec(
        center=GeoPoint(latitude=body.latitude, longitude=body.longitude),
        radius_m=max(body.radius_m, 0.001),
        within_hours=max(body.time_window_h, 0.001),
        limit=body.limit,
        exclude_incident_ids=[body.report_id],
        category_filter=None,  # duplicate engine handles related-category logic itself
    )
    memory_incidents = None
    if retriever._executor is None:
        memory_incidents = reports_ops.list_incidents(limit=1000)
    result = retriever.retrieve(
        spec, memory_incidents=memory_incidents, boundary=DEFAULT_BOUNDARY, now=body.submitted_at
    )
    candidates = []
    for cand in result.candidates:
        row = reports_ops.get_incident(cand.incident_id)
        if not row:
            continue
        landmark_ids = [d.landmark.landmark_id for d in cand.landmark_context]
        candidates.append(
            {
                "report_id": cand.incident_id,
                "description": row.get("description") or "",
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "submitted_at": row["reported_at"],
                "category": row.get("category"),
                "landmark_ids": landmark_ids,
                "media_references": _media_refs(cand.incident_id),
                "incident_id": cand.incident_id,
            }
        )
    return success_envelope(
        {
            "request": body.model_dump(mode="json"),
            "candidates": candidates,
            "count": len(candidates),
            "basis": list(result.basis),
        }
    )


@router.get("/landmarks")
def landmarks(_: Annotated[None, Depends(require_internal_key)]) -> dict[str, Any]:
    index = get_landmark_index()
    return success_envelope(
        {
            "landmarks": [lm.model_dump(mode="json") for lm in index.landmarks],
            "basis": ["backend landmark index"],
        }
    )


@router.get("/media/{media_id}/metadata")
def media_metadata(
    media_id: str, _: Annotated[None, Depends(require_internal_key)]
) -> dict[str, Any]:
    row = reports_ops.get_media(media_id)
    if row is None:
        raise HTTPException(status_code=404, detail="media not found")
    return success_envelope(
        {
            "media_id": row["media_id"],
            "kind": row["kind"],
            "mime_type": row.get("mime_type"),
            "local_path": None,
            "note": None,
        }
    )


@router.get("/media/{media_id}")
def media_bytes(media_id: str, _: Annotated[None, Depends(require_internal_key)]) -> Response:
    row = reports_ops.get_media(media_id)
    if row is None:
        raise HTTPException(status_code=404, detail="media not found")
    storage_path = str(row["storage_path"])
    try:
        data = get_storage().get(storage_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="media object not found") from exc
    return Response(content=data, media_type=row.get("mime_type") or "application/octet-stream")
