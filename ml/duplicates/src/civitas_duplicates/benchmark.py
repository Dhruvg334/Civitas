"""Phase 4 pair benchmark: same-incident vs distinct-incident reports.

Evaluates the FULL product answer — "do these two reports describe the same
real-world incident?" — on synthetic pairs:

  - duplicate pairs    : same incident (same GPS cell, same burst window,
                         same category, same landmarks, different
                         descriptions and photo variants)
  - non-duplicate pairs: genuinely different incidents (far apart in space
                         and/or time, different categories)

Metrics are computed against the `incident_similarity` decision (gate +
fused embeddings + signals), and a threshold sweep reports how the
precision/recall trade-off moves.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from civitas_duplicates.embeddings import (
    ClassicalImageEmbedder,
    HashNgramEmbedder,
    ReportEmbeddings,
    build_report_embeddings,
)
from civitas_duplicates.similarity import (
    INCIDENT_ANCHORED_WEIGHTS,
    ScoringConfig,
    incident_similarity,
)

NOW = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
CENTER = (28.6139, 77.2090)  # demo-city centre

CATEGORIES = ("pothole", "water_leak", "garbage", "streetlight", "fallen_tree")

SYNTHETIC_DESCRIPTIONS: dict[str, list[str]] = {
    "pothole": [
        "deep pothole on the main road near the crossing, tyres keep bottoming out",
        "pinch point in the asphalt right before the junction, cars swerve around it",
        "big crater in the tarmac by the market entrance, hard to miss",
    ],
    "water_leak": [
        "pipe burst spraying water across the footpath",
        "water leaking from the ground near the parking entrance",
        "flooding on the road, water gushing out of a broken main",
    ],
    "garbage": [
        "garbage overflow, bags scattered all over the pavement",
        "waste dumped beside the dustbin, the smell is terrible",
        "trash pile blocking the walkway near the shops",
    ],
    "streetlight": [
        "streetlight not working, the whole stretch is dark at night",
        "lamp post dead near the bus stop, very dark corner",
        "street lamp flickering and then went off completely",
    ],
    "fallen_tree": [
        "tree uprooted across the road, traffic blocked both ways",
        "big branch came down on the pathway after the storm",
        "fallen tree blocking the main gate and the footpath",
    ],
}

_LANDMARK_DUP = ["lm-school-1", "lm-junction-2"]
_LANDMARK_OTHER = ["lm-market-3"]

# Canonical incident categories -> civitas-vision scene categories.
_VISION_CATEGORY: dict[str, str] = {
    "pothole": "pothole_road_damage",
    "water_leak": "water_leakage",
    "garbage": "garbage_overflow",
    "streetlight": "broken_streetlight",
    "fallen_tree": "fallen_tree",
}


def _scene_image(category: str, seed: int) -> Any:
    """Synthetic category scene; colour-only fallback without civitas-vision."""
    try:
        from civitas_vision.benchmark import (
            make_image,  # type: ignore[import-not-found]
        )

        return make_image(_VISION_CATEGORY[category], seed=seed)
    except ImportError:
        from PIL import Image  # type: ignore[import-not-found]

        colors = {
            "pothole": (70, 70, 74),
            "water_leak": (30, 80, 140),
            "garbage": (110, 95, 45),
            "streetlight": (245, 220, 80),
            "fallen_tree": (45, 130, 70),
        }
        return Image.new("RGB", (64, 64), colors[category])


class ReportScenario:
    """Deterministic report factories for synthetic pairs."""

    def __init__(self, seed: int = 7) -> None:
        self.rng = random.Random(seed)

    def duplicate_second_report(
        self,
        report_id: str,
        category: str,
        first: ReportEmbeddings,
        text_embedder: HashNgramEmbedder,
        image_embedder: ClassicalImageEmbedder,
        variant_index: int,
    ) -> ReportEmbeddings:
        """Second witness of the SAME incident: jittered GPS, same window,
        same landmark anchors, different description and photo variant."""
        assert first.gps is not None
        jitter = 0.00015  # ~15 m of consumer-GPS noise
        lat = first.gps[0] + self.rng.uniform(-jitter, jitter)
        lon = first.gps[1] + self.rng.uniform(-jitter, jitter)
        delta = self.rng.uniform(0.5, 2.0)
        submitted = NOW + timedelta(hours=delta)
        return build_report_embeddings(
            report_id=report_id,
            description=self.rng.choice(SYNTHETIC_DESCRIPTIONS[category]),
            text_embedder=text_embedder,
            image=_scene_image(category, 7000 + variant_index),
            image_embedder=image_embedder,
            gps=(lat, lon),
            submitted_at=submitted.isoformat(),
            category=category,
            landmark_ids=_LANDMARK_DUP,
        )

    def first_report(
        self,
        report_id: str,
        category: str,
        text_embedder: HashNgramEmbedder,
        image_embedder: ClassicalImageEmbedder,
        variant_index: int,
    ) -> ReportEmbeddings:
        time_offset_h = self.rng.uniform(-72, 0)
        submitted = NOW + timedelta(hours=time_offset_h)
        return build_report_embeddings(
            report_id=report_id,
            description=self.rng.choice(SYNTHETIC_DESCRIPTIONS[category]),
            text_embedder=text_embedder,
            image=_scene_image(category, 1000 + variant_index),
            image_embedder=image_embedder,
            gps=CENTER,
            submitted_at=submitted.isoformat(),
            category=category,
            landmark_ids=_LANDMARK_DUP,
        )

    def distinct_report(
        self,
        report_id: str,
        category: str,
        text_embedder: HashNgramEmbedder,
        image_embedder: ClassicalImageEmbedder,
        variant_index: int,
        far: bool,
    ) -> ReportEmbeddings:
        """A genuinely different incident (different place & usually time)."""
        if far:
            # ~6 km southeast
            lat, lon = CENTER[0] - 0.055, CENTER[1] + 0.045
            submitted = NOW - timedelta(days=self.rng.uniform(10, 40))
        else:
            lat, lon = CENTER[0] + self.rng.uniform(-0.003, 0.003), CENTER[1] + self.rng.uniform(-0.003, 0.003)
            submitted = NOW + timedelta(hours=self.rng.uniform(3, 24))
        return build_report_embeddings(
            report_id=report_id,
            description=self.rng.choice(SYNTHETIC_DESCRIPTIONS[category]),
            text_embedder=text_embedder,
            image=_scene_image(category, 5000 + variant_index),
            image_embedder=image_embedder,
            gps=(lat, lon),
            submitted_at=submitted.isoformat(),
            category=category,
            landmark_ids=_LANDMARK_OTHER,
        )


def make_synthetic_pairs(
    seed: int = 7,
    n_duplicates: int = 25,
    n_distinct: int = 25,
) -> list[tuple[ReportEmbeddings, ReportEmbeddings, int]]:
    """(report_a, report_b, label) where label = 1 for same incident."""
    text_embedder = HashNgramEmbedder()
    image_embedder = ClassicalImageEmbedder()
    scenario = ReportScenario(seed)
    pairs: list[tuple[ReportEmbeddings, ReportEmbeddings, int]] = []
    for i in range(n_duplicates):
        category = CATEGORIES[i % len(CATEGORIES)]
        first = scenario.first_report(
            f"dup-a-{i}", category, text_embedder, image_embedder, variant_index=i
        )
        second = scenario.duplicate_second_report(
            f"dup-b-{i}", category, first, text_embedder, image_embedder, variant_index=i + 100
        )
        pairs.append((first, second, 1))
    for i in range(n_distinct):
        category = CATEGORIES[i % len(CATEGORIES)]
        a = scenario.distinct_report(
            f"dist-a-{i}", category, text_embedder, image_embedder, variant_index=i,
            far=(i % 3 == 0),
        )
        b_cat = CATEGORIES[(i + 1) % len(CATEGORIES)]
        b = scenario.distinct_report(
            f"dist-b-{i}", b_cat, text_embedder, image_embedder, variant_index=i + 200,
            far=(i % 3 == 1),
        )
        pairs.append((a, b, 0))
    return pairs


@dataclass
class PairEvaluation:
    """Measurable performance of the incident-anchored duplicate answer."""

    n_duplicates: int
    n_distinct: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    threshold: float
    weights_name: str
    review_flag_count: int
    notes: list[str] = field(default_factory=list)

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def accuracy(self) -> float:
        total = self.n_duplicates + self.n_distinct
        correct = self.true_positives + self.true_negatives
        return correct / total if total else 0.0

    def summary(self) -> str:
        return (
            f"pair evaluation: accuracy {self.accuracy:.3f} | precision "
            f"{self.precision:.3f} | recall {self.recall:.3f} | F1 {self.f1:.3f} "
            f"on {self.n_duplicates} duplicate + {self.n_distinct} distinct pairs "
            f"(threshold {self.threshold:.2f}, {self.weights_name})"
        )


def run_pair_evaluation(
    seed: int = 7,
    n_duplicates: int = 25,
    n_distinct: int = 25,
    weights_name: str = "incident_anchored",
    threshold: float = 0.70,
) -> PairEvaluation:
    """Full evaluation of the Phase 4 same-incident answer on synthetic pairs."""
    pairs = make_synthetic_pairs(seed, n_duplicates, n_distinct)
    weights = dict(INCIDENT_ANCHORED_WEIGHTS)
    cfg = ScoringConfig(
        weights=weights,
        duplicate_threshold=threshold,
        max_reasonable_distance_m=2_000.0,
        max_reasonable_delta_h=72.0,
    )
    tp = fp = tn = fn = reviews = 0
    for a, b, label in pairs:
        result = incident_similarity(a, b, cfg=cfg)
        if result.requires_review:
            reviews += 1
        predicted = int(result.is_duplicate)
        if label == 1:
            if predicted:
                tp += 1
            else:
                fn += 1
        else:
            if predicted:
                fp += 1
            else:
                tn += 1
    return PairEvaluation(
        n_duplicates=n_duplicates,
        n_distinct=n_distinct,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        threshold=threshold,
        weights_name=weights_name,
        review_flag_count=reviews,
    )


__all__ = [
    "CATEGORIES",
    "SYNTHETIC_DESCRIPTIONS",
    "PairEvaluation",
    "ReportScenario",
    "make_synthetic_pairs",
    "run_pair_evaluation",
]