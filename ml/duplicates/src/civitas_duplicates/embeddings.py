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
from typing import Callable, Protocol

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