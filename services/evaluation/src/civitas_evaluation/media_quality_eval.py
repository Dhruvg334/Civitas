"""Media-quality gate evaluation (Phase 11/12).

Tests that the pipeline correctly identifies unusable evidence instead of
forcing a classification: valid, blurred, tiny, near-black, over-exposed,
ambiguous, unsupported-bytes, missing-file, video-without-path and
no-media cases. Quality checks run at the gate level (`civitas_vision`
quality thresholds) and at the service level (`civitas_ml` media
resolution contract: media_not_found / media_unreadable /
media_invalid_kind).
"""

from __future__ import annotations

import json
from typing import Any

from civitas_ml.analyze import LOW_VISION_CONFIDENCE
from civitas_ml.contracts import MediaReference, ReportInput
from civitas_ml.pipeline import run_report
from civitas_vision.detector import VisualIntelligencePipeline
from PIL import Image

from civitas_evaluation import datasets
from civitas_evaluation.contracts import ComponentMetrics

COMPONENT = "media-quality-gate"


def _gate_row(
    case: dict[str, Any], image: Image.Image | None
) -> dict[str, object]:
    pipeline = VisualIntelligencePipeline()
    result = pipeline.analyze_image(image) if image is not None else None
    unusable_without_forced_category = (result is None) or (
        (not result.media_usable) and (result.primary_category is None)
    )
    return {
        "case_id": case["case_id"],
        "kind": case["kind"],
        "expected_usable": case["expected_usable"],
        "gate_usable": result.media_usable if result else False,
        "forced_category": result.primary_category if result else None,
        "unusable_without_forced_category": unusable_without_forced_category,
        "rejection_basis": (result.basis if result and not result.media_usable else []),
    }


def _service_row(case: dict[str, Any]) -> dict[str, object]:
    case_id = str(case["case_id"])
    kind = str(case["kind"])
    if kind == "unsupported":
        media = [
            MediaReference(
                media_id=None,
                kind="image",
                mime_type="image/png",
                local_path=str(datasets.media_file(case_id)),
            )
        ]
    elif kind == "missing":
        media = [
            MediaReference(
                media_id=None,
                kind="image",
                mime_type="image/png",
                local_path=str(datasets.RESULTS_DIR / "does-not-exist.png"),
            )
        ]
    elif kind == "video-no-path":
        media = [MediaReference(media_id="mock:video-bytes.mp4", kind="video", mime_type="video/mp4")]
    else:
        media = []
    record = ReportInput(report_id=f"qm-{case_id}", media=media, description="quality gate check")
    analysis = run_report(record)
    error_code = analysis.vision.media_rejected_basis[0].split(":")[0] if analysis.vision.media_rejected_basis else None
    return {
        "case_id": case_id,
        "kind": kind,
        "expected_usable": False,
        "service_usable": analysis.vision.media_usable,
        "forced_category": analysis.vision.primary_category,
        "unusable_without_forced_category": (
            not analysis.vision.media_usable and analysis.vision.primary_category is None
        ),
        "rejection_basis": analysis.vision.media_rejected_basis,
        "error_code": error_code,
        "basis": analysis.vision.basis,
    }


def run() -> tuple[ComponentMetrics, list[dict[str, object]]]:
    cases = datasets.load_labels("media_quality/labels.json")
    gate_rows: list[dict[str, object]] = []
    service_rows: list[dict[str, object]] = []
    ambiguity_ok = 0
    for case in cases:
        kind = str(case["kind"])
        if kind in ("unsupported", "missing", "video-no-path", "no-media"):
            row = _service_row(case)
            service_rows.append(row)
        else:
            image = datasets.media_image(str(case["case_id"]))
            row = _gate_row(case, image)
            gate_rows.append(row)
            if kind == "ambiguous":
                if row["gate_usable"] and row["forced_category"] is not None:
                    result = VisualIntelligencePipeline().analyze_image(image)
                    low_conf = result.confidence < LOW_VISION_CONFIDENCE
                    row["low_confidence_flagged"] = low_conf
                    ambiguity_ok = int(low_conf)

    rows = gate_rows + service_rows
    correct_gate_verdicts = sum(
        1
        for r in gate_rows
        if bool(r["expected_usable"]) == bool(r["gate_usable"])
    )
    no_forced = sum(1 for r in rows if r.get("unusable_without_forced_category"))

    metrics = ComponentMetrics(
        component=COMPONENT,
        model_version="vision-knn-v1 + civitas-ml media resolution",
        thresholds={
            "max_blur_score": "0.001 (variance of Laplacian)",
            "min_width_px": "64",
            "min_luminance": "0.02",
            "max_luminance": "0.98",
            "low_vision_confidence": str(LOW_VISION_CONFIDENCE),
        },
        test_set="test_data/media_quality (14 cases: valid/blurred/tiny/dark/bright/ambiguous/unsupported/missing/video/no-media)",
        n=len(rows),
        metrics={
            "correct_quality_verdicts": correct_gate_verdicts,
            "correct_quality_rate": round(correct_gate_verdicts / len(gate_rows), 4) if gate_rows else 0.0,
            "unusable_cases_without_forced_category": no_forced,
            "ambiguous_low_confidence_flagged": ambiguity_ok,
            "gate_rejections_of_blur_tiny_dark_bright": sum(
                1 for r in gate_rows if r["kind"] in ("blurred", "tiny", "near-black", "over-exposed") and not r["gate_usable"]
            ),
            "valid_images_classified": sum(
                1 for r in gate_rows if r["kind"] == "valid" and r["gate_usable"]
            ),
        },
        notes=[
            "unsupported bytes / missing file / video-without-path / no-media are rejected at the "
            "service layer with structured codes (media_unreadable, media_not_found, "
            "media_invalid_kind) and never force a category",
            "the ambiguous 50/50 blend is a derived input (committed train-prototype mix, "
            "documented in the manifest); it must be flagged low-confidence, not asserted",
        ],
    )
    all_rows = gate_rows + service_rows
    (datasets.RESULTS_DIR / "media_quality_predictions.json").write_text(
        json.dumps(all_rows, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "media_quality_metrics.json").write_text(
        json.dumps(json.loads(metrics.model_dump_json()), indent=2), encoding="utf-8"
    )
    return metrics, all_rows