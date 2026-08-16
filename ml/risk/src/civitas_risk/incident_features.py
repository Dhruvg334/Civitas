"""Phase 6: incident-level severity feature engineering.

Phase 1-3 engineered features for one *report*. Phase 6 asks the same
question about the *consolidated incident* (the cluster Phase 5 merged):
"how bad is this incident?" — and answers it by combining three evidence
families into one typed feature vector:

- visual evidence (from the computer-vision pipeline: active water flow,
  flooded-area coverage),
- geospatial intelligence (school/hospital distance, traffic exposure),
- context (how many citizens reported it, how long it has been going on).

The feature vector is evidence-only: no scores, no levels, no decisions.
Every feature carries a provenance string so the models below can cite
"near school (37 m)" instead of printing a bare number. Normalized where it
matters, raw where the model needs the real world value.
"""

from __future__ import annotations

from typing import Literal

from civitas_geo.models import ExposureContext
from pydantic import BaseModel, Field

TrafficExposure = Literal["low", "moderate", "high"]

WATER_FLOW_EVIDENCE_MARKERS = (
    "water flowing across road",
    "standing water",
    "active water flow",
)


class IncidentVisualEvidence(BaseModel):
    """What the computer-vision pipeline observed on the incident.

    `active_water_flow` and `water_coverage` can be supplied directly or
    derived from `observed_evidence` (see `visual_evidence_to_features`).
    """

    primary_category: str | None = None
    observed_evidence: list[str] = Field(default_factory=list)
    active_water_flow: int = Field(default=0, ge=0, le=1)
    water_coverage: float = Field(default=0.0, ge=0.0, le=1.0)

    @classmethod
    def from_evidence(
        cls,
        primary_category: str | None,
        observed_evidence: list[str],
        water_coverage: float = 0.0,
    ) -> IncidentVisualEvidence:
        """Derive the typed visual features from the CV evidence strings."""
        active = int(
            any(marker in " ".join(observed_evidence).lower() for marker in WATER_FLOW_EVIDENCE_MARKERS)
        )
        return cls(
            primary_category=primary_category,
            observed_evidence=list(observed_evidence),
            active_water_flow=active,
            water_coverage=max(0.0, min(1.0, water_coverage)),
        )


class ConsolidatedIncident(BaseModel):
    """The merged incident (Phase 5 cluster) with all observable context."""

    incident_id: str
    category: str
    visual: IncidentVisualEvidence | None = None
    exposure: ExposureContext | None = None
    report_count: int = Field(default=1, ge=1)
    duration_hours: float = Field(default=0.0, ge=0)
    rain_intensity_mm_h: float | None = Field(default=None, ge=0)


class IncidentFeatures(BaseModel):
    """Typed severity feature vector for one consolidated incident.

    Evidence only — no score, no level, no decision. `provenance[feature]`
    explains where the value came from in human terms.
    """

    incident_id: str
    category: str
    active_water_flow: int = Field(default=0, ge=0, le=1)
    water_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    school_distance_m: float | None = None
    hospital_distance_m: float | None = None
    traffic_exposure: TrafficExposure | None = None
    junction_density_1km: float = Field(default=0.0, ge=0)
    report_count: int = Field(default=1, ge=1)
    duration_hours: float = Field(default=0.0, ge=0)
    rain_intensity_mm_h: float | None = Field(default=None, ge=0)
    provenance: dict[str, str] = Field(default_factory=dict)


def build_incident_features(incident: ConsolidatedIncident) -> IncidentFeatures:
    """Convert the consolidated incident into the typed feature vector.

    Every value is copied from observed evidence or a verified landmark;
    missing signals stay `None` (recorded as absent, never invented).
    Missing data is also recorded in the provenance entry when relevant.
    """
    features: dict[str, object] = {
        "incident_id": incident.incident_id,
        "category": incident.category,
        "active_water_flow": incident.visual.active_water_flow if incident.visual else 0,
        "water_coverage": incident.visual.water_coverage if incident.visual else 0.0,
        "school_distance_m": None,
        "hospital_distance_m": None,
        "traffic_exposure": None,
        "junction_density_1km": 0.0,
        "report_count": incident.report_count,
        "duration_hours": incident.duration_hours,
        "rain_intensity_mm_h": incident.rain_intensity_mm_h,
    }
    provenance: dict[str, str] = {}

    provenance["category"] = f"incident category: {incident.category}"
    if incident.visual is not None:
        basis = "visual evidence: " + (
            ", ".join(incident.visual.observed_evidence) or incident.visual.primary_category or "none recorded"
        )
        provenance["active_water_flow"] = basis
        provenance["water_coverage"] = (
            f"visual evidence: flooded-area share {incident.visual.water_coverage:.2f}"
        )
    else:
        provenance["active_water_flow"] = "no visual evidence recorded; flow assumed absent"
        provenance["water_coverage"] = "no visual evidence recorded; coverage assumed absent"

    if incident.exposure is not None:
        exp = incident.exposure
        features["school_distance_m"] = exp.nearest_school_m
        features["hospital_distance_m"] = exp.nearest_hospital_m
        features["traffic_exposure"] = exp.traffic_exposure
        features["junction_density_1km"] = exp.junction_density_1km
        provenance["school_distance_m"] = (
            f"landmark index: nearest school at "
            f"{exp.nearest_school_m:.0f} m" if exp.nearest_school_m is not None
            else "landmark index: no school within search radius"
        )
        provenance["hospital_distance_m"] = (
            f"landmark index: nearest hospital at "
            f"{exp.nearest_hospital_m:.0f} m" if exp.nearest_hospital_m is not None
            else "landmark index: no hospital within search radius"
        )
        provenance["traffic_exposure"] = (
            f"map reasoning: traffic exposure {exp.traffic_exposure} "
            f"(junction density {exp.junction_density_1km:.2f}/km2)"
        )
        provenance["junction_density_1km"] = (
            f"map reasoning: {exp.junction_density_1km:.2f} junctions/km2"
        )
    else:
        provenance["school_distance_m"] = "no geospatial exposure computed"
        provenance["hospital_distance_m"] = "no geospatial exposure computed"
        provenance["traffic_exposure"] = "no geospatial exposure computed"

    provenance["report_count"] = f"{incident.report_count} merged report(s) in the incident cluster"
    provenance["duration_hours"] = (
        f"incident window: first to last report = {incident.duration_hours:.2f} h"
    )
    if incident.rain_intensity_mm_h is not None:
        provenance["rain_intensity_mm_h"] = (
            f"weather context: {incident.rain_intensity_mm_h:.0f} mm/h"
        )

    features["provenance"] = provenance
    return IncidentFeatures.model_validate(features)