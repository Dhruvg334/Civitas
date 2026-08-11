"""Civitas ML integration contracts (Phases 9-10).

The canonical, typed, schema-validated surface of the ML/CV intelligence
layer. Two families of models:

- section/output models consumed by the agent and API layers
  (`ReportAnalysis`, `ResolutionVerification`, ...);
- input/backend models exchanged with the backend adapter
  (`ReportInput`, `NearbyCandidatesRequest/Response`, `CandidateReport`,
  `LandmarkSet`, `MediaReference`).

Every output records what actually ran in `basis`; unavailable sections
record *why* instead of guessing. Field names reuse the repository-wide
conventions from `schemas/json/report.schema.json` (report_id,
description, location fields, submitted_at, citizen_selected_category)
and `schemas/json/common-error.schema.json` (code, message, details,
trace_id). All phases keep the strict rule: inspectable evidence,
measured confidence, no invented facts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Error / trace envelope (mirrors schemas/json/common-error.schema.json)
# ---------------------------------------------------------------------------


class ErrorPayload(BaseModel):
    """Structured error raised by ML/backends, mirrored on the JSON schema."""

    code: str
    message: str
    details: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)
    trace_id: str | None = None


# ---------------------------------------------------------------------------
# Report input (mirrors schemas/json/report.schema.json + media)
# ---------------------------------------------------------------------------


class MediaReference(BaseModel):
    """One image/video reference on a report: local path or backend id.

    Exactly one of `media_id` (backend reference) and `local_path` (local
    test media) is required in practice; both may be absent only when the
    report has no media at all.
    """

    media_id: str | None = None
    kind: Literal["image", "video"]
    mime_type: str | None = None
    local_path: str | None = None
    note: str | None = None


class ReportInput(BaseModel):
    """Everything the ML pipeline needs about one citizen report.

    Required: report_id. Everything else degrades gracefully and records
    why in `basis` — the pipeline never refuses a report for missing GPS,
    missing text or missing media; it returns uncertainty instead.
    """

    report_id: str
    media: list[MediaReference] = Field(default_factory=list)
    description: str = ""
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    submitted_at: datetime | None = None
    citizen_category: str | None = Field(default=None, description="incident category already known (nullable)")
    trace_id: str | None = None
    retrieval_radius_m: float = Field(default=2000.0, ge=0, description="spatial window for nearby-candidate retrieval")
    retrieval_window_h: float = Field(default=72.0, ge=0, description="temporal window (h) for nearby-candidate retrieval")


class ResolutionInput(BaseModel):
    """The after-action check: BEFORE and AFTER media for one incident."""

    incident_id: str
    before: MediaReference
    after: MediaReference
    before_source: str = "citizen upload (before)"
    after_source: str = "inspector upload (after)"
    trace_id: str | None = None


# ---------------------------------------------------------------------------
# Backend adapter wire models (nearby-candidate retrieval + landmarks)
# ---------------------------------------------------------------------------


class NearbyCandidatesRequest(BaseModel):
    """What the ML module needs back from the backend (PostGIS layer).

    The retrieval *implementation* lives in the backend (Utkarsh's
    PostGIS); the ML module only defines the window and consumes the
    schema-valid answer.
    """

    report_id: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    submitted_at: datetime
    category: str | None = None
    radius_m: float = Field(default=2000.0, ge=0)
    time_window_h: float = Field(default=72.0, ge=0)
    limit: int = Field(default=25, ge=1, le=100)


class CandidateReport(BaseModel):
    """One nearby/known report returned by the backend for duplicate work."""

    report_id: str
    description: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    submitted_at: datetime
    category: str | None = None
    landmark_ids: list[str] = Field(default_factory=list)
    media_references: list[MediaReference] = Field(default_factory=list)
    incident_id: str | None = Field(default=None, description="stable incident id when already grouped by backend")


class NearbyCandidatesResponse(BaseModel):
    """Schema-valid answer to a retrieval request."""

    request: NearbyCandidatesRequest
    candidates: list[CandidateReport] = Field(default_factory=list)
    count: int = Field(ge=0)
    basis: list[str] = Field(default_factory=list, description="what the backend ran (spatial + temporal window)")


class LandmarkInfo(BaseModel):
    """One landmark the backend knows about, needed by geo feature models."""

    landmark_id: str
    name: str
    kind: str = Field(description="e.g. school, hospital, junction, metro")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: float = Field(default=200.0, ge=0)


class LandmarkSet(BaseModel):
    """The landmark context the pipeline asks the backend for once."""

    landmarks: list[LandmarkInfo] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Output sections (Phase 9 surface, extended in Phase 10)
# ---------------------------------------------------------------------------


class VisionSection(BaseModel):
    """What the vision pipeline observed on the report media."""

    media_usable: bool
    media_rejected_basis: list[str] = Field(default_factory=list)
    primary_category: str | None = None
    secondary_categories: list[str] = Field(default_factory=list)
    secondary_label: str | None = Field(
        default=None,
        description="real-media subcategory label (e.g. 'Open/unsafe drain') or None",
    )
    precise_observable_description: str = Field(
        default="",
        description="template-generated plain-language description of the visible evidence",
    )
    observable_evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    ood_ratio: float | None = Field(default=None, ge=0, description="out-of-distribution ratio > 2.0 = uncertain")
    uncertainty: list[str] = Field(default_factory=list)
    media_kind: Literal["image", "video", "none"] = "none"
    frames_selected: int = Field(default=0, ge=0)
    video_total_frames: int | None = Field(default=None, ge=0, description="decoded frames from the video stream (bounded)")
    video_duration_s: float | None = Field(default=None, ge=0, description="container-reported duration in seconds, when available")
    video_fps: float | None = Field(default=None, ge=0, description="container-reported frame rate, when available")
    basis: list[str] = Field(default_factory=list)


class EmbeddingSection(BaseModel):
    """The canonical retrieval embeddings for this report (text, image)."""

    available: bool = True
    failure: str | None = None
    text_embedding: list[float] = Field(default_factory=list)
    text_dim: int = Field(ge=0)
    method: str
    image_embedding: list[float] | None = None
    image_dim: int | None = None
    basis: list[str] = Field(default_factory=list)


class DuplicateCandidate(BaseModel):
    """One memory report compared against the new report."""

    report_id: str
    similarity: float = Field(ge=0, le=1)
    is_duplicate: bool
    requires_review: bool
    feature_contributions: dict[str, float | int | bool | str] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


class DuplicateSection(BaseModel):
    """Duplicate verdict for the new report against the incident memory."""

    mode: Literal["full", "no-memory", "no-geo"]
    verdict: Literal["new", "duplicate", "unknown"]
    candidates: list[DuplicateCandidate] = Field(default_factory=list)
    best_match: DuplicateCandidate | None = None
    basis: list[str] = Field(default_factory=list)


class ClusterSection(BaseModel):
    """The incident-clustering answer for this report (conservative merge)."""

    available: bool
    cluster_id: str | None = None
    member_count: int = Field(default=1, ge=1)
    member_report_ids: list[str] = Field(default_factory=list)
    mean_pairwise_score: float = Field(default=0.0, ge=0, le=1)
    span_m: float = Field(default=0.0, ge=0)
    verdict: Literal["merged", "isolated", "unknown"]
    basis: list[str] = Field(default_factory=list)


class GeospatialSection(BaseModel):
    """Spatial signals the geo feature engine produced for this report."""

    available: bool
    population_density_proxy: float | None = Field(default=None, ge=0, le=1)
    incident_density_1km: float | None = Field(default=None, ge=0, le=1)
    nearby_landmarks: list[str] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class FactorPoint(BaseModel):
    """One named contribution/reason with points and evidence."""

    factor: str
    points: int
    evidence: str


class SeveritySection(BaseModel):
    """Severity verdict: how serious is the physical incident itself."""

    available: bool
    score: int | None = Field(default=None, ge=0, le=100)
    level: str | None = None
    factors: list[FactorPoint] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class PrioritySection(BaseModel):
    """Priority verdict: how urgently should the municipality respond."""

    available: bool
    score: int | None = Field(default=None, ge=0, le=100)
    level: str | None = None
    reasons: list[FactorPoint] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class ModelReference(BaseModel):
    """One model that ran, with its version and configured thresholds."""

    component: str
    model_version: str
    thresholds: dict[str, float] = Field(default_factory=dict)
    note: str | None = None


class ReportAnalysis(BaseModel):
    """The complete analyse-a-report answer (stable ML interface).

    Agent/API layers consume exactly this object; all ML evidence and
    model metadata is inside it.
    """

    report_id: str
    trace_id: str | None = None
    vision: VisionSection
    embeddings: EmbeddingSection
    duplicate: DuplicateSection
    cluster: ClusterSection
    geospatial: GeospatialSection
    severity: SeveritySection
    priority: PrioritySection
    models: list[ModelReference] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class ResolutionVerification(BaseModel):
    """The verify-resolution answer: status, confidence, evidence."""

    incident_id: str
    trace_id: str | None = None
    status: Literal["resolved", "partial", "unverifiable", "conflicting"]
    label: str
    confidence: float = Field(ge=0, le=1)
    resolved_signals: int = Field(ge=0)
    total_signals: int = Field(ge=0)
    evidence: list[str] = Field(default_factory=list)
    reasons: list[FactorPoint] = Field(default_factory=list)
    models: list[ModelReference] = Field(default_factory=list)
    model_version: str
    basis: list[str] = Field(default_factory=list)