"""Work Orders Batching, BOQ Costing & Priority Acceleration Router."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from civitas_api.core.envelope import envelope
from civitas_api.operations.crew_batching import batch_work_orders_by_crew_and_spatial_hex
from civitas_api.operations.reports import list_incidents
from civitas_ml.boq_costing import generate_boq_estimate
from civitas_ml.priority_acceleration import evaluate_dynamic_priority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/work-orders", tags=["Work Orders Optimization"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class BOQCalculationRequest(BaseModel):
    category: str = Field(default="water_leakage", description="Incident category")
    defect_area_cm2: float = Field(default=1500.0, ge=10.0, description="Defect surface area in cm²")
    defect_depth_mm: float = Field(default=60.0, ge=1.0, description="Defect depth in mm")
    is_emergency: bool = Field(default=False, description="Emergency contingency multiplier flag")


class PriorityAccelerationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    base_severity: int = Field(default=50, ge=0, le=100)
    base_sla_hours: int = Field(default=24, ge=2, le=168)
    school_distance_m: float | None = Field(default=None, ge=0.0)
    hospital_distance_m: float | None = Field(default=None, ge=0.0)
    transit_distance_m: float | None = Field(default=None, ge=0.0)
    is_arterial_road: bool = Field(default=False)
    is_rush_hour: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/batches")
async def get_work_order_dispatch_batches():
    """Generates optimized spatial work order bundles for municipal crew dispatch."""
    open_incidents = list_incidents(status="in_progress", limit=50)
    if not open_incidents:
        open_incidents = list_incidents(limit=20)

    # Convert incidents to work order format
    work_orders = []
    for inc in open_incidents:
        work_orders.append({
            "work_order_id": f"wo-{inc.get('incident_id', 'demo')}",
            "incident_id": inc.get("incident_id"),
            "assigned_department": inc.get("assigned_department") or "water_supply",
            "category": inc.get("category", "water_leakage"),
            "latitude": inc.get("latitude", 20.29614),
            "longitude": inc.get("longitude", 85.82451),
        })

    bundles = batch_work_orders_by_crew_and_spatial_hex(work_orders)
    return envelope({
        "total_bundles": len(bundles),
        "bundles": [
            {
                "bundle_id": b.bundle_id,
                "crew_type": b.crew_type,
                "target_hex_cell": b.target_hex_cell,
                "work_order_ids": b.work_order_ids,
                "total_duration_hours": b.total_estimated_duration_hours,
                "total_cost_inr": b.total_estimated_cost_inr,
                "total_cost_usd": b.total_estimated_cost_usd,
                "waypoints": b.waypoints,
                "created_at": b.created_at,
            }
            for b in bundles
        ],
    })


@router.post("/boq-estimate")
async def calculate_boq_estimate(req: BOQCalculationRequest):
    """Calculates itemized municipal Bill of Quantities (BOQ) for defect repair."""
    est = generate_boq_estimate(
        category=req.category,
        area_cm2=req.defect_area_cm2,
        depth_mm=req.defect_depth_mm,
        is_emergency=req.is_emergency,
    )
    return envelope({
        "category": est.category,
        "defect_area_m2": est.defect_area_m2,
        "defect_depth_cm": est.defect_depth_cm,
        "subtotal_inr": est.subtotal_inr,
        "contingency_inr": est.contingency_inr,
        "total_estimated_cost_inr": est.total_estimated_cost_inr,
        "total_estimated_cost_usd": est.total_estimated_cost_usd,
        "estimated_duration_hours": est.estimated_repair_duration_hours,
        "line_items": [
            {
                "item_code": item.item_code,
                "description": item.description,
                "unit": item.unit,
                "quantity": item.quantity,
                "unit_rate_inr": item.unit_rate_inr,
                "total_cost_inr": item.total_cost_inr,
            }
            for item in est.line_items
        ],
    })


@router.post("/priority-accelerate")
async def calculate_priority_acceleration(req: PriorityAccelerationRequest):
    """Calculates dynamic priority score and compressed SLA target based on vulnerability factors."""
    res = evaluate_dynamic_priority(
        latitude=req.latitude,
        longitude=req.longitude,
        base_severity=req.base_severity,
        base_sla_hours=req.base_sla_hours,
        school_distance_m=req.school_distance_m,
        hospital_distance_m=req.hospital_distance_m,
        transit_distance_m=req.transit_distance_m,
        is_arterial_road=req.is_arterial_road,
        is_rush_hour=req.is_rush_hour,
    )
    return envelope({
        "base_priority_score": res.base_priority_score,
        "dynamic_priority_score": res.dynamic_priority_score,
        "priority_band": res.priority_band,
        "base_sla_hours": res.base_sla_hours,
        "accelerated_sla_hours": res.accelerated_sla_hours,
        "justification": res.summary_justification,
        "acceleration_factors": [
            {
                "name": f.name,
                "points": f.points,
                "sla_multiplier": f.sla_multiplier,
                "distance_meters": f.distance_meters,
                "description": f.description,
            }
            for f in res.acceleration_factors
        ],
    })
