"""Priority: how urgently should the authority respond?

Priority is a separate decision from severity. It combines the severity
score with operational urgency (exposure to children/emergency assets,
traffic) and pressure (repeated reports, time unresolved). All weights are
explicit and every tier is explained.
"""

from __future__ import annotations

from dataclasses import dataclass

from civitas_risk.contracts import PriorityResult, PriorityTier, RiskContext
from civitas_risk.features import assemble_feature_vector


@dataclass(frozen=True)
class PriorityConfig:
    weight_severity: float = 0.45
    weight_urgency: float = 0.35
    weight_reports: float = 0.15
    weight_longevity: float = 0.05

    def __post_init__(self) -> None:
        total = self.weight_severity + self.weight_urgency + self.weight_reports + self.weight_longevity
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"priority weights must sum to 1.0, got {total}")


def urgency_score(features: dict[str, float], provenance: dict[str, str]) -> tuple[float, dict[str, float], list[str]]:
    """Urgency from exposure signals (separate from severity itself)."""
    school = features["school_proximity"] * 0.45
    traffic = features["traffic"] * 0.30
    hospital = features["hospital_proximity"] * 0.25
    contributions = {
        "school_exposure": round(school, 4),
        "traffic_exposure": round(traffic, 4),
        "emergency_asset": round(hospital, 4),
    }
    basis = [
        f"urgency school_exposure {school:.2f}: {provenance['school_proximity']}",
        f"urgency traffic_exposure {traffic:.2f}: {provenance['traffic']}",
        f"urgency emergency_asset {hospital:.2f}: {provenance['hospital_proximity']}",
    ]
    return round(school + traffic + hospital, 4), contributions, basis


def tier_for(score: float) -> PriorityTier:
    if score >= 0.80:
        return "P1"
    if score >= 0.60:
        return "P2"
    if score >= 0.40:
        return "P3"
    return "P4"


class PriorityAssessor:
    def __init__(self, config: PriorityConfig | None = None) -> None:
        self.config = config or PriorityConfig()

    def assess(self, ctx: RiskContext, severity_score: float) -> PriorityResult:
        features, provenance = assemble_feature_vector(ctx)
        urgency, urgency_parts, urgency_basis = urgency_score(features, provenance)
        report_pressure = features["repeated_reports"]
        longevity = features["longevity"]

        score = (
            self.config.weight_severity * severity_score
            + self.config.weight_urgency * urgency
            + self.config.weight_reports * report_pressure
            + self.config.weight_longevity * longevity
        )
        score = max(0.0, min(1.0, round(score, 4)))
        basis = [
            f"priority = {self.config.weight_severity:.2f}*severity({severity_score:.2f}) "
            f"+ {self.config.weight_urgency:.2f}*urgency({urgency:.2f}) "
            f"+ {self.config.weight_reports:.2f}*reports({report_pressure:.2f}) "
            f"+ {self.config.weight_longevity:.2f}*longevity({longevity:.2f}) = {score:.3f}",
            *urgency_basis,
            f"repeated-report pressure {report_pressure:.2f}: {provenance['repeated_reports']}",
            f"longevity pressure {longevity:.2f}: {provenance['longevity']}",
        ]
        return PriorityResult(
            report_id=ctx.report_id,
            score=score,
            tier=tier_for(score),
            urgency_contributions=urgency_parts,
            decision_basis=basis,
        )