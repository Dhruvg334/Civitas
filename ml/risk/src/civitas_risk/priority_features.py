"""Phase 7: priority feature engineering for the consolidated incident.

Priority asks the operational question the severity model never answers:
"how urgently should the municipality respond?" It needs its OWN feature
vector — the same raw facts (school at 37 m, 3 reports, 1.2 h) become
different engineered signals when the decision is "how fast must a crew
get there" instead of "how bad is the damage".

Ten signals, each normalized to [0, 1] with a provenance string (the
GeoGPT-style approach: spatial and physical characteristics become
engineered ML features, then a weighted model produces the risk verdict —
here the "risk" is municipal urgency):

1. severity             — the Phase 6 verdict (how bad the incident is)
2. school_proximity     — children on the street right now
3. hospital_proximity   — emergency-corridor interference
4. traffic_exposure     — how many people are stuck in it
5. population_exposure  — how many people live/work around it
6. repeated_reports     — how many citizens confirm it independently
7. incident_duration    — how long it has been allowed to fester
8. nearby_density       — how unusual this neighbourhood pressure is
9. category_urgency     — how fast this incident class escalates
10. time_sensitivity    — what the street looks like at this hour

Missing inputs are recorded as absent (neutral signal + provenance note),
never guessed.
"""

from __future__ import annotations

import math
from datetime import datetime, time as dt_time

from pydantic import BaseModel, Field

from civitas_risk.incident_features import ConsolidatedIncident

# Normalized category urgency: how quickly this incident class escalates
# toward harm (public health, flooding, structural failure).
CATEGORY_URGENCY: dict[str, float] = {
    "pothole": 0.4,
    "water_leak": 0.6,
    "garbage": 0.8,
    "streetlight": 0.2,
    "fallen_tree": 0.5,
}

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

UNKNOWN_CATEGORY_URGENCY = 0.4

_SCHOOL_NEAR_M = 300
_SCHOOL_ZONE_M = 1000
_HOSPITAL_NEAR_M = 500
_HOSPITAL_ZONE_M = 2000
_RAIN_HEAVY_MM_H = 20.0


def category_urgency_signal(category: str) -> tuple[float, str]:
    """How fast this incident class escalates toward harm."""
    key = category.strip().lower()
    canonical = CATEGORY_ALIASES.get(key, key)
    if canonical not in CATEGORY_URGENCY:
        return UNKNOWN_CATEGORY_URGENCY, (
            f"category '{category}' not in urgency table -> neutral {UNKNOWN_CATEGORY_URGENCY:.1f}"
        )
    return CATEGORY_URGENCY[canonical], (
        f"category urgency {CATEGORY_URGENCY[canonical]:.1f} ({canonical})"
    )


def time_sensitivity_signal(
    current_time: datetime | None,
    rain_intensity_mm_h: float | None = None,
) -> tuple[float, str]:
    """Street occupancy at this hour (daytime peak vs night), plus rain escalation.

    Weekday-agnostic: band 07:00-19:00 is peak activity regardless of the
    calendar, so no school-holiday or weekend assumptions are baked in.
    """
    if current_time is None:
        return 0.5, "time of day unknown -> neutral 0.5"
    hour = current_time.time()
    if dt_time(7, 0) <= hour <= dt_time(19, 0):
        signal = 0.8
        basis = f"{hour.strftime('%H:%M')} — daytime peak activity window"
    elif dt_time(19, 0) < hour <= dt_time(22, 0):
        signal = 0.4
        basis = f"{hour.strftime('%H:%M')} — evening hours"
    else:
        signal = 0.2
        basis = f"{hour.strftime('%H:%M')} — night hours"
    if rain_intensity_mm_h is not None and rain_intensity_mm_h >= _RAIN_HEAVY_MM_H:
        signal = min(1.0, signal + 0.2)
        basis += f" + heavy rain {rain_intensity_mm_h:.0f} mm/h escalation"
    return round(signal, 4), basis


class PriorityContext(BaseModel):
    """Everything the priority feature engineer needs (all observable)."""

    incident: ConsolidatedIncident
    severity_score: int = Field(ge=0, le=100)
    population_density_proxy: float | None = Field(default=None, ge=0, le=1)
    nearby_density_norm: float | None = Field(default=None, ge=0, le=1)
    current_time: datetime | None = None


class PriorityFeatures(BaseModel):
    """Typed priority feature vector (evidence only, one incident).

    All signals normalized [0, 1] except `severity_score` (0-100, the Phase 6
    verdict). `provenance[signal]` explains the value in human terms.
    """

    incident_id: str
    severity_score: int = Field(ge=0, le=100)
    school_proximity: float = Field(default=0.0, ge=0, le=1)
    hospital_proximity: float = Field(default=0.0, ge=0, le=1)
    traffic_exposure: float = Field(default=0.0, ge=0, le=1)
    population_exposure: float = Field(default=0.0, ge=0, le=1)
    repeated_reports: float = Field(default=0.0, ge=0, le=1)
    incident_duration: float = Field(default=0.0, ge=0, le=1)
    nearby_density: float = Field(default=0.0, ge=0, le=1)
    category_urgency: float = Field(default=0.0, ge=0, le=1)
    time_sensitivity: float = Field(default=0.5, ge=0, le=1)
    provenance: dict[str, str] = Field(default_factory=dict)


def build_priority_features(context: PriorityContext) -> PriorityFeatures:
    """Engineer the ten priority signals from the consolidated incident.

    Reuses the same raw facts as severity feature engineering (same
    `ConsolidatedIncident`), because the facts do not change — the question
    does. Every signal cites where it came from.
    """
    incident = context.incident
    provenance: dict[str, str] = {}

    provenance["severity_score"] = (
        f"severity model verdict {context.severity_score}/100 for {incident.incident_id}"
    )

    school, school_hospital_basis = _proximity_signals(incident)
    school_sig, school_basis = school
    hospital_sig, hospital_basis = school_hospital_basis
    provenance["school_proximity"] = school_basis
    provenance["hospital_proximity"] = hospital_basis

    if incident.exposure is not None:
        traffic_sig = {"high": 1.0, "moderate": 0.5, "low": 0.0}.get(
            incident.exposure.traffic_exposure, 0.0
        )
        provenance["traffic_exposure"] = (
            f"map reasoning: {incident.exposure.traffic_exposure} traffic "
            f"(junction density {incident.exposure.junction_density_1km:.2f}/km2)"
        )
    else:
        traffic_sig = 0.0
        provenance["traffic_exposure"] = "no geospatial exposure computed -> neutral 0"

    if context.population_density_proxy is not None:
        population_sig = max(0.0, min(1.0, context.population_density_proxy))
        provenance["population_exposure"] = (
            f"geospatial proxy: population density {population_sig:.2f}"
        )
    else:
        population_sig = 0.0
        provenance["population_exposure"] = "population proxy not computed -> neutral 0"

    reports_sig = 1.0 - math.exp(-max(0, incident.report_count - 1) / 2.0)
    provenance["repeated_reports"] = (
        f"{incident.report_count} merged report(s) -> independent-pressure {reports_sig:.2f}"
    )

    duration_sig = math.tanh(incident.duration_hours / 24.0)
    provenance["incident_duration"] = (
        f"{incident.duration_hours:.2f} h unresolved -> pressure {duration_sig:.2f}"
    )

    if context.nearby_density_norm is not None:
        density_sig = max(0.0, min(1.0, context.nearby_density_norm))
        provenance["nearby_density"] = (
            f"neighbourhood density norm {density_sig:.2f} (grid-cell statistics)"
        )
    else:
        density_sig = 0.0
        provenance["nearby_density"] = "neighbourhood density not computed -> neutral 0"

    category_sig, category_basis = category_urgency_signal(incident.category)
    provenance["category_urgency"] = category_basis

    time_sig, time_basis = time_sensitivity_signal(
        context.current_time, incident.rain_intensity_mm_h
    )
    provenance["time_sensitivity"] = time_basis

    return PriorityFeatures(
        incident_id=incident.incident_id,
        severity_score=context.severity_score,
        school_proximity=round(school_sig, 4),
        hospital_proximity=round(hospital_sig, 4),
        traffic_exposure=round(traffic_sig, 4),
        population_exposure=round(population_sig, 4),
        repeated_reports=round(reports_sig, 4),
        incident_duration=round(duration_sig, 4),
        nearby_density=round(density_sig, 4),
        category_urgency=round(category_sig, 4),
        time_sensitivity=round(time_sig, 4),
        provenance=provenance,
    )


def _proximity_signals(
    incident: ConsolidatedIncident,
) -> tuple[tuple[float, str], tuple[float, str]]:
    """School and hospital proximity from the verified landmark index."""
    if incident.exposure is None:
        return (0.0, "no geospatial exposure computed -> neutral 0"), (
            0.0, "no geospatial exposure computed -> neutral 0"
        )
    school_m = incident.exposure.nearest_school_m
    hospital_m = incident.exposure.nearest_hospital_m
    if school_m is not None and school_m <= _SCHOOL_NEAR_M:
        school = (1.0, f"school at {school_m:.0f} m — children on the street")
    elif school_m is not None and school_m <= _SCHOOL_ZONE_M:
        school = (0.5, f"school within 1 km ({school_m:.0f} m)")
    else:
        school = (0.0, "no school within 1 km" if school_m is not None else "no school in exposure")
    if hospital_m is not None and hospital_m <= _HOSPITAL_NEAR_M:
        hospital = (1.0, f"hospital at {hospital_m:.0f} m — emergency corridor affected")
    elif hospital_m is not None and hospital_m <= _HOSPITAL_ZONE_M:
        hospital = (0.5, f"hospital within 2 km ({hospital_m:.0f} m)")
    else:
        hospital = (0.0, "no hospital within 2 km" if hospital_m is not None else "no hospital in exposure")
    return school, hospital