"""Open311 GeoReport v2 Standard API Adapter for Civitas.

Implements the open municipal standard GeoReport v2 specification for
interoperability with municipal 311 systems, mobile reporting apps,
and civic tech portals.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Query, Request
from pydantic import BaseModel, Field

from civitas_api.operations.reports import create_incident, get_incident

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/open311/v2", tags=["Open311 GeoReport v2"])

# Standard Open311 Service Definition Catalog
OPEN311_SERVICES = [
    {
        "service_code": "001",
        "service_name": "Pothole and Road Damage",
        "description": "Potholes, surface cracks, road subsidence, and pavement cavities.",
        "metadata": True,
        "type": "realtime",
        "keywords": "pothole,road,asphalt,cavity,subsidence",
        "group": "Infrastructure & Transportation",
    },
    {
        "service_code": "002",
        "service_name": "Water Main Leakage & Drainage",
        "description": "Active pipe rupture, standing water, inlet grate obstruction, or sewer overflow.",
        "metadata": True,
        "type": "realtime",
        "keywords": "water,leak,flooding,pipe,drainage,sewer",
        "group": "Water Supply & Public Works",
    },
    {
        "service_code": "003",
        "service_name": "Streetlight Malfunction",
        "description": "Non-functional luminaire, exposed electrical wiring, or broken pole.",
        "metadata": True,
        "type": "realtime",
        "keywords": "streetlight,light,electricity,pole,darkness",
        "group": "Electrical & Energy",
    },
    {
        "service_code": "004",
        "service_name": "Fallen Tree & Pathway Obstruction",
        "description": "Fallen trees, dangerous hanging limbs, or blocked pedestrian sidewalks.",
        "metadata": True,
        "type": "realtime",
        "keywords": "tree,branch,sidewalk,obstruction,hazard",
        "group": "Parks & Urban Forestry",
    },
    {
        "service_code": "005",
        "service_name": "Solid Waste & Illegal Dumping",
        "description": "Overflowing public waste bin or illegal trash dumping.",
        "metadata": True,
        "type": "realtime",
        "keywords": "garbage,waste,dumping,trash,sanitation",
        "group": "Solid Waste & Sanitation",
    },
]

SERVICE_CODE_MAP = {
    "001": "pothole_road_damage",
    "002": "water_leakage",
    "003": "broken_streetlight",
    "004": "fallen_tree",
    "005": "garbage_overflow",
}


@router.get("/services.json")
async def list_open311_services():
    """List available Open311 civic service categories."""
    return OPEN311_SERVICES


@router.post("/requests.json")
async def submit_open311_request(
    service_code: str = Form(...),
    lat: float = Form(20.29614),
    long: float = Form(85.82451),
    address_string: str = Form(""),
    description: str = Form(""),
    first_name: str = Form(""),
    last_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    media_url: str = Form(""),
):
    """Submit a civic incident request conforming to Open311 GeoReport v2."""
    category = SERVICE_CODE_MAP.get(service_code, "general_hazard")
    full_desc = description.strip()
    if not full_desc:
        full_desc = f"Open311 {category} report"
        if address_string:
            full_desc += f" at {address_string}"

    inc = create_incident(
        description=full_desc,
        latitude=lat,
        longitude=long,
        citizen_selected_category=category,
    )

    # Format standard Open311 response array
    return [
        {
            "service_request_id": inc["incident_id"],
            "status": "open",
            "status_notes": "Queued for multimodal verification and municipal dispatch.",
            "service_name": next((s["service_name"] for s in OPEN311_SERVICES if s["service_code"] == service_code), "General Hazard"),
            "service_code": service_code,
            "description": full_desc,
            "agency_responsible": "Municipal Dispatch Center",
            "service_notice": "Report registered in Civitas PostGIS spatial repository.",
            "requested_datetime": datetime.now(UTC).isoformat(),
            "updated_datetime": datetime.now(UTC).isoformat(),
            "expected_datetime": None,
            "address": address_string,
            "lat": lat,
            "long": long,
            "media_url": media_url or None,
        }
    ]


@router.get("/requests/{service_request_id}.json")
async def get_open311_request(service_request_id: str):
    """Retrieve the status of a previously submitted Open311 request."""
    row = get_incident(service_request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Service request ID not found")

    status_val = row.get("status") or "open"
    return [
        {
            "service_request_id": row["incident_id"],
            "status": "open" if status_val in ("submitted", "in_progress", "open") else "closed",
            "status_notes": f"Current status: {status_val}",
            "service_code": "002" if row.get("category") == "water_leakage" else "001",
            "description": row.get("description", ""),
            "requested_datetime": row["reported_at"].isoformat() if hasattr(row["reported_at"], "isoformat") else str(row["reported_at"]),
            "updated_datetime": datetime.now(UTC).isoformat(),
            "lat": row.get("latitude", 20.29614),
            "long": row.get("longitude", 85.82451),
        }
    ]
