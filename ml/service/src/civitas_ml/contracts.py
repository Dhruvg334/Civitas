"""Civitas ML service contracts (Phase 9).

The stable, typed surface LangGraph agents consume. `analyze_report`
returns one `ReportAnalysis`; `verify_resolution` returns one
`ResolutionVerification`. Every section carries a `basis` (what was
actually run) and unavailable sections record *why* instead of guessing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class VisionSection(BaseModel):
    """What the vision pipeline observed on the report media."""

    media_usable: bool
    media_rejected_basis: list[str] = Field(default_factory=list)
    primary_category: str | None = None
    observable_evidence: list[str] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class EmbeddingSection(BaseModel):
    """The canonical retrieval embeddings for this report (text, image)."""

    text_embedding: list[float] = Field(default_factory=list)
    text_dim: int = Field(ge=0)
    image_embedding: list[float] | None = None
    image_dim: int | None = None
    method: str
    basis: list[str] = Field(default_factory=list)


class DuplicateCandidate(BaseModel):
    """One memory report compared against the new report."""

    report_id: str
    similarity: float = Field(ge=0, le=1)
    is_duplicate: bool
    requires_review: bool
    reasons: list[str] = Field(default_factory=list)


class DuplicateSection(BaseModel):
    """Duplicate verdict for the new report against the incident memory."""

    mode: Literal["full", "no-memory", "no-geo"]
    verdict: Literal["new", "duplicate", "unknown"]
    candidates: list[DuplicateCandidate] = Field(default_factory=list)
    best_match: DuplicateCandidate | None = None
    basis: list[str] = Field(default_factory=list)


class FactorPoint(BaseModel):
    """One named contribution/reason with points and evidence."""

    factor: str
    points: int
    evidence: str


class SeveritySection(BaseModel):
    """Severity verdict for the report as a standalone incident."""

    available: bool
    score: int | None = Field(default=None, ge=0, le=100)
    level: str | None = None
    factors: list[FactorPoint] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class PrioritySection(BaseModel):
    """Priority verdict for the report as a standalone incident."""

    available: bool
    score: int | None = Field(default=None, ge=0, le=100)
    level: str | None = None
    reasons: list[FactorPoint] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class ReportAnalysis(BaseModel):
    """The complete analyse-a-report answer (stable ML interface)."""

    report_id: str
    vision: VisionSection
    embeddings: EmbeddingSection
    duplicate: DuplicateSection
    severity: SeveritySection
    priority: PrioritySection
    basis: list[str] = Field(default_factory=list)


class ResolutionVerification(BaseModel):
    """The verify-resolution answer: status, confidence, evidence."""

    incident_id: str
    status: Literal["resolved", "partial", "unverifiable", "conflicting"]
    label: str
    confidence: float = Field(ge=0, le=1)
    resolved_signals: int = Field(ge=0)
    total_signals: int = Field(ge=0)
    evidence: list[str] = Field(default_factory=list)
    reasons: list[FactorPoint] = Field(default_factory=list)
    model_version: str
    basis: list[str] = Field(default_factory=list)