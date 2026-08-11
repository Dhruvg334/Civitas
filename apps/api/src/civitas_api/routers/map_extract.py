"""Map-link extraction utility route.

    POST /api/v1/map-extract

Accepts a Google Maps or OpenStreetMap share URL and returns the
embedded ``(latitude, longitude)`` pair. The endpoint is open
(no role gate) because it is a pure string-parsing utility — it
does not touch the database, the user record, or any private state.

The extracted coordinates are intended to be passed straight into
POST /api/v1/reports (the existing report submission path) so a
citizen can paste a map link instead of typing coordinates.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from civitas_api.core.envelope import success_envelope
from civitas_api.operations.map_link import MapLinkError, extract_coords

router = APIRouter(prefix="/api/v1", tags=["map-extract"])


@router.post("/map-extract")
def extract_map_coordinates(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parse a map URL and return its embedded coordinates.

    Request:
        ``{"url": "<map URL>"}``

    Success (200):
        ``{"success": true, "data": {"latitude": ..., "longitude": ..., "url": ...}, ...}``

    Errors:
        ``422 MAP_LINK_INVALID`` — url missing / malformed / unsupported pattern
        ``422 MAP_LINK_OUT_OF_RANGE`` — coordinates outside [-90,90] / [-180,180]
    """
    url = (payload or {}).get("url")
    if not isinstance(url, str) or not url.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "payload.url (non-empty string) required",
                "retryable": False,
            },
        )

    try:
        latitude, longitude = extract_coords(url)
    except MapLinkError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message, "retryable": False},
        )

    return success_envelope({
        "latitude": latitude,
        "longitude": longitude,
        "url": url,
    })
