"""Vision classifier evaluation over the frozen 50-image test set.

Reports accuracy, macro-F1 and class-wise precision/recall/F1 plus the
confusion matrix to evaluate performance balance across
the five Civitas core categories. The model is the committed k-NN
classifier inside `civitas_vision` (model edition `vision-knn-v1`, k=3,
T=2.0) - no training, no threshold changes, no parameter search here.
"""

from __future__ import annotations

import json

from civitas_vision.contracts import CIVITAS_CATEGORIES
from civitas_vision.detector import VisualIntelligencePipeline

from civitas_evaluation import datasets
from civitas_evaluation.contracts import ComponentMetrics
from civitas_evaluation.metrics import (
    accuracy,
    confusion_matrix,
    macro_f1,
    per_class_metrics,
)

COMPONENT = "vision-classifier"


def run() -> tuple[ComponentMetrics, list[dict[str, object]]]:
    labels = datasets.load_labels("vision/labels.json")
    pipeline = VisualIntelligencePipeline()
    predictions: list[dict[str, object]] = []
    true, pred = [], []
    for row in labels:
        case_id = str(row["case_id"])
        result = pipeline.analyze_image(datasets.vision_image(case_id))
        predicted = result.primary_category if result.media_usable else None
        predictions.append(
            {
                "case_id": case_id,
                "expected": row["expected"],
                "actual": predicted,
                "media_usable": result.media_usable,
                "confidence": result.confidence,
                "ood_ratio": result.ood_ratio,
                "basis": result.basis,
            }
        )
        true.append(str(row["expected"]))
        pred.append(str(predicted) if predicted in CIVITAS_CATEGORIES else "unusable")

    cm = confusion_matrix(true, pred, [*CIVITAS_CATEGORIES, "unusable"])
    class_wise = per_class_metrics(cm)
    metrics = ComponentMetrics(
        component=COMPONENT,
        model_version="vision-knn-v1",
        thresholds={"k": "3", "softmax_temperature": "2.0", "ood_uncertainty_floor": "2.0"},
        test_set="test_data/vision (50 images, seeds 2000-2049, disjoint from train/dev)",
        n=len(labels),
        metrics={
            "accuracy": accuracy(true, pred),
            "macro_f1": macro_f1(class_wise),
            "misclassified": sum(1 for t, p in zip(true, pred) if t != p),
        },
        class_wise=class_wise,
        confusion=cm,
        notes=[
            "every image passed the quality gate (media_usable=True) and received a category",
            "confidence = top-1/top-2 vote-share margin; ood_ratio flags out-of-manifold inputs",
        ],
    )
    (datasets.RESULTS_DIR / "vision_predictions.json").write_text(
        json.dumps(predictions, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "vision_metrics.json").write_text(
        json.dumps(json.loads(metrics.model_dump_json()), indent=2), encoding="utf-8"
    )
    return metrics, predictions