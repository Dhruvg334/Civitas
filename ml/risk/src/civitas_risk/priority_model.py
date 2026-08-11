"""Phase 7: priority model for the consolidated incident.

Priority answers "how urgently should the municipality respond?" — a
separate decision from severity (Phase 6) with its own feature vector
(`priority_features.PriorityFeatures`), its own weights and its own output
shape: a score out of 100, a plain-language level, and named reasons with
the evidence lines that earned them.

The ten engineered signals are combined with explicit weights (sum 1.0,
validated): severity verdict, school proximity, hospital proximity, traffic
exposure, population exposure, repeated reports, incident duration, nearby
incident density, category urgency and time sensitivity. This is the
GeoGPT-style pattern the project follows: spatial and physical
characteristics become engineered features, and a weighted model turns them
into a risk prediction — here "risk" is municipal urgency.

Level bands: <40 low, 40-59 medium, 60-79 high, >=80 critical. The band is
a human-readable name for the score, not a separate computation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from civitas_risk.contracts import SeverityLevel
from civitas_risk.priority_features import PriorityFeatures

PriorityLevel = SeverityLevel  # low | medium | high | critical


class PriorityReason(BaseModel):
    """One named reason with the points it contributed and its evidence."""

    factor: str
    points: int
    evidence: str


class PriorityAssessment(BaseModel):
    """The priority verdict for one consolidated incident."""

    incident_id: str
    score: int = Field(ge=0, le=100)
    level: PriorityLevel
    reasons: list[PriorityReason] = Field(default_factory=list)
    severity_score: int = Field(ge=0, le=100)
    model_version: str = "priority-model-v2"


REASON_FACTORS = {
    "severity_score": "incident severity",
    "school_proximity": "school nearby",
    "hospital_proximity": "hospital proximity",
    "traffic_exposure": "traffic exposure",
    "population_exposure": "population exposure",
    "repeated_reports": "multiple independent reports",
    "incident_duration": "time unresolved",
    "nearby_density": "nearby incident density",
    "category_urgency": "category urgency",
    "time_sensitivity": "time sensitivity",
}


def priority_level_for(score: int) -> PriorityLevel:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


class PriorityModel:
    """Deterministic 10-signal priority model; every point is explainable."""

    model_version = "priority-model-v2"
    WEIGHTS: dict[str, float] = {
        "severity_score": 0.25,
        "school_proximity": 0.18,
        "hospital_proximity": 0.08,
        "traffic_exposure": 0.12,
        "population_exposure": 0.07,
        "repeated_reports": 0.10,
        "incident_duration": 0.05,
        "nearby_density": 0.05,
        "category_urgency": 0.05,
        "time_sensitivity": 0.05,
    }

    def __init__(self) -> None:
        total = sum(self.WEIGHTS.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"priority weights must sum to 1.0, got {total}")

    def assess(self, features: PriorityFeatures) -> PriorityAssessment:
        signals: dict[str, float] = {
            "severity_score": features.severity_score / 100.0,
            "school_proximity": features.school_proximity,
            "hospital_proximity": features.hospital_proximity,
            "traffic_exposure": features.traffic_exposure,
            "population_exposure": features.population_exposure,
            "repeated_reports": features.repeated_reports,
            "incident_duration": features.incident_duration,
            "nearby_density": features.nearby_density,
            "category_urgency": features.category_urgency,
            "time_sensitivity": features.time_sensitivity,
        }
        score = round(100.0 * sum(self.WEIGHTS[k] * signals[k] for k in self.WEIGHTS))
        score = max(0, min(100, score))

        reasons: list[PriorityReason] = []
        for key in self.WEIGHTS:
            points = round(100.0 * self.WEIGHTS[key] * signals[key])
            if points < 1:
                continue
            reasons.append(
                PriorityReason(
                    factor=REASON_FACTORS[key],
                    points=points,
                    evidence=features.provenance[key],
                )
            )

        return PriorityAssessment(
            incident_id=features.incident_id,
            score=score,
            level=priority_level_for(score),
            reasons=reasons,
            severity_score=features.severity_score,
            model_version=self.model_version,
        )