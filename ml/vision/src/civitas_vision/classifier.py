"""Deterministic k-NN classifier over the classical feature vector (Phase 3).

A real, trainable ML component: k-nearest-neighbour over z-scored features
with a softmax (temperature-scaled) confidence. It is trained on the synthetic
benchmark set (`civitas_vision.benchmark`) and evaluated on a held-out split —
the evaluation report is measurable (accuracy, macro-F1, confusion matrix).
The classifier makes no claims about real photos: that corpus does not exist
yet (recorded limitation).

Confidence is calibrated relative to the training distance distribution
(median distance), temperature T; both are documented constants.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from civitas_vision.contracts import ClassificationProbs, CIVITAS_CATEGORIES
from civitas_vision.features import FEATURE_NAMES, extract_features

TRAIN_SEED = 11
K_NEIGHBOURS = 3
SOFTMAX_TEMPERATURE = 2.0
_MIN_CONFIDENCE_FLOOR = 0.01
_CONFIDENCE_EPS = 1e-9


class KNNClassifier:
    """k-NN over standardized features with explainable outputs."""

    def __init__(
        self,
        k: int = K_NEIGHBOURS,
        temperature: float = SOFTMAX_TEMPERATURE,
        seed: int = TRAIN_SEED,
    ) -> None:
        self.k = k
        self.temperature = temperature
        self.seed = seed
        self._train_x: np.ndarray | None = None
        self._train_y: list[str] = []
        self._classes: list[str] = []
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._median_distance: float = 1.0

    def fit(self, feature_vectors: list[dict[str, float]], labels: list[str]) -> None:
        """Store standardized training prototypes (deterministic)."""
        rows = np.array([[f.get(n, 0.0) for n in FEATURE_NAMES] for f in feature_vectors])
        self._mean = rows.mean(axis=0)
        self._std = rows.std(axis=0)
        self._std = np.where(self._std < 1e-6, 1.0, self._std)
        self._train_x = (rows - self._mean) / self._std
        self._train_y = list(labels)
        self._classes = list(dict.fromkeys(labels))
        ordered = list(CIVITAS_CATEGORIES)
        self._classes = [c for c in ordered if c in self._classes]
        if self._train_x.size:
            pair_dists = np.linalg.norm(self._train_x[:, None, :] - self._train_x[None, :, :], axis=2)
            n = pair_dists.shape[0]
            off_diag = pair_dists[np.triu_indices(n, k=1)]
            self._median_distance = float(np.median(off_diag)) if off_diag.size else 1.0

    def predict_proba(self, features: dict[str, float]) -> ClassificationProbs:
        """Distance-weighted vote with softmax confidence."""
        if self._train_x is None or self._mean is None or self._std is None:
            raise RuntimeError("KNNClassifier.fit() must run before predict_proba()")
        x = np.array([features.get(n, 0.0) for n in FEATURE_NAMES])
        x = (x - self._mean) / self._std
        dists = np.linalg.norm(self._train_x - x, axis=1)
        order = np.argsort(dists)
        neighbour_dists = dists[order[: self.k]]
        neighbour_labels = [self._train_y[i] for i in order[: self.k]]

        votes = {c: 0.0 for c in self._classes}
        for label, d in zip(neighbour_labels, neighbour_dists):
            weight = 1.0 / max(d, _CONFIDENCE_EPS)
            votes[label] += weight
        total = sum(votes.values())
        probs = {c: (v / total if total > 0 else 0.0) for c, v in votes.items()}

        mean_neighbour_distance = float(neighbour_dists.mean())
        ood_ratio = mean_neighbour_distance / self._median_distance

        scaled = np.array([-d / (self._median_distance * self.temperature) for d in neighbour_dists])
        scaled = scaled - scaled.max()
        exp_s = np.exp(scaled)
        softmax = exp_s / exp_s.sum()
        confidence = float(softmax.max())
        confidence = max(confidence, _MIN_CONFIDENCE_FLOOR)
        confidence = min(confidence, 1.0)

        primary = max(probs, key=lambda c: probs[c]) if probs else None
        basis = [
            f"k-NN(k={self.k}) over {len(self._train_x)} z-scored prototypes; "
            f"nearest distances {neighbour_dists.round(2)}",
            f"softmax confidence {confidence:.3f} (T={self.temperature}, "
            f"median-distance scale {self._median_distance:.2f})",
            f"out-of-distribution ratio {ood_ratio:.2f} (mean neighbour distance / corpus median)",
        ]
        return ClassificationProbs(
            probabilities=probs,
            primary_category=primary,
            confidence=confidence,
            ood_ratio=round(ood_ratio, 3),
            basis=basis,
        )

    def predict(self, image: Image.Image) -> ClassificationProbs:
        """Compat entry point shared with the neural classifier."""
        return self.predict_proba(extract_features(image))

    @property
    def classes(self) -> list[str]:
        return list(self._classes)

    @property
    def fitted(self) -> bool:
        return self._train_x is not None


def merge_media_probs(per_frame: list[ClassificationProbs]) -> ClassificationProbs:
    """Average frame probabilities into one media-level classification.

    `confidence` is the *margin* between the top-1 and top-2 averaged vote
    shares (0..1). A unanimous frame gets ~1.0; a scene that genuinely
    straddles categories collapses toward 0.0, so low confidence is an
    honest signal of ambiguity instead of a saturated softmax.
    """
    if not per_frame:
        return ClassificationProbs(probabilities={}, basis=["no usable frames"])
    probs: dict[str, float] = {c: 0.0 for c in CIVITAS_CATEGORIES}
    ratios = [p.ood_ratio for p in per_frame if p.ood_ratio is not None]
    for frame in per_frame:
        for c in CIVITAS_CATEGORIES:
            probs[c] += frame.probabilities.get(c, 0.0)
    probs = {c: v / len(per_frame) for c, v in probs.items()}
    primary = max(probs, key=lambda c: probs[c]) if probs else None
    ordered = sorted(probs.values(), reverse=True) if probs else [0.0]
    margin = max(0.0, (ordered[0] - ordered[1]) if len(ordered) > 1 else ordered[0])
    return ClassificationProbs(
        probabilities=probs,
        primary_category=primary,
        confidence=round(margin, 4),
        ood_ratio=round(sum(ratios) / len(ratios), 3) if ratios else None,
        basis=[
            f"mean of {len(per_frame)} usable frame probability vectors; "
            f"confidence = top-1/top-2 vote-share margin {margin:.3f}",
        ],
    )


def secondary_categories(
    probs: dict[str, float], primary: str | None, threshold: float = 0.25, max_items: int = 2
) -> list[str]:
    """Categories with meaningful probability besides the primary."""
    ranked = sorted(
        ((c, p) for c, p in probs.items() if c != primary and p >= threshold),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [c for c, _ in ranked[:max_items]]


__all__ = ["KNNClassifier", "merge_media_probs", "secondary_categories"]