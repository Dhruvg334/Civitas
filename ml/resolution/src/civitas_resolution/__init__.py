"""Civitas resolution verification (Phase 8).

The second ML moment: after the municipality acts, compare the BEFORE photo
evidence with the AFTER photo evidence and answer RESOLVED, PARTIALLY
RESOLVED, UNVERIFIABLE, or CONFLICTING — every verdict fully explainable.
"""

from civitas_resolution.evidence import ResolutionEvidence, Stage
from civitas_resolution.model import (
    CATEGORY_HAZARD_MARKERS,
    COVERAGE_GROWTH_CONFLICT_RATIO,
    DISPLAY_LABELS,
    STANDING_WATER_EVIDENCE_MIN,
    Outcome,
    ResolutionModel,
    ResolutionReason,
    ResolutionVerdict,
    outcome_label,
)

__all__ = [
    "CATEGORY_HAZARD_MARKERS",
    "COVERAGE_GROWTH_CONFLICT_RATIO",
    "DISPLAY_LABELS",
    "STANDING_WATER_EVIDENCE_MIN",
    "Outcome",
    "ResolutionEvidence",
    "ResolutionModel",
    "ResolutionReason",
    "ResolutionVerdict",
    "Stage",
    "outcome_label",
]