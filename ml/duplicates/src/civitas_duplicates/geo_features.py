"""GPS-based duplicate signals."""

from __future__ import annotations

import math

from civitas_geo import distance as geo


def gps_distance_m(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Great-circle distance in metres."""
    return geo.haversine_m(lat1, lon1, lat2, lon2)


def gps_similarity(
    lat1: float, lon1: float, lat2: float, lon2: float, sigma_m: float = 150.0
) -> tuple[float, float]:
    """(similarity, distance_m). RBF decay: 1.0 at identical GPS.

    sigma_m default 150 m reflects typical consumer-GPS noise plus the
    physical extent of a single incident (pothole / leak / obstruction);
    two readings 300 m apart are half as similar.
    """
    d = gps_distance_m(lat1, lon1, lat2, lon2)
    sim = math.exp(-((d / sigma_m) ** 2))
    return sim, d


def within_duplicate_radius_m(distance_m: float, radius_m: float = 2000.0) -> bool:
    """Spatial gate: beyond this radius a duplicate claim needs very strong
    text/image evidence to be credible."""
    return distance_m <= radius_m