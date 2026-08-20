"""Spatial Work Order Batching & Crew Dispatch Optimizer.

Bundles open work orders within spatial H3 hexagonal neighborhoods by crew specialty
to minimize truck rolls, mobilization overhead, and transit emissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from civitas_geo.hex_index import geo_to_h3
from civitas_ml.boq_costing import generate_boq_estimate


@dataclass(frozen=True)
class WorkOrderDispatchBundle:
    bundle_id: str
    crew_type: str
    target_hex_cell: str
    work_order_ids: list[str]
    total_estimated_duration_hours: float
    total_estimated_cost_inr: float
    total_estimated_cost_usd: float
    waypoints: list[dict[str, Any]]
    created_at: str


def batch_work_orders_by_crew_and_spatial_hex(
    open_work_orders: list[dict[str, Any]],
) -> list[WorkOrderDispatchBundle]:
    """Clusters open work orders by department/crew type and H3 hexagonal cell."""
    if not open_work_orders:
        return []

    # Map department to crew type
    crew_map = {
        "water_supply": "Water Main & Dewatering Specialist Crew",
        "road_maintenance": "Hot-Mix Asphalt & Road Compaction Crew",
        "electrical_engineering": "High-Voltage Linesman & Bucket Truck Crew",
        "solid_waste_management": "Heavy Sanitation & Hydraulic Loader Crew",
        "parks_and_urban_forestry": "Arboriculture & Chainsaw Clearance Crew",
    }

    # Group by (crew_type, hex_cell_8)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for wo in open_work_orders:
        dept = wo.get("assigned_department") or "public_works"
        crew = crew_map.get(dept, "General Municipal Maintenance Crew")
        lat = float(wo.get("latitude", 20.29614))
        lon = float(wo.get("longitude", 85.82451))
        hex_cell = geo_to_h3(lat, lon, 8)  # type: ignore[arg-type]

        key = (crew, hex_cell)
        if key not in groups:
            groups[key] = []
        groups[key].append(wo)

    bundles: list[WorkOrderDispatchBundle] = []
    for idx, ((crew, hex_cell), wos) in enumerate(groups.items(), 1):
        wo_ids = [str(w.get("work_order_id", f"wo-{i}")) for i, w in enumerate(wos)]
        total_dur = 0.0
        total_inr = 0.0
        waypoints = []

        for w in wos:
            cat = w.get("category", "general_hazard")
            boq = generate_boq_estimate(cat)
            total_dur += boq.estimated_repair_duration_hours
            total_inr += boq.total_estimated_cost_inr
            waypoints.append({
                "work_order_id": w.get("work_order_id"),
                "incident_id": w.get("incident_id"),
                "latitude": w.get("latitude", 20.29614),
                "longitude": w.get("longitude", 85.82451),
                "category": cat,
                "estimated_hours": boq.estimated_repair_duration_hours,
            })

        bundles.append(
            WorkOrderDispatchBundle(
                bundle_id=f"BUNDLE-CREW-{idx:03d}",
                crew_type=crew,
                target_hex_cell=hex_cell,
                work_order_ids=wo_ids,
                total_estimated_duration_hours=round(total_dur, 1),
                total_estimated_cost_inr=round(total_inr, 2),
                total_estimated_cost_usd=round(total_inr / 86.5, 2),
                waypoints=waypoints,
                created_at=datetime.now(UTC).isoformat(),
            )
        )

    return bundles
