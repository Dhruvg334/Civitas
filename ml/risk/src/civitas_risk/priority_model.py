"""Phase 6: priority model for the consolidated incident.

Priority answers "how urgently must the authority respond?" — a separate
decision from severity with its own model, weights, tiers and contributing
factors. Priority blends the severity verdict (what is at stake) with
operational urgency (children near school, emergency assets, traffic load)
and pressure (crowd corroboration, time unresolved):

    priority = 0.45 * severity + 0.30 * urgency
               + 0.15 * crowd pressure + 0.10 * protraction

Tiers: P1 >= 80, P2 >= 60, P3 >= 40, P4 below. Every tier is explained in
`contributing_factors`.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from civitas_risk.contracts import PriorityTier
from civitas_risk.incident_features import IncidentFeatures
from civitas_risk.severity_model import SeverityAssessment


class PriorityContribution(BaseModel):
    """One named contributing factor with its points and evidence."""

    factor: str
    points: int
    evidence: str


class PriorityAssessment(BaseModel):
    """How urgently the authority should respond to the incident."""

    incident_id: str
    score: int = Field(ge=0, le=100)
    tier: PriorityTier
    contributing_factors: list[PriorityContribution] = Field(default_factory=list)
    severity_score: int = Field(ge=0, le=100)
    model_version: str = "priority-model-v1"


class PriorityModel:
    """Deterministic priority model, separate from the severity model."""

    model_version = "priority-model-v1"

    # Blend weights (sum to 1.0, validated in __post_init__ style at use).
    weight_severity = 0.45
    weight_urgency = 0.30
    weight_crowd = 0.15
    weight_protraction = 0.10

    def __init__(self) -> None:
        total = (
            self.weight_severity + self.weight_urgency
            + self.weight_crowd + self.weight_protraction
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"priority weights must sum to 1.0, got {total}")

    def assess(self, features: IncidentFeatures, severity: SeverityAssessment) -> PriorityAssessment:
        contributions: list[PriorityContribution] = []
        urgency, urgency_contributions = self._urgency(features)

        crowd = 1.0 - math.exp(-max(0, features.report_count - 1) / 2.0)
        protraction = math.tanh(features.duration_hours / 24.0)

        score = int(round(100.0 * (
            self.weight_severity * severity.score / 100.0
            + self.weight_urgency * urgency
            + self.weight_crowd * crowd
            + self.weight_protraction * protraction
        )))

        contributions.append(
            PriorityContribution(
                factor="incident severity",
                points=int(round(100.0 * self.weight_severity * severity.score / 100.0)),
                evidence=(
                    f"severity model scored {severity.score}/100 ({severity.level}); "
                    f"weight {self.weight_severity:.2f}"
                ),
            )
        )
        contributions.extend(urgency_contributions)
        if crowd > 0.001:
            contributions.append(
                PriorityContribution(
                    factor="crowd pressure",
                    points=int(round(100.0 * self.weight_crowd * crowd)),
                    evidence=features.provenance.get(
                        "report_count", f"{features.report_count} merged report(s)"
                    ),
                )
            )
        if protraction > 0.001:
            contributions.append(
                PriorityContribution(
                    factor="time unresolved",
                    points=int(round(100.0 * self.weight_protraction * protraction)),
                    evidence=features.provenance.get(
                        "duration_hours", f"{features.duration_hours:.1f} h"
                    ),
                )
            )

        return PriorityAssessment(
            incident_id=features.incident_id,
            score=score,
            tier=self.tier_for(score),
            contributing_factors=contributions,
            severity_score=severity.score,
            model_version=self.model_version,
        )

    @staticmethod
    def _urgency(features: IncidentFeatures) -> tuple[float, list[PriorityContribution]]:
        """Operational urgency: who and what is exposed right now.

        urgency = 0.5 * school + 0.3 * hospital + 0.2 * traffic, and the whole
        family carries `weight_urgency = 0.30` of the final priority score.
        """
        school = features.school_distance_m
        hospital = features.hospital_distance_m
        school_sig = 1.0 if school is not None and school <= 300 else (
            0.5 if school is not None and school <= 1000 else 0.0
        )
        hospital_sig = 1.0 if hospital is not None and hospital <= 500 else (
            0.5 if hospital is not None and hospital <= 2000 else 0.0
        )
        traffic_sig = 0.0
        if features.traffic_exposure == "high":
            traffic_sig = 1.0
        elif features.traffic_exposure == "moderate":
            traffic_sig = 0.5
        elif features.traffic_exposure == "low":
            traffic_sig = 0.0

        urgency = 0.5 * school_sig + 0.3 * hospital_sig + 0.2 * traffic_sig
        family_weight = PriorityModel.weight_urgency
        contributions = [
            PriorityContribution(
                factor="children exposure",
                points=int(round(100.0 * family_weight * 0.5 * school_sig)),
                evidence=(
                    f"school at {school:.0f} m" if school is not None
                    else "no school in exposure"
                ),
            ),
            PriorityContribution(
                factor="emergency asset",
                points=int(round(100.0 * family_weight * 0.3 * hospital_sig)),
                evidence=(
                    f"hospital at {hospital:.0f} m" if hospital is not None
                    else "no hospital in exposure"
                ),
            ),
            PriorityContribution(
                factor="traffic load",
                points=int(round(100.0 * family_weight * 0.2 * traffic_sig)),
                evidence=features.provenance["traffic_exposure"],
            ),
        ]
        return round(urgency, 4), contributions

    @staticmethod
    def tier_for(score: int) -> PriorityTier:
        if score >= 80:
            return "P1"
        if score >= 60:
            return "P2"
        if score >= 40:
            return "P3"
        return "P4"