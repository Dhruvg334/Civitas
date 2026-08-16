"""Provider-agnostic embedding layer with a deterministic offline fallback.

Civitas never hard-codes a model provider. `TextEmbedder` / `ImageEmbedder`
are protocols; the shipped fallback (`HashNgramEmbedder`) is deterministic,
dependency-free and works offline so the engine is fully testable. Production
deployments plug in their own embedding service (e.g. sentence-transformers
or CLIP) via `ProviderEmbedder`.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable
from typing import Any, Protocol

from pydantic import BaseModel, Field

_TEXT_DIM = 512
_NGRAM_MIN = 2
_NGRAM_MAX = 3


class TextEmbedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class ImageEmbedder(Protocol):
    def embed(self, image_bytes: bytes) -> list[float]: ...


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]: ...
    def embed_image(self, image_bytes: bytes) -> list[float]: ...


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity in [0, 1] with engine-safe handling of empty vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    num = sum(x * y for x, y in zip(a, b))
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if denom == 0.0:
        return 0.0
    return max(0.0, min(1.0, num / denom))


def _stable_hash(term: str) -> int:
    """Deterministic 64-bit FNV-1a variant stable across runs."""
    h = 14695981039346656037
    for byte in term.encode("utf-8"):
        h ^= byte
        h = (h * 1099511628211) & ((1 << 64) - 1)
    return h


def _terms(text: str) -> list[str]:
    text = text.lower()
    words = [w for w in re.split(r"[^a-z0-9]+", text) if w]
    out: list[str] = []
    for word in words:
        if len(word) >= 2:
            out.append(word)
    if not out:
        return out
    joined = "".join(words)
    for n in range(_NGRAM_MIN, _NGRAM_MAX + 1):
        out.extend(joined[i : i + n] for i in range(len(joined) - n + 1))
    return out


class HashNgramEmbedder:
    """Deterministic hashing TF embedding; no external dependencies."""

    def __init__(self, dimension: int = _TEXT_DIM) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        counts = Counter(_terms(text))
        if not counts:
            return [0.0] * self.dimension
        vec = [0.0] * self.dimension
        for term, count in counts.items():
            vec[_stable_hash(term) % self.dimension] += 1.0 + math.log(count)
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]

    def embed_terms(self, terms: list[str]) -> list[float]:
        return self.embed(" ".join(terms))


class ProviderEmbedder:
    """Wraps an externally supplied embedding callable."""

    def __init__(self, embed_text: Callable[[str], list[float]], embed_image: Callable[[bytes], list[float]] | None = None) -> None:
        self._embed_text = embed_text
        self._embed_image = embed_image

    def embed_text(self, text: str) -> list[float]:
        return self._embed_text(text)

    def embed_image(self, image_bytes: bytes) -> list[float]:
        if self._embed_image is None:
            raise NotImplementedError("image embedding provider not configured")
        return self._embed_image(image_bytes)


# ---------------------------------------------------------------------------
# Phase 4: real image embeddings + per-report embedding sets.
# ---------------------------------------------------------------------------

class ImageEmbedding(BaseModel):
    """Embedding record with full provenance (Phase 4)."""

    vector: list[float]
    method: str
    basis: list[str] = Field(default_factory=list)

    @property
    def dim(self) -> int:
        return len(self.vector)


class ReportEmbeddings(BaseModel):
    """The embedding layer's output for one report (Phase 4).

    Combines the two learned/derived modalities (text, image) with the raw
    geospatial signals (GPS, timestamp, category, landmarks) so the similarity
    layer can answer the product question: "do these two reports describe the
    same real-world incident?" — not "do these sentences look similar?".
    """

    report_id: str
    text_embedding: list[float] = Field(default_factory=list)
    image_embedding: list[float] | None = None
    gps: tuple[float, float] | None = None
    submitted_at: str | None = None
    category: str | None = None
    landmark_ids: list[str] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)


class ClassicalImageEmbedder:
    """Deterministic image embedding from classical CV measurements (Phase 4).

    Vector = the civitas-vision pixel-feature measurements (standardized by
    benchmark-population scale constants, see `_CLASSICAL_FEATURE_SCALES`)
    concatenated with a 32-bin hue histogram and a 32-bin saturation
    histogram, L2 normalized. Real measurements, reproducible offline, and
    documented — no GPU provider required. Production can swap in CLIP via
    `ProviderEmbedder`.
    """

    HUE_BINS = 32
    SAT_BINS = 32

    def __init__(self) -> None:
        try:
            from civitas_vision.features import (
                FEATURE_NAMES,  # type: ignore[import-not-found]
            )

            self._feature_names: tuple[str, ...] = tuple(FEATURE_NAMES)
        except ImportError:  # pragma: no cover - guarded fallback
            self._feature_names = _VISION_FEATURE_ORDER
        self.method = (
            f"classical-features({len(self._feature_names)}) standardized"
            f"+hue{self.HUE_BINS}+sat{self.SAT_BINS}, L2-normalized"
        )

    def embed_image(self, image: Any) -> ImageEmbedding:
        """Embed a PIL image (or bytes / numpy array) into a vector."""
        arr = self._to_array(image)
        features_basis: list[str] = []
        feat: dict[str, float] = {}
        try:
            from civitas_vision.features import (
                extract_features,  # type: ignore[import-not-found]
            )
            from PIL import Image as PILImage

            feat = extract_features(PILImage.fromarray((arr * 255).astype("uint8"), mode="RGB"))
            features_basis = [f"vision measurements: {len(feat)} classical pixel features"]
        except ImportError:
            features_basis = ["civitas-vision unavailable; colour-only embedding"]
        vector = [
            float(feat.get(k, 0.0)) / _CLASSICAL_FEATURE_SCALES.get(k, 1.0)
            for k in self._feature_names
        ]
        vector.extend(self._histogram(arr, self.HUE_BINS, hue=True))
        vector.extend(self._histogram(arr, self.SAT_BINS, hue=False))
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0.0:
            vector = [v / norm for v in vector]
        return ImageEmbedding(
            vector=vector,
            method=self.method,
            basis=features_basis + [
                f"dim {len(vector)}: {len(self._feature_names)} classical + "
                f"{self.HUE_BINS} hue + {self.SAT_BINS} saturation histogram bins"
            ],
        )

    def embed(self, image_bytes: bytes) -> list[float]:  # protocol compat
        import io

        from PIL import Image as PILImage

        return self.embed_image(PILImage.open(io.BytesIO(image_bytes))).vector

    @staticmethod
    def _to_array(image: Any) -> Any:
        import io

        import numpy as np
        from PIL import Image as PILImage

        if isinstance(image, bytes):
            image = PILImage.open(io.BytesIO(image))
        if isinstance(image, PILImage.Image):
            arr = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
        else:
            arr = np.asarray(image, dtype=np.float64) / 255.0
        return arr

    @staticmethod
    def _histogram(arr: Any, bins: int, hue: bool) -> list[float]:
        import numpy as np

        if arr.size == 0:
            return [0.0] * bins
        mx = arr.max(axis=2)
        mn = arr.min(axis=2)
        delta = mx - mn
        eps = 1e-6
        with np.errstate(divide="ignore", invalid="ignore"):
            if hue:
                r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
                out = np.zeros_like(mx)
                mask = delta > eps
                np.copyto(out, np.mod(60.0 * (g - b) / np.maximum(delta, eps), 360.0), where=mask & (mx == r))
                np.copyto(out, np.mod(60.0 * (b - r) / np.maximum(delta, eps) + 120.0, 360.0), where=mask & (mx == g))
                np.copyto(out, np.mod(60.0 * (r - g) / np.maximum(delta, eps) + 240.0, 360.0), where=mask & (mx == b))
                hist, _ = np.histogram(out, bins=bins, range=(0.0, 360.0))
            else:
                sat = delta / np.maximum(mx, eps)
                hist, _ = np.histogram(sat, bins=bins, range=(0.0, 1.0))
        total = float(hist.sum())
        return [float(c / total) if total > 0 else 0.0 for c in hist]


_VISION_FEATURE_ORDER: tuple[str, ...] = (
    "laplacian_variance", "edge_density", "vertical_edge_ratio", "flow_edge_ratio",
    "flow_blue_ratio", "band_dark_ratio", "luminance_mean", "luminance_std",
    "saturation_mean", "saturation_std", "hue_variance", "blue_dominance",
    "green_dominance", "blue_smooth_share", "color_scatter", "bright_peak_mean",
    "bright_upper_share", "dark_lowtexture_share", "contrast_ratio",
)

# Feature-wise scale constants for the classical CV measurements, estimated as
# population standard deviations over the civitas synthetic benchmark set
# (5 incident categories x 8 seeds, 40 images). Without standardization the
# cosine between any two images is dominated by the highest-magnitude
# measurements (hue_variance ~1e3-1e4, color_scatter ~1e2) and visually
# different incidents score ~1.0. Known limitation: constants are fitted to
# the benchmark generation family, not to real-world photos.
_CLASSICAL_FEATURE_SCALES: dict[str, float] = {
    "laplacian_variance": 0.0027,
    "edge_density": 0.0347,
    "vertical_edge_ratio": 0.1008,
    "flow_edge_ratio": 0.1355,
    "flow_blue_ratio": 0.0159,
    "band_dark_ratio": 0.0136,
    "luminance_mean": 0.0757,
    "luminance_std": 0.0200,
    "saturation_mean": 0.0598,
    "saturation_std": 0.0436,
    "hue_variance": 2175.8325,
    "blue_dominance": 0.0609,
    "green_dominance": 0.0217,
    "blue_smooth_share": 0.2045,
    "color_scatter": 117.5489,
    "bright_peak_mean": 0.0672,
    "bright_upper_share": 0.2286,
    "dark_lowtexture_share": 0.2982,
    "contrast_ratio": 0.0535,
}


def build_report_embeddings(
    report_id: str,
    description: str,
    text_embedder: TextEmbedder,
    image: Any | None = None,
    image_embedder: ClassicalImageEmbedder | ProviderEmbedder | None = None,
    gps: tuple[float, float] | None = None,
    submitted_at: str | None = None,
    category: str | None = None,
    landmark_ids: list[str] | None = None,
) -> ReportEmbeddings:
    """Produce the full embedding set for one report (Phase 4).

    Text embedding always; image embedding only when an image and an embedder
    are supplied (missing modality is recorded, never fabricated).
    """
    basis = [f"text embedding: {text_embedder.__class__.__name__}"]
    image_vec: list[float] | None = None
    if image is not None and image_embedder is not None:
        if isinstance(image_embedder, ClassicalImageEmbedder):
            emb = image_embedder.embed_image(image)
            image_vec = emb.vector
            basis.append(f"image embedding ({emb.method})")
        else:
            image_vec = image_embedder.embed_image(image)
            basis.append("image embedding (provider)")
    else:
        basis.append("no image supplied; image modality absent")

    return ReportEmbeddings(
        report_id=report_id,
        text_embedding=text_embedder.embed(description),
        image_embedding=image_vec,
        gps=gps,
        submitted_at=submitted_at,
        category=category,
        landmark_ids=list(landmark_ids or []),
        basis=basis,
    )