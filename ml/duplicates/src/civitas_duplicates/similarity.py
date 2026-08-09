"""Composite duplicate scoring with explainable contributions (Phase 4).

The product question is "do these two reports describe the same real-world
incident?" — not "do these two sentences look similar?". The Phase 4 layer
enforces that distinction structurally:

- `incident_gate()` asks "is the same incident even plausible here?" using the
  geospatial signals (GPS distance, time delta). If a pair is 8 km apart or
  two weeks apart, it cannot be the same incident regardless of how similar
  the wording or pixels look — the pair is answered with `incident_possible =
  False` and explicit reasons.
- `incident_similarity()` then combines image + text embeddings with GPS,
  timestamp, category and landmark signals into a weighted score and a
  decision; every contribution is traceable via `contributions` and
  `decision_basis`.

Weights are explicit and caller-visible; when image embedding is unavailable
its weight is redistributed proportionally instead of silently dropping the
signal budget.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from pydantic import BaseModel, Field

from civitas_duplicates.contracts import PairFeatures
from civitas_duplicates.embeddings import ReportEmbeddings, cosine_similarity
from civitas_duplicates.geo_features import gps_similarity
from civitas_duplicates.signals import category_agreement
from civitas_duplicates.time_features import time_similarity

DEFAULT_WEIGHTS: dict[str, float] = {
    "text_similarity": 0.20,
    "image_similarity": 0.20,
    "category_agreement": 0.10,
    "gps_similarity": 0.20,
    "time_similarity": 0.10,
    "landmark_similarity": 0.20,
}

# Incident-anchored preset (Phase 4): geospatial + temporal signals dominate
# because "same incident" is a physical-place-time claim; language and pixels
# confirm it. Replaces the balanced default when callers want the strict
# product semantics.
INCIDENT_ANCHORED_WEIGHTS: dict[str, float] = {
    "gps_similarity": 0.35,
    "time_similarity": 0.15,
    "landmark_similarity": 0.15,
    "category_agreement": 0.10,
    "text_similarity": 0.15,
    "image_similarity": 0.10,
}


@dataclass(frozen=True)
class ScoringConfig:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    duplicate_threshold: float = 0.70
    # Gates: pairs outside these are duplicates only with exceptional evidence.
    max_reasonable_distance_m: float = 2_000.0
    max_reasonable_delta_h: float = 72.0
    landmark_radius_m: float = 250.0

    def __post_init__(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"duplicate weights must sum to 1.0, got {total}")


class IncidentGateResult(BaseModel):
    """Phase 4: the geospatial plausibility question answered explicitly."""

    incident_possible: bool
    distance_m: float = Field(ge=0)
    time_delta_h: float = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)


def incident_gate(pair: PairFeatures, cfg: ScoringConfig | None = None) -> IncidentGateResult:
    """Is the same real-world incident physically plausible for this pair?

    Uses only the geospatial signals (distance, time), never language or
    pixels, so similar-sounding reports in different places cannot be merged
    as the same incident.
    """
    cfg = cfg or ScoringConfig()
    reasons: list[str] = []
    possible = True
    if pair.gps_distance_m > cfg.max_reasonable_distance_m:
        possible = False
        reasons.append(
            f"reports {pair.gps_distance_m:.0f} m apart (limit "
            f"{cfg.max_reasonable_distance_m:.0f} m): different physical spot"
        )
    if pair.time_delta_h > cfg.max_reasonable_delta_h:
        possible = False
        reasons.append(
            f"reports {pair.time_delta_h:.1f} h apart (limit "
            f"{cfg.max_reasonable_delta_h:.0f} h): not the same event window"
        )
    if possible:
        reasons.append(
            f"same-incident plausible: {pair.gps_distance_m:.0f} m and "
            f"{pair.time_delta_h:.1f} h inside geospatial gates"
        )
    return IncidentGateResult(
        incident_possible=possible,
        distance_m=pair.gps_distance_m,
        time_delta_h=pair.time_delta_h,
        reasons=reasons,
    )


class IncidentSimilarityResult(BaseModel):
    """The Phase 4 answer: same real-world incident? With full traceability."""

    is_duplicate: bool
    score: float = Field(ge=0, le=1)
    incident_possible: bool
    requires_review: bool = Field(default=False)
    contributions: dict[str, float | int | bool | str] = Field(default_factory=dict)
    decision_basis: list[str] = Field(default_factory=list)


def make_pair(
    report_a: ReportEmbeddings,
    report_b: ReportEmbeddings,
) -> PairFeatures:
    """Phase 4: derive PairFeatures from two report embedding records.

    Text and image similarities come from the real embeddings; GPS, time,
    category and landmark signals come from the report's raw geospatial
    signals stored alongside the embeddings.
    """
    if not report_a.text_embedding or not report_b.text_embedding:
        raise ValueError(
            "text embeddings are required on both reports; "
            "build them with build_report_embeddings() first"
        )
    text_sim = cosine_similarity(report_a.text_embedding, report_b.text_embedding)

    img_sim: float | None = None
    if report_a.image_embedding and report_b.image_embedding:
        img_sim = cosine_similarity(report_a.image_embedding, report_b.image_embedding)

    gps_sim = 0.0
    dist_m = 0.0
    if report_a.gps and report_b.gps:
        gps_sim, dist_m = gps_similarity(
            report_a.gps[0], report_a.gps[1], report_b.gps[0], report_b.gps[1]
        )

    t_sim = 0.0
    delta_h = 0.0
    if report_a.submitted_at and report_b.submitted_at:
        t_sim, delta_h = time_similarity(
            datetime.fromisoformat(report_a.submitted_at),
            datetime.fromisoformat(report_b.submitted_at),
        )

    set_a = set(report_a.landmark_ids)
    set_b = set(report_b.landmark_ids)
    landmark_sim = 0.0
    if set_a and set_b:
        landmark_sim = len(set_a & set_b) / len(set_a | set_b)

    return PairFeatures(
        text_similarity=text_sim,
        image_similarity=img_sim,
        category_agreement=category_agreement(report_a.category, report_b.category),
        gps_similarity=gps_sim,
        gps_distance_m=dist_m,
        time_similarity=t_sim,
        time_delta_h=delta_h,
        landmark_similarity=landmark_sim,
    )


def incident_similarity(
    report_a: ReportEmbeddings,
    report_b: ReportEmbeddings,
    cfg: ScoringConfig | None = None,
    weights: dict[str, float] | None = None,
) -> IncidentSimilarityResult:
    """The Phase 4 question: do these two reports describe the same incident?

    Structure of the answer:
    1. Geospatial gate first — physical place + time plausibility. If the
       gate fails, the pair is answered "no" using only observed signals,
       regardless of how similar wording or pixels are.
    2. If plausible, fusion of text + image embeddings with category, GPS,
       time and landmark signals into a weighted score, then a threshold
       decision with near-threshold/conflict escalations to human review.

    When GPS or timestamps are missing the question cannot be answered from
    evidence: the pair is escalated for human review, never guessed.
    """
    cfg = cfg or ScoringConfig()
    if weights is not None:
        cfg = replace(cfg, weights=dict(weights))

    missing = [
        note
        for note, present in (
            ("GPS signal missing on one or both reports", bool(report_a.gps and report_b.gps)),
            ("timestamp signal missing on one or both reports", bool(report_a.submitted_at and report_b.submitted_at)),
        )
        if not present
    ]
    if missing:
        return IncidentSimilarityResult(
            is_duplicate=False,
            score=0.0,
            incident_possible=False,
            requires_review=True,
            contributions={"same_incident": "cannot_answer", "missing_signals": "; ".join(missing)},
            decision_basis=[
                "cannot answer same-incident question on evidence: " + "; ".join(missing),
                "escalated to human review",
            ],
        )

    pair = make_pair(report_a, report_b)
    gate = incident_gate(pair, cfg)
    if not gate.incident_possible:
        return IncidentSimilarityResult(
            is_duplicate=False,
            score=0.0,
            incident_possible=False,
            contributions=pair.contributions(),
            decision_basis=gate.reasons
            + ["answered with geospatial evidence only; language and pixels were not consulted"],
        )

    score = composite_score(pair, cfg)
    is_dup, basis, review = decide_duplicate(pair, cfg)
    return IncidentSimilarityResult(
        is_duplicate=is_dup,
        score=score,
        incident_possible=True,
        requires_review=review,
        contributions=pair.contributions(),
        decision_basis=gate.reasons + basis,
    )


def compute_pair_features(
    pair: PairFeatures,
) -> dict[str, float]:
    return {
        "text_similarity": pair.text_similarity,
        "image_similarity": pair.image_similarity if pair.image_similarity is not None else 0.0,
        "category_agreement": pair.category_agreement,
        "gps_similarity": pair.gps_similarity,
        "time_similarity": pair.time_similarity,
        "landmark_similarity": pair.landmark_similarity,
    }


def composite_score(pair: PairFeatures, cfg: ScoringConfig | None = None) -> float:
    """Weighted composite similarity in [0, 1].

    When image similarity is unavailable its weight is redistributed
    proportionally across the available signals so the score is not
    under-weighted by a missing modality.
    """
    cfg = cfg or ScoringConfig()
    weights = dict(cfg.weights)
    features = compute_pair_features(pair)
    if pair.image_similarity is None:
        dropped = weights.pop("image_similarity", 0.0)
        features.pop("image_similarity", None)
        remaining = sum(weights.values())
        if remaining > 0 and dropped > 0:
            weights = {k: v + dropped * (v / remaining) for k, v in weights.items()}
    return sum(features[k] * weights[k] for k in features if k in weights)


def decide_duplicate(
    pair: PairFeatures,
    cfg: ScoringConfig | None = None,
) -> tuple[bool, list[str], bool]:
    """Apply composite scoring plus explicit gates.

    Returns (is_duplicate, basis, requires_review). Ambiguous pairs are
    flagged for human review rather than silently accepted or rejected.
    """
    cfg = cfg or ScoringConfig()
    score = composite_score(pair, cfg)
    basis: list[str] = [
        f"composite similarity {score:.2f} (threshold {cfg.duplicate_threshold:.2f})",
        f"text cosine {pair.text_similarity:.2f}",
        f"gps distance {pair.gps_distance_m:.0f} m (similarity {pair.gps_similarity:.2f})",
        f"time delta {pair.time_delta_h:.1f} h (similarity {pair.time_similarity:.2f})",
        f"category agreement {pair.category_agreement:.0f}",
        f"landmark overlap {pair.landmark_similarity:.2f}",
    ]
    if pair.image_similarity is not None:
        basis.append(f"image cosine {pair.image_similarity:.2f}")
    else:
        basis.append("image embedding unavailable; weight redistributed")

    requires_review = False
    near_merge = 0.55 <= score < cfg.duplicate_threshold

    if score >= cfg.duplicate_threshold:
        if pair.category_agreement == 0.0 and pair.text_similarity < 0.85:
            # Strong spatial overlap but conflicting semantics (location terms
            # often dominate cosine): merging may collapse two distinct
            # incidents. Escalate to review unless language agrees very firmly.
            basis.append(
                "conflicting categories -> not merged automatically; "
                "flagged for human review"
            )
            return False, basis, True
        return True, basis, False

    # Exceptional-evidence override: a pair may still count as duplicate when
    # geometry and language agree firmly even if the mean stays below threshold.
    # The spatial gate prevents cross-town same-category day reports (frequently
    # distinct incidents) from being merged on wording alone.
    strong_spatial = pair.gps_similarity > 0.85 and pair.landmark_similarity > 0.9
    strong_language = (
        pair.text_similarity > 0.80
        and pair.category_agreement == 1.0
        and pair.gps_distance_m <= cfg.max_reasonable_distance_m * 0.75
    )
    same_day = pair.time_delta_h <= 24.0
    if (strong_spatial or strong_language) and same_day:
        basis.append("exceptional-evidence override (spatial or language agreement)")
        return True, basis, False

    conflict_with_overlap = (
        pair.category_agreement == 0.0
        and pair.gps_similarity > 0.85
        and pair.time_delta_h <= 48.0
    )
    if near_merge or conflict_with_overlap:
        basis.append(
            "near-threshold or conflicting evidence -> requires human review"
        )
        requires_review = True
    return False, basis, requires_review