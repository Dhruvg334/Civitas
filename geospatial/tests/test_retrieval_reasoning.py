"""Tests for retrieval (memory + fake PostGIS executor) and map reasoning."""

from datetime import datetime, timezone

from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import GeoPoint, SpatialSearchSpec
from civitas_geo.reasoning import compute_exposure
from civitas_geo.retrieval import NearbyRetriever, retrieve_memory, retrieve_postgis

CENTER = GeoPoint(latitude=28.6139, longitude=77.2090)

INCIDENTS = [
    {"incident_id": "i1", "latitude": 28.6139, "longitude": 77.2090, "category": "pothole", "duplicates_seen": 1},
    {"incident_id": "i2", "latitude": 28.6142, "longitude": 77.2095, "category": "pothole", "duplicates_seen": 3},
    {"incident_id": "i3", "latitude": 28.6148, "longitude": 77.2190, "category": "water leak", "duplicates_seen": 1},
    {"incident_id": "i4", "latitude": 28.6200, "longitude": 77.2400, "category": "streetlight", "duplicates_seen": 2},
]


class FakeExecutor:
    """Stands in for a PostGIS cursor; returns precomputed rows."""

    def __init__(self, rows=None):
        self.rows = rows or []
        self.last_sql = None
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params
        return self.rows


def test_memory_retrieval_radius_and_sort():
    spec = SpatialSearchSpec(center=CENTER, radius_m=1000, limit=10)
    res = retrieve_memory(spec, INCIDENTS)
    assert res.mode == "memory"
    ids = [i.incident_id for i in res.incidents]
    assert ids[0] == "i1" and "i2" in ids
    assert "i4" not in ids
    assert all(i.distance_m <= 1000 for i in res.incidents)


def test_memory_retrieval_filters():
    spec = SpatialSearchSpec(center=CENTER, radius_m=5000, limit=10, category_filter="water leak")
    res = retrieve_memory(spec, INCIDENTS)
    assert [i.incident_id for i in res.incidents] == ["i3"]
    spec2 = SpatialSearchSpec(center=CENTER, radius_m=5000, limit=10, exclude_incident_ids=["i1"])
    res2 = retrieve_memory(spec2, INCIDENTS)
    assert "i1" not in [i.incident_id for i in res2.incidents]


def test_memory_retrieval_limit():
    spec = SpatialSearchSpec(center=CENTER, radius_m=5000, limit=2)
    res = retrieve_memory(spec, INCIDENTS)
    assert len(res.incidents) == 2


def test_postgis_retrieval_uses_executor():
    rows = [
        {"incident_id": "x1", "latitude": 28.61, "longitude": 77.21, "category": "pothole",
         "reported_at": datetime(2026, 1, 2, tzinfo=timezone.utc), "duplicates_seen": 2, "distance_m": 12.5},
    ]
    ex = FakeExecutor(rows)
    spec = SpatialSearchSpec(center=CENTER, radius_m=800, limit=10)
    res = retrieve_postgis(spec, ex)
    assert res.mode == "postgis"
    assert res.incidents[0].distance_m == 12.5
    assert ex.last_sql is not None


def test_retriever_prefers_postgis():
    retriever = NearbyRetriever(executor=FakeExecutor())
    res = retriever.retrieve(SpatialSearchSpec(center=CENTER, radius_m=100, limit=5), memory_incidents=INCIDENTS)
    assert res.mode == "postgis"


def test_exposure_school_hospital_and_traffic():
    exp = compute_exposure(CENTER, landmarks=LandmarkIndex())
    assert exp.nearest_school_m is not None
    assert exp.nearest_hospital_m is not None
    assert exp.traffic_exposure in ("low", "moderate", "high")
    assert any("landmark:" in s for s in exp.sources)


def test_exposure_high_traffic_with_primary_road():
    exp = compute_exposure(CENTER, roads=[{"type": "primary", "distance_m": 30}])
    assert exp.traffic_exposure == "high"
    assert any("road:primary-class proximity" in s for s in exp.sources)


def test_exposure_junction_density_inference():
    # Center sits between two demo junctions within 1km -> density > 0
    exp = compute_exposure(CENTER)
    assert exp.junction_density_1km >= 0.0