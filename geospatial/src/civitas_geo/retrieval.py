"""Nearby-incident retrieval.

Two modes with identical output contract:
  - "postgis": executes the parameterized spatial queries against PostGIS.
  - "memory": deterministic in-memory scan over incident records (tests, local
    dev, offline fallback). Labeled "memory" in the result so callers know the
    provenance of the geometry stage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from civitas_geo import distance as geo
from civitas_geo.models import (
    GeoPoint,
    NearbyIncident,
    NearbyIncidentsResult,
    SpatialSearchSpec,
)
from civitas_geo.queries import nearby_incidents_sql


class RowExecutor(Protocol):
    """Minimal DB executor interface (psycopg3 cursor or test double)."""

    def execute(self, sql: str, params: dict[str, object] | None = None) -> list[dict[str, Any]]: ...


class IncidentSource(Protocol):
    """In-memory incident records for memory-mode retrieval."""

    def iter_incidents(self) -> list[dict[str, Any]]: ...


def _row_to_incident(row: dict[str, Any], center: GeoPoint) -> NearbyIncident:
    return NearbyIncident(
        incident_id=str(row["incident_id"]),
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        category=row.get("category"),
        distance_m=float(row.get("distance_m") or geo.haversine_m(
            center.latitude, center.longitude, float(row["latitude"]), float(row["longitude"])
        )),
        reported_at=row.get("reported_at"),
        duplicates_seen=int(row.get("duplicates_seen") or 1),
    )


def retrieve_postgis(spec: SpatialSearchSpec, executor: RowExecutor) -> NearbyIncidentsResult:
    sql, params = nearby_incidents_sql(spec)
    rows = executor.execute(sql, params)
    incidents = [_row_to_incident(r, spec.center) for r in rows]
    return NearbyIncidentsResult(
        center=spec.center,
        radius_m=spec.radius_m,
        incidents=incidents,
        total_in_radius=len(incidents),
        mode="postgis",
        basis=[f"ST_DWithin(radius={spec.radius_m:.0f}m) over PostGIS spheroid"],
    )


def retrieve_memory(
    spec: SpatialSearchSpec,
    incidents: list[dict[str, Any]],
    now: datetime | None = None,
) -> NearbyIncidentsResult:
    """Deterministic offline retrieval; incidents listed as report records."""
    now = now or datetime.now(timezone.utc)
    results: list[NearbyIncident] = []
    for rec in incidents:
        if rec.get("incident_id") in spec.exclude_incident_ids:
            continue
        if spec.category_filter and rec.get("category") != spec.category_filter:
            continue
        d = geo.haversine_m(
            spec.center.latitude,
            spec.center.longitude,
            float(rec["latitude"]),
            float(rec["longitude"]),
        )
        if d > spec.radius_m:
            continue
        reported_at = rec.get("reported_at")
        if spec.since is not None:
            if reported_at is None or reported_at < spec.since:
                continue
        results.append(
            NearbyIncident(
                incident_id=str(rec["incident_id"]),
                latitude=float(rec["latitude"]),
                longitude=float(rec["longitude"]),
                category=rec.get("category"),
                distance_m=d,
                reported_at=reported_at,
                duplicates_seen=int(rec.get("duplicates_seen") or 1),
            )
        )
    results.sort(key=lambda i: i.distance_m)
    results = results[: spec.limit]
    return NearbyIncidentsResult(
        center=spec.center,
        radius_m=spec.radius_m,
        incidents=results,
        total_in_radius=len(results),
        mode="memory",
        basis=[f"haversine scan over {len(incidents)} incident records (offline mode)"],
    )


class NearbyRetriever:
    """Retrieval facade that prefers PostGIS when an executor is supplied."""

    def __init__(self, executor: RowExecutor | None = None) -> None:
        self._executor = executor

    def retrieve(
        self,
        spec: SpatialSearchSpec,
        memory_incidents: list[dict[str, Any]] | None = None,
    ) -> NearbyIncidentsResult:
        if self._executor is not None:
            return retrieve_postgis(spec, self._executor)
        if memory_incidents is None:
            memory_incidents = []
        return retrieve_memory(spec, memory_incidents)