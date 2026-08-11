"""Typed contracts for the Civitas computer vision pipeline (Phase 3).

The pipeline consumes citizen image/video evidence and returns structured
visual intelligence: quality verdict, usable-frame summary, incident category
probabilities, observable evidence and confidence. All probabilities,
measurements and rules are explainable: every result carries `basis` entries
naming the concrete measurements behind each decision.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CivitasCategory = Literal[
    "pothole_road_damage",
    "water_leakage",
    "garbage_overflow",
    "broken_streetlight",
    "fallen_tree",
]

CIVITAS_CATEGORIES: tuple[str, ...] = (
    "pothole_road_damage",
    "water_leakage",
    "garbage_overflow",
    "broken_streetlight",
    "fallen_tree",
)

# The real-media (zero-shot CLIP) classifier additionally recognises these
# categories; the deterministic k-NN stays on the five MVP classes so the
# frozen synthetic evaluation is untouched.
REAL_MEDIA_CATEGORIES: tuple[str, ...] = CIVITAS_CATEGORIES + (
    "other_infrastructure_damage",
    "drainage_damage",
    "no_incident",
    "pest_infestation",
)


class SceneQuality(BaseModel):
    """Quality verdict for a single frame/image before classification."""

    usable: bool
    width_px: int = Field(ge=0)
    height_px: int = Field(ge=0)
    blur_score: float = Field(ge=0)
    luminance_mean: float = Field(ge=0, le=1)
    saturation_mean: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class FramePick(BaseModel):
    """A selected key frame from video media."""

    index: int = Field(ge=0)
    quality: SceneQuality


class ClassificationProbs(BaseModel):
    """Per-category probabilities for one image (or merged over media)."""

    probabilities: dict[str, float] = Field(default_factory=dict)
    primary_category: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    ood_ratio: float | None = Field(
        default=None,
        ge=0,
        description="mean nearest-prototype distance / corpus median distance; "
        "> 2.0 means the input is far outside the training manifold (uncertain)",
    )
    secondary_label: str | None = Field(
        default=None,
        description="real-media subcategory label for the primary category "
        "(e.g. 'Wall moisture damage' under water_leakage); None when none is confident",
    )
    subcategory_scores: dict[str, float] = Field(
        default_factory=dict,
        description="per-subcategory similarities scoped to the primary category",
    )
    basis: list[str] = Field(default_factory=list)


class VisualClassificationResult(BaseModel):
    """Structured visual intelligence for one media upload.

    Mirrors the product contract:
        primary_category, secondary_categories, observable_evidence,
        confidence
    plus the provenance fields that keep the decision reviewable.
    """

    primary_category: str | None = None
    secondary_categories: list[str] = Field(default_factory=list)
    secondary_label: str | None = Field(
        default=None,
        description="real-media subcategory label (e.g. 'Open/unsafe drain') "
        "or None; distinct from secondary_categories which lists competing categories",
    )
    precise_observable_description: str = Field(
        default="",
        description="deterministic, template-generated plain-language description "
        "of what the media observably shows (built from the detected category "
        "and subcategory; not an LLM caption)",
    )
    observable_evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    ood_ratio: float | None = Field(
        default=None,
        ge=0,
        description="out-of-distribution ratio of the media (see ClassificationProbs)",
    )
    media_usable: bool = True
    frames_selected: int = Field(default=0, ge=0)
    quality: SceneQuality | None = None
    probability_vector: dict[str, float] = Field(default_factory=dict)
    basis: list[str] = Field(default_factory=list)

    def as_json(self) -> dict[str, object]:
        return {
            "primary_category": self.primary_category,
            "secondary_categories": self.secondary_categories,
            "secondary_label": self.secondary_label,
            "precise_observable_description": self.precise_observable_description,
            "observable_evidence": self.observable_evidence,
            "confidence": round(self.confidence, 4),
        }