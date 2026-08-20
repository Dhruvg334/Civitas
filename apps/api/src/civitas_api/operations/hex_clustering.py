"""Hexagonal spatial clustering and historical recurrence engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from civitas_geo.hex_index import geo_to_h3, get_hex_neighbors
from civitas_api.operations.reports import get_connection, _is_sqlite


@dataclass(frozen=True)
class HexRecurrenceSummary:
    cell_id: str
    resolution: int
    incident_count_6m: int
    is_chronic_failure_zone: bool
    recurrence_velocity_per_month: float
    neighbor_hotspots_count: int


def calculate_hex_recurrence(
    latitude: float,
    longitude: float,
    resolution: int = 8,
    months_lookback: int = 6,
) -> HexRecurrenceSummary:
    """Analyze historical recurrence rate in the containing hexagonal spatial cell."""
    cell_id = geo_to_h3(latitude, longitude, resolution)  # type: ignore[arg-type]
    cutoff = datetime.now(UTC) - timedelta(days=months_lookback * 30)

    # In SQLite or Postgres, we query nearby incidents within roughly 500m
    lat_delta = 0.005
    lon_delta = 0.005

    incident_count = 0
    with get_connection() as conn, conn.cursor() as cur:
        if _is_sqlite():
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM incidents WHERE reported_at >= ? "
                "AND latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?",
                (
                    cutoff.isoformat(),
                    latitude - lat_delta,
                    latitude + lat_delta,
                    longitude - lon_delta,
                    longitude + lon_delta,
                ),
            )
            res = cur.fetchone()
            if res:
                if isinstance(res, dict):
                    incident_count = res.get("cnt", 0)
                elif hasattr(res, "keys"):
                    incident_count = res["cnt"] if "cnt" in res.keys() else list(res)[0]
                else:
                    incident_count = res[0]
        else:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt FROM incidents
                WHERE reported_at >= %(cutoff)s
                AND ST_DWithin(
                    location_geom::geography,
                    ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography,
                    500
                )
                """,
                {"cutoff": cutoff, "lat": latitude, "lon": longitude},
            )
            res = cur.fetchone()
            if res:
                if isinstance(res, dict):
                    incident_count = res.get("cnt", 0)
                elif hasattr(res, "keys"):
                    incident_count = res["cnt"] if "cnt" in res.keys() else list(res)[0]
                else:
                    incident_count = res[0]

    is_chronic = incident_count >= 4
    velocity = round(incident_count / float(months_lookback), 2)

    return HexRecurrenceSummary(
        cell_id=cell_id,
        resolution=resolution,
        incident_count_6m=incident_count,
        is_chronic_failure_zone=is_chronic,
        recurrence_velocity_per_month=velocity,
        neighbor_hotspots_count=1 if is_chronic else 0,
    )
