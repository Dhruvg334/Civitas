"""Reports-per-cell transactional density aggregates (Phase 4).

The density history of a cell is observable: every report that lands inside
a grid cell increments that cell's running report count over the configured
recency window. This module answers "how many reports landed in this cell,
and what is the category mix?" — the transactional analog of the aggregated
terrain fields in the GeoGPT framing, kept strictly observable (never
predicted).

Two modes share one output contract, mirroring the Phase 2 candidate
retrieval stages:

  - "postgis": ST_SnapToGrid grouping executed by a RowExecutor.
  - "memory": identical floor-anchored math offline (tests, local dev,
    fallback). Cell keys match the postgis mode because the grid origin is
    (0, 0) in both.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence

from civitas_geo.boundary import DEFAULT_BOUNDARY
from civitas_geo.candidates import RowExecutor
from civitas_geo.models import (
    DensityAggregateResult,
    DensityCell,
    OperationalBoundary,
)
from civitas_geo.queries import reports_per_cell_sql

DEFAULT_CELL_SIZE_M = 200.0

# Metres per degree of latitude (spherical approximation; documented trade-off
# for the demo grid so SQL and memory modes share one constant).
METRES_PER_DEGREE = 111_320.0


class DensityRecord(Protocol):
    """Minimal report record shape accepted by the memory aggregator."""

    latitude: float
    longitude: float
    category: str | None = None
    reported_at: datetime | None = None


def _cell_span_deg(cell_size_m: float) -> float:
    return cell_size_m / METRES_PER_DEGREE


def _snap(coord: float, span: float) -> float:
    """Round to the nearest grid multiple (same alignment as ST_SnapToGrid)."""
    return math.floor(coord / span + 0.5) * span


def cell_id_for(latitude: float, longitude: float, cell_size_m: float = DEFAULT_CELL_SIZE_M) -> str:
    """Stable cell key: the snapped (lat, lon) anchor pair.

    Deterministic and shared between memory and postgis modes so cell
    histories can be joined across geometry stages.
    """
    span = _cell_span_deg(cell_size_m)
    return f"{_snap(latitude, span):.5f}|{_snap(longitude, span):.5f}"


def _normalize(records: Sequence[Any]) -> list[tuple[float, float, str | None, datetime | None]]:
    """Accept DensityRecord objects or plain dicts (memory-incident rows)."""
    out: list[tuple[float, float, str | None, datetime | None]] = []
    for rec in records:
        if isinstance(rec, Mapping):
            lat, lon = float(rec["latitude"]), float(rec["longitude"])
            cat = rec.get("category")
            reported_at = rec.get("reported_at")
        else:
            lat, lon = float(rec.latitude), float(rec.longitude)
            cat = rec.category
            reported_at = rec.reported_at
        out.append((lat, lon, cat if isinstance(cat, str) else None,
                    reported_at if isinstance(reported_at, datetime) else None))
    return out


def _rows_to_cells(rows: list[dict[str, Any]], cell_span_m: float) -> list[DensityCell]:
    """Merge per-(cell, category) rows into DensityCell records."""
    merged: dict[str, dict[str, Any]] = {}
    for row in rows:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        key = f"{lat:.5f}|{lon:.5f}"
        entry = merged.setdefault(
            key, {"anchor_lat": lat, "anchor_lon": lon, "count": 0, "cats": Counter()}
        )
        n = int(row.get("report_count") or 0)
        entry["count"] += n
        cat = row.get("category")
        if isinstance(cat, str) and n:
            entry["cats"][cat] += n
    cells = [
        DensityCell(
            cell_id=key,
            anchor_lat=entry["anchor_lat"],
            anchor_lon=entry["anchor_lon"],
            center_lat=entry["anchor_lat"] + _cell_span_deg(cell_span_m) / 2.0,
            center_lon=entry["anchor_lon"] + _cell_span_deg(cell_span_m) / 2.0,
            cell_span_m=cell_span_m,
            report_count=entry["count"],
            category_distribution=dict(entry["cats"]),
        )
        for key, entry in merged.items()
    ]
    return sorted(cells, key=lambda c: c.report_count, reverse=True)


def reports_per_cell_postgis(
    executor: RowExecutor,
    cell_size_m: float = DEFAULT_CELL_SIZE_M,
    since: datetime | None = None,
    boundary: OperationalBoundary | None = None,
) -> DensityAggregateResult:
    """PostGIS mode: ST_SnapToGrid grouping over the incidents table."""
    sql, params = reports_per_cell_sql(cell_size_m=cell_size_m, since=since, boundary=boundary)
    try:
        rows = executor.execute(sql, params)
    except Exception as exc:  # noqa: BLE001 - surfaced as unavailable mode, never fabricates data
        return DensityAggregateResult(
            cell_size_m=cell_size_m,
            mode="unavailable",
            basis=[f"postgis query failed: {exc}"],
        )
    cells = _rows_to_cells(rows, cell_size_m)
    window_hours = None
    if since is not None:
        window_hours = max(0.0, (datetime.now(timezone.utc) - _as_utc(since)).total_seconds() / 3600.0)
    return DensityAggregateResult(
        cell_size_m=cell_size_m,
        cells=cells,
        total_reports=sum(c.report_count for c in cells),
        window_hours=window_hours,
        mode="postgis",
        basis=[
            f"ST_SnapToGrid({cell_size_m:.0f} m cells) over PostGIS spheroid"
            + (f", recency {window_hours:.1f} h" if window_hours is not None else ""),
            "geometry provenance: PostGIS",
        ],
    )


def reports_per_cell_memory(
    records: Sequence[DensityRecord | Mapping[str, Any]],
    cell_size_m: float = DEFAULT_CELL_SIZE_M,
    boundary: OperationalBoundary | None = DEFAULT_BOUNDARY,
    since: datetime | None = None,
) -> DensityAggregateResult:
    """Deterministic offline density aggregate with identical cell keys."""
    span = _cell_span_deg(cell_size_m)
    buckets: dict[str, dict[str, Any]] = {}
    skipped_boundary = 0
    skipped_since = 0
    untimestamped_count = 0
    for lat, lon, cat, reported_at in _normalize(records):
        if boundary is not None and not boundary.contains(lat, lon):
            skipped_boundary += 1
            continue
        if since is not None and reported_at is not None and reported_at < since:
            skipped_since += 1
            continue
        if reported_at is None:
            untimestamped_count += 1
        a_lat, a_lon = _snap(lat, span), _snap(lon, span)
        key = f"{a_lat:.5f}|{a_lon:.5f}"
        entry = buckets.setdefault(
            key, {"anchor_lat": a_lat, "anchor_lon": a_lon, "count": 0, "cats": Counter()}
        )
        entry["count"] += 1
        if cat:
            entry["cats"][cat] += 1
    cells = [
        DensityCell(
            cell_id=key,
            anchor_lat=entry["anchor_lat"],
            anchor_lon=entry["anchor_lon"],
            center_lat=entry["anchor_lat"] + span / 2.0,
            center_lon=entry["anchor_lon"] + span / 2.0,
            cell_span_m=cell_size_m,
            report_count=entry["count"],
            category_distribution=dict(entry["cats"]),
        )
        for key, entry in buckets.items()
    ]
    cells.sort(key=lambda c: c.report_count, reverse=True)
    window_hours = None
    if since is not None:
        window_hours = max(0.0, (datetime.now(timezone.utc) - _as_utc(since)).total_seconds() / 3600.0)
    basis = [
        f"floor-anchored grid of {cell_size_m:.0f} m cells over "
        f"{len(records)} incident record(s) (offline mode)"
        + (f", recency window {window_hours:.1f} h" if window_hours is not None else ""),
    ]
    if skipped_boundary:
        basis.append(f"note: {skipped_boundary} record(s) outside the operational boundary were excluded")
    if skipped_since:
        basis.append(f"note: {skipped_since} record(s) older than the recency window were excluded")
    if untimestamped_count:
        basis.append(
            f"note: {untimestamped_count} record(s) had no timestamp; kept in the count"
        )
    return DensityAggregateResult(
        cell_size_m=cell_size_m,
        cells=cells,
        total_reports=sum(c.report_count for c in cells),
        window_hours=window_hours,
        mode="memory",
        basis=basis,
    )


class DensityAggregator:
    """Facade for reports-per-cell density aggregates (Phase 4).

    With an executor configured and no records supplied it queries PostGIS;
    otherwise it runs the deterministic memory scan over the supplied records.
    The result always labels its geometry provenance via `mode`.
    """

    def __init__(
        self,
        cell_size_m: float = DEFAULT_CELL_SIZE_M,
        executor: RowExecutor | None = None,
        boundary: OperationalBoundary | None = DEFAULT_BOUNDARY,
    ) -> None:
        self.cell_size_m = cell_size_m
        self._executor = executor
        self._boundary = boundary

    def reports_per_cell(
        self,
        records: Sequence[DensityRecord | Mapping[str, Any]] | None = None,
        since: datetime | None = None,
    ) -> DensityAggregateResult:
        if self._executor is not None and records is None:
            return reports_per_cell_postgis(
                self._executor,
                cell_size_m=self.cell_size_m,
                since=since,
                boundary=self._boundary,
            )
        if records is None:
            raise ValueError(
                "records are required in memory mode (no executor configured)"
            )
        return reports_per_cell_memory(
            records, cell_size_m=self.cell_size_m, boundary=self._boundary, since=since
        )


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


__all__ = [
    "DEFAULT_CELL_SIZE_M",
    "DensityAggregator",
    "DensityRecord",
    "cell_id_for",
    "reports_per_cell_memory",
    "reports_per_cell_postgis",
]