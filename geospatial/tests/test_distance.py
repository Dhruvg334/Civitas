"""Tests for civitas_geo.distance."""

import math

from civitas_geo import distance as geo


def test_haversine_known_distance():
    # Delhi (28.6139, 77.2090) -> Agra (27.1767, 78.0081) ~ 176-180 km
    d = geo.haversine_m(28.6139, 77.2090, 27.1767, 78.0081)
    assert 160_000 < d < 200_000


def test_haversine_zero():
    assert geo.haversine_m(28.6, 77.2, 28.6, 77.2) == 0.0


def test_haversine_symmetric():
    a = geo.haversine_m(12.3, 45.6, -33.8, 151.2)
    b = geo.haversine_m(-33.8, 151.2, 12.3, 45.6)
    assert abs(a - b) < 1e-6


def test_haversine_antipodal_less_than_semicircle():
    d = geo.haversine_m(0.0, 0.0, 0.0, 180.0)
    assert d <= math.pi * geo.EARTH_RADIUS_M + 1e-6  # <= pi*R, never beyond


def test_bearing_known():
    # Due east from equator: 90 deg
    b = geo.initial_bearing_deg(0.0, 0.0, 0.0, 10.0)
    assert abs(b - 90.0) < 1.0


def test_bearing_range():
    for _ in range(20):  # deterministic set; asserts normalization
        b = geo.initial_bearing_deg(28.6, 77.2, 28.61, 77.21)
        assert 0.0 <= b < 360.0


def test_midpoint_between_known_points():
    lat, lon = geo.midpoint(28.6139, 77.2090, 27.1767, 78.0081)
    assert 27.5 < lat < 28.5
    assert 77.3 < lon < 78.0


def test_bbox_covers_radius():
    lat, lon = 28.6139, 77.2090
    min_lat, min_lon, max_lat, max_lon = geo.bbox_for_radius(lat, lon, 1000.0)
    # bbox must contain the boundary point 1km due north
    north_lat = lat + math.degrees(1000.0 / geo.EARTH_RADIUS_M)
    assert north_lat <= max_lat + 1e-9
    east_lon = lon + math.degrees(1000.0 / (geo.EARTH_RADIUS_M * abs(math.cos(math.radians(lat)))))
    assert east_lon <= max_lon + 1e-6


def test_offset_point_distance():
    lat, lon = geo.offset_point(28.6139, 77.2090, 100.0, 0.0)
    d = geo.haversine_m(28.6139, 77.2090, lat, lon)
    assert 90.0 < d < 110.0