"""Civitas ML service: `verify_resolution` composition (Phase 9).

One typed call that runs the after-action ML stack: vision on both
photos -> BEFORE/AFTER evidence -> resolution model -> a
`ResolutionVerification` with status, computed confidence and the
evidence lines the workflow agents can quote. Phase 10 adds the trace
identifier and the resolution model metadata to the answer.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import TypeAlias

from PIL import Image

from civitas_resolution import (
    COVERAGE_GROWTH_CONFLICT_RATIO,
    STANDING_WATER_EVIDENCE_MIN,
    ResolutionEvidence,
    ResolutionModel,
    outcome_label,
)
from civitas_vision.detector import VisualIntelligencePipeline
from civitas_vision.features import extract_features

from civitas_ml.contracts import FactorPoint, ModelReference, ResolutionVerification

Media: TypeAlias = Image.Image | str | os.PathLike[str]

_VISION = VisualIntelligencePipeline()
_RESOLUTION = ResolutionModel()


def _evidence_for(media: Media, incident_id: str, stage: str, source: str) -> ResolutionEvidence:
    image = media if isinstance(media, Image.Image) else Image.open(Path(media))
    result = _VISION.analyze_image(image)
    return ResolutionEvidence.from_vision(
        incident_id, stage, source, result,
        water_coverage=extract_features(image)["blue_smooth_share"],
    )


def _resolution_model_ref() -> ModelReference:
    return ModelReference(
        component="resolution",
        model_version=_RESOLUTION.model_version,
        thresholds={
            "standing_water_evidence_min": STANDING_WATER_EVIDENCE_MIN,
            "coverage_growth_conflict_ratio": COVERAGE_GROWTH_CONFLICT_RATIO,
        },
    )


def verify_resolution(
    before_media: Media,
    after_media: Media,
    *,
    incident_id: str = "INC-001",
    before_source: str = "citizen upload (before)",
    after_source: str = "inspector upload (after)",
    trace_id: str | None = None,
) -> ResolutionVerification:
    """Compare the BEFORE photo with the AFTER photo and answer.

    Returns `status` in {resolved, partial, unverifiable, conflicting},
    a computed `confidence` (never curated), and `evidence` — the exact
    human-readable lines behind the verdict.
    """
    before = _evidence_for(
        before_media, incident_id, "before", before_source
    )
    after = _evidence_for(
        after_media, incident_id, "after", after_source
    )
    verdict = _RESOLUTION.assess(before, after)
    return ResolutionVerification(
        incident_id=incident_id,
        trace_id=trace_id or uuid.uuid4().hex,
        status=verdict.outcome,
        label=outcome_label(verdict.outcome),
        confidence=verdict.confidence,
        resolved_signals=verdict.resolved_signals,
        total_signals=verdict.total_signals,
        evidence=[f"{r.factor}: {r.status} — {r.evidence}" for r in verdict.reasons],
        reasons=[FactorPoint(factor=r.factor, points=0, evidence=r.evidence) for r in verdict.reasons],
        models=[_resolution_model_ref()],
        model_version=_RESOLUTION.model_version,
        basis=list(verdict.basis),
    )