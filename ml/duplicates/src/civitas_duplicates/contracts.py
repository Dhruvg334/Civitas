"""Typed contracts for the duplicate detection engine.

Mirrors the stable `DuplicateResult` shape from services/ml so callers of the
ml service boundary stay compatible.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReportLike(BaseModel):
    """Normalized report record consumed by the duplicate engine."""

    report_id: str
    description: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    submitted_at: datetime
    category: str | None = None
    landmark_ids: list[str] = Field(default_factory=list)
    text_embedding: list[float] | None = None
    image_embedding: list[float] | None = None
    media_count: int = Field(default=0, ge=0)


class PairFeatures(BaseModel):
    """One row of explainable duplicate features for a report pair."""

    text_similarity: float = Field(ge=0, le=1)
    image_similarity: float | None = Field(default=None, ge=0, le=1)
    category_agreement: float = Field(ge=0, le=1)
    gps_similarity: float = Field(ge=0, le=1)
    gps_distance_m: float = Field(ge=0)
    time_similarity: float = Field(ge=0, le=1)
    time_delta_h: float = Field(ge=0)
    landmark_similarity: float = Field(ge=0, le=1)

    def contributions(self) -> dict[str, float | int | bool | str]:
        return {
            "text_similarity": self.text_similarity,
            "image_similarity": self.image_similarity or 0.0,
            "category_agreement": self.category_agreement,
            "gps_similarity": self.gps_similarity,
            "time_similarity": self.time_similarity,
            "landmark_similarity": self.landmark_similarity,
        }


class DuplicateResult(BaseModel):
    """Per-pair duplicate decision with full traceability."""

    report_a: str
    report_b: str
    is_duplicate: bool
    matched_incident_id: str | None = None
    score: float = Field(ge=0, le=1)
    feature_contributions: dict[str, float | int | bool | str] = Field(default_factory=dict)
    decision_basis: list[str] = Field(default_factory=list)
    requires_review: bool = Field(default=False)


def _no_device_fallback_note() -> str:
    return "no GPU-dependent provider configured; deterministic hashing embeddings used"


class IncidentCluster(BaseModel):
    """A single real-world incident formed from several reports."""

    cluster_id: str
    report_ids: list[str] = Field(default_factory=list)
    representative_report_id: str
    member_count: int = Field(ge=1)
    mean_pairwise_score: float = Field(ge=0, le=1)
    span_m: float = Field(ge=0)
    basis: list[str] = Field(default_factory=list)

    @property
    def duplicate_evidence_strength(self) -> str:
        if self.mean_pairwise_score >= 0.85 and self.member_count >= 1:
            return "strong"
        if self.mean_pairwise_score >= 0.7:
            return "moderate"
        return "weak"

    @property
    def summarizing_note(self) -> str:
        return (
            f"Cluster {self.cluster_id}: {self.member_count} report(s), "
            f"mean pairwise similarity {self.mean_pairwise_score:.2f} "
            f"({self.duplicate_evidence_strength})."
        )


def report_dedup_key(report: ReportLike) -> str:
    """Deterministic cache key for a report's derived embeddings."""
    return f"{report.report_id}:{len(report.description)}:{report.category}"