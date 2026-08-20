"""Dynamic Vulnerability, Traffic Exposure & SLA Acceleration Engine.

Evaluates spatial proximity to schools, hospitals, transit corridors, and peak
traffic hours to accelerate response priority and compress statutory SLA windows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AccelerationFactor:
    name: str
    points: int
    sla_multiplier: float
    distance_meters: float | None
    description: str


@dataclass(frozen=True)
class DynamicPriorityResult:
    base_priority_score: int
    dynamic_priority_score: int
    priority_band: str  # "P1_CRITICAL", "P2_HIGH", "P3_MODERATE", "P4_LOW"
    base_sla_hours: int
    accelerated_sla_hours: int
    acceleration_factors: list[AccelerationFactor]
    summary_justification: str


def evaluate_dynamic_priority(
    latitude: float,
    longitude: float,
    base_severity: int = 50,
    base_sla_hours: int = 24,
    school_distance_m: float | None = None,
    hospital_distance_m: float | None = None,
    transit_distance_m: float | None = None,
    is_arterial_road: bool = False,
    is_rush_hour: bool = False,
) -> DynamicPriorityResult:
    """Computes dynamic priority score and accelerated SLA target."""
    score = base_severity
    factors: list[AccelerationFactor] = []
    combined_multiplier = 1.0

    # 1. School proximity buffer (≤ 100m)
    if school_distance_m is not None and school_distance_m <= 100.0:
        pts = 25
        mult = 0.5
        score += pts
        combined_multiplier *= mult
        factors.append(
            AccelerationFactor(
                name="VULNERABLE_SCHOOL_ZONE",
                points=pts,
                sla_multiplier=mult,
                distance_meters=round(school_distance_m, 1),
                description=f"Located {round(school_distance_m)}m from school gate; high pedestrian child traffic.",
            )
        )

    # 2. Hospital / Emergency Route proximity buffer (≤ 250m)
    if hospital_distance_m is not None and hospital_distance_m <= 250.0:
        pts = 30
        mult = 0.4
        score += pts
        combined_multiplier *= mult
        factors.append(
            AccelerationFactor(
                name="HOSPITAL_EMERGENCY_CORRIDOR",
                points=pts,
                sla_multiplier=mult,
                distance_meters=round(hospital_distance_m, 1),
                description=f"Located {round(hospital_distance_m)}m from hospital/trauma center ambulance route.",
            )
        )

    # 3. Transit Hub proximity buffer (≤ 150m)
    if transit_distance_m is not None and transit_distance_m <= 150.0:
        pts = 20
        mult = 0.6
        score += pts
        combined_multiplier *= mult
        factors.append(
            AccelerationFactor(
                name="MASS_TRANSIT_HUB",
                points=pts,
                sla_multiplier=mult,
                distance_meters=round(transit_distance_m, 1),
                description=f"Located {round(transit_distance_m)}m from metro/bus terminal.",
            )
        )

    # 4. Arterial Major Roadway
    if is_arterial_road:
        pts = 15
        mult = 0.7
        score += pts
        combined_multiplier *= mult
        factors.append(
            AccelerationFactor(
                name="ARTERIAL_HIGH_VOLUME_ROAD",
                points=pts,
                sla_multiplier=mult,
                distance_meters=None,
                description="Located on high-capacity arterial thoroughfare.",
            )
        )

    # 5. Rush Hour traffic condition
    if is_rush_hour:
        pts = 10
        score += pts
        factors.append(
            AccelerationFactor(
                name="PEAK_RUSH_HOUR",
                points=pts,
                sla_multiplier=0.9,
                distance_meters=None,
                description="Active peak commuter traffic window.",
            )
        )

    final_score = min(100, score)

    # Calculate accelerated SLA (clamped to minimum 2 hours)
    acc_sla = max(2, int(math.ceil(base_sla_hours * combined_multiplier)))

    # Priority bands
    if final_score >= 80:
        band = "P1_CRITICAL"
    elif final_score >= 60:
        band = "P2_HIGH"
    elif final_score >= 40:
        band = "P3_MODERATE"
    else:
        band = "P4_LOW"

    justification = (
        f"Dynamic priority escalated to {final_score}/100 ({band}) with SLA accelerated from "
        f"{base_sla_hours}h to {acc_sla}h due to {len(factors)} spatial/vulnerability factors."
        if factors
        else f"Standard baseline priority of {final_score}/100 ({band}) with {base_sla_hours}h SLA."
    )

    return DynamicPriorityResult(
        base_priority_score=base_severity,
        dynamic_priority_score=final_score,
        priority_band=band,
        base_sla_hours=base_sla_hours,
        accelerated_sla_hours=acc_sla,
        acceleration_factors=factors,
        summary_justification=justification,
    )
