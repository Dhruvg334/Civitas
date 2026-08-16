"""In-process composition of the persisted Civitas report with the unified ML pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, cast

from civitas_ml.adapters.base import BackendAdapter
from civitas_ml.contracts import (
    CandidateReport,
    LandmarkInfo,
    LandmarkSet,
    MediaReference,
    NearbyCandidatesRequest,
    NearbyCandidatesResponse,
    ReportAnalysis,
    ReportInput,
)
from civitas_ml.pipeline import run_report

from civitas_api.core.spatial import (
    DEFAULT_BOUNDARY,
    GeoPoint,
    get_candidate_retriever,
    get_landmark_index,
)
from civitas_api.core.storage import get_storage
from civitas_api.operations import reports as reports_ops


class PersistedReportBackend(BackendAdapter):
    """BackendAdapter backed directly by Civitas persistence/storage.

    This is used when ML executes in the same FastAPI process. It preserves the
    same typed ML boundary without making the backend call itself over HTTP.
    """

    def fetch_nearby_candidates(
        self, request: NearbyCandidatesRequest
    ) -> NearbyCandidatesResponse:
        from civitas_geo.models import CandidateSearchSpec

        retriever = get_candidate_retriever()
        spec = CandidateSearchSpec(
            center=GeoPoint(latitude=request.latitude, longitude=request.longitude),
            radius_m=max(request.radius_m, 0.001),
            within_hours=max(request.time_window_h, 0.001),
            limit=request.limit,
            exclude_incident_ids=[request.report_id],
            category_filter=None,
        )
        memory_incidents = None
        if retriever._executor is None:
            memory_incidents = reports_ops.list_incidents(limit=1000)
        result = retriever.retrieve(
            spec,
            memory_incidents=memory_incidents,
            boundary=DEFAULT_BOUNDARY,
            now=request.submitted_at,
        )

        candidates: list[CandidateReport] = []
        for candidate in result.candidates:
            row = reports_ops.get_incident(candidate.incident_id)
            if not row:
                continue
            candidates.append(
                CandidateReport(
                    report_id=candidate.incident_id,
                    incident_id=candidate.incident_id,
                    description=str(row.get("description") or ""),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    submitted_at=row["reported_at"],
                    category=row.get("category"),
                    landmark_ids=[
                        distance.landmark.landmark_id
                        for distance in candidate.landmark_context
                    ],
                    media_references=_media_references(candidate.incident_id),
                )
            )
        return NearbyCandidatesResponse(
            request=request,
            candidates=candidates,
            count=len(candidates),
            basis=list(result.basis),
        )

    def fetch_landmarks(self) -> LandmarkSet:
        index = get_landmark_index()
        return LandmarkSet(
            landmarks=[
                LandmarkInfo(
                    landmark_id=landmark.landmark_id,
                    name=landmark.name,
                    kind=landmark.kind,
                    latitude=landmark.latitude,
                    longitude=landmark.longitude,
                    radius_m=landmark.radius_m,
                )
                for landmark in index.landmarks
            ],
            basis=["Civitas landmark index"],
        )

    def fetch_media(self, reference: str) -> bytes:
        row = reports_ops.get_media(reference)
        if row is None:
            raise FileNotFoundError(reference)
        return get_storage().get(str(row["storage_path"]))

    def resolve_media_metadata(self, reference: str) -> MediaReference:
        row = reports_ops.get_media(reference)
        if row is None:
            raise FileNotFoundError(reference)
        return MediaReference(
            media_id=str(row["media_id"]),
            kind=cast(Literal["image", "video"], str(row["kind"])),
            mime_type=str(row.get("mime_type") or "") or None,
        )


def _media_references(report_id: str) -> list[MediaReference]:
    return [
        MediaReference(
            media_id=str(row["media_id"]),
            kind=cast(Literal["image", "video"], str(row["kind"])),
            mime_type=str(row.get("mime_type") or "") or None,
        )
        for row in reports_ops.list_media_for_incident(report_id)
    ]


def analyze_persisted_report(report_id: str, *, trace_id: str | None = None) -> ReportAnalysis:
    """Load one stored report and execute the canonical adapter-driven ML pipeline."""
    row = reports_ops.get_incident(report_id)
    if row is None:
        raise LookupError(f"report {report_id} not found")

    submitted_at = row.get("reported_at")
    if isinstance(submitted_at, str):
        submitted_at = datetime.fromisoformat(submitted_at)

    record = ReportInput(
        report_id=report_id,
        media=_media_references(report_id),
        description=str(row.get("description") or ""),
        latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
        longitude=float(row["longitude"]) if row.get("longitude") is not None else None,
        submitted_at=submitted_at,
        citizen_category=row.get("category"),
        trace_id=trace_id,
    )
    return run_report(record, backend=PersistedReportBackend())


__all__ = ["PersistedReportBackend", "analyze_persisted_report"]
