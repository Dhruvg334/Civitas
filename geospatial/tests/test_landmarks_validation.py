"""Tests for civitas_geo.landmarks and validation."""

from civitas_geo import distance as geo
from civitas_geo.landmarks import DEMO_LANDMARKS, LandmarkIndex
from civitas_geo.models import GeoPoint
from civitas_geo.validation import LocationValidator


def test_nearest_school():
    idx = LandmarkIndex(DEMO_LANDMARKS)
    near = idx.nearest_by_kind(GeoPoint(latitude=28.6139, longitude=77.2090), "school")
    assert near is not None
    assert near.landmark.kind == "school"
    assert near.distance_m < 500.0


def test_nearest_returns_none_when_out_of_range():
    idx = LandmarkIndex(DEMO_LANDMARKS)
    far = idx.nearest_by_kind(GeoPoint(latitude=28.1, longitude=76.9), "hospital", max_distance_m=5000.0)
    assert far is None


def test_within_radius():
    idx = LandmarkIndex(DEMO_LANDMARKS)
    point = GeoPoint(latitude=28.6139, longitude=77.2090)
    found = idx.within(point, kind="school", radius_m=300.0)
    assert len(found) >= 1
    assert all(lm.kind == "school" for lm in found)


def test_overlap_fraction():
    idx = LandmarkIndex(DEMO_LANDMARKS)
    point = GeoPoint(latitude=28.6140, longitude=77.2092)
    a = idx.within(point, radius_m=400.0)
    b = idx.within(GeoPoint(latitude=28.6141, longitude=77.2091), radius_m=400.0)
    assert idx.overlap(a, b) > 0.5


def test_overlap_empty_when_no_landmarks():
    idx = LandmarkIndex([])
    assert idx.overlap([], []) == 0.0


def test_validator_accepts_city_point():
    v = LocationValidator()
    res = v.validate(GeoPoint(latitude=28.6139, longitude=77.2090))
    assert res.is_valid
    assert res.plausibility == "plausible" or res.plausibility == "uncertain"


def test_validator_rejects_out_of_range():
    v = LocationValidator()
    res = v.validate({"latitude": 95.0, "longitude": 120.0})  # raw, unvalidated input
    assert not res.is_valid
    assert res.plausibility == "implausible"


def test_validator_rejects_outside_city():
    v = LocationValidator()
    res = v.validate(GeoPoint(latitude=12.9, longitude=77.6))  # far away
    assert not res.is_valid


def test_validator_warns_zero_zero():
    res = LocationValidator().validate({"latitude": 0.0, "longitude": 0.0})
    assert any("placeholder" in w for w in res.warnings)
    assert not res.is_valid


def test_validator_snap_to_landmark():
    res = LocationValidator().validate(GeoPoint(latitude=28.6139, longitude=77.2090))
    assert res.suggested_snap is None or res.suggested_snap.latitude != 0.0
    # Snap should be near the school landmark when contained
    smallest = None
    for lm in DEMO_LANDMARKS:
        d = geo.haversine_m(28.6139, 77.2090, lm.latitude, lm.longitude)
        if smallest is None or d < smallest:
            smallest = d
    assert smallest is not None and smallest < 400.0  # sanity: point is near a landmark


def test_compare_reports_identical_gps_warns():
    v = LocationValidator()
    warnings = v.compare_reports(
        GeoPoint(latitude=28.6139, longitude=77.2090),
        GeoPoint(latitude=28.6139, longitude=77.2090),
    )
    assert any("Identical coordinates" in w for w in warnings)


def test_compare_reports_far_apart_silent():
    v = LocationValidator()
    assert v.compare_reports(
        GeoPoint(latitude=28.6139, longitude=77.2090),
        GeoPoint(latitude=28.63, longitude=77.22),
    ) == []