"""Phase 5: labelled evaluation of the duplicate detection engine.

The engine is measured on three labelled pair classes, mirroring how a real
operation would audit it:

  - positive  : two reports of the SAME real-world incident -> must merge
  - negative  : two genuinely DISTINCT incidents                -> must not merge
  - ambiguous : co-located and co-temporal reports that are nonetheless
                distinct incidents (e.g. different, unrelated categories) ->
                the correct behaviour is to ESCALATE to human review, never
                to auto-merge silently

The report covers precision / recall / F1 on positive vs negative pairs plus
the operational failure modes the user asked for:

  - false merges (negatives and ambiguous pairs that the engine auto-merged)
  - false splits (positives the engine refused to merge)

All pairs are synthetic and deterministic (seeded), with real embeddings:
HashNgram text embeddings and ClassicalImageEmbedder image embeddings when
`with_images=True`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from civitas_duplicates.benchmark import SYNTHETIC_DESCRIPTIONS, _scene_image
from civitas_duplicates.contracts import ReportLike
from civitas_duplicates.detector import DuplicateDetector
from civitas_duplicates.embeddings import ClassicalImageEmbedder
from civitas_duplicates.geo_features import gps_distance_m

Label = Literal["positive", "negative", "ambiguous"]

NOW = datetime(2026, 3, 5, 9, 0, tzinfo=timezone.utc)
CENTER = (28.6139, 77.2090)

CATEGORIES = ("pothole", "water_leak", "garbage", "streetlight", "fallen_tree")

# ground truth: ambiguous pairs must never be auto-merged
TRUTH: dict[Label, int] = {"positive": 1, "negative": 0, "ambiguous": 0}

_LANDMARK_DUP = ["lm-school-01", "lm-junction-01"]
_LANDMARK_OTHER = ["lm-market-01", "lm-park-01"]


@dataclass(frozen=True)
class LabelledPair:
    """One engine input with the ground-truth label and audit note."""

    a: ReportLike
    b: ReportLike
    label: Label
    note: str


class LabelledScenario:
    """Deterministic factory for the three labelled pair classes."""

    def __init__(self, seed: int = 11) -> None:
        self.rng = random.Random(seed)

    def _report(
        self,
        report_id: str,
        description: str,
        category: str,
        lat: float,
        lon: float,
        submitted_at: datetime,
        landmark_ids: list[str],
        image: Any | None,
        image_embedder: ClassicalImageEmbedder | None,
    ) -> ReportLike:
        return ReportLike(
            report_id=report_id,
            description=description,
            latitude=lat,
            longitude=lon,
            submitted_at=submitted_at,
            category=category,
            landmark_ids=landmark_ids,
            image_embedding=(
                image_embedder.embed_image(image).vector
                if image is not None and image_embedder is not None
                else None
            ),
            media_count=1 if image else 0,
        )

    def positive_pair(
        self,
        index: int,
        image_embedder: ClassicalImageEmbedder | None,
    ) -> LabelledPair:
        """Two witnesses of one real incident: sniffing-close GPS, same
        incident window, same category and landmarks; different wording and
        photo variant."""
        category = CATEGORIES[index % len(CATEGORIES)]
        jitter = 0.0001  # ~11 m
        a = self._report(
            f"pos-a-{index}",
            SYNTHETIC_DESCRIPTIONS[category][index % 3],
            category,
            CENTER[0] + self.rng.uniform(-jitter, jitter),
            CENTER[1] + self.rng.uniform(-jitter, jitter),
            NOW + timedelta(minutes=self.rng.uniform(10, 50)),
            list(_LANDMARK_DUP),
            _scene_image(category, 3000 + index) if image_embedder else None,
            image_embedder,
        )
        b = self._report(
            f"pos-b-{index}",
            SYNTHETIC_DESCRIPTIONS[category][(index + 1) % 3],
            category,
            CENTER[0] + self.rng.uniform(-jitter, jitter),
            CENTER[1] + self.rng.uniform(-jitter, jitter),
            NOW + timedelta(minutes=self.rng.uniform(60, 120)),
            list(_LANDMARK_DUP),
            _scene_image(category, 3100 + index) if image_embedder else None,
            image_embedder,
        )
        return LabelledPair(a, b, "positive",
                            "same incident, two witnesses (similar GPS/time/category/landmark)")

    def negative_pair(
        self,
        index: int,
        image_embedder: ClassicalImageEmbedder | None,
    ) -> LabelledPair:
        """Two genuinely distinct incidents: far apart in space (~6 km) and
        time (10-40 days), different categories and landmarks."""
        cat_a = CATEGORIES[index % len(CATEGORIES)]
        cat_b = CATEGORIES[(index + 2) % len(CATEGORIES)]
        a = self._report(
            f"neg-a-{index}",
            SYNTHETIC_DESCRIPTIONS[cat_a][index % 3],
            cat_a,
            CENTER[0] + self.rng.uniform(-0.001, 0.001),
            CENTER[1] + self.rng.uniform(-0.001, 0.001),
            NOW - timedelta(days=self.rng.uniform(10, 40)),
            list(_LANDMARK_OTHER),
            _scene_image(cat_a, 4000 + index) if image_embedder else None,
            image_embedder,
        )
        b = self._report(
            f"neg-b-{index}",
            SYNTHETIC_DESCRIPTIONS[cat_b][(index + 1) % 3],
            cat_b,
            CENTER[0] - 0.055 + self.rng.uniform(-0.001, 0.001),
            CENTER[1] + 0.045 + self.rng.uniform(-0.001, 0.001),
            NOW - timedelta(days=self.rng.uniform(10, 40)),
            list(_LANDMARK_OTHER),
            _scene_image(cat_b, 4100 + index) if image_embedder else None,
            image_embedder,
        )
        return LabelledPair(a, b, "negative",
                            "distinct incidents (different place, time, category, landmark)")

    def ambiguous_pair(
        self,
        index: int,
        image_embedder: ClassicalImageEmbedder | None,
    ) -> LabelledPair:
        """Co-located, co-temporal reports that ARE distinct incidents:
        same cell and window, shared landmark, but unrelated categories
        (no causal link) and clearly different evidence. The correct engine
        behaviour is escalation to review, not an auto-merge."""
        cat_a = CATEGORIES[index % len(CATEGORIES)]
        cat_b = CATEGORIES[(index + 3) % len(CATEGORIES)]
        jitter = 0.0001
        a = self._report(
            f"amb-a-{index}",
            SYNTHETIC_DESCRIPTIONS[cat_a][index % 3],
            cat_a,
            CENTER[0] + self.rng.uniform(-jitter, jitter),
            CENTER[1] + self.rng.uniform(-jitter, jitter),
            NOW + timedelta(minutes=self.rng.uniform(10, 50)),
            list(_LANDMARK_DUP),
            _scene_image(cat_a, 5000 + index) if image_embedder else None,
            image_embedder,
        )
        b = self._report(
            f"amb-b-{index}",
            SYNTHETIC_DESCRIPTIONS[cat_b][(index + 2) % 3],
            cat_b,
            CENTER[0] + self.rng.uniform(-jitter, jitter),
            CENTER[1] + self.rng.uniform(-jitter, jitter),
            NOW + timedelta(minutes=self.rng.uniform(60, 150)),
            list(_LANDMARK_DUP),
            _scene_image(cat_b, 5100 + index) if image_embedder else None,
            image_embedder,
        )
        return LabelledPair(a, b, "ambiguous",
                            "co-located but distinct (unrelated categories; escalate, do not merge)")


def build_labelled_pairs(
    seed: int = 11,
    n_per_label: int = 6,
    with_images: bool = True,
) -> list[LabelledPair]:
    """Deterministic labelled pair set for engine evaluation."""
    image_embedder = ClassicalImageEmbedder() if with_images else None
    scenario = LabelledScenario(seed)
    pairs: list[LabelledPair] = []
    for i in range(n_per_label):
        pairs.append(scenario.positive_pair(i, image_embedder))
        pairs.append(scenario.negative_pair(i, image_embedder))
        pairs.append(scenario.ambiguous_pair(i, image_embedder))
    return pairs


@dataclass
class PairRow:
    """One labelled pair and how the engine answered it."""

    note: str
    label: Label
    score: float
    is_duplicate: bool
    requires_review: bool


@dataclass
class EngineEvaluation:
    """Measurable quality of the duplicate engine on the labelled set."""

    n_positive: int
    n_negative: int
    n_ambiguous: int
    true_positives: int
    false_negatives: int  # false splits: positives not merged
    false_positives: int  # false merges: negatives auto-merged
    true_negatives: int
    ambiguous_merged: int
    ambiguous_reviewed: int
    ambiguous_rejected: int
    rows: list[PairRow] = field(default_factory=list)

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
        decided = self.n_positive + self.n_negative
        correct = self.true_positives + self.true_negatives
        return correct / decided if decided else 0.0

    @property
    def false_merges_total(self) -> int:
        return self.false_positives + self.ambiguous_merged

    @property
    def false_splits_total(self) -> int:
        return self.false_negatives

    def summary(self) -> str:
        return (
            f"engine evaluation: precision {self.precision:.3f} | recall {self.recall:.3f} "
            f"| F1 {self.f1:.3f} | accuracy {self.accuracy:.3f} | "
            f"false merges {self.false_merges_total} (negatives {self.false_positives}, "
            f"ambiguous {self.ambiguous_merged}) | false splits {self.false_splits_total} "
            f"| ambiguous escalated to review {self.ambiguous_reviewed}/{self.n_ambiguous}"
        )


def evaluate_engine(
    pairs: list[LabelledPair],
    engine: DuplicateDetector | None = None,
) -> EngineEvaluation:
    """Run every labelled pair through the engine and aggregate metrics."""
    engine = engine or DuplicateDetector()
    tp = fp = tn = fn = 0
    amb_merged = amb_reviewed = amb_rejected = 0
    rows: list[PairRow] = []
    for labelled in pairs:
        result = engine.evaluate_pair(labelled.a, labelled.b)
        rows.append(
            PairRow(
                note=labelled.note,
                label=labelled.label,
                score=round(result.score, 4),
                is_duplicate=result.is_duplicate,
                requires_review=result.requires_review,
            )
        )
        if labelled.label == "positive":
            if result.is_duplicate:
                tp += 1
            else:
                fn += 1
        elif labelled.label == "negative":
            if result.is_duplicate:
                fp += 1
            else:
                tn += 1
        else:  # ambiguous
            if result.is_duplicate:
                amb_merged += 1
            elif result.requires_review:
                amb_reviewed += 1
            else:
                amb_rejected += 1
    counts = {
        "n_positive": len([p for p in pairs if p.label == "positive"]),
        "n_negative": len([p for p in pairs if p.label == "negative"]),
        "n_ambiguous": len([p for p in pairs if p.label == "ambiguous"]),
    }
    return EngineEvaluation(
        n_positive=counts["n_positive"],
        n_negative=counts["n_negative"],
        n_ambiguous=counts["n_ambiguous"],
        true_positives=tp,
        false_negatives=fn,
        false_positives=fp,
        true_negatives=tn,
        ambiguous_merged=amb_merged,
        ambiguous_reviewed=amb_reviewed,
        ambiguous_rejected=amb_rejected,
        rows=rows,
    )


def gps_margin_check(pairs: list[LabelledPair]) -> None:
    """Sanity guard: positive pairs close, negative pairs far (test aid)."""
    for labelled in pairs:
        d = gps_distance_m(
            labelled.a.latitude, labelled.a.longitude,
            labelled.b.latitude, labelled.b.longitude,
        )
        if labelled.label == "positive":
            assert d < 2_000.0, f"positive pair {labelled.a.report_id} too far: {d:.0f} m"
        elif labelled.label == "negative":
            assert d > 2_000.0, f"negative pair {labelled.a.report_id} too close: {d:.0f} m"


__all__ = [
    "CATEGORIES",
    "EngineEvaluation",
    "LabelledPair",
    "LabelledScenario",
    "PairRow",
    "TRUTH",
    "build_labelled_pairs",
    "evaluate_engine",
]