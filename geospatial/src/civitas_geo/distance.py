"""Pure-Python geodesic helpers (WGS84, sphere model).

Used by landmark lookup, memory-mode retrieval, and duplicate detection so
the same distance semantics apply inside and outside PostGIS.
"""

from __future__ import annotations

import math

EARTH_RADIUS_M = 6_371_008.8


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two coordinates."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def initial_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing in degrees [0, 360) from point 1 to point 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def midpoint(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
    """Approximate geodesic midpoint as (lat, lon)."""
    dlam = math.radians(lon2 - lon1)
    bx = math.cos(math.radians(lat2)) * math.cos(dlam)
    by = math.cos(math.radians(lat2)) * math.sin(dlam)
    phim = math.atan2(
        math.sin(math.radians(lat1)) + math.sin(math.radians(lat2)),
        math.sqrt(
            (math.cos(math.radians(lat1)) + bx) ** 2 + by**2
        ),
    )
    lam = math.radians(lon1) + math.atan2(by, math.cos(math.radians(lat1)) + bx)
    return math.degrees(phim), (math.degrees(lam) + 540.0) % 360.0 - 180.0


def bbox_for_radius(lat: float, lon: float, radius_m: float) -> tuple[float, float, float, float]:
    """Bounding box (min_lat, min_lon, max_lat, max_lon) around a point.

    Useful for index-accelerated ST_MakeEnvelope pre-filters.
    """
    dlat = math.degrees(radius_m / EARTH_RADIUS_M)
    lat_r = math.radians(lat)
    dlon = math.degrees(radius_m / (EARTH_RADIUS_M * max(0.01, abs(math.cos(lat_r)))))
    min_lat = max(-90.0, lat - dlat)
    max_lat = min(90.0, lat + dlat)
    min_lon = max(-180.0, lon - dlon)
    max_lon = min(180.0, lon + dlon)
    return min_lat, min_lon, max_lat, max_lon


def offset_point(lat: float, lon: float, dx_m: float, dy_m: float) -> tuple[float, float]:
    """Offset a point by local east/north metres (small distances only)."""
    new_lat = lat + math.degrees(dy_m / EARTH_RADIUS_M)
    new_lon = lon + math.degrees(
        dx_m / (EARTH_RADIUS_M * max(0.01, abs(math.cos(math.radians(lat)))))
    )
    return new_lat, new_lon