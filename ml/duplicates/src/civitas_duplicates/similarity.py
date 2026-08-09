"""Composite duplicate scoring with explainable contributions.

The composite score is a weighted sum of per-signal similarities in [0, 1].
Weights are explicit and caller-visible; when image embedding is unavailable
its weight is redistributed proportionally instead of silently dropping the
signal budget. Decision thresholds and gates are data-driven defaults and can
be overridden per deployment.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from civitas_duplicates.contracts import PairFeatures

DEFAULT_WEIGHTS: dict[str, float] = {
    "text_similarity": 0.20,
    "image_similarity": 0.20,
    "category_agreement": 0.10,
    "gps_similarity": 0.20,
    "time_similarity": 0.10,
    "landmark_similarity": 0.20,
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