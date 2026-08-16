"""Resolution-verification evaluation (Phase 11/12).

16 hand-authored before/after cases across the four outcomes (resolved,
partial, unverifiable, conflicting). Reports overall accuracy plus
class-specific precision/recall, with emphasis on partial-resolution
recall and unverifiable-case detection: Civitas must not mark an issue
fully resolved when evidence is insufficient or only part of the fix
happened.
"""

from __future__ import annotations

import json
from typing import Any

from civitas_resolution.evidence import ResolutionEvidence
from civitas_resolution.model import ResolutionModel

from civitas_evaluation import datasets
from civitas_evaluation.contracts import ComponentMetrics
from civitas_evaluation.metrics import (
    accuracy,
    cohen_kappa,
    confusion_matrix,
    per_class_metrics,
)

COMPONENT = "resolution-verification"
OUTCOMES = ["resolved", "partial", "unverifiable", "conflicting"]


def _evidence(row: dict[str, Any], incident_id: str) -> ResolutionEvidence:
    return ResolutionEvidence(
        incident_id=incident_id,
        stage=row["stage"],  # type: ignore[arg-type]
        source="labelled test case (synthetic)",
        media_usable=bool(row.get("media_usable", True)),
        primary_category=None,
        observable_evidence=list(row["observable_evidence"]),  # type: ignore[arg-type]
        active_water_flow=int(any("flowing" in str(e) or "water flowing" in str(e) for e in row["observable_evidence"])),  # type: ignore[arg-type]
        water_coverage=float(row.get("water_coverage", 0.0)),
    )


def run() -> tuple[ComponentMetrics, list[dict[str, object]]]:
    cases = datasets.load_labels("resolution/labels.json")
    model = ResolutionModel()
    rows: list[dict[str, object]] = []
    for row in cases:
        case_id = str(row["case_id"])
        before = _evidence(row["before"], case_id)  # type: ignore[arg-type]
        after = _evidence(row["after"], case_id)  # type: ignore[arg-type]
        verdict = model.assess(before, after)
        rows.append(
            {
                "case_id": case_id,
                "expected": row["expected_outcome"],
                "actual": verdict.outcome,
                "confidence": verdict.confidence,
                "basis": verdict.basis,
            }
        )

    labels = [str(r["expected"]) for r in rows]
    preds = [str(r["actual"]) for r in rows]
    cm = confusion_matrix(labels, preds, OUTCOMES)
    class_wise = per_class_metrics(cm)
    by_outcome = {o: [r for r in rows if r["expected"] == o] for o in OUTCOMES}

    metrics = ComponentMetrics(
        component=COMPONENT,
        model_version=ResolutionModel.model_version,
        thresholds={
            "standing_water_evidence_min": "0.20",
            "coverage_growth_conflict_ratio": "1.10",
        },
        test_set="test_data/resolution (16 labelled before/after cases, 4 per outcome)",
        n=len(rows),
        metrics={
            "accuracy": accuracy(labels, preds),
            "cohen_kappa": cohen_kappa(labels, preds),
            "partial_recall": next(
                (c.recall or 0.0 for c in class_wise if c.class_name == "partial"), 0.0
            ),
            "partial_accuracy": next(
                (c.precision or 0.0 for c in class_wise if c.class_name == "partial"), 0.0
            ),
            "unverifiable_recall": next(
                (c.recall or 0.0 for c in class_wise if c.class_name == "unverifiable"), 0.0
            ),
            "unverifiable_detected": sum(1 for r in by_outcome["unverifiable"] if r["actual"] == "unverifiable"),
            "unverifiable_labeled": len(by_outcome["unverifiable"]),
            "unverifiable_never_marked_resolved": sum(
                1 for r in by_outcome["unverifiable"] if r["actual"] != "resolved"
            ),
            "conflicting_precision": next(
                (c.precision or 0.0 for c in class_wise if c.class_name == "conflicting"), 0.0
            ),
        },
        class_wise=class_wise,
        confusion=cm,
        notes=[
            "the safety guard is explicit in the metrics: unverifiable evidence must never be "
            "marked fully resolved",
            "partial is only correct when standing water (or equivalent) remains after the flow is gone",
        ],
    )
    (datasets.RESULTS_DIR / "resolution_predictions.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "resolution_metrics.json").write_text(
        json.dumps(json.loads(metrics.model_dump_json()), indent=2), encoding="utf-8"
    )
    return metrics, rows