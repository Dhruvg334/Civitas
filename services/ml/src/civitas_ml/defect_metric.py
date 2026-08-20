"""Automated Defect Polygon Metric Sizing & Pavement Condition Index (PCI) Rating.

Estimates defect geometric area (cm²), depth (mm), and infrastructure distress
deductions based on computer vision feature extractions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DistressSeverity = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class DefectMetricEvaluation:
    category: str
    estimated_area_cm2: float
    estimated_depth_mm: float
    distress_level: DistressSeverity
    pci_deduction_score: float
    infrastructure_health_index: float  # 0 to 100
    recommended_patch_type: str


def evaluate_defect_metrics(
    category: str,
    visual_features: list[str] | None = None,
    bounding_box_ratio: float = 0.25,
) -> DefectMetricEvaluation:
    """Computes geometric defect sizing and Pavement Condition Index (PCI) distress score."""
    features = [f.lower() for f in (visual_features or [])]
    norm_cat = category.lower()

    # Base estimates
    area_cm2 = max(100.0, bounding_box_ratio * 4000.0)
    depth_mm = 20.0
    patch_type = "Standard Surface Seal"

    cat_tokens = set(norm_cat.replace("-", "_").split("_"))

    if "pothole" in cat_tokens or "road" in cat_tokens or "asphalt" in cat_tokens:
        if any("deep" in f or "cavity" in f or "severe" in f for f in features):
            depth_mm = 75.0
            area_cm2 = max(800.0, area_cm2 * 2.2)
            distress: DistressSeverity = "high"
            deduction = 45.0
            patch_type = "Hot-Mix Asphalt Full-Depth Patch"
        elif any("crack" in f or "fissure" in f for f in features):
            depth_mm = 30.0
            distress = "medium"
            deduction = 22.0
            patch_type = "Cold-Pour Crack Seal & Compact"
        else:
            distress = "low"
            deduction = 12.0
            patch_type = "Cold-Mix Surface Infill"

    elif "water" in cat_tokens or "leakage" in cat_tokens or "flood" in cat_tokens or "drainage" in cat_tokens:
        if any("burst" in f or "submerged" in f or "ponding" in f for f in features):
            depth_mm = 120.0
            area_cm2 = max(2500.0, area_cm2 * 4.0)
            distress = "critical"
            deduction = 60.0
            patch_type = "Ductile Iron Pipe Sleeve + Road Sub-base Reconstruction"
        else:
            depth_mm = 40.0
            distress = "medium"
            deduction = 25.0
            patch_type = "Grate Clearing & Localized Excavation"

    elif "tree" in cat_tokens or "branch" in cat_tokens or "forestry" in cat_tokens:
        distress = "high" if any("blocked" in f or "down" in f for f in features) else "medium"
        deduction = 35.0 if distress == "high" else 15.0
        patch_type = "Hydraulic Chainsaw Crew + Debris Loader"

    elif "streetlight" in cat_tokens or "light" in cat_tokens or "pole" in cat_tokens:
        distress = "high" if any("wire" in f or "exposed" in f for f in features) else "low"
        deduction = 30.0 if distress == "high" else 10.0
        patch_type = "Bucket Truck Luminaire / Wiring Replacement"

    else:
        distress = "low"
        deduction = 10.0
        patch_type = "District Inspection & General Maintenance"

    health_index = max(0.0, min(100.0, 100.0 - deduction))

    return DefectMetricEvaluation(
        category=category,
        estimated_area_cm2=round(area_cm2, 1),
        estimated_depth_mm=round(depth_mm, 1),
        distress_level=distress,
        pci_deduction_score=round(deduction, 1),
        infrastructure_health_index=round(health_index, 1),
        recommended_patch_type=patch_type,
    )
