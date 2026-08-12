"""Incidents + geospatial routes for the Civitas backend.

Exposes the four endpoints identified by the integration plan:

    GET /api/v1/incidents/nearby
    GET /api/v1/incidents/{incident_id}/candidates
    GET /api/v1/landmarks/nearby
    GET /api/v1/incidents/nearby/density

All wrapped in the standard success/error envelope.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from civitas_api.core.envelope import error_envelope, success_envelope
from civitas_api.core.spatial import (
    DEFAULT_BOUNDARY,
    GeoPoint,
    get_candidate_retriever,
    get_density_aggregator,
    get_landmark_index,
    get_nearby_retriever,
)
from civitas_api.operations import reports as reports_ops

router = APIRouter(prefix="/api/v1", tags=["incidents"])


def _nearby_result_to_dict(result: Any) -> dict[str, Any]:
    """Convert NearbyIncidentsResult Pydantic model to a dict for the envelope."""
    return result.model_dump(mode="json")


def _candidate_result_to_dict(result: Any) -> dict[str, Any]:
    return result.model_dump(mode="json")


def _density_result_to_dict(result: Any) -> dict[str, Any]:
    return result.model_dump(mode="json")


@router.get("/incidents/nearby")
def incidents_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(500.0, gt=0, le=50_000),
    limit: int = Query(25, ge=1, le=200),
    category: str | None = Query(None),
) -> dict[str, Any]:
    """Return incidents within `radius_m` of (lat, lon), ordered by distance."""
    if lat == 0.0 and lon == 0.0:
        return error_envelope(
            code="LOCATION_PLACEHOLDER",
            message="(0,0) is a placeholder; reject before spatial retrieval.",
            retryable=False,
        )
    retriever = get_nearby_retriever()
    spec = {
        "center": GeoPoint(latitude=lat, longitude=lon),
        "radius_m": radius_m,
        "limit": limit,
        "category_filter": category,
    }
    from civitas_geo.models import SpatialSearchSpec

    result = retriever.retrieve(SpatialSearchSpec(**spec))
    return success_envelope(_nearby_result_to_dict(result))


@router.get("/incidents/{incident_id}/candidates")
def incident_candidates(
    incident_id: str,
    radius_m: float = Query(500.0, gt=0, le=50_000),
    within_hours: float = Query(72.0, gt=0, le=8_760),
    limit: int = Query(25, ge=1, le=200),
    category: str | None = Query(None),
) -> dict[str, Any]:
    """Return candidate incidents for duplicate detection around a given incident."""
    row = reports_ops.get_incident(incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="incident not found")
    lat = float(row["latitude"])
    lon = float(row["longitude"])
    if lat == 0.0 and lon == 0.0:
        return error_envelope(
            code="LOCATION_PLACEHOLDER",
            message="incident has placeholder (0,0) coordinates; refusing spatial scan.",
            retryable=False,
        )
    retriever = get_candidate_retriever()
    from civitas_geo.models import CandidateSearchSpec

    spec = CandidateSearchSpec(
        center=GeoPoint(latitude=lat, longitude=lon),
        radius_m=radius_m,
        within_hours=within_hours,
        limit=limit,
        exclude_incident_ids=[incident_id],
        category_filter=category,
    )
    # When the retriever is in PostGIS mode it goes straight to the DB; in
    # memory mode we hand it the full incidents list read from the DB so the
    # candidate window still works on a sqlite test DB.
    memory_incidents: list[dict[str, Any]] | None = None
    if retriever._executor is None:
        memory_incidents = _all_incidents_for_memory_mode()
    result = retriever.retrieve(
        spec, memory_incidents=memory_incidents, boundary=DEFAULT_BOUNDARY
    )
    return success_envelope(_candidate_result_to_dict(result))


def _all_incidents_for_memory_mode() -> list[dict[str, Any]]:
    """Read all incidents (id, lat, lon, category, reported_at, duplicates_seen)
    for memory-mode candidate retrieval when PostGIS is not available."""
    with reports_ops.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT incident_id, category, reported_at, duplicates_seen, "
                "latitude, longitude "
                "FROM incidents"
            )
            rows = list(cur.fetchall())
    return [dict(r) for r in rows]


@router.get("/landmarks/nearby")
def landmarks_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(2_000.0, gt=0, le=50_000),
    kind: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
) -> dict[str, Any]:
    """Return nearest landmarks within `radius_m` of (lat, lon)."""
    from civitas_geo import distance as geo_dist

    point = GeoPoint(latitude=lat, longitude=lon)
    landmarks = get_landmark_index().landmarks
    out = []
    for lm in landmarks:
        if kind and lm.kind != kind:
            continue
        d = geo_dist.haversine_m(lat, lon, lm.latitude, lm.longitude)
        if d > radius_m:
            continue
        out.append({
            "landmark_id": lm.landmark_id,
            "name": lm.name,
            "kind": lm.kind,
            "latitude": lm.latitude,
            "longitude": lm.longitude,
            "radius_m": lm.radius_m,
            "distance_m": round(d, 2),
        })
    out.sort(key=lambda x: x["distance_m"])
    return success_envelope({"landmarks": out[:limit], "mode": "memory"})


@router.get("/incidents/nearby/density")
def incidents_nearby_density(
    cell_size_m: float = Query(200.0, gt=0, le=5_000),
    within_hours: float | None = Query(None, gt=0, le=8_760),
) -> dict[str, Any]:
    """Return reports-per-cell transactional density aggregate."""
    from datetime import datetime, timedelta, timezone

    from civitas_geo.aggregates import DEFAULT_CELL_SIZE_M

    cell_size = cell_size_m if cell_size_m else DEFAULT_CELL_SIZE_M
    since = None
    if within_hours is not None:
        since = datetime.now(timezone.utc) - timedelta(hours=within_hours)
    aggregator = get_density_aggregator()
    try:
        # In sqlite mode we hand records from the local DB so memory-mode
        # density computation still works.  In PostGIS mode the aggregator
        # queries the DB itself.
        records = None
        if aggregator._executor is None:
            records = _all_incidents_for_memory_mode()
        result = aggregator.reports_per_cell(records=records, since=since)
    except Exception as exc:  # noqa: BLE001 - density is best-effort
        return error_envelope(
            code="DENSITY_UNAVAILABLE",
            message=f"density aggregate failed: {exc}",
            retryable=True,
        )
    return success_envelope(_density_result_to_dict(result))