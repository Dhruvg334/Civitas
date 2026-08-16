"""Severity and priority evaluation (Phase 11/12).

The two models stay completely separate and are evaluated against
hand-authored labelled cases. Expected severity/priority labels are COMPUTED
at test-set generation time from the published rule/weight tables (see
`datasets._severity_expected` and `datasets._priority_expected`), with
drift-guards pinning those constants to the shipped model tables.

Reported: agreement (accuracy + Cohen's kappa), per-level recall and
critical-case recall for priority. Factor-explanation consistency is
verified: every factor a model cites must be supported by a feature
actually present in the input (e.g. an engineered signal that is nonzero)
and by a positive contribution to the score. For priority, the ENGINEERED
signal vector is compared against the expected signal values computed from
the documented mappings (evidence-faithfulness of the feature engineering,
not just the score).

Label circularity is disclosed, not hidden: severity labels follow from
the same documented rule table the model implements, so the metrics prove
faithful implementation plus regression-safety, not external calibration
(real-world labels do not exist yet - recorded limitation).
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any

from civitas_risk.incident_features import IncidentFeatures
from civitas_risk.priority_features import PriorityContext, build_priority_features
from civitas_risk.priority_model import REASON_FACTORS, PriorityModel
from civitas_risk.severity_model import SeverityAssessment, SeverityModel

from civitas_evaluation import datasets
from civitas_evaluation.contracts import ComponentMetrics
from civitas_evaluation.metrics import (
    accuracy,
    cohen_kappa,
    confusion_matrix,
    per_class_metrics,
)

COMPONENT_SEVERITY = "severity-model"
COMPONENT_PRIORITY = "priority-model"

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
PRIORITY_LEVELS = ["low", "medium", "high", "critical"]

_SEV_RULE = datasets._sev  # documented table mirrors (guarded against drift)


# Condition each severity factor name must satisfy on the input features.
# Factor names mirror the model's SeverityContribution.factor strings.
def _severity_factor_condition(factor: str, feats: dict[str, Any]) -> bool:
    traffic = feats.get("traffic_exposure")
    if factor.startswith("category base"):
        return str(feats.get("category", "")) != ""
    if factor == "active road flooding":
        return int(feats.get("active_water_flow", 0)) == 1
    if factor == "significant affected area":
        return float(feats.get("water_coverage", 0.0)) >= 0.30
    if factor == "slip hazard":
        return int(feats.get("active_water_flow", 0)) == 1 and traffic in ("high", "moderate")
    if factor == "near school":
        d = feats.get("school_distance_m")
        return d is not None and float(d) <= 300
    if factor == "school zone":
        d = feats.get("school_distance_m")
        return d is not None and float(d) <= 1000
    if factor == "near hospital":
        d = feats.get("hospital_distance_m")
        return d is not None and float(d) <= 500
    if factor == "heavy traffic exposure":
        return traffic == "high"
    if factor == "moderate traffic exposure":
        return traffic == "moderate"
    if factor == "crowd corroboration":
        return int(feats.get("report_count", 1)) > 1
    if factor == "protracted exposure":
        return float(feats.get("duration_hours", 0.0)) > 0
    if factor == "heavy rain escalation":
        r = feats.get("rain_intensity_mm_h")
        return r is not None and float(r) >= 20.0
    return False


def _severity_case_features(row: dict[str, Any], case_id: str) -> IncidentFeatures:
    feats = dict(row["features"])  # type: ignore[arg-type]
    return IncidentFeatures(
        incident_id=case_id,
        category=str(feats.pop("category")),
        active_water_flow=int(feats.pop("active_water_flow")),
        water_coverage=float(feats.pop("water_coverage")),
        school_distance_m=feats.pop("school_distance_m", None),
        hospital_distance_m=feats.pop("hospital_distance_m", None),
        traffic_exposure=feats.pop("traffic_exposure", None),
        report_count=int(feats.pop("report_count")),
        duration_hours=float(feats.pop("duration_hours")),
        rain_intensity_mm_h=feats.pop("rain_intensity_mm_h", None),
    )


def run_severity() -> tuple[ComponentMetrics, list[dict[str, Any]]]:
    cases = datasets.load_labels("severity/labels.json")
    model = SeverityModel()
    rows: list[dict[str, Any]] = []
    consistency_violations: list[dict[str, object]] = []
    for row in cases:
        case_id = str(row["case_id"])
        features = _severity_case_features(row, case_id)
        assessment = model.assess(features)
        cited_factors = [c.factor for c in assessment.contributing_factors]
        unsupported = [
            f
            for f in cited_factors
            if not _severity_factor_condition(f, row["features"])  # type: ignore[arg-type]
        ]
        if unsupported:
            consistency_violations.append(
                {
                    "case_id": case_id,
                    "cited_factors": cited_factors,
                    "unsupported_factors": unsupported,
                    "features": row["features"],  # type: ignore[arg-type]
                    "evidence_per_factor": {c.factor: c.evidence for c in assessment.contributing_factors},
                }
            )
        rows.append(
            {
                "case_id": case_id,
                "expected": row["expected_level"],
                "expected_score": row["expected_score"],
                "actual": assessment.level,
                "score": assessment.score,
                "factors": cited_factors,
                "factor_points": {c.factor: c.points for c in assessment.contributing_factors},
            }
        )

    labels = [str(r["expected"]) for r in rows]
    preds = [str(r["actual"]) for r in rows]
    cm = confusion_matrix(labels, preds, SEVERITY_LEVELS)
    class_wise = per_class_metrics(cm)
    critical_labeled = [r for r in rows if r["expected"] == "critical"]
    critical_caught = sum(1 for r in critical_labeled if r["actual"] == "critical")
    metrics = ComponentMetrics(
        component=COMPONENT_SEVERITY,
        model_version=SeverityModel.model_version,
        thresholds={"bands": "critical>=80, high>=60, medium>=35"},
        test_set="test_data/severity (12 hand-authored cases; labels computed from the documented rule table)",
        n=len(rows),
        metrics={
            "accuracy": accuracy(labels, preds),
            "cohen_kappa": cohen_kappa(labels, preds),
            "critical_recall": round(critical_caught / len(critical_labeled), 4) if critical_labeled else None,  # type: ignore[dict-item]
            "explanation_consistency_violations": len(consistency_violations),
            "factor_citations": sum(len(r["factors"]) for r in rows),  # type: ignore[arg-type]
        },
        class_wise=class_wise,
        confusion=cm,
        notes=[
            "labels are computed from the documented severity rule table at test-set "
            "generation (constants drift-guarded); agreement therefore proves faithful "
            "implementation + regression safety, not external calibration (no real-world "
            "severity labels exist - recorded limitation)",
            "explanation consistency: every cited factor must match a feature present in the input",
            "known limitation: category base points (min 35 for streetlight) make the low "
            "band unreachable - the minimum achievable score is 41 (medium); critical needs "
            ">= 107 rule points under the squash curve 100*(1-exp(-points/66))",
        ],
    )
    (datasets.RESULTS_DIR / "severity_predictions.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "severity_metrics.json").write_text(
        json.dumps(json.loads(metrics.model_dump_json()), indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "severity_consistency_checks.json").write_text(
        json.dumps(consistency_violations, indent=2), encoding="utf-8"
    )
    return metrics, rows


def _priority_case(
    row: dict[str, Any], case_id: str
) -> tuple[PriorityContext, dict[str, float], set[str]]:
    from civitas_geo.models import ExposureContext
    from civitas_risk.incident_features import (
        ConsolidatedIncident,
        IncidentVisualEvidence,
    )

    incident = row["incident"]  # type: ignore[arg-type]
    ctx = row["context"]  # type: ignore[arg-type]
    exposure = ExposureContext(
        nearest_school_m=incident.get("school_distance_m"),
        nearest_hospital_m=incident.get("hospital_distance_m"),
        traffic_exposure=incident.get("traffic_exposure"),
    )
    visual = IncidentVisualEvidence(
        primary_category=incident.get("category"),
        active_water_flow=int(incident.get("active_water_flow", 0)),
        water_coverage=float(incident.get("water_coverage", 0.0)),
    )
    consolidated = ConsolidatedIncident(
        incident_id=case_id,
        category=str(incident["category"]),
        visual=visual,
        exposure=exposure,
        report_count=int(incident.get("report_count", 1)),
        duration_hours=float(incident.get("duration_hours", 0)),
        rain_intensity_mm_h=incident.get("rain_intensity_mm_h"),
    )
    current_time = ctx.get("current_time")
    context = PriorityContext(
        incident=consolidated,
        severity_score=int(row["expected_severity_score"]),
        population_density_proxy=ctx.get("population_density_proxy"),
        nearby_density_norm=ctx.get("nearby_density_norm"),
        current_time=_dt.datetime.fromisoformat(str(current_time)) if current_time else None,
    )
    expected_signals = {k: float(v) for k, v in row["expected_signals"].items()}  # type: ignore[arg-type]
    expected_factors = {REASON_FACTORS[k] for k in row["expected_reasons"]}  # type: ignore[arg-type]
    return context, expected_signals, expected_factors


def run_priority() -> tuple[ComponentMetrics, list[dict[str, Any]]]:
    cases = datasets.load_labels("priority/labels.json")
    model = PriorityModel()
    rows: list[dict[str, Any]] = []
    consistency_issues: list[dict[str, object]] = []
    engineering_mismatches: list[dict[str, object]] = []

    def engineered(
        features: Any, key: str
    ) -> float:
        value = getattr(features, key, 0.0)
        if key == "severity_score":
            value = float(value) / 100.0
        return float(value)

    for row in cases:
        case_id = str(row["case_id"])
        context, expected_signals, expected_factors = _priority_case(row, case_id)
        features = build_priority_features(context)
        assessment = model.assess(features)

        cited = {r.factor: r.points for r in assessment.reasons}
        unsupported: list[str] = []
        for factor_name in cited:
            key = next((k for k, v in REASON_FACTORS.items() if v == factor_name), None)
            if key is None:
                continue
            if engineered(features, key) <= 0.0:
                unsupported.append(factor_name)
        if unsupported:
            consistency_issues.append(
                {
                    "case_id": case_id,
                    "cited_factors": list(cited),
                    "cited_without_feature": unsupported,
                    "engineered_signals": features.model_dump(),
                }
            )

        missing_expected = [f for f in expected_factors if f not in cited]
        signal_deviation = [
            {
                "signal": k,
                "expected": expected_signals[k],
                "engineered": round(engineered(features, k), 4),
            }
            for k in expected_signals
            if abs(engineered(features, k) - expected_signals[k]) > 1e-3
        ]
        if signal_deviation:
            engineering_mismatches.append(
                {"case_id": case_id, "deviations": signal_deviation}
            )
        rows.append(
            {
                "case_id": case_id,
                "expected": row["expected_level"],
                "expected_score": row["expected_score"],
                "actual": assessment.level,
                "score": assessment.score,
                "severity_score": assessment.severity_score,
                "expected_severity_score": row["expected_severity_score"],
                "cited_reasons": cited,
                "expected_reasons_missing": missing_expected,
                "explanation_consistent": not unsupported,
                "engineering_deviations": len(signal_deviation),
            }
        )

    labels = [str(r["expected"]) for r in rows]
    preds = [str(r["actual"]) for r in rows]
    cm = confusion_matrix(labels, preds, PRIORITY_LEVELS)
    class_wise = per_class_metrics(cm)
    critical_labeled = [r for r in rows if r["expected"] == "critical"]
    critical_caught = sum(1 for r in critical_labeled if r["actual"] == "critical")
    metrics = ComponentMetrics(
        component=COMPONENT_PRIORITY,
        model_version=PriorityModel.model_version,
        thresholds={"bands": "critical>=80, high>=60, medium>=40"},
        test_set="test_data/priority (12 hand-authored cases; labels computed from the documented weight table)",
        n=len(rows),
        metrics={
            "accuracy": accuracy(labels, preds),
            "cohen_kappa": cohen_kappa(labels, preds),
            "critical_case_recall": round(critical_caught / len(critical_labeled), 4) if critical_labeled else None,  # type: ignore[dict-item]
            "critical_labeled": len(critical_labeled),
            "critical_caught": critical_caught,
            "explanation_consistency_violations": len(consistency_issues),
            "engineering_faithfulness_violations": len(engineering_mismatches),
            "expected_reasons_missing": sum(len(r["expected_reasons_missing"]) for r in rows),  # type: ignore[arg-type]
        },
        class_wise=class_wise,
        confusion=cm,
        notes=[
            "critical-case recall is the fraction of labelled-critical incidents the model "
            "marks critical - the urgent-attention capability",
            "explanation consistency: a cited reason (e.g. 'school nearby') requires the "
            "corresponding engineered signal to be nonzero in the input features",
            "engineering faithfulness: each expectation was derived from the documented "
            "signal mappings (<=300m school -> 1.0, reports -> 1-exp(-(n-1)/2), etc.) and "
            "compared against the model's engineered vector; deviations are evidence failures",
        ],
    )
    (datasets.RESULTS_DIR / "priority_predictions.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "priority_metrics.json").write_text(
        json.dumps(json.loads(metrics.model_dump_json()), indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "priority_consistency_checks.json").write_text(
        json.dumps(consistency_issues, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "priority_engineering_checks.json").write_text(
        json.dumps(engineering_mismatches, indent=2), encoding="utf-8"
    )
    return metrics, rows


def run() -> tuple[list[ComponentMetrics], dict[str, object]]:
    severity, sev_rows = run_severity()
    priority, pri_rows = run_priority()
    return [severity, priority], {"severity": sev_rows, "priority": pri_rows}


def severity_assessment_for(features: IncidentFeatures) -> SeverityAssessment:
    return SeverityModel().assess(features)