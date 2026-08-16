"""Tests for PostGIS query builders: parameterization and shape."""

from datetime import datetime, timezone

import pytest
from civitas_geo.models import GeoPoint, SpatialSearchSpec
from civitas_geo.queries import (
    ensure_postgis_sql,
    incident_region_bbox_sql,
    nearby_incidents_sql,
    nearby_landmark_counts_sql,
    nearest_landmarks_sql,
    spatial_clusters_sql,
)

CENTER = GeoPoint(latitude=28.6139, longitude=77.2090)


def test_nearby_incidents_sql_is_parameterized():
    sql, params = nearby_incidents_sql(
        SpatialSearchSpec(center=CENTER, radius_m=500, limit=25)
    )
    assert "%(" in sql  # no f-string interpolation of user data
    assert params["center_lat"] == 28.6139
    assert params["radius_m"] == 500
    assert "ST_DWithin" in sql
    assert "ORDER BY distance_m ASC" in sql


def test_nearby_incidents_sql_excludes_and_filters():
    spec = SpatialSearchSpec(
        center=CENTER,
        radius_m=300,
        limit=10,
        exclude_incident_ids=["i1", "i2"],
        category_filter="pothole",
        since=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    sql, params = nearby_incidents_sql(spec)
    assert "ANY(%(exclude_ids)s)" in sql
    assert "category = %(category)s" in sql
    assert "reported_at >= %(since)s" in sql


def test_nearest_landmarks_sql_kind():
    sql, params = nearest_landmarks_sql(CENTER, kind="school", radius_m=2000, limit=5)
    assert "l.kind = %(kind)s" in sql
    assert params["kind"] == "school"


def test_nearest_landmarks_sql_without_kind():
    sql, _ = nearest_landmarks_sql(CENTER, limit=10)
    assert "l.kind = " not in sql


def test_counts_sql_groups_by_kind():
    sql, _ = nearby_landmark_counts_sql(CENTER)
    assert "GROUP BY l.kind" in sql


def test_spatial_clusters_sql_having():
    sql, params = spatial_clusters_sql(radius_m=150, min_duplicates=2)
    assert "HAVING COUNT(b.incident_id) >= %(min_dups)s" in sql


def test_incident_region_bbox_sql():
    sql, params = incident_region_bbox_sql("inc-1", radius_m=800)
    assert params["incident_id"] == "inc-1"
    assert "ST_Envelope" in sql and "ST_Buffer" in sql


def test_ensure_postgis_sql():
    assert ensure_postgis_sql().startswith("CREATE EXTENSION")


def test_unsafe_identifier_rejected():
    from civitas_geo.queries import _safe_ident

    with pytest.raises(ValueError):
        _safe_ident("incidents; DROP TABLE users;--")
    assert _safe_ident("incidents_geo") == "incidents_geo"