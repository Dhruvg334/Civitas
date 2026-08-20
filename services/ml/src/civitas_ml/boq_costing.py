"""Automated Bill of Quantities (BOQ) & Municipal Repair Cost Estimation.

Calculates itemized material quantities (asphalt tonnage, pipe sleeves, aggregate sub-base),
machinery operating hours, and labor costs based on defect metric sizing (cm², mm).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BOQLineItem:
    item_code: str
    description: str
    unit: str
    quantity: float
    unit_rate_inr: float
    total_cost_inr: float


@dataclass(frozen=True)
class BOQEstimate:
    category: str
    defect_area_m2: float
    defect_depth_cm: float
    line_items: list[BOQLineItem]
    subtotal_inr: float
    contingency_inr: float
    total_estimated_cost_inr: float
    total_estimated_cost_usd: float
    estimated_repair_duration_hours: float


def generate_boq_estimate(
    category: str,
    area_cm2: float = 1200.0,
    depth_mm: float = 50.0,
    is_emergency: bool = False,
) -> BOQEstimate:
    """Generates an itemized municipal Bill of Quantities (BOQ) estimate."""
    area_m2 = max(0.1, area_cm2 / 10000.0)
    depth_cm = max(1.0, depth_mm / 10.0)
    volume_m3 = area_m2 * (depth_cm / 100.0)

    cat_norm = category.lower()
    line_items: list[BOQLineItem] = []

    if "pothole" in cat_norm or "road" in cat_norm or "asphalt" in cat_norm:
        # Asphalt density ~ 2.4 tonnes/m3
        asphalt_tonnes = max(0.05, round(volume_m3 * 2.4 * 1.15, 2))  # 15% compaction allowance
        tack_coat_liters = max(1.0, round(area_m2 * 0.75, 1))
        roller_hours = max(1.0, round(area_m2 * 0.25, 1))
        labor_hours = max(2.0, round(area_m2 * 1.5, 1))

        line_items = [
            BOQLineItem(
                item_code="SOR-RDS-101",
                description="Cold Milling & Surface Edge Saw-Cutting (50mm depth)",
                unit="m²",
                quantity=round(area_m2, 2),
                unit_rate_inr=350.0,
                total_cost_inr=round(area_m2 * 350.0, 2),
            ),
            BOQLineItem(
                item_code="SOR-RDS-108",
                description="Bitumen Tack Coat Primer Emulsion (RS-1)",
                unit="liters",
                quantity=tack_coat_liters,
                unit_rate_inr=120.0,
                total_cost_inr=round(tack_coat_liters * 120.0, 2),
            ),
            BOQLineItem(
                item_code="SOR-RDS-204",
                description="Dense Bituminous Macadam (DBM) / Hot Mix Asphalt Compaction",
                unit="tonnes",
                quantity=asphalt_tonnes,
                unit_rate_inr=6500.0,
                total_cost_inr=round(asphalt_tonnes * 6500.0, 2),
            ),
            BOQLineItem(
                item_code="SOR-EQP-012",
                description="Vibratory Road Roller & Compactor Operating Hours",
                unit="hours",
                quantity=roller_hours,
                unit_rate_inr=1800.0,
                total_cost_inr=round(roller_hours * 1800.0, 2),
            ),
            BOQLineItem(
                item_code="SOR-LAB-001",
                description="Skilled Pavement Mason & Labor Crew",
                unit="crew-hours",
                quantity=labor_hours,
                unit_rate_inr=850.0,
                total_cost_inr=round(labor_hours * 850.0, 2),
            ),
        ]
        duration = round(max(2.0, roller_hours + 1.0), 1)

    elif "water" in cat_norm or "leak" in cat_norm or "drainage" in cat_norm:
        excavation_m3 = max(0.5, round(volume_m3 * 3.0, 2))
        dewatering_hours = max(2.0, round(area_m2 * 1.2, 1))

        line_items = [
            BOQLineItem(
                item_code="SOR-WAT-015",
                description="Mechanical Dewatering Submersible Slurry Pump Operation",
                unit="hours",
                quantity=dewatering_hours,
                unit_rate_inr=1400.0,
                total_cost_inr=round(dewatering_hours * 1400.0, 2),
            ),
            BOQLineItem(
                item_code="SOR-WAT-022",
                description="Trench Excavation & Soil Shoring (Up to 1.5m depth)",
                unit="m³",
                quantity=excavation_m3,
                unit_rate_inr=850.0,
                total_cost_inr=round(excavation_m3 * 850.0, 2),
            ),
            BOQLineItem(
                item_code="SOR-WAT-044",
                description="Stainless Steel Ductile Iron Pipe Repair Sleeve Clamp (150mm - 300mm)",
                unit="units",
                quantity=1.0,
                unit_rate_inr=8500.0,
                total_cost_inr=8500.0,
            ),
            BOQLineItem(
                item_code="SOR-WAT-060",
                description="Granular Aggregate Sub-base Backfilling & Compaction",
                unit="m³",
                quantity=excavation_m3,
                unit_rate_inr=1250.0,
                total_cost_inr=round(excavation_m3 * 1250.0, 2),
            ),
            BOQLineItem(
                item_code="SOR-LAB-005",
                description="Certified Master Plumber & Water Pipeline Repair Crew",
                unit="crew-hours",
                quantity=3.5,
                unit_rate_inr=1100.0,
                total_cost_inr=round(3.5 * 1100.0, 2),
            ),
        ]
        duration = 4.5

    elif "streetlight" in cat_norm or "electrical" in cat_norm:
        line_items = [
            BOQLineItem(
                item_code="SOR-ELE-010",
                description="High-Efficiency LED Luminaire Fixture Replacement (90W - 120W)",
                unit="units",
                quantity=1.0,
                unit_rate_inr=4200.0,
                total_cost_inr=4200.0,
            ),
            BOQLineItem(
                item_code="SOR-ELE-018",
                description="Underground Armoured Copper Cable Splicing & Weatherproof Junction",
                unit="meters",
                quantity=5.0,
                unit_rate_inr=320.0,
                total_cost_inr=1600.0,
            ),
            BOQLineItem(
                item_code="SOR-EQP-005",
                description="Hydraulic Aerial Bucket Truck Operating Hours",
                unit="hours",
                quantity=1.5,
                unit_rate_inr=2200.0,
                total_cost_inr=3300.0,
            ),
            BOQLineItem(
                item_code="SOR-LAB-008",
                description="Licensed Electrical Linesman & Helper",
                unit="crew-hours",
                quantity=2.0,
                unit_rate_inr=950.0,
                total_cost_inr=1900.0,
            ),
        ]
        duration = 2.5

    else:
        line_items = [
            BOQLineItem(
                item_code="SOR-GEN-001",
                description="Municipal Rapid Response Inspection & General Clearance Crew",
                unit="crew-hours",
                quantity=2.0,
                unit_rate_inr=750.0,
                total_cost_inr=1500.0,
            ),
            BOQLineItem(
                item_code="SOR-GEN-009",
                description="Consumables, Warning Barricades & Traffic Cones Deployment",
                unit="lot",
                quantity=1.0,
                unit_rate_inr=1200.0,
                total_cost_inr=1200.0,
            ),
        ]
        duration = 2.0

    subtotal = sum(item.total_cost_inr for item in line_items)
    contingency_rate = 0.15 if is_emergency else 0.08
    contingency = round(subtotal * contingency_rate, 2)
    total_inr = round(subtotal + contingency, 2)
    total_usd = round(total_inr / 86.5, 2)  # Current USD/INR conversion rate

    return BOQEstimate(
        category=category,
        defect_area_m2=round(area_m2, 2),
        defect_depth_cm=round(depth_cm, 1),
        line_items=line_items,
        subtotal_inr=subtotal,
        contingency_inr=contingency,
        total_estimated_cost_inr=total_inr,
        total_estimated_cost_usd=total_usd,
        estimated_repair_duration_hours=duration,
    )
