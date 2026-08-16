"""Duplicate-detection evaluation over the frozen labelled pair set (Phase 11/12).

Pairs: 6 positive (same physical incident), 5 clearly negative and 11
hard negatives (nearby-but-unrelated, similar-text-different-location,
same-location-different-category, different-time). The FINAL engine runs
with production defaults (ScoringConfig.duplicate_threshold=0.70) - the
threshold is NOT tuned here. Pairs the engine escalates to review
(requires_review) are decisions withheld, counted and inspected, not
counted as wrong.

Metrics: precision / recall / F1 over decisive pairs, false-merge rate
(FP/(FP+TN)) and false-split rate (FN/(FN+TP)), plus inspection of
representative false positives and false negatives with the feature
contributions that caused each error.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from civitas_duplicates.contracts import ReportLike
from civitas_duplicates.detector import DuplicateDetector
from civitas_duplicates.embeddings import HashNgramEmbedder

from civitas_evaluation import datasets
from civitas_evaluation.contracts import ComponentMetrics
from civitas_evaluation.metrics import accuracy, binary_prf

COMPONENT = "duplicate-detection"


def _as_report_like(raw: dict[str, Any]) -> ReportLike:
    return ReportLike(
        report_id=str(raw["report_id"]),
        description=str(raw["description"]),
        latitude=float(raw["latitude"]),
        longitude=float(raw["longitude"]),
        submitted_at=datetime.fromisoformat(str(raw["submitted_at"])),
        category=str(raw["category"]),
        text_embedding=HashNgramEmbedder().embed(str(raw["description"])),
    )


def run() -> tuple[ComponentMetrics, dict[str, Any]]:
    pairs = datasets.load_labels("duplicates/labels.json")
    engine = DuplicateDetector()
    rows: list[dict[str, Any]] = []
    for pair_raw in pairs:
        pair: dict[str, Any] = dict(pair_raw)
        a = _as_report_like(pair["reports"][0])
        b = _as_report_like(pair["reports"][1])
        result = engine.evaluate_pair(a, b)
        rows.append(
            {
                "pair_id": pair["pair_id"],
                "kind": pair["kind"],
                "hard": pair["hard"],
                "expected": pair["label"],
                "predicted": int(result.is_duplicate),
                "withheld_review": result.requires_review,
                "score": result.score,
                "feature_contributions": result.feature_contributions,
                "reasons": result.reasons,
                "decision_basis": result.decision_basis,
            }
        )

    decisive = [r for r in rows if not r["withheld_review"]]
    labels = [int(r["expected"]) for r in decisive]
    preds = [int(r["predicted"]) for r in decisive]
    tp = sum(1 for label, p in zip(labels, preds) if label == 1 and p == 1)
    fp = sum(1 for label, p in zip(labels, preds) if label == 0 and p == 1)
    tn = sum(1 for label, p in zip(labels, preds) if label == 0 and p == 0)
    fn = sum(1 for label, p in zip(labels, preds) if label == 1 and p == 0)
    precision, recall, f1 = binary_prf(tp, fp, fn)

    fp_rows = [r for r in rows if not r["withheld_review"] and r["expected"] == 0 and r["predicted"] == 1]
    fn_rows = [r for r in rows if not r["withheld_review"] and r["expected"] == 1 and r["predicted"] == 0]
    review_rows = [r for r in rows if r["withheld_review"]]
    hard_reviewed = sum(1 for r in review_rows if r["hard"])

    metrics = ComponentMetrics(
        component=COMPONENT,
        model_version="duplicates-engine-v1",
        thresholds={
            "duplicate_threshold": "0.70 (ScoringConfig, frozen)",
            "max_reasonable_distance_m": "2000.0",
            "max_reasonable_delta_h": "72.0",
        },
        test_set="test_data/duplicates (15 labelled pairs: 6 positive, 5 negative, 4 hard-negative)",
        n=len(rows),
        metrics={
            "decisive_pairs": len(decisive),
            "review_escalated": len(review_rows),
            "review_escalated_hard": hard_reviewed,
            "precision": precision or 0.0,
            "recall": recall or 0.0,
            "f1": f1 or 0.0,
            "accuracy": accuracy([str(label) for label in labels], [str(p) for p in preds]),
            "false_merge_rate": round(fp / (fp + tn), 4) if (fp + tn) else 0.0,
            "false_split_rate": round(fn / (fn + tp), 4) if (fn + tp) else 0.0,
            "false_merges": fp,
            "false_splits": fn,
        },
        notes=[
            "escalated pairs are decisions withheld for human review (near-threshold or "
            "conflicting evidence), never counted as wrong",
            "false-merge rate = fraction of genuinely-different pairs merged; "
            "false-split rate = fraction of same-incident pairs kept apart",
        ],
    )
    artifacts = {
        "metrics": json.loads(metrics.model_dump_json()),
        "predictions": rows,
        "false_positives": fp_rows,
        "false_negatives": fn_rows,
        "review_escalations": review_rows,
    }
    (datasets.RESULTS_DIR / "duplicate_predictions.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "duplicate_metrics.json").write_text(
        json.dumps(json.loads(metrics.model_dump_json()), indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "duplicate_failure_cases.json").write_text(
        json.dumps({"false_positives": fp_rows, "false_negatives": fn_rows}, indent=2), encoding="utf-8"
    )
    return metrics, artifacts