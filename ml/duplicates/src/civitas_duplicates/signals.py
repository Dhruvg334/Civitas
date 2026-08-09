"""Per-signal similarity computation for report pairs."""

from __future__ import annotations

from civitas_duplicates.embeddings import TextEmbedder, cosine_similarity
from civitas_duplicates.landmark_features import landmark_similarity, landmarks_for_point
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import GeoPoint


def text_similarity(
    a: str, b: str, embedder: TextEmbedder, cached_a: list[float] | None = None, cached_b: list[float] | None = None
) -> float:
    """Cosine similarity of text embeddings; sentence-level semantics."""
    va = cached_a if cached_a is not None else embedder.embed(a)
    vb = cached_b if cached_b is not None else embedder.embed(b)
    return cosine_similarity(va, vb)


def image_similarity(
    embedding_a: list[float] | None,
    embedding_b: list[float] | None,
) -> float | None:
    """Cosine similarity of CLIP-compatible image embeddings.

    None when either report lacks an image embedding; the scorer renormalizes
    weights so a missing modality never masquerades as low similarity.
    """
    if embedding_a is None or embedding_b is None:
        return None
    return cosine_similarity(embedding_a, embedding_b)


CANONICAL_CATEGORIES = ("pothole", "water_leak", "garbage", "streetlight", "fallen_tree")

CATEGORY_ALIASES: dict[str, str] = {
    "potholes": "pothole",
    "road damage": "pothole",
    "water leak": "water_leak",
    "water leakage": "water_leak",
    "waterlogging": "water_leak",
    "flooding": "water_leak",
    "garbage overflow": "garbage",
    "waste": "garbage",
    "street light": "streetlight",
    "streetlights": "streetlight",
    "light": "streetlight",
    "fallen tree": "fallen_tree",
    "tree": "fallen_tree",
    "blocked pathway": "fallen_tree",
}

# Incident categories that are physically linked: reports in different
# categories may describe ONE incident when the categories are causally
# related (Phase 5 — "related categories" reason in duplicate decisions).
RELATED_CATEGORIES: dict[frozenset[str], str] = {
    frozenset({"water_leak", "pothole"}): "water damage erodes and wash out the road surface",
    frozenset({"water_leak", "garbage"}): "waterlogging spreads waste and blocks drains",
}


def normalize_category(category: str | None) -> str | None:
    """Canonical category form so citizen/vison spellings compare equal."""
    if not category:
        return None
    key = category.strip().lower()
    if key in CANONICAL_CATEGORIES:
        return key
    return CATEGORY_ALIASES.get(key)


def category_agreement(a: str | None, b: str | None) -> float:
    """1.0 if canonical categories agree (or one is missing), else 0.0.

    Phase 5: related categories score 0.5 (see `category_relation`); truly
    conflicting categories score 0.0.
    """
    return category_relation(a, b)[0]


def category_relation(a: str | None, b: str | None) -> tuple[float, str | None]:
    """(score, reason): 1.0 identical/alias, 0.5 related, 0.0 conflicting.

    `reason` carries the human-readable causal link ("related categories:
    flooding undermines the road surface") used in decision basis lines —
    never fabricated: only `RELATED_CATEGORIES` pairs produce a reason.
    """
    ca, cb = normalize_category(a), normalize_category(b)
    if ca is None or cb is None:
        return 1.0, None
    if ca == cb:
        return 1.0, None
    note = RELATED_CATEGORIES.get(frozenset({ca, cb}))
    if note is not None:
        return 0.5, note
    return 0.0, None


def landmark_signal(
    lat_a: float,
    lon_a: float,
    landmark_ids_a: list[str],
    lat_b: float,
    lon_b: float,
    landmark_ids_b: list[str],
    index: LandmarkIndex,
    radius_m: float = 250.0,
) -> float:
    """Landmark overlap signal, defaulting to spatial containment lookups."""
    points_a = [GeoPoint(latitude=lat_a, longitude=lon_a)]
    points_b = [GeoPoint(latitude=lat_b, longitude=lon_b)]
    lms_a = [lm for lm in index.landmarks if lm.landmark_id in landmark_ids_a]
    lms_b = [lm for lm in index.landmarks if lm.landmark_id in landmark_ids_b]
    if not lms_a:
        lms_a = landmarks_for_point(points_a[0], index, radius_m)
    if not lms_b:
        lms_b = landmarks_for_point(points_b[0], index, radius_m)
    return landmark_similarity(lms_a, lms_b, index, radius_m=min(radius_m, 150.0))