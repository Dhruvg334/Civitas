"""Rule-based severity with optional ML calibration blend.

Severity answers: how dangerous or harmful is this incident?

The rule scorer is fully explainable and deterministic. The ML hybrid
(optional) learns a calibration correction from the labeled training
dataset (datasets/generators/generate_risk_dataset.py) and blends into the
rule score with an explicit weight — the rule output always participates.
"""

from __future__ import annotations

import json
from pathlib import Path

from civitas_risk.contracts import RiskContext, SeverityLevel, SeverityResult
from civitas_risk.features import FEATURE_KEYS, assemble_feature_vector
from civitas_risk.ml_models import LogisticCalibrator

SEVERITY_MODIFIERS = {
    "electrical": 0.15,
    "public_health": 0.15,
    "accessibility": 0.10,
    "school_close": 0.15,
    "traffic_high": 0.10,
    "weather_rain": 0.10,
    "hospital_close": 0.05,
}


def _cap(score: float) -> float:
    return max(0.0, min(1.0, score))


def severity_level(score: float) -> SeverityLevel:
    if score >= 0.80:
        return "critical"
    if score >= 0.60:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def rule_severity(ctx: RiskContext) -> tuple[float, dict[str, float], list[str]]:
    """Deterministic rule severity with per-factor contributions."""
    features, provenance = assemble_feature_vector(ctx)
    score = features["category_base"]
    contributions: dict[str, float] = {}
    basis: list[str] = [provenance["category_base"]]

    if features["electrical"] > 0:
        contributions["electrical"] = SEVERITY_MODIFIERS["electrical"]
        score += SEVERITY_MODIFIERS["electrical"]
        basis.append(f"+{SEVERITY_MODIFIERS['electrical']:.2f} severity: {provenance['electrical']}")
    if features["public_health"] > 0:
        contributions["public_health"] = SEVERITY_MODIFIERS["public_health"]
        score += SEVERITY_MODIFIERS["public_health"]
        basis.append(f"+{SEVERITY_MODIFIERS['public_health']:.2f} severity: {provenance['public_health']}")
    if features["accessibility"] > 0:
        contributions["accessibility"] = SEVERITY_MODIFIERS["accessibility"]
        score += SEVERITY_MODIFIERS["accessibility"]
        basis.append(f"+{SEVERITY_MODIFIERS['accessibility']:.2f} severity: {provenance['accessibility']}")
    if features["school_proximity"] >= 1.0:
        contributions["school_close"] = SEVERITY_MODIFIERS["school_close"]
        score += SEVERITY_MODIFIERS["school_close"]
        basis.append(f"+{SEVERITY_MODIFIERS['school_close']:.2f} severity: {provenance['school_proximity']}")
    if features["traffic"] >= 1.0:
        contributions["traffic_high"] = SEVERITY_MODIFIERS["traffic_high"]
        score += SEVERITY_MODIFIERS["traffic_high"]
        basis.append(f"+{SEVERITY_MODIFIERS['traffic_high']:.2f} severity: {provenance['traffic']}")
    if features["weather"] >= 0.5:
        contributions["weather_rain"] = SEVERITY_MODIFIERS["weather_rain"]
        score += SEVERITY_MODIFIERS["weather_rain"]
        basis.append(f"+{SEVERITY_MODIFIERS['weather_rain']:.2f} severity: {provenance['weather']}")
    if features["hospital_proximity"] >= 1.0:
        contributions["hospital_close"] = SEVERITY_MODIFIERS["hospital_close"]
        score += SEVERITY_MODIFIERS["hospital_close"]
        basis.append(f"+{SEVERITY_MODIFIERS['hospital_close']:.2f} severity: {provenance['hospital_proximity']}")

    # Bound per-category severity so modifiers cannot silently flip levels.
    score = _cap(score)
    return round(score, 4), contributions, basis


class SeverityAssessor:
    """Explanable severity scorer; optionally blends a calibrated ML model."""

    def __init__(
        self,
        calibrator: LogisticCalibrator | None = None,
        ml_blend_weight: float = 0.35,
        model_version: str = "severity-rule-v1",
    ) -> None:
        if calibrator is not None and not (0.0 <= ml_blend_weight <= 1.0):
            raise ValueError("ml_blend_weight must be in [0, 1]")
        self.calibrator = calibrator
        self.ml_blend_weight = ml_blend_weight
        self.model_version = model_version

    def assess(self, ctx: RiskContext) -> SeverityResult:
        rule_score, contributions, basis = rule_severity(ctx)
        ml_blend = 0.0
        if self.calibrator is not None:
            features, _ = assemble_feature_vector(ctx)
            ml_pred = self.calibrator.predict_proba([[features[k] for k in FEATURE_KEYS]])[0]
            blended = self.ml_blend_weight * ml_pred + (1.0 - self.ml_blend_weight) * rule_score
            ml_blend = self.ml_blend_weight
            basis.append(
                f"ML calibration blend {ml_blend:.2f} x {ml_pred:.3f} + "
                f"{1 - ml_blend:.2f} x rule {rule_score:.3f} = {blended:.3f}"
            )
            rule_score = round(_cap(blended), 4)
        return SeverityResult(
            report_id=ctx.report_id,
            score=rule_score,
            level=severity_level(rule_score),
            contributing_factors=contributions,
            decision_basis=basis,
            model_version=self.model_version,
            ml_blend_weight=ml_blend,
        )

    @classmethod
    def from_artifact(cls, path: str | Path, ml_blend_weight: float = 0.35) -> SeverityAssessor:
        """Load a fitted coefficient artifact (see train_severity.py)."""
        artifact = Path(path)
        data = json.loads(artifact.read_text(encoding="utf-8"))
        calibrator = LogisticCalibrator(feature_names=FEATURE_KEYS)
        calibrator.coef_ = data["coefficients"]
        calibrator.intercept_ = data["intercept"]
        calibrator.fitted_ = True
        return cls(calibrator=calibrator, ml_blend_weight=ml_blend_weight, model_version=data.get("model_version", "severity-ml-v1"))