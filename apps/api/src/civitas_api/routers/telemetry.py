"""SCADA & Municipal Smart City IoT Telemetry Fusion Router.

Ingests real-time sensor events (water pressure transducers, acoustic leak noise loggers,
power grid telemetry) and correlates sensor spikes with spatial citizen incident clusters.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from civitas_api.core.envelope import envelope
from civitas_api.operations.hex_clustering import calculate_hex_recurrence
from civitas_geo.hex_index import geo_to_h3
from civitas_ml.weather_context import get_weather_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["SCADA & IoT Telemetry"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ScadaTelemetryEvent(BaseModel):
    sensor_id: str = Field(..., description="Unique municipal sensor/transducer ID")
    sensor_type: Literal["water_pressure", "acoustic_leak", "power_grid", "storm_drain", "air_quality"] = Field(
        ...,
        description="Type of municipal transducer",
    )
    reading_value: float = Field(..., description="Measured sensor value")
    threshold_value: float = Field(..., description="Normal operational threshold")
    unit: str = Field(default="psi", description="Engineering unit (psi, dB, kW, mm)")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/scada")
async def ingest_scada_telemetry(event: ScadaTelemetryEvent):
    """Ingests a municipal SCADA / IoT threshold anomaly and computes spatial hex correlation."""
    ref_thresh = max(abs(event.threshold_value), 1.0)
    is_anomaly = abs(event.reading_value - event.threshold_value) > (0.15 * ref_thresh)
    hex_cell = geo_to_h3(event.latitude, event.longitude, 8)  # type: ignore[arg-type]
    recurrence = calculate_hex_recurrence(event.latitude, event.longitude, resolution=8)

    weather = get_weather_context(event.latitude, event.longitude)

    return envelope({
        "sensor_id": event.sensor_id,
        "sensor_type": event.sensor_type,
        "is_anomaly": is_anomaly,
        "hex_cell_id": hex_cell,
        "chronic_failure_zone": recurrence.is_chronic_failure_zone,
        "historical_incident_count_6m": recurrence.incident_count_6m,
        "weather_attribution": weather.summary_note,
        "status": "ANOMALY_CORRELATED" if is_anomaly else "NORMAL_TELEMETRY",
        "ingested_at": datetime.now(UTC).isoformat(),
    })


@router.get("/sensors")
async def list_municipal_sensors(
    sensor_type: str | None = Query(None, description="Filter by sensor type"),
):
    """List active municipal infrastructure telemetry sensors."""
    demo_sensors = [
        {
            "sensor_id": "SCADA-WAT-014",
            "type": "water_pressure",
            "location_name": "Ward 12 Distribution Main Valve V-04",
            "latitude": 20.29614,
            "longitude": 85.82451,
            "current_reading": "28.4 psi (Normal: 45.0 psi)",
            "status": "ALERT_LOW_PRESSURE",
        },
        {
            "sensor_id": "SCADA-DRAIN-008",
            "type": "storm_drain",
            "location_name": "East Gate Culvert Level Sensor",
            "latitude": 20.30150,
            "longitude": 85.83120,
            "current_reading": "88% Capacity",
            "status": "MONITORING",
        },
        {
            "sensor_id": "SCADA-ELEC-102",
            "type": "power_grid",
            "location_name": "Substation 4 Feeder Line",
            "latitude": 20.29180,
            "longitude": 85.82050,
            "current_reading": "220 V (Nominal)",
            "status": "HEALTHY",
        },
    ]
    if sensor_type:
        demo_sensors = [s for s in demo_sensors if s["type"] == sensor_type]
    return envelope(demo_sensors)


@router.get("/hex-density")
async def get_hex_density(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    resolution: int = Query(8, ge=7, le=10),
):
    """Retrieve hexagonal spatial recurrence density and chronic failure status."""
    summary = calculate_hex_recurrence(latitude, longitude, resolution)
    return envelope({
        "cell_id": summary.cell_id,
        "resolution": summary.resolution,
        "incident_count_6m": summary.incident_count_6m,
        "is_chronic_failure_zone": summary.is_chronic_failure_zone,
        "recurrence_velocity_per_month": summary.recurrence_velocity_per_month,
    })
