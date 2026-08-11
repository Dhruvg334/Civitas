"""Landmark-based duplicate signals.

Reports frequently mention a landmark ("near the school gate", "at
Kingsway junction"). Landmark identity overlap is a strong, human-verifiable
duplicate signal even when GPS jitters.
"""

from __future__ import annotations

from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import GeoPoint, Landmark


def landmarks_for_point(
    point: GeoPoint,
    index: LandmarkIndex,
    radius_m: float = 250.0,
) -> list[Landmark]:
    """Landmarks a report is plausibly anchored to (within radius)."""
    return index.within(point, radius_m=radius_m)


def landmark_similarity(
    landmarks_a: list[Landmark],
    landmarks_b: list[Landmark],
    index: LandmarkIndex,
    radius_m: float = 150.0,
) -> float:
    """Symmetric centroid overlap in [0, 1] between two landmark sets."""
    if not landmarks_a or not landmarks_b:
        return 0.0
    fa = index.overlap(landmarks_a, landmarks_b, radius_m=radius_m)
    fb = index.overlap(landmarks_b, landmarks_a, radius_m=radius_m)
    return max(fa, fb)


def landmark_text_match(
    description_a: str,
    description_b: str,
    index: LandmarkIndex,
) -> tuple[float, list[str]]:
    """Keyword overlap between landmark names and both descriptions.

    Returns (signal in [0,1], matched landmark names). Uses only observable
    landmark vocabulary; no free-form generation.
    """
    matched: set[str] = set()
    haystacks = (description_a.lower(), description_b.lower())
    for lm in index.landmarks:
        terms = lm.name.lower().replace("-", " ").split()
        if terms and all(any(t in h for h in haystacks) for t in terms[:2]):
            matched.add(lm.name)
    if not matched:
        return 0.0, []
    signal = min(1.0, len(matched) / 2.0)
    return signal, sorted(matched)