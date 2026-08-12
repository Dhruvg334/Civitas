"""Report and incident persistence for the Civitas backend.

Persists into the `incidents` table defined by Pavit's migration
`database/migrations/0001_spatial_core.sql`.  The schema is intentionally
minimal:

    incidents(incident_id text PK, category text, reported_at timestamptz,
               duplicates_seen int DEFAULT 1,
               location_geom geometry(Point, 4326) NOT NULL)

We add a `description` column on top so the API can store citizen text.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from civitas_api.core.database import get_connection as _get_connection


def to_json(value: Any) -> str | None:
    """Serialize `value` for a jsonb column. None passes through."""
    if value is None:
        return None
    import json as _json
    return _json.dumps(value, default=str)


def get_connection():
    """Re-export so routers don't import core.database directly."""
    return _get_connection()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def generate_incident_id() -> str:
    """Generate a UUID-shaped incident id (text column)."""
    return f"inc-{uuid4().hex}"


def _normalize_category(citizen_selected: str | None) -> str | None:
    """Map citizen-selected category text to the normalised category the
    geospatial/feature-engineering layer expects."""
    if not citizen_selected:
        return None
    aliases = {
        "pothole": "pothole_road_damage",
        "potholes": "pothole_road_damage",
        "road damage": "pothole_road_damage",
        "water leakage": "water_leakage",
        "water_leakage": "water_leakage",
        "water leak": "water_leakage",
        "road flooding": "water_leakage",
        "flooding": "water_leakage",
        "garbage overflow": "garbage_overflow",
        "garbage": "garbage_overflow",
        "waste": "garbage_overflow",
        "broken streetlight": "broken_streetlight",
        "streetlight": "broken_streetlight",
        "streetlight_night": "broken_streetlight",
        "fallen tree": "fallen_tree",
        "tree": "fallen_tree",
        "blocked pathway": "fallen_tree",
    }
    return aliases.get(citizen_selected.strip().lower(), citizen_selected)


def _is_sqlite() -> bool:
    """True when the configured DB is SQLite (tests or local-dev mode)."""
    from civitas_api.core.config import get_settings
    return get_settings().database_url.startswith("sqlite:///")


def create_incident(
    description: str,
    latitude: float,
    longitude: float,
    citizen_selected_category: str | None,
) -> dict[str, Any]:
    """Persist a new incident. Returns the inserted row as a dict.

    Uses PostGIS SQL when running against PostgreSQL, plain SQL when
    running against SQLite (test mode).
    """
    incident_id = generate_incident_id()
    category = _normalize_category(citizen_selected_category)
    reported_at = _now()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            if _is_sqlite():
                cur.execute(
                    "INSERT INTO incidents "
                    "(incident_id, category, reported_at, duplicates_seen, "
                    "description, latitude, longitude) "
                    "VALUES (?, ?, ?, 1, ?, ?, ?)",
                    (incident_id, category, reported_at.isoformat(),
                     description, latitude, longitude),
                )
                conn.commit()
                row = {
                    "incident_id": incident_id,
                    "category": category,
                    "reported_at": reported_at,
                    "duplicates_seen": 1,
                    "description": description,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            else:
                cur.execute(
                    """
                    INSERT INTO incidents (
                        incident_id, category, reported_at, duplicates_seen,
                        description, location_geom
                    ) VALUES (
                        %(incident_id)s, %(category)s, %(reported_at)s, 1,
                        %(description)s,
                        ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326)
                    )
                    RETURNING incident_id, category, reported_at, duplicates_seen,
                              description,
                              ST_Y(location_geom::geometry) AS latitude,
                              ST_X(location_geom::geometry) AS longitude
                    """,
                    {
                        "incident_id": incident_id,
                        "category": category,
                        "reported_at": reported_at,
                        "description": description,
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                )
                row = cur.fetchone()
                conn.commit()
    if row is None:
        raise RuntimeError("INSERT returned no row")
    return dict(row)


def get_incident(incident_id: str) -> dict[str, Any] | None:
    """Read one incident by id. None if not found."""
    with _get_connection() as conn:
        with conn.cursor() as cur:
            if _is_sqlite():
                cur.execute(
                    "SELECT incident_id, category, reported_at, duplicates_seen, "
                    "description, status, source, status_updated_at, "
                    "last_assessment_model, "
                    "assigned_department, assigned_work_order_id, resolution_class, "
                    "latitude, longitude "
                    "FROM incidents WHERE incident_id = ?",
                    (incident_id,),
                )
            else:
                cur.execute(
                    "SELECT incident_id, category, reported_at, duplicates_seen, "
                    "description, status, source, status_updated_at, "
                    "last_assessment_model, "
                    "assigned_department, assigned_work_order_id, resolution_class, "
                    "ST_Y(location_geom::geometry) AS latitude, "
                    "ST_X(location_geom::geometry) AS longitude "
                    "FROM incidents WHERE incident_id = %(incident_id)s",
                    {"incident_id": incident_id},
                )
            row = cur.fetchone()
    return dict(row) if row else None


def list_incidents(
    status: str | None = None,
    category: str | None = None,
    since: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Paginated list of incidents with optional status / category / since filters."""
    sql = (
        "SELECT incident_id, category, reported_at, duplicates_seen, description, "
        "status, source, status_updated_at, last_assessment_model, "
        "assigned_department, assigned_work_order_id, resolution_class, "
    )
    if _is_sqlite():
        sql += "latitude, longitude "
    else:
        sql += "ST_Y(location_geom::geometry) AS latitude, ST_X(location_geom::geometry) AS longitude "
    sql += "FROM incidents WHERE 1=1"
    params: dict[str, Any] = {"limit": limit}
    if status:
        sql += " AND status = %(status)s"
        params["status"] = status
    if category:
        sql += " AND category = %(cat)s"
        params["cat"] = category
    if since:
        sql += " AND reported_at >= %(since)s"
        params["since"] = since
    sql += " ORDER BY reported_at DESC LIMIT %(limit)s"
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = list(cur.fetchall())
    return [dict(r) for r in rows]


def list_media_for_incident(incident_id: str) -> list[dict[str, Any]]:
    """List media rows for an incident (without signed URLs — those are added
    by the route after storage lookup)."""
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM media WHERE incident_id = %(i)s "
                "ORDER BY uploaded_at ASC",
                {"i": incident_id},
            )
            rows = list(cur.fetchall())
    return [dict(r) for r in rows]

def get_media(media_id: str) -> dict[str, Any] | None:
    """Read one media record by stable media id."""
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM media WHERE media_id = %(m)s", {"m": media_id})
            row = cur.fetchone()
    return dict(row) if row else None
