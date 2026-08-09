"""Candidate retrieval for the ML duplicate engine (Phase 2).

Pipeline for every new incident:

    Current report
        |  (location validation gate)
        v
    PostGIS / memory scan
        |  windows: radius X m, recency Y hours, category, boundary
        v
    Nearby reports -> CandidateRecord (enriched with landmark context)
        v
    Candidate list -> ML duplicate engine

Two modes share one output contract:
  - "postgis": parameterized window query executed by a RowExecutor.
  - "memory": deterministic offline scan over incident records (tests, local
    dev, fallback); labeled "memory" so consumers know the geometry
    provenance. Landmark/context enrichment is the same in both modes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from civitas_geo import distance as geo
from civitas_geo.boundary import DEFAULT_BOUNDARY
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import (
    CandidateListResult,
    CandidateRecord,
    CandidateSearchSpec,
    GeoPoint,
    LandmarkDistance,
    OperationalBoundary,
)
from civitas_geo.queries import candidate_incidents_sql

# Kinds the ML models consume for grounding/context; nearest per kind is kept
# on each candidate so duplicate and exposure features never re-query.
CONTEXT_KINDS: tuple[str, ...] = (
    "school", "hospital", "junction", "market", "park", "waterbody",
    "metro_station", "pathway",
)


class RowExecutor(Protocol):
    """Minimal DB executor interface (psycopg3 cursor or test double)."""

    def execute(self, sql: str, params: dict[str, object] | None = None) -> list[dict[str, Any]]: ...


def _row_to_candidate(
    row: dict[str, Any], center: GeoPoint, within_hours: float
) -> CandidateRecord:
    hours_since = row.get("hours_since_reported")
    return CandidateRecord(
        incident_id=str(row["incident_id"]),
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        category=row.get("category"),
        distance_m=float(row.get("distance_m") or geo.haversine_m(
            center.latitude, center.longitude, float(row["latitude"]), float(row["longitude"])
        )),
        reported_at=row.get("reported_at"),
        duplicates_seen=int(row.get("duplicates_seen") or 1),
        hours_since_reported=float(hours_since) if hours_since is not None else None,
        within_time_window=(hours_since is None) or (float(hours_since) <= within_hours),
    )


def enrich_landmark_context(
    candidates: list[CandidateRecord],
    landmarks: LandmarkIndex,
    kinds: tuple[str, ...] = CONTEXT_KINDS,
    max_distance_m: float = 1_500.0,
) -> list[CandidateRecord]:
    """Attach nearest landmark per context kind to every candidate.

    Deterministic and side-effect free; runs in both postgis and memory modes
    so downstream models see identical context regardless of geometry stage.
    """
    enriched: list[CandidateRecord] = []
    for cand in candidates:
        point = GeoPoint(latitude=cand.latitude, longitude=cand.longitude)
        ctx: list[LandmarkDistance] = []
        for kind in kinds:
            nearest = landmarks.nearest(point, kind=kind, max_distance_m=max_distance_m)
            if nearest is not None:
                ctx.append(nearest)
        ctx.sort(key=lambda d: d.distance_m)
        enriched.append(cand.model_copy(update={"landmark_context": ctx}))
    return enriched


def retrieve_candidates_postgis(
    spec: CandidateSearchSpec,
    executor: RowExecutor,
    landmarks: LandmarkIndex,
    boundary: OperationalBoundary | None = None,
) -> CandidateListResult:
    sql, params = candidate_incidents_sql(spec, boundary=boundary)
    rows = executor.execute(sql, params)
    candidates = [_row_to_candidate(r, spec.center, spec.within_hours) for r in rows]
    candidates = enrich_landmark_context(candidates, landmarks)
    return CandidateListResult(
        center=spec.center,
        radius_m=spec.radius_m,
        within_hours=spec.within_hours,
        candidates=candidates,
        total_in_window=len(candidates),
        mode="postgis",
        boundary=boundary,
        basis=[
            f"ST_DWithin(radius={spec.radius_m:.0f}m) + recency {spec.within_hours:g}h "
            "over PostGIS spheroid",
            "landmark context from PostGIS landmark rows",
        ],
    )


def retrieve_candidates_memory(
    spec: CandidateSearchSpec,
    incidents: list[dict[str, Any]],
    landmarks: LandmarkIndex,
    boundary: OperationalBoundary | None = None,
    now: datetime | None = None,
) -> CandidateListResult:
    """Deterministic offline candidate retrieval with identical windows."""
    now = now or datetime.now(timezone.utc)
    reference = now - timedelta(hours=spec.within_hours)
    results: list[CandidateRecord] = []
    untimestamped_included = 0
    for rec in incidents:
        if rec.get("incident_id") in spec.exclude_incident_ids:
            continue
        if spec.category_filter and rec.get("category") != spec.category_filter:
            continue
        lat, lon = float(rec["latitude"]), float(rec["longitude"])
        if boundary is not None and not boundary.contains(lat, lon):
            continue
        d = geo.haversine_m(spec.center.latitude, spec.center.longitude, lat, lon)
        if d > spec.radius_m:
            continue
        reported_at = rec.get("reported_at")
        if isinstance(reported_at, datetime):
            if reported_at.tzinfo is None:
                reported_at = reported_at.replace(tzinfo=timezone.utc)
            hours_since = (now - reported_at).total_seconds() / 3600.0
            if reported_at < reference:
                continue
        else:
            hours_since = None
            untimestamped_included += 1
        results.append(
            CandidateRecord(
                incident_id=str(rec["incident_id"]),
                latitude=lat,
                longitude=lon,
                category=rec.get("category"),
                distance_m=d,
                reported_at=reported_at,
                duplicates_seen=int(rec.get("duplicates_seen") or 1),
                hours_since_reported=hours_since,
                within_time_window=hours_since is None or hours_since <= spec.within_hours,
            )
        )
    results.sort(key=lambda c: c.distance_m)
    results = results[: spec.limit]
    results = enrich_landmark_context(results, landmarks)
    basis = [
        f"haversine scan over {len(incidents)} incident records: "
        f"radius {spec.radius_m:.0f}m, recency {spec.within_hours:g}h "
        f"(offline mode)",
        "landmark context from LandmarkIndex",
    ]
    if untimestamped_included:
        basis.append(
            f"note: {untimestamped_included} record(s) lacked timestamps and were "
            "kept (recency window not enforced on them)"
        )
    return CandidateListResult(
        center=spec.center,
        radius_m=spec.radius_m,
        within_hours=spec.within_hours,
        candidates=results,
        total_in_window=len(results),
        mode="memory",
        boundary=boundary,
        basis=basis,
    )


class CandidateRetriever:
    """Retrieval facade for the duplicate engine's spatial stage.

    Prefers PostGIS when an executor is supplied; otherwise falls back to the
    deterministic memory scan. The caller decides which boundary applies; the
    default is the demo-city boundary.
    """

    def __init__(self, executor: RowExecutor | None = None) -> None:
        self._executor = executor

    def retrieve(
        self,
        spec: CandidateSearchSpec,
        memory_incidents: list[dict[str, Any]] | None = None,
        landmarks: LandmarkIndex | None = None,
        boundary: OperationalBoundary | None = DEFAULT_BOUNDARY,
        now: datetime | None = None,
    ) -> CandidateListResult:
        landmark_index = landmarks or LandmarkIndex()
        if self._executor is not None:
            return retrieve_candidates_postgis(spec, self._executor, landmark_index, boundary)
        return retrieve_candidates_memory(spec, memory_incidents or [], landmark_index, boundary, now)


__all__ = [
    "CONTEXT_KINDS",
    "CandidateRetriever",
    "RowExecutor",
    "enrich_landmark_context",
    "retrieve_candidates_memory",
    "retrieve_candidates_postgis",
]