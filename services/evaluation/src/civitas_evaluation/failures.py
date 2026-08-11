"""Structured failure-analysis pass across all evaluated components (Phase 11/12).

Consumes the per-component artifacts produced by the evaluation run and
emits a FailureRecord per discovered failure with: input, expected,
actual, component, model version, feature evidence (the actual
contributions the model saw), likely reason, whether the failure is
acceptable, and a concrete future improvement. Dangerous failures
(false merges, false splits, wrong critical priority, unsupported
explanations, wrong full-resolution verdicts, confident classification
of unusable media) get `acceptable=False` and are flagged by the report.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter

from civitas_evaluation import datasets
from civitas_evaluation.contracts import FailureRecord

_ADAPTER = TypeAdapter(list[FailureRecord])


def _top_contributions(contrib: dict[str, Any], k: int = 3) -> list[str]:
    ordered = sorted(contrib.items(), key=lambda kv: -abs(float(kv[1])))[:k]
    return [f"{name}={value}" for name, value in ordered]


def _duplicate_failures(artifacts: dict[str, Any]) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, row in enumerate(artifacts.get("false_positives", [])):  # type: ignore[arg-type]
        contrib = dict(row["feature_contributions"])  # type: ignore[index]
        records.append(
            FailureRecord(
                failure_id=f"dup-fp-{i}",
                component="duplicate-detection",
                test_case=str(row["pair_id"]),
                input_summary=f"{row['kind']} pair (hard={row['hard']})",
                expected="not a duplicate (0)",
                actual=f"merged (1), composite {row['score']:.2f}",
                model_version="duplicates-engine-v1",
                feature_evidence=_top_contributions(contrib) + list(row["decision_basis"]),  # type: ignore[arg-type]
                likely_reason=(
                    f"composite {row['score']:.2f} crossed the 0.70 threshold; dominant "
                    f"contributions: {', '.join(_top_contributions(contrib, 2))}"
                ),
                acceptable=False,
                improvement=(
                    "strengthen the conflicting-category gate on spatial overlap or add an "
                    "image-evidence signal for ambiguous overlaps"
                ),
            )
        )
    for i, row in enumerate(artifacts.get("false_negatives", [])):  # type: ignore[arg-type]
        contrib = dict(row["feature_contributions"])  # type: ignore[index]
        records.append(
            FailureRecord(
                failure_id=f"dup-fn-{i}",
                component="duplicate-detection",
                test_case=str(row["pair_id"]),
                input_summary=f"{row['kind']} pair (hard={row['hard']})",
                expected="duplicate (1)",
                actual=f"kept apart (0), composite {row['score']:.2f}",
                model_version="duplicates-engine-v1",
                feature_evidence=_top_contributions(contrib) + list(row["decision_basis"]),  # type: ignore[arg-type]
                likely_reason=(
                    f"composite {row['score']:.2f} stayed under 0.70 despite "
                    f"{', '.join(_top_contributions(contrib, 2))}"
                ),
                acceptable=False,
                improvement=(
                    "add a minimum-criteria override for same-category + overlapping "
                    "location + corroborating reports"
                ),
            )
        )
    return records


def _clustering_failures(rows: list[dict[str, Any]]) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, row in enumerate(rows):
        if row["correct"]:
            continue
        records.append(
            FailureRecord(
                failure_id=f"cluster-{i}",
                component="incident-clustering",
                test_case=str(row["scenario_id"]),
                input_summary="scenario with expected cluster assignment",
                expected=(
                    f"merged_correctly={row['merged_correctly']}, "
                    f"separated_correctly={row['separated_correctly']}, both True"
                ),
                actual=json.dumps(row["actual_clusters"]),
                model_version="duplicates-engine-v1",
                feature_evidence=[json.dumps(row["cluster_details"])],
                likely_reason=(
                    "the 0.70 composite threshold on text+spatial features could not "
                    "resolve this scenario's ambiguity"
                ),
                acceptable=False,
                improvement=(
                    "a sector/street prior or an image-evidence signal would separate "
                    "same-format-text different-location cases without raising the threshold"
                ),
            )
        )
    return records


def _severity_consistency_records(
    violations: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, violation in enumerate(violations):
        records.append(
            FailureRecord(
                failure_id=f"sev-cons-{i}",
                component="severity-model",
                test_case=str(violation["case_id"]),
                input_summary=f"cited factors: {violation['cited_factors']}",
                expected="every cited factor supported by input features",
                actual=(
                    f"unsupported factors: {violation['unsupported_factors']} "
                    f"(features: {violation['features']})"
                ),
                model_version="severity-model-v1",
                feature_evidence=[
                    f"{factor}: {evidence}" for factor, evidence in violation["evidence_per_factor"].items()
                ],
                likely_reason="factor cited without the matching evidence condition in the input",
                acceptable=False,
                improvement="bind every factor emission to its input condition in one unit-checked table",
            )
        )
    return records


def _priority_consistency_records(
    violations: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, violation in enumerate(violations):
        records.append(
            FailureRecord(
                failure_id=f"pri-cons-{i}",
                component="priority-model",
                test_case=str(violation["case_id"]),
                input_summary=f"cited reasons: {violation['cited_factors']}",
                expected="every cited reason backed by a nonzero signal feature",
                actual=f"cited without feature support: {violation['cited_without_feature']}",
                model_version="priority-model-v2",
                feature_evidence=[f"engineered={json.dumps(violation['engineered_signals'])}"],
                likely_reason="reason emitted although its input signal was zero",
                acceptable=False,
                improvement="filter reasons on the actual signal values at emission time",
            )
        )
    return records


def _risk_failures(
    severity_rows: list[dict[str, Any]],
    priority_rows: list[dict[str, Any]],
    severity_violations: list[dict[str, Any]],
    priority_violations: list[dict[str, Any]],
) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, row in enumerate(severity_rows):
        if row["expected"] == row["actual"]:
            continue
        records.append(
            FailureRecord(
                failure_id=f"sev-{i}",
                component="severity-model",
                test_case=str(row["case_id"]),
                input_summary=f"expected {row['expected']}",
                expected=str(row["expected"]),
                actual=f"{row['actual']} (score {row['score']})",
                model_version="severity-model-v1",
                feature_evidence=[f"{k}={v}" for k, v in row["factor_points"].items()],  # type: ignore[arg-type]
                likely_reason="severity score landed in the neighbouring band for this case",
                acceptable=True,
                improvement="treat scores within a few points of a band edge as review candidates",
            )
        )
    for i, row in enumerate(priority_rows):
        if row["expected"] == row["actual"]:
            continue
        critical_miss = row["expected"] == "critical" and row["actual"] != "critical"
        records.append(
            FailureRecord(
                failure_id=f"pri-{i}",
                component="priority-model",
                test_case=str(row["case_id"]),
                input_summary=(
                    f"expected {row['expected']}" + (" (DANGEROUS: critical case missed)" if critical_miss else "")
                ),
                expected=str(row["expected"]),
                actual=f"{row['actual']} (score {row['score']})",
                model_version="priority-model-v2",
                feature_evidence=list(row["cited_reasons"].keys()),  # type: ignore[arg-type]
                likely_reason=(
                    "the weighted signals did not reach the critical band (>= 80)"
                    if critical_miss
                    else "priority score landed in the neighbouring band"
                ),
                acceptable=not critical_miss,
                improvement=(
                    "recalibrate signal weights against labelled real incidents; high-stakes "
                    "critical band needs review escalation when near the boundary"
                ),
            )
        )
    records.extend(_severity_consistency_records(severity_violations, severity_rows))
    records.extend(_priority_consistency_records(priority_violations, priority_rows))
    return records


def _resolution_failures(rows: list[dict[str, Any]]) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, row in enumerate(rows):
        if row["expected"] == row["actual"]:
            continue
        unverif_as_resolved = row["expected"] == "unverifiable" and row["actual"] == "resolved"
        records.append(
            FailureRecord(
                failure_id=f"res-{i}",
                component="resolution-verification",
                test_case=str(row["case_id"]),
                input_summary=f"expected {row['expected']}",
                expected=str(row["expected"]),
                actual=f"{row['actual']} (confidence {row['confidence']:.2f})",
                model_version="resolution-model-v1",
                feature_evidence=list(row["basis"]),  # type: ignore[arg-type]
                likely_reason=(
                    "unverifiable evidence interpreted as resolved"
                    if unverif_as_resolved
                    else "evidence thresholds decided differently on this case"
                ),
                acceptable=not unverif_as_resolved,
                improvement=(
                    "require a minimum evidence floor before 'resolved' can be emitted"
                    if unverif_as_resolved
                    else "tune the standing-water minimum / growth-conflict ratio on hard cases, "
                    "then re-run the frozen set"
                ),
            )
        )
    return records


def _vision_failures(predictions: list[dict[str, Any]]) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, row in enumerate(predictions):
        if row["expected"] == row["actual"]:
            continue
        if row["actual"] is None:
            continue  # media rejected: that is the media-quality gate's record, not a classifier error
        records.append(
            FailureRecord(
                failure_id=f"vis-{i}",
                component="vision-classifier",
                test_case=str(row["case_id"]),
                input_summary=f"expected {row['expected']}",
                expected=str(row["expected"]),
                actual=str(row["actual"]),
                model_version="vision-knn-v1",
                feature_evidence=[f"confidence={row['confidence']:.3f}", f"ood_ratio={row['ood_ratio']:.2f}"],
                likely_reason="nearest-prototype decision fell in the wrong class for this scene",
                acceptable=True,
                improvement="more per-category training scenes plus an augmentation set",
            )
        )
    return records


def _media_quality_failures(rows: list[dict[str, Any]]) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    for i, row in enumerate(rows):
        if row["kind"] == "ambiguous":
            if not row.get("low_confidence_flagged"):
                records.append(
                    FailureRecord(
                        failure_id=f"mq-amb-{i}",
                        component="media-quality-gate",
                        test_case=str(row["case_id"]),
                        input_summary="ambiguous blend input",
                        expected="low confidence flagged (uncertainty recorded)",
                        actual="confident category asserted",
                        model_version="vision-knn-v1",
                        feature_evidence=["margin-based confidence"],
                        likely_reason="margin confidence stayed at or above the 0.40 floor",
                        acceptable=True,
                        improvement="tighten ambiguity detection for mixed/derived inputs",
                    )
                )
            continue
        actual_usable = row.get("gate_usable", row.get("service_usable"))
        verdict_wrong = bool(row["expected_usable"]) != bool(actual_usable)
        forced_when_unusable = not row["expected_usable"] and not row.get("unusable_without_forced_category")
        if verdict_wrong or forced_when_unusable:
            records.append(
                FailureRecord(
                    failure_id=f"mq-{i}",
                    component="media-quality-gate",
                    test_case=str(row["case_id"]),
                    input_summary=str(row["kind"]),
                    expected=f"usable={row['expected_usable']}, no forced category when unusable",
                    actual=json.dumps({"usable": actual_usable, "forced_category": row.get("forced_category")}),
                    model_version="vision-knn-v1",
                    feature_evidence=list(row.get("rejection_basis", [])),  # type: ignore[arg-type]
                    likely_reason="quality gate or media-resolution contract deviation",
                    acceptable=bool(row["expected_usable"]),
                    improvement="verify the gate threshold on the failing case and re-run the frozen set",
                )
            )
    return records


def run(
    vision_predictions: list[dict[str, Any]],
    media_rows: list[dict[str, Any]],
    duplicate_artifacts: dict[str, Any],
    cluster_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    severity_rows: list[dict[str, Any]],
    priority_rows: list[dict[str, Any]],
    severity_violations: list[dict[str, Any]],
    priority_violations: list[dict[str, Any]],
) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    records.extend(_vision_failures(vision_predictions))
    records.extend(_media_quality_failures(media_rows))
    records.extend(_duplicate_failures(duplicate_artifacts))
    records.extend(_clustering_failures(cluster_rows))
    records.extend(_risk_failures(severity_rows, priority_rows, severity_violations, priority_violations))
    records.extend(_resolution_failures(resolution_rows))
    return records


def save(records: list[FailureRecord]) -> None:
    payload = _ADAPTER.validate_python(records) if records else []
    (datasets.RESULTS_DIR / "failures.json").write_text(
        json.dumps(json.loads(json.dumps([r.model_dump() for r in payload])), indent=2), encoding="utf-8"
    )
