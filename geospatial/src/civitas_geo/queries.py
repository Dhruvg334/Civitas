"""Parameterized PostGIS query builders.

Every builder returns (sql, params) with all user input bound as parameters
or cast through typed parameters; geometry literals are constructed server
side. No dynamic string interpolation of user values.

Expected schema (see geospatial/README.md for the setup SQL):
    incidents(incident_id text PK, ..., location_geom geometry(Point, 4326),
              reported_at timestamptz, category text, duplicates_seen int)
    landmarks(landmark_id text PK, name text, kind text,
              geom geometry(Point, 4326), radius_m double precision)
    gist indexes on both geometry columns.
"""

from __future__ import annotations

from datetime import datetime

from civitas_geo.models import (
    CandidateSearchSpec,
    GeoPoint,
    OperationalBoundary,
    SpatialSearchSpec,
)


def ensure_postgis_sql() -> str:
    return "CREATE EXTENSION IF NOT EXISTS postgis;"


def bbox_gist_index_sql(table: str = "incidents", geom_column: str = "location_geom") -> str:
    return (
        f"CREATE INDEX IF NOT EXISTS {_safe_ident(table)}_{_safe_ident(geom_column)}_gix "
        f"ON {_safe_ident(table)} USING GIST ({_safe_ident(geom_column)});"
    )


def _safe_ident(name: str) -> str:
    """Validate schema identifiers: allow lowercase alnum and underscore only."""
    if not name or not all(c.isalnum() or c == "_" for c in name):
        raise ValueError(f"unsafe identifier: {name!r}")
    return name


def _bound_geog_param(name: str) -> str:
    return f"ST_SetSRID(ST_MakePoint(%({name}_lon)s, %({name}_lat)s), 4326)::geography"


def nearby_incidents_sql(spec: SpatialSearchSpec) -> tuple[str, dict[str, object]]:
    """Select incidents within radius_m of center, ordered by distance.

    Uses ST_DWithin (geography) for the radius test with a GIST index, plus
    an envelope pre-filter; distance computed as metres on geography.
    """
    params: dict[str, object] = {
        "center_lat": spec.center.latitude,
        "center_lon": spec.center.longitude,
        "radius_m": spec.radius_m,
        "limit": spec.limit,
    }
    filters = [
        f"ST_DWithin(i.location_geom::geography, {_bound_geog_param('center')}, %(radius_m)s)"
    ]
    if spec.exclude_incident_ids:
        params["exclude_ids"] = spec.exclude_incident_ids
        filters.append("i.incident_id = ANY(%(exclude_ids)s) = false")
    if spec.category_filter:
        params["category"] = spec.category_filter
        filters.append("i.category = %(category)s")
    if spec.since is not None:
        params["since"] = spec.since
        filters.append("i.reported_at >= %(since)s")
    return (
        "SELECT i.incident_id, "
        "ST_Y(i.location_geom::geography::geometry) AS latitude, "
        "ST_X(i.location_geom::geography::geometry) AS longitude, "
        "i.category, i.reported_at, i.duplicates_seen, "
        "ST_Distance(i.location_geom::geography, "
        f"{_bound_geog_param('center')}) AS distance_m "
        f"FROM {_safe_ident('incidents')} i "
        "WHERE " + " AND ".join(filters) + " "
        "ORDER BY distance_m ASC LIMIT %(limit)s",
        params,
    )


def candidate_incidents_sql(
    spec: CandidateSearchSpec,
    boundary: OperationalBoundary | None = None,
) -> tuple[str, dict[str, object]]:
    """Candidate-window query for the ML duplicate engine (Phase 2).

    Retrieves incidents within `radius_m` (X metres) that were reported within
    `within_hours` (Y hours), optionally category-filtered, ordered by
    distance. Includes the operational-boundary envelope pre-filter so the
    spatial scan stays inside coverage. All user input is a bound parameter.
    """
    params: dict[str, object] = {
        "center_lat": spec.center.latitude,
        "center_lon": spec.center.longitude,
        "radius_m": spec.radius_m,
        "hours_back": spec.within_hours,
        "limit": spec.limit,
    }
    filters = [
        f"ST_DWithin(i.location_geom::geography, {_bound_geog_param('center')}, %(radius_m)s)",
        "i.reported_at >= now() - make_interval(hours => %(hours_back)s)",
    ]
    if spec.exclude_incident_ids:
        params["exclude_ids"] = spec.exclude_incident_ids
        filters.append("i.incident_id = ANY(%(exclude_ids)s) = false")
    if spec.category_filter:
        params["category"] = spec.category_filter
        filters.append("i.category = %(category)s")
    if boundary is not None:
        min_lat, min_lon, max_lat, max_lon = boundary.bbox
        params.update(
            {
                "b_min_lat": min_lat,
                "b_min_lon": min_lon,
                "b_max_lat": max_lat,
                "b_max_lon": max_lon,
            }
        )
        filters.append(
            "i.location_geom && ST_MakeEnvelope("
            "%(b_min_lon)s, %(b_min_lat)s, %(b_max_lon)s, %(b_max_lat)s, 4326)"
        )
    return (
        "SELECT i.incident_id, "
        "ST_Y(i.location_geom::geography::geometry) AS latitude, "
        "ST_X(i.location_geom::geography::geometry) AS longitude, "
        "i.category, i.reported_at, i.duplicates_seen, "
        "ST_Distance(i.location_geom::geography, "
        f"{_bound_geog_param('center')}) AS distance_m, "
        "EXTRACT(EPOCH FROM (now() - i.reported_at)) / 3600.0 AS hours_since_reported "
        f"FROM {_safe_ident('incidents')} i "
        "WHERE " + " AND ".join(filters) + " "
        "ORDER BY distance_m ASC LIMIT %(limit)s",
        params,
    )


def nearest_landmarks_sql(
    center: GeoPoint,
    radius_m: float = 5_000.0,
    kind: str | None = None,
    limit: int = 10,
) -> tuple[str, dict[str, object]]:
    """Nearest landmarks within radius, ordered by distance (KNN via ORDER BY)."""
    params: dict[str, object] = {
        "center_lat": center.latitude,
        "center_lon": center.longitude,
        "radius_m": radius_m,
        "limit": limit,
    }
    sql = (
        "SELECT l.landmark_id, l.name, l.kind, l.radius_m, "
        "ST_Y(l.geom::geometry) AS latitude, ST_X(l.geom::geometry) AS longitude, "
        "ST_Distance(l.geom::geography, "
        f"{_bound_geog_param('center')}) AS distance_m "
        f"FROM {_safe_ident('landmarks')} l "
        "WHERE ST_DWithin(l.geom::geography, "
        f"{_bound_geog_param('center')}, %(radius_m)s) "
    )
    if kind:
        params["kind"] = kind
        sql += "AND l.kind = %(kind)s "
    sql += "ORDER BY distance_m ASC LIMIT %(limit)s"
    return sql, params


def nearby_landmark_counts_sql(
    center: GeoPoint, radius_m: float = 1_000.0
) -> tuple[str, dict[str, object]]:
    """Per-kind landmark counts inside radius, used for exposure features."""
    params: dict[str, object] = {
        "center_lat": center.latitude,
        "center_lon": center.longitude,
        "radius_m": radius_m,
    }
    return (
        "SELECT l.kind AS kind, COUNT(*) AS n "
        f"FROM {_safe_ident('landmarks')} l "
        "WHERE ST_DWithin(l.geom::geography, "
        f"{_bound_geog_param('center')}, %(radius_m)s) "
        "GROUP BY l.kind",
        params,
    )


def spatial_clusters_sql(
    radius_m: float = 150.0, min_duplicates: int = 2
) -> tuple[str, dict[str, object]]:
    """Candidate duplicate clusters purely from spatial proximity.

    Returns reference incident plus all neighborhoods; the duplicate engine
    re-scores these candidates with text/image/time signals.
    """
    params: dict[str, object] = {"radius_m": radius_m, "min_dups": min_duplicates}
    return (
        "SELECT a.incident_id AS reference_id, "
        "ST_Y(a.location_geom::geography::geometry) AS ref_lat, "
        "ST_X(a.location_geom::geography::geometry) AS ref_lon, "
        "COUNT(b.incident_id) AS neighbours "
        f"FROM {_safe_ident('incidents')} a "
        f"JOIN {_safe_ident('incidents')} b "
        "ON a.incident_id <> b.incident_id "
        "AND ST_DWithin(a.location_geom::geography, b.location_geom::geography, "
        "%(radius_m)s) "
        "GROUP BY a.incident_id, ref_lat, ref_lon "
        "HAVING COUNT(b.incident_id) >= %(min_dups)s",
        params,
    )


def incident_region_bbox_sql(incident_id: str, radius_m: float = 800.0) -> tuple[str, dict[str, object]]:
    """Map-viewport envelope around a single incident (for map reasoning)."""
    params: dict[str, object] = {"incident_id": incident_id, "radius_m": radius_m}
    return (
        "SELECT ST_AsText(ST_Envelope(ST_Buffer("
        f"{_bound_geog_param('center')}::geometry, %(radius_m)s))) AS envelope, "
        "ST_X(ST_Centroid(ST_Envelope(ST_Buffer("
        f"{_bound_geog_param('center')}::geometry, %(radius_m)s)))) AS lon, "
        "ST_Y(ST_Centroid(ST_Envelope(ST_Buffer("
        f"{_bound_geog_param('center')}::geometry, %(radius_m)s)))) AS lat "
        f"FROM {_safe_ident('incidents')} i WHERE i.incident_id = %(incident_id)s",
        params,
    )


def reports_per_cell_sql(
    cell_size_m: float = 200.0,
    since: datetime | None = None,
    boundary: OperationalBoundary | None = None,
) -> tuple[str, dict[str, object]]:
    """Reports-per-cell density aggregate query (Phase 4).

    Groups incidents by ST_SnapToGrid cell of the configured size (degrees =
    metres / 111320 at this latitude) with one row per (cell, category), so
    both the cell count and the per-category distribution come from the same
    geometry. The grid origin is (0, 0) — identical to the memory-mode
    floor-anchored math, so cell_id matches across modes.

    Returns: per (snapped lat, snapped lon, category) count rows; the
    aggregate facade merges them into DensityCell records.
    """
    params: dict[str, object] = {"span_deg": cell_size_m / 111_320.0}
    filters: list[str] = ["i.location_geom IS NOT NULL"]
    if since is not None:
        params["since"] = since
        filters.append("i.reported_at >= %(since)s")
    if boundary is not None:
        min_lat, min_lon, max_lat, max_lon = boundary.bbox
        params.update(
            {
                "b_min_lat": min_lat,
                "b_min_lon": min_lon,
                "b_max_lat": max_lat,
                "b_max_lon": max_lon,
            }
        )
        filters.append(
            "i.location_geom && ST_MakeEnvelope("
            "%(b_min_lon)s, %(b_min_lat)s, %(b_max_lon)s, %(b_max_lat)s, 4326)"
        )
    return (
        "SELECT "
        "ST_Y(ST_SnapToGrid(i.location_geom, %(span_deg)s)) AS latitude, "
        "ST_X(ST_SnapToGrid(i.location_geom, %(span_deg)s)) AS longitude, "
        "i.category AS category, "
        "COUNT(*) AS report_count "
        f"FROM {_safe_ident('incidents')} i "
        "WHERE " + " AND ".join(filters) + " "
        "GROUP BY latitude, longitude, i.category",
        params,
    )