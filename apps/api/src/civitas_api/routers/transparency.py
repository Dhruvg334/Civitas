"""Public Open Data Transparency Router."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Response

from civitas_api.core.envelope import envelope
from civitas_api.operations.transparency import (
    generate_public_csv_export,
    generate_public_geojson_feature_collection,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public Transparency & Open Data"])


@router.get("/incidents.geojson")
async def get_public_incidents_geojson(limit: int = Query(default=200, ge=1, le=1000)):
    """Emits standard RFC 7946 GeoJSON FeatureCollection with differential privacy spatial jitter."""
    data = generate_public_geojson_feature_collection(limit=limit)
    return data


@router.get("/incidents.csv")
async def get_public_incidents_csv(limit: int = Query(default=500, ge=1, le=5000)):
    """Streams sanitized public incident records in CSV format for civic analytics."""
    csv_data = generate_public_csv_export(limit=limit)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=civitas_public_incidents.csv"},
    )
