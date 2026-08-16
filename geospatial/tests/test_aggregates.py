"""Phase 4 tests: reports-per-cell density aggregates and feature wiring."""

from datetime import datetime, timedelta, timezone

import pytest
from civitas_geo.aggregates import (
    DensityAggregator,
    cell_id_for,
    reports_per_cell_memory,
    reports_per_cell_postgis,
)
from civitas_geo.feature_engineering import (
    CivicIncidentContext,
    GeospatialFeatureEngine,
)
from civitas_geo.models import DensityAggregateResult
from civitas_geo.queries import reports_per_cell_sql

T0 = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
CENTER = {"latitude": 28.6139, "longitude": 77.2090, "category": "pothole"}


def _incident(incident_id: str, lat: float, lon: float, category: str = "pothole",
              reported_at: datetime = T0) -> dict:
    return {
        "incident_id": incident_id,
        "latitude": lat,
        "longitude": lon,
        "category": category,
        "reported_at": reported_at,
    }


class TestMemoryAggregation:
    def test_same_cell_counts_and_categories(self):
        # Three reports nearly on top of each other (same 200 m cell anchor
        # 28.61301|77.20985), one far away in its own cell.
        records = [
            _incident("i1", 28.61302, 77.20986, "pothole"),
            _incident("i2", 28.61305, 77.20990, "pothole"),
            _incident("i3", 28.61300, 77.20988, "water_leak"),
            _incident("i4", 28.6190, 77.2165, "garbage"),
        ]
        result = reports_per_cell_memory(records, cell_size_m=200)
        assert isinstance(result, DensityAggregateResult)
        assert result.mode == "memory"
        assert result.total_reports == 4
        assert result.cell_count() == 2
        top = result.top_cells(1)[0]
        assert top.cell_id == cell_id_for(28.61302, 77.20986, 200)
        assert top.report_count == 3
        assert top.category_distribution == {"pothole": 2, "water_leak": 1}

    def test_cell_id_matches_rows(self):
        records = [_incident("i1", 28.6140, 77.2092)]
        result = reports_per_cell_memory(records, cell_size_m=200)
        assert result.cells[0].cell_id == cell_id_for(28.6140, 77.2092, 200)

    def test_cell_size_changes_buckets(self):
        records = [
            _incident("i1", 28.6139, 77.2090),
            _incident("i2", 28.6152, 77.2092),
        ]
        fine = reports_per_cell_memory(records, cell_size_m=100)
        coarse = reports_per_cell_memory(records, cell_size_m=500)
        assert fine.cell_count() == 2
        assert coarse.cell_count() == 1
        assert coarse.total_reports == 2

    def test_boundary_excludes_outside_records(self):
        records = [
            _incident("in", 28.6139, 77.2090),
            _incident("out", 28.8000, 77.3000),
        ]
        result = reports_per_cell_memory(records, cell_size_m=200)
        assert result.total_reports == 1
        assert any("outside the operational boundary" in b for b in result.basis)

    def test_since_window_filters_old_records(self):
        records = [
            _incident("new", 28.6139, 77.2090, reported_at=T0),
            _incident("old", 28.6140, 77.2091, reported_at=T0 - timedelta(days=30)),
        ]
        result = reports_per_cell_memory(records, cell_size_m=200, since=T0 - timedelta(days=7))
        assert result.total_reports == 1
        assert result.window_hours is not None
        assert any("recency window" in b for b in result.basis)

    def test_dict_and_object_records_both_accepted(self):
        from civitas_geo.models import NearbyIncident

        as_obj = NearbyIncident(incident_id="o1", latitude=28.6139, longitude=77.2090,
                                category="pothole", distance_m=0.0, reported_at=T0)
        result = reports_per_cell_memory([as_obj], cell_size_m=200)
        assert result.total_reports == 1

    def test_empty_input(self):
        result = reports_per_cell_memory([], cell_size_m=200)
        assert result.cell_count() == 0
        assert result.total_reports == 0


class _FakeExecutor:
    def __init__(self, rows=None, fail: bool = False):
        self.rows = rows or []
        self.fail = fail
        self.called_with = None

    def execute(self, sql, params=None):
        self.called_with = (sql, params)
        if self.fail:
            raise RuntimeError("db down")
        return self.rows


class TestPostgisAggregation:
    def test_rows_merged_per_cell(self):
        executor = _FakeExecutor(rows=[
            {"latitude": 28.6139, "longitude": 77.2090, "category": "pothole",
             "report_count": 2},
            {"latitude": 28.6139, "longitude": 77.2090, "category": "water_leak",
             "report_count": 1},
            {"latitude": 28.6190, "longitude": 77.2165, "category": "garbage",
             "report_count": 1},
        ])
        result = reports_per_cell_postgis(executor, cell_size_m=200)
        assert result.mode == "postgis"
        assert result.total_reports == 4
        assert result.cell_count() == 2
        top = result.top_cells(1)[0]
        assert top.report_count == 3
        assert top.category_distribution == {"pothole": 2, "water_leak": 1}

    def test_executor_failure_becomes_unavailable(self):
        executor = _FakeExecutor(fail=True)
        result = reports_per_cell_postgis(executor, cell_size_m=200)
        assert result.mode == "unavailable"
        assert result.cell_count() == 0
        assert any("query failed" in b for b in result.basis)

    def test_facade_mode_selection(self):
        memory = DensityAggregator(cell_size_m=200).reports_per_cell(
            [_incident("i1", 28.6139, 77.2090)]
        )
        assert memory.mode == "memory"
        postgis = DensityAggregator(cell_size_m=200, executor=_FakeExecutor()).reports_per_cell()
        assert postgis.mode == "postgis"
        with pytest.raises(ValueError):
            DensityAggregator().reports_per_cell()


class TestQueries:
    def test_reports_per_cell_sql_parameterized(self):
        sql, params = reports_per_cell_sql(cell_size_m=200)
        assert "ST_SnapToGrid" in sql
        assert params["span_deg"] == pytest.approx(200 / 111_320.0)
        assert "%(" in sql

    def test_reports_per_cell_sql_since_and_boundary(self):
        since = datetime(2026, 2, 1, tzinfo=timezone.utc)
        from civitas_geo.boundary import DEFAULT_BOUNDARY

        sql, params = reports_per_cell_sql(cell_size_m=200, since=since,
                                           boundary=DEFAULT_BOUNDARY)
        assert "reported_at >= %(since)s" in sql
        assert "ST_MakeEnvelope" in sql
        assert params["since"] == since


class TestDensityFeatureWiring:
    def test_density_provided(self):
        engine = GeospatialFeatureEngine()
        vector = engine.compute(
            CivicIncidentContext(
                latitude=28.6139, longitude=77.2090, submitted_at=T0,
                category="pothole", cell_report_density=60.0,
            )
        )
        assert vector.features["cell_report_density_norm"] == 1.0
        assert vector.raw["cell_report_density_cell_count"] == 60
        assert "reports-per-cell" in vector.provenance["cell_report_density_norm"]

    def test_density_absent_recorded_not_fabricated(self):
        engine = GeospatialFeatureEngine()
        vector = engine.compute(
            CivicIncidentContext(
                latitude=28.6139, longitude=77.2090, submitted_at=T0, category="pothole",
            )
        )
        assert vector.features["cell_report_density_norm"] == 0.0
        assert "no reports-per-cell" in vector.provenance["cell_report_density_norm"]
        assert vector.raw["cell_report_density_cell_count"] == -1

    def test_compute_for_point_fills_density(self):
        engine = GeospatialFeatureEngine()
        memory = [_incident("i1", 28.61302, 77.20986), _incident("i2", 28.61305, 77.20988)]
        vector = engine.compute_for_point(
            latitude=28.61304, longitude=77.20987, submitted_at=T0,
            category="pothole", memory_incidents=memory,
        )
        assert vector.features["cell_report_density_norm"] == pytest.approx(2 / 50.0)
        assert vector.raw["cell_report_density_cell_count"] == 2