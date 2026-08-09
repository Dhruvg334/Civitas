"""Synthetic benchmark for the visual pipeline (Phase 3).

Procedurally composed scenes (deterministic per seed) covering the five
Civitas categories plus blur/quality variants. This is an explicit, recorded
limitation: the corpus is synthetic, not real citizen photos — but it makes
evaluation measurable and reproducible today (accuracy, macro-F1, confusion
matrix), and the same harness will consume a real photo corpus when the
ingestion pipeline lands.

Scene grammar per category:
  pothole_road_damage     asphalt noise + dark elliptical cavities + cracks
  water_leakage           blue overlay region + horizontal ripple lines
                          (flow) or still pooled water (standing)
  garbage_overflow        clustered high-saturation multi-hue blobs + bin
  broken_streetlight      dark scene + bright bulb blob in upper half + pole
  fallen_tree             diagonal dark trunk + canopy cluster + blocked road
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from PIL import Image

from civitas_vision.classifier import KNNClassifier, TRAIN_SEED
from civitas_vision.contracts import CIVITAS_CATEGORIES
from civitas_vision.features import extract_features

DEFAULT_N_TRAIN_PER_CLASS = 16
DEFAULT_N_TEST_PER_CLASS = 8

SIZE = 224


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _asphalt(rng: np.random.Generator) -> np.ndarray:
    base = np.clip(rng.normal(0.32, 0.09, (SIZE, SIZE, 3)), 0.0, 1.0)
    grain = np.clip(rng.normal(0.0, 0.03, (SIZE, SIZE, 1)), -0.4, 0.4)
    lane = np.zeros((SIZE, SIZE, 1))
    lane[:, SIZE // 2 : SIZE // 2 + 8] = 0.55
    return np.clip(base + grain + lane, 0.0, 1.0)


def _poly(center: tuple[float, float], rx: float, ry: float, angle_deg: float) -> np.ndarray:
    """Binary mask of an ellipse (rotated) centered at (cx, cy) in pixels."""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float64)
    theta = np.deg2rad(angle_deg)
    cos, sin = np.cos(theta), np.sin(theta)
    dx, dy = xx - center[0], yy - center[1]
    u = cos * dx + sin * dy
    v = -sin * dx + cos * dy
    return ((u / rx) ** 2 + (v / ry) ** 2) <= 1.0


def make_scene(category: str, seed: int, variant: str = "default") -> np.ndarray:
    """Generate one deterministic scene. Variants add realism/noise."""
    rng = _rng(seed)
    img = _asphalt(rng)

    if category == "pothole_road_damage":
        for _ in range(2 if variant != "default" else 1):
            cx, cy = rng.uniform(60, 164), rng.uniform(60, 164)
            rx, ry = rng.uniform(24, 46), rng.uniform(18, 34)
            mask = _poly((cx, cy), rx, ry, rng.uniform(-20, 20))
            img[mask] = np.clip(
                img[mask] * rng.uniform(0.25, 0.45) + rng.normal(0.0, 0.03, img[mask].shape),
                0.0, 1.0,
            )
            img = img.astype(np.float64)
            edge = np.roll(mask, 1, axis=0) & ~mask
            img[edge] = np.clip(img[edge] + 0.25, 0.0, 1.0)
        for _ in range(4):
            x0, y0 = int(rng.uniform(20, 200)), int(rng.uniform(20, 200))
            img[y0 : y0 + 3, x0 : x0 + 40] *= rng.uniform(0.5, 0.7)
        return np.clip(img, 0.0, 1.0)

    if category == "water_leakage":
        flow = variant == "flow"
        y_start = int(rng.uniform(70, 130))
        water = np.zeros_like(img)
        water[y_start:, :, 0] = rng.uniform(0.30, 0.45)
        water[y_start:, :, 1] = rng.uniform(0.42, 0.52)
        water[y_start:, :, 2] = rng.uniform(0.62, 0.72)
        water[y_start:, :] += rng.normal(0.0, 0.02, water[y_start:, :].shape)
        img[y_start:] = water[y_start:]
        if flow:
            for row in range(y_start + 8, SIZE, 8):
                sigma = 4
                ys = np.arange(SIZE, dtype=np.float64)
                waves = np.exp(-((ys - row) ** 2) / (2 * sigma**2)) * 0.32
                img += waves[:, None, None]
        else:
            spark = _poly((SIZE * rng.uniform(0.4, 0.6), SIZE * rng.uniform(0.65, 0.8)),
                          rng.uniform(30, 55), rng.uniform(14, 30), 0)
            img[spark] = np.clip(img[spark] + 0.35, 0.0, 1.0)
        return np.clip(img, 0.0, 1.0)

    if category == "garbage_overflow":
        hues = rng.uniform(0.0, 0.9, 6)
        for h in hues:
            cx, cy = rng.uniform(40, 190), rng.uniform(50, 190)
            r = rng.uniform(10, 22)
            yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float64)
            blob = ((xx - cx) ** 2 + (yy - cy) ** 2) <= r**2
            base = np.array(
                [np.clip(1.0 - abs(h - x), 0.0, 1.0) for x in (0.0, 0.33, 0.66)]
            )
            img[blob] = np.clip(0.55 * base[None, None, :] + rng.normal(0.0, 0.08, 3), 0.0, 1.0)
        bin_mask = _poly((int(rng.uniform(45, 90)), int(rng.uniform(45, 90))), 26, 34, 0)
        img[bin_mask] = np.array([0.25, 0.22, 0.20])
        return np.clip(img, 0.0, 1.0)

    if category == "broken_streetlight":
        img = np.clip(img * rng.uniform(0.45, 0.6), 0.0, 1.0)
        pole_cx = SIZE * rng.uniform(0.5, 0.6)
        pole = _poly((pole_cx, SIZE * rng.uniform(0.45, 0.55)), 4.5, 70, 0)
        img[pole] = 0.12
        bulb_cy = SIZE * rng.uniform(0.22, 0.3)
        bulb = _poly((pole_cx, bulb_cy), rng.uniform(8, 14), rng.uniform(6, 11), 0)
        img[bulb] = np.clip(
            np.array([1.0, 0.95, 0.75]) * rng.uniform(0.8, 1.0), 0.0, 1.0
        )
        glow = _poly((pole_cx, bulb_cy), 30, 24, 0) & ~bulb
        img[glow] = np.clip(img[glow] + 0.12, 0.0, 1.0)
        return np.clip(img, 0.0, 1.0)

    if category == "fallen_tree":
        trunk = _poly((SIZE * rng.uniform(0.42, 0.58), SIZE * rng.uniform(0.55, 0.65)),
                      rng.uniform(10, 15), rng.uniform(72, 90), rng.uniform(-25, 5))
        img[trunk] = np.array([0.18, 0.12, 0.08])
        for _ in range(3):
            cx, cy = rng.uniform(60, 170), rng.uniform(40, 180)
            canopy = _poly((cx, cy), rng.uniform(18, 34), rng.uniform(14, 26), 0)
            greens = np.array([0.14, 0.34, 0.10])
            img[canopy] = np.clip(greens[None, None, :] * rng.uniform(0.8, 1.3), 0.0, 1.0)
        return np.clip(img, 0.0, 1.0)

    raise ValueError(f"unknown category: {category}")


def make_image(category: str, seed: int, variant: str = "default") -> Image.Image:
    arr = make_scene(category, seed, variant)
    return Image.fromarray((arr * 255).astype(np.uint8), mode="RGB")


def gaussian_blur(image: Image.Image, radius: float = 4.0) -> Image.Image:
    """Deterministic blur (quality-evaluation negative variant)."""
    from PIL import ImageFilter

    return image.filter(ImageFilter.GaussianBlur(radius=radius))


@dataclass
class EvaluationReport:
    accuracy: float
    macro_f1: float
    per_class: dict[str, dict[str, float]]
    confusion_matrix: list[list[int]]
    n_samples: int
    basis: list[str]


def _build_split(
    seed_floor: int,
    n_per_class: int,
    rng: np.random.Generator,
    variant_pool: list[str],
    weights: list[int],
) -> tuple[list[dict[str, float]], list[str]]:
    feats: list[dict[str, float]] = []
    labels: list[str] = []
    for cat in CIVITAS_CATEGORIES:
        for _ in range(n_per_class):
            variant = rng.choice(variant_pool, p=np.asarray(weights) / sum(weights))
            img = make_image(cat, seed_floor + len(feats), variant)
            feats.append(extract_features(img))
            labels.append(cat)
    return feats, labels


@lru_cache(maxsize=1)
def train_default_model(n_train_per_class: int = DEFAULT_N_TRAIN_PER_CLASS) -> KNNClassifier:
    """Train (and cache) the deterministic baseline classifier.

    Uses the default train split; callers get a fitted model without
    re-running the full evaluation. Deterministic per seed.
    """
    variant_pool = ["default", "flow"]
    weights = [3, 1]
    rng = np.random.default_rng(TRAIN_SEED)
    feats, labels = _build_split(100, n_train_per_class, rng, variant_pool, weights)
    model = KNNClassifier()
    model.fit(feats, labels)
    return model


def run_evaluation(
    variants: dict[str, int] | None = None,
    train_seed_floor: int = 100,
    test_seed_floor: int = 1000,
    n_train_per_class: int = DEFAULT_N_TRAIN_PER_CLASS,
    n_test_per_class: int = DEFAULT_N_TEST_PER_CLASS,
) -> EvaluationReport:
    """Train on one deterministic split, evaluate on a held-out split."""
    variant_pool = list((variants or {}).keys()) or ["default"]
    weights = [variants[v] if variants else 1 for v in variant_pool]

    train_rng = np.random.default_rng(TRAIN_SEED)
    train_feats, train_labels = _build_split(
        train_seed_floor, n_train_per_class, train_rng, variant_pool, weights
    )
    test_rng = np.random.default_rng(TRAIN_SEED + 1)
    test_feats, test_labels = _build_split(
        test_seed_floor, n_test_per_class, test_rng, variant_pool, weights
    )

    model = KNNClassifier()
    model.fit(train_feats, train_labels)

    predicted: list[str] = []
    for feats in test_feats:
        probs = model.predict_proba(feats)
        assert probs.primary_category is not None
        predicted.append(probs.primary_category)

    classes = list(CIVITAS_CATEGORIES)
    n = len(classes)
    matrix = np.zeros((n, n), dtype=int)
    for true, pred in zip(test_labels, predicted):
        matrix[classes.index(true), classes.index(pred)] += 1

    per_class: dict[str, dict[str, float]] = {}
    for i, cat in enumerate(classes):
        tp = float(matrix[i, i])
        fp = float(matrix[:, i].sum() - tp)
        fn = float(matrix[i, :].sum() - tp)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[cat] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    accuracy = float(np.trace(matrix) / max(matrix.sum(), 1))
    macro_f1 = float(np.mean([per_class[c]["f1"] for c in classes]))
    return EvaluationReport(
        accuracy=round(accuracy, 4),
        macro_f1=round(macro_f1, 4),
        per_class=per_class,
        confusion_matrix=matrix.tolist(),
        n_samples=int(matrix.sum()),
        basis=[
            f"synthetic benchmark: {n_train_per_class} train + {n_test_per_class} test "
            f"per class, variants={variant_pool}",
            "k-NN(k=3) over 16 z-scored classical features; held-out split by seed floor",
        ],
    )