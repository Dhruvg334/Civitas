"""Phase 6: severity model for the consolidated incident.

Severity answers "how bad is this incident?" for one merged incident —
how dangerous, how harmful. The model is a separate decision from priority
(see `priority_model.py`): severity is about the incident itself, priority
is about how urgently the authority must respond.

Scoring is deterministic and fully explainable: each contributing factor
awards explicit points, and the point total is squashed with diminishing
returns (see `_SEVERITY_SQUASH_SCALE`) so an incident that has every factor
cannot exceed 100. The level bands name the result for a human:
<35 low, 35-59 medium, 60-79 high, >=80 critical.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from civitas_risk.contracts import SeverityLevel
from civitas_risk.incident_features import IncidentFeatures


class SeverityContribution(BaseModel):
    """One named contributing factor with its points and evidence."""

    factor: str
    points: int
    evidence: str


class SeverityAssessment(BaseModel):
    """The severity verdict for one consolidated incident."""

    incident_id: str
    score: int = Field(ge=0, le=100)
    level: SeverityLevel
    contributing_factors: list[SeverityContribution] = Field(default_factory=list)
    model_version: str = "severity-model-v1"


# Base danger of the incident category, scaled to 100 (mirrors the
# Phase 1-3 severity table so both layers tell the same story).
CATEGORY_BASE_POINTS: dict[str, int] = {
    "pothole": 55,
    "water_leak": 50,
    "garbage": 45,
    "streetlight": 35,
    "fallen_tree": 65,
}

UNKNOWN_CATEGORY_POINTS = 45

CATEGORY_ALIASES: dict[str, str] = {
    "water leak": "water_leak",
    "water leakage": "water_leak",
    "flooding": "water_leak",
    "waterlogging": "water_leak",
    "potholes": "pothole",
    "road damage": "pothole",
    "garbage overflow": "garbage",
    "waste": "garbage",
    "street light": "streetlight",
    "streetlights": "streetlight",
    "fallen tree": "fallen_tree",
}

# Points awarded per contributing factor. Every constant is deliberate and
# documented; changing one changes the demo walk-through in
# `ml/demo_end_to_end.py` section 10.
RULE_POINTS = {
    "active_water_flow": 12,
    "significant_coverage": 8,   # water coverage >= 0.30 (affected area)
    "slip_hazard": 5,            # active flow on a road people use
    "school_near": 10,           # within 300 m of a school
    "school_zone": 5,            # within 1 km of a school
    "hospital_near": 4,          # within 500 m of a hospital
    "traffic_high": 7,
    "traffic_moderate": 5,
    "crowd_per_extra_report": 4,  # capped at 9 points
    "duration_per_hour": 2,       # capped at 8 points
    "rain_heavy": 5,              # >= 20 mm/h on a flood-prone category
}

_CROWD_CAP = 9
_DURATION_CAP = 8
_COVERAGE_THRESHOLD = 0.30
_SCHOOL_NEAR_M = 300
_SCHOOL_ZONE_M = 1000
_HOSPITAL_NEAR_M = 500
_RAIN_HEAVY_MM_H = 20.0

# Diminishing-returns squash: score = 100 * (1 - exp(-points / scale)).
# With the demo water-leak scenario totalling 100 points the model lands on
# 78, the HIGH band, with its factors visible one by one.
_SEVERITY_SQUASH_SCALE = 66.0


def severity_level_for(score: int) -> SeverityLevel:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


class SeverityModel:
    """Deterministic severity model; every factor is explainable."""

    model_version = "severity-model-v1"

    def assess(self, features: IncidentFeatures) -> SeverityAssessment:
        contributions: list[SeverityContribution] = []
        points = 0.0

        base = self._category_base(features.category)
        points += base
        contributions.append(
            SeverityContribution(
                factor=f"category base ({features.category})",
                points=base,
                evidence=features.provenance.get("category", f"category base severity for {features.category}"),
            )
        )

        if features.active_water_flow:
            points += RULE_POINTS["active_water_flow"]
            contributions.append(
                SeverityContribution(
                    factor="active road flooding",
                    points=RULE_POINTS["active_water_flow"],
                    evidence=features.provenance.get("active_water_flow", "active water flow observed"),
                )
            )

        if features.water_coverage >= _COVERAGE_THRESHOLD:
            points += RULE_POINTS["significant_coverage"]
            contributions.append(
                SeverityContribution(
                    factor="significant affected area",
                    points=RULE_POINTS["significant_coverage"],
                    evidence=(
                        f"flooded-area share {features.water_coverage:.2f} "
                        f"({features.provenance.get('water_coverage', 'visual coverage')})"
                    ),
                )
            )

        traffic = features.traffic_exposure
        if features.active_water_flow and traffic in ("high", "moderate"):
            points += RULE_POINTS["slip_hazard"]
            contributions.append(
                SeverityContribution(
                    factor="slip hazard",
                    points=RULE_POINTS["slip_hazard"],
                    evidence=(
                        f"active water flow on a road with {traffic} traffic "
                        f"({features.provenance.get('traffic_exposure', 'map reasoning')})"
                    ),
                )
            )

        school = features.school_distance_m
        if school is not None:
            if school <= _SCHOOL_NEAR_M:
                points += RULE_POINTS["school_near"]
                contributions.append(
                    SeverityContribution(
                        factor="near school",
                        points=RULE_POINTS["school_near"],
                        evidence=f"school at {school:.0f} m — children exposure",
                    )
                )
            elif school <= _SCHOOL_ZONE_M:
                points += RULE_POINTS["school_zone"]
                contributions.append(
                    SeverityContribution(
                        factor="school zone",
                        points=RULE_POINTS["school_zone"],
                        evidence=f"school within 1 km ({school:.0f} m)",
                    )
                )

        hospital = features.hospital_distance_m
        if hospital is not None and hospital <= _HOSPITAL_NEAR_M:
            points += RULE_POINTS["hospital_near"]
            contributions.append(
                SeverityContribution(
                    factor="near hospital",
                    points=RULE_POINTS["hospital_near"],
                    evidence=f"hospital at {hospital:.0f} m — emergency access affected",
                )
            )

        if traffic == "high":
            points += RULE_POINTS["traffic_high"]
            contributions.append(
                SeverityContribution(
                    factor="heavy traffic exposure",
                    points=RULE_POINTS["traffic_high"],
                    evidence=features.provenance.get("traffic_exposure", "high traffic"),
                )
            )
        elif traffic == "moderate":
            points += RULE_POINTS["traffic_moderate"]
            contributions.append(
                SeverityContribution(
                    factor="moderate traffic exposure",
                    points=RULE_POINTS["traffic_moderate"],
                    evidence=features.provenance.get("traffic_exposure", "moderate traffic"),
                )
            )

        crowd = min(_CROWD_CAP, RULE_POINTS["crowd_per_extra_report"] * max(0, features.report_count - 1))
        if crowd:
            points += crowd
            contributions.append(
                SeverityContribution(
                    factor="crowd corroboration",
                    points=int(crowd),
                    evidence=features.provenance.get(
                        "report_count", f"{features.report_count} merged report(s)"
                    ),
                )
            )

        duration_pts = min(
            _DURATION_CAP,
            RULE_POINTS["duration_per_hour"] * round(features.duration_hours),
        )
        if duration_pts:
            points += duration_pts
            contributions.append(
                SeverityContribution(
                    factor="protracted exposure",
                    points=int(duration_pts),
                    evidence=features.provenance.get(
                        "duration_hours", f"{features.duration_hours:.1f} h unresolved"
                    ),
                )
            )

        if (features.rain_intensity_mm_h or 0.0) >= _RAIN_HEAVY_MM_H:
            points += RULE_POINTS["rain_heavy"]
            contributions.append(
                SeverityContribution(
                    factor="heavy rain escalation",
                    points=RULE_POINTS["rain_heavy"],
                    evidence=features.provenance.get(
                        "rain_intensity_mm_h", f"{features.rain_intensity_mm_h:.0f} mm/h"
                    ),
                )
            )

        score = int(round(100.0 * (1.0 - math.exp(-points / _SEVERITY_SQUASH_SCALE))))
        return SeverityAssessment(
            incident_id=features.incident_id,
            score=score,
            level=severity_level_for(score),
            contributing_factors=contributions,
            model_version=self.model_version,
        )

    @staticmethod
    def _category_base(category: str) -> int:
        key = category.strip().lower()
        if key in CATEGORY_BASE_POINTS:
            return CATEGORY_BASE_POINTS[key]
        canonical = CATEGORY_ALIASES.get(key, key)
        return CATEGORY_BASE_POINTS.get(canonical, UNKNOWN_CATEGORY_POINTS)