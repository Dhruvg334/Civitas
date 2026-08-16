"""Phase 8: resolution-verification evidence (the BEFORE/AFTER snapshot).

After the municipality acts, the system receives a BEFORE photo (taken at
report time) and an AFTER photo (taken by the inspector). This module types
the evidence each stage carries through the vision pipeline, and provides
the two construction helpers:

- `from_vision` — map a `VisualClassificationResult` (pixel measurements,
  k-NN classification, evidence rules) onto typed evidence;
- `from_evidence` — build evidence from the evidence strings directly
  (tests and evidence-level checks where no photo corpus exists).

`active_water_flow` is derived only from the *flowing* markers
("water flowing across road"); standing water is tracked separately via
`water_coverage`, because a leftover puddle is a partial, not an active
flow. This mirrors `IncidentVisualEvidence` in civitas_risk but keeps the
resolution layer dependency-light: it needs only the vision pipeline.
"""

from __future__ import annotations

from typing import Literal

from civitas_vision.contracts import VisualClassificationResult
from pydantic import BaseModel, Field

WATER_FLOW_MARKERS = ("water flowing across road", "active water flow")
STANDING_WATER_MARKER = "standing water"

Stage = Literal["before", "after"]


class ResolutionEvidence(BaseModel):
    """One side of the before/after pair, captured through the vision pipeline."""

    incident_id: str
    stage: Stage
    source: str
    media_usable: bool = Field(default=True)
    rejection_basis: list[str] = Field(default_factory=list)
    primary_category: str | None = None
    observable_evidence: list[str] = Field(default_factory=list)
    active_water_flow: int = Field(default=0, ge=0, le=1)
    water_coverage: float = Field(default=0.0, ge=0.0, le=1.0)

    @classmethod
    def from_vision(
        cls,
        incident_id: str,
        stage: Stage,
        source: str,
        result: VisualClassificationResult,
        water_coverage: float = 0.0,
    ) -> ResolutionEvidence:
        """Map a visual-pipeline result onto typed evidence for this stage."""
        active = int(any(m in result.observable_evidence for m in WATER_FLOW_MARKERS))
        return cls(
            incident_id=incident_id,
            stage=stage,
            source=source,
            media_usable=result.media_usable,
            rejection_basis=list(result.basis) if not result.media_usable else [],
            primary_category=result.primary_category,
            observable_evidence=list(result.observable_evidence),
            active_water_flow=active,
            water_coverage=max(0.0, min(1.0, water_coverage)),
        )

    @classmethod
    def from_evidence(
        cls,
        incident_id: str,
        stage: Stage,
        source: str,
        primary_category: str | None = None,
        observable_evidence: list[str] | tuple[str, ...] = (),
        water_coverage: float = 0.0,
    ) -> ResolutionEvidence:
        """Build evidence directly from the CV evidence strings."""
        active = int(any(m in " ".join(observable_evidence).lower() for m in WATER_FLOW_MARKERS))
        return cls(
            incident_id=incident_id,
            stage=stage,
            source=source,
            primary_category=primary_category,
            observable_evidence=list(observable_evidence),
            active_water_flow=active,
            water_coverage=max(0.0, min(1.0, water_coverage)),
        )