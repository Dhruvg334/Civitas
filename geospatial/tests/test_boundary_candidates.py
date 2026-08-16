"""Tests for the Phase 2 spatial foundation: operational boundary, candidate
retrieval windows (radius / hours / category / boundary), landmark context
enrichment and the location-validation pipeline gate."""

from datetime import datetime, timedelta, timezone

import pytest
from civitas_geo.boundary import DEFAULT_BOUNDARY, point_in_boundary
from civitas_geo.candidates import (
    CandidateRetriever,
    retrieve_candidates_memory,
    retrieve_candidates_postgis,
)
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import (
    CandidateSearchSpec,
    GeoPoint,
    OperationalBoundary,
)
from civitas_geo.queries import candidate_incidents_sql
from civitas_geo.validation import gate_for_pipeline

T0 = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
CENTER = GeoPoint(latitude=28.6139, longitude=77.2090)

RECORDS = [
    {"incident_id": "c1", "latitude": 28.6139, "longitude": 77.2090, "category": "pothole",
     "reported_at": T0 - timedelta(hours=1), "duplicates_seen": 1},
    {"incident_id": "c2", "latitude": 28.6145, "longitude": 77.2100, "category": "pothole",
     "reported_at": T0 - timedelta(hours=5), "duplicates_seen": 3},
    {"incident_id": "c3", "latitude": 28.6200, "longitude": 77.2165, "category": "streetlight",
     "reported_at": T0 - timedelta(hours=30), "duplicates_seen": 1},
    {"incident_id": "c4", "latitude": 28.6135, "longitude": 77.2085, "category": "water leak",
     "reported_at": T0 - timedelta(hours=200), "duplicates_seen": 2},
    {"incident_id": "c5", "latitude": 28.40, "longitude": 77.00, "category": "pothole",
     "reported_at": T0 - timedelta(hours=2), "duplicates_seen": 1},
]

LANDMARKS = LandmarkIndex()


class FakeExecutor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.last_sql = None
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params
        return self.rows


class TestBoundary:
    def test_default_boundary_contains_city_points(self):
        assert DEFAULT_BOUNDARY.contains(28.6139, 77.2090)
        assert not DEFAULT_BOUNDARY.contains(28.40, 77.00)

    def test_point_in_boundary(self):
        assert point_in_boundary(GeoPoint(latitude=28.6139, longitude=77.2090))
        assert not point_in_boundary(GeoPoint(latitude=10.0, longitude=10.0))

    def test_custom_boundary(self):
        near = OperationalBoundary(
            name="test-only", bbox=(28.60, 77.20, 28.62, 77.22), source="unit test"
        )
        assert near.contains(28.61, 77.21)
        assert not near.contains(28.52, 77.13)
        assert "test-only" in near.description


class TestCandidateSql:
    def test_windows_bound_as_parameters(self):
        spec = CandidateSearchSpec(center=CENTER, radius_m=800, within_hours=24, limit=10)
        sql, params = candidate_incidents_sql(spec, boundary=DEFAULT_BOUNDARY)
        assert "ST_DWithin" in sql and "make_interval" in sql
        assert "ST_MakeEnvelope" in sql and "location_geom &&" in sql
        assert "EXTRACT(EPOCH FROM (now() - i.reported_at))" in sql
        assert params["radius_m"] == 800 and params["hours_back"] == 24
        assert all(p in sql for p in ("%(center_lat)s", "%(hours_back)s", "%(b_min_lat)s"))
        assert "ORDER BY distance_m ASC" in sql and "LIMIT %(limit)s" in sql

    def test_optional_filters_absent_by_default(self):
        sql, params = candidate_incidents_sql(
            CandidateSearchSpec(center=CENTER, radius_m=500, within_hours=48)
        )
        assert "category = %(category)s" not in sql
        assert "ST_MakeEnvelope" not in sql

    def test_category_and_exclusions_bound(self):
        spec = CandidateSearchSpec(
            center=CENTER, radius_m=500, within_hours=48,
            category_filter="pothole", exclude_incident_ids=["c1"],
        )
        sql, params = candidate_incidents_sql(spec)
        assert "i.category = %(category)s" in sql
        assert "= ANY(%(exclude_ids)s) = false" in sql
        assert params["category"] == "pothole" and params["exclude_ids"] == ["c1"]


class TestMemoryCandidates:
    def test_radius_and_recency_windows(self):
        spec = CandidateSearchSpec(center=CENTER, radius_m=800, within_hours=24, limit=10)
        res = retrieve_candidates_memory(spec, RECORDS, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        ids = [c.incident_id for c in res.candidates]
        assert res.mode == "memory"
        assert "c1" in ids and "c2" in ids
        assert "c3" not in ids          # within radius but 30 h old
        assert "c4" not in ids          # within radius but 200 h old
        assert all(c.distance_m <= 800 for c in res.candidates)
        assert all(c.hours_since_reported <= 24 for c in res.candidates)
        assert all(c.within_time_window for c in res.candidates)

    def test_boundary_excludes_out_of_coverage(self):
        spec = CandidateSearchSpec(center=CENTER, radius_m=50_000, within_hours=24, limit=50)
        res = retrieve_candidates_memory(spec, RECORDS, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        assert "c5" not in [c.incident_id for c in res.candidates]
        assert res.boundary is DEFAULT_BOUNDARY

    def test_category_filter_and_exclusion(self):
        spec = CandidateSearchSpec(
            center=CENTER, radius_m=50_000, within_hours=24, limit=50,
            category_filter="pothole", exclude_incident_ids=["c1"],
        )
        res = retrieve_candidates_memory(spec, RECORDS, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        assert [c.incident_id for c in res.candidates] == ["c2"]

    def test_ordered_by_distance_and_limit(self):
        spec = CandidateSearchSpec(center=CENTER, radius_m=50_000, within_hours=24, limit=1)
        res = retrieve_candidates_memory(spec, RECORDS, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        assert len(res.candidates) == 1 and res.candidates[0].incident_id == "c1"

    def test_naive_timestamps_normalized(self):
        records = [dict(RECORDS[0]), {**RECORDS[0], "reported_at": T0.replace(tzinfo=None)}]
        spec = CandidateSearchSpec(center=CENTER, radius_m=800, within_hours=24, limit=10)
        res = retrieve_candidates_memory(spec, records, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        assert any(c.hours_since_reported is not None for c in res.candidates)


class TestLandmarkContext:
    def test_each_candidate_carries_nearest_landmarks(self):
        spec = CandidateSearchSpec(center=CENTER, radius_m=800, within_hours=24, limit=10)
        res = retrieve_candidates_memory(spec, RECORDS, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        assert res.candidates
        for cand in res.candidates:
            kinds = {d.landmark.kind for d in cand.landmark_context}
            assert "school" in kinds and "hospital" in kinds
            school = next(d for d in cand.landmark_context if d.landmark.kind == "school")
            assert school.distance_m <= 1_500

    def test_enrichment_is_deterministic(self):
        spec = CandidateSearchSpec(center=CENTER, radius_m=800, within_hours=24, limit=10)
        a = retrieve_candidates_memory(spec, RECORDS, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        b = retrieve_candidates_memory(spec, RECORDS, LANDMARKS, DEFAULT_BOUNDARY, now=T0)
        for ca, cb in zip(a.candidates, b.candidates):
            assert [d.landmark.landmark_id for d in ca.landmark_context] == [
                d.landmark.landmark_id for d in cb.landmark_context
            ]


class TestPostgisCandidates:
    def test_postgis_path_with_fake_executor(self):
        rows = [
            {"incident_id": "x1", "latitude": 28.6139, "longitude": 77.2090,
             "category": "pothole", "reported_at": T0, "duplicates_seen": 2,
             "distance_m": 12.5, "hours_since_reported": 1.5},
        ]
        ex = FakeExecutor(rows)
        spec = CandidateSearchSpec(center=CENTER, radius_m=800, within_hours=24, limit=10)
        res = retrieve_candidates_postgis(spec, ex, LANDMARKS, DEFAULT_BOUNDARY)
        assert res.mode == "postgis"
        assert res.candidates[0].incident_id == "x1"
        assert res.candidates[0].hours_since_reported == pytest.approx(1.5)
        assert ex.last_params["radius_m"] == 800
        assert len(res.candidates[0].landmark_context) >= 2

    def test_retriever_prefers_postgis(self):
        retriever = CandidateRetriever(executor=FakeExecutor())
        spec = CandidateSearchSpec(center=CENTER, radius_m=800, within_hours=24, limit=5)
        res = retriever.retrieve(spec, memory_incidents=RECORDS, landmarks=LANDMARKS)
        assert res.mode == "postgis"


class TestPipelineGate:
    def test_valid_in_city_approved(self):
        g = gate_for_pipeline({"latitude": 28.6139, "longitude": 77.2090})
        assert g.can_enter and g.reason == "approved"
        assert g.validation is not None and g.validation.is_valid

    def test_missing_coordinates_rejected(self):
        g = gate_for_pipeline({})
        assert not g.can_enter and g.reason == "rejected_malformed"

    def test_placeholder_rejected(self):
        g = gate_for_pipeline({"latitude": 0.0, "longitude": 0.0})
        assert not g.can_enter and g.reason == "rejected_placeholder"

    def test_out_of_coverage_rejected(self):
        g = gate_for_pipeline({"latitude": 28.40, "longitude": 77.00})
        assert not g.can_enter and g.reason == "rejected_out_of_coverage"

    def test_uncertain_inside_city_enters_with_warnings(self):
        g = gate_for_pipeline({"latitude": 28.6139, "longitude": 77.2090})
        assert g.can_enter
        assert isinstance(g.warnings, list)