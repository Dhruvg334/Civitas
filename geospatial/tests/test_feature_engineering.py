"""Tests for the Civitas geospatial feature-engineering module."""

from datetime import datetime, timedelta, timezone

import pytest
from civitas_geo.feature_engineering import (
    CivicIncidentContext,
    GeospatialFeatureEngine,
    normalize_category,
)
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import GeoPoint, NearbyIncident, SpatialSearchSpec
from civitas_geo.retrieval import retrieve_memory

T0 = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
SCHOOL_SPOT = (28.6139, 77.2090)  # Sunrise Public School landmark sits here
METRO_SPOT = (28.6190, 77.2165)   # Civic Centre Metro
FAR_CITY = (28.55, 77.15)         # inside demo city bbox but landmark-free


def nearby(records: list[dict]) -> list[NearbyIncident]:
    spec = SpatialSearchSpec(center=GeoPoint(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1]), radius_m=800, limit=50)
    return retrieve_memory(spec, records).incidents


def default_records() -> list[dict]:
    return [
        {"incident_id": "n1", "latitude": SCHOOL_SPOT[0] + 0.0005, "longitude": SCHOOL_SPOT[1], "category": "pothole",
         "duplicates_seen": 2, "reported_at": T0 - timedelta(hours=5)},
        {"incident_id": "n2", "latitude": SCHOOL_SPOT[0] + 0.0012, "longitude": SCHOOL_SPOT[1] + 0.0010, "category": "pothole",
         "duplicates_seen": 1, "reported_at": T0 - timedelta(hours=2)},
        {"incident_id": "n3", "latitude": METRO_SPOT[0], "longitude": METRO_SPOT[1], "category": "streetlight",
         "duplicates_seen": 1, "reported_at": T0 - timedelta(hours=30)},
    ]


def engine() -> GeospatialFeatureEngine:
    return GeospatialFeatureEngine(landmarks=LandmarkIndex())


class TestSchema:
    def test_vector_shape_and_bounds(self):
        v = engine().compute(
            CivicIncidentContext(
                latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1],
                submitted_at=T0, category="pothole",
                nearby_reports=nearby(default_records()),
            )
        )
        assert v.schema_version == "civitas-geo-features-v1"
        assert len(v.features) >= 24
        assert len(v.provenance) == len(v.features)
        for name, val in v.features.items():
            assert 0.0 <= val <= 1.0, name
        assert v.basis

    def test_all_feature_keys_have_provenance(self):
        v = engine().compute(
            CivicIncidentContext(
                latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1],
                submitted_at=T0, category=None, nearby_reports=[],
            )
        )
        for key in v.features:
            assert v.provenance.get(key), key

    def test_normalize_category(self):
        assert normalize_category("water leakage") == "water_leak"
        assert normalize_category("pothole") == "pothole"
        assert normalize_category("weird thing") is None


class TestLocationValidity:
    def test_valid_location_feature(self):
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, nearby_reports=[])
        )
        assert v.features["location_validity"] >= 0.5

    def test_invalid_location_feature_zero_and_warning(self):
        v = engine().compute(
            CivicIncidentContext(latitude=0.0, longitude=0.0, submitted_at=T0, nearby_reports=[])
        )
        assert v.features["location_validity"] == 0.0
        assert any("placeholder" in w or "outside" in w or "malformed" in w for w in v.warnings)


class TestProximityFeatures:
    def test_school_hospital_proximity_high_at_school_spot(self):
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, nearby_reports=[])
        )
        assert v.features["school_proximity"] > 0.9
        assert v.raw["school_distance_m"] < 100.0

    def test_proximity_low_away_from_landmarks(self):
        v = engine().compute(
            CivicIncidentContext(latitude=FAR_CITY[0], longitude=FAR_CITY[1], submitted_at=T0, nearby_reports=[])
        )
        assert v.features["landmark_proximity"] < 0.1

    def test_pathway_proximity_flag(self):
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, nearby_reports=[])
        )
        assert v.features["pathway_proximity"] == 1.0

    def test_population_proxy_present_near_metro(self):
        v = engine().compute(
            CivicIncidentContext(latitude=METRO_SPOT[0], longitude=METRO_SPOT[1], submitted_at=T0, nearby_reports=[])
        )
        assert v.raw["population_proxy_landmarks_1km"] >= 1
        assert v.features["population_density_proxy"] > 0.0


class TestReportNeighbourhood:
    def test_counts_density_and_distances(self):
        v = engine().compute(
            CivicIncidentContext(
                latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1],
                submitted_at=T0, nearby_reports=nearby(default_records()),
            )
        )
        assert v.raw["nearby_report_count"] >= 2
        assert v.features["incident_density_1km"] > 0.0
        assert 0 < v.raw["nearest_report_distance_m"] < 300
        assert v.raw["mean_report_distance_m"] > 0

    def test_nearest_report_similarity_rbf(self):
        close = nearby([{"incident_id": "x", "latitude": SCHOOL_SPOT[0] + 0.0002,
                         "longitude": SCHOOL_SPOT[1], "category": "pothole",
                         "duplicates_seen": 1, "reported_at": T0 - timedelta(hours=1)}])
        far = nearby([{"incident_id": "y", "latitude": SCHOOL_SPOT[0] + 0.05,
                       "longitude": SCHOOL_SPOT[1], "category": "pothole",
                       "duplicates_seen": 1, "reported_at": T0 - timedelta(hours=1)}])
        v_close = engine().compute(CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, nearby_reports=close))
        v_far = engine().compute(CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, nearby_reports=far))
        assert v_close.features["nearest_report_distance_sim"] > v_far.features["nearest_report_distance_sim"]

    def test_repeated_reports_accumulates_duplicates_seen(self):
        v = engine().compute(
            CivicIncidentContext(
                latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1],
                submitted_at=T0, nearby_reports=nearby(default_records()),
            )
        )
        assert v.raw["repeated_reports_total"] >= 2
        assert v.features["repeated_reports"] > 0.0

    def test_time_since_first_report(self):
        v = engine().compute(
            CivicIncidentContext(
                latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1],
                submitted_at=T0, nearby_reports=nearby(default_records()),
            )
        )
        assert v.raw["time_since_first_report_h"] == pytest.approx(5.0, abs=1e-3)
        assert 0.0 < v.features["time_since_first_report_norm"] < 0.3

    def test_no_nearby_reports_graceful(self):
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, nearby_reports=[])
        )
        assert v.raw["nearby_report_count"] == 0
        assert v.features["nearby_report_count"] == 0.0
        assert v.features["time_since_first_report_norm"] == 0.0


class TestTemporal:
    def test_hour_and_weekend(self):
        sunday = T0.replace(hour=10)  # 2026-03-01 is a Sunday
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=sunday, nearby_reports=[])
        )
        assert v.raw["hour_of_day_utc"] == 10
        assert v.features["hour_of_day_norm"] == pytest.approx(round(10 / 24.0, 4))
        assert v.features["is_weekend"] == 1.0

    def test_naive_timestamp_handled(self):
        v = engine().compute(
            CivicIncidentContext(
                latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1],
                submitted_at=datetime(2026, 3, 2, 12, 0), nearby_reports=[],
            )
        )
        assert v.raw["hour_of_day_utc"] == 12


class TestCategory:
    def test_one_hot(self):
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, category="water leakage", nearby_reports=[])
        )
        assert v.features["category_water_leak"] == 1.0
        assert v.features["category_pothole"] == 0.0
        assert v.features["category_is_known"] == 1.0

    def test_unknown_category(self):
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, category="mystery thing", nearby_reports=[])
        )
        assert v.features["category_is_known"] == 0.0
        assert sum(v.features[f"category_{c}"] for c in ("pothole", "water_leak", "garbage", "streetlight", "fallen_tree")) == 0.0


class TestIntegration:
    def test_compute_for_point_with_memory_retrieval(self):
        eng = engine()
        v = eng.compute_for_point(
            SCHOOL_SPOT[0], SCHOOL_SPOT[1],
            submitted_at=T0, category="pothole",
            memory_incidents=default_records(),
        )
        assert v.raw["nearby_report_count"] >= 2
        assert v.features["school_proximity"] > 0.9

    def test_evidence_only_no_decisions(self):
        """The module must not contain decision fields (severity/priority!)."""
        v = engine().compute(
            CivicIncidentContext(latitude=SCHOOL_SPOT[0], longitude=SCHOOL_SPOT[1], submitted_at=T0, nearby_reports=[])
        )
        assert not any("severity" in k or "priority" in k or "tier" in k for k in v.features)
        assert not any("severity" in k or "priority" in k for k in v.raw)