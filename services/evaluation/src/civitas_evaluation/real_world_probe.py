"""Real-world media probe (Phase 12 refining track).

Runs the Civitas image/video analyser against real-world, openly
licensed media curated under `datasets/demo_data/` (Wikimedia Commons),
and writes an honest, per-file report: vision verdict, confidence,
out-of-distribution ratio, uncertainty notes, video frame metadata and
structured rejection codes.

This is a *robustness probe*, not part of the frozen Phase 11/12
evaluation: the classifier was trained on procedural scenes, so real
photos are expected to be partly out-of-manifold. The probe's job is to
show *what the system honestly says* about real media — including when
it says "I am not sure".

Usage (from services/evaluation):
    python -m civitas_evaluation.real_world_probe
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEMO_DATA = REPO_ROOT / "datasets" / "demo_data"
MANIFEST = DEMO_DATA / "manifest.json"
RESULTS = DEMO_DATA / "results"

sys.path.insert(0, str(REPO_ROOT / "services" / "ml" / "src"))
for pkg in ("vision", "duplicates", "risk", "resolution"):
    sys.path.insert(0, str(REPO_ROOT / "ml" / pkg / "src"))
sys.path.insert(0, str(REPO_ROOT / "geospatial" / "src"))

from civitas_ml.analyze import analyze_report  # noqa: E402
from civitas_ml.vision_model import build_vision_pipeline  # noqa: E402

# Real-world probe policy: real citizen media is classified by the
# zero-shot CLIP classifier (vision-clip-v2) when it is available —
# measured accurate on natural photos — falling back to the deterministic
# k-NN otherwise. The service default stays 'knn' so the frozen synthetic
# evaluation never depends on an external model download.
_REAL_MEDIA_PIPELINE, _REAL_MEDIA_MODEL = build_vision_pipeline(model="clip")


def _run_image(path: Path, expected: str) -> dict[str, object]:
    analysis = analyze_report(
        image=path,
        description="real-world media probe (no citizen description supplied)",
        report_id=f"RW-IMG-{path.stem}",
        timestamp=datetime.now(timezone.utc),
        vision_pipeline=_REAL_MEDIA_PIPELINE,
    )
    vision = analysis.vision
    return {
        "file": path.relative_to(REPO_ROOT).as_posix(),
        "kind": "image",
        "model_version": _REAL_MEDIA_MODEL,
        "expected_category": expected,
        "media_usable": vision.media_usable,
        "media_kind": vision.media_kind,
        "primary_category": vision.primary_category,
        "secondary_label": vision.secondary_label,
        "precise_observable_description": vision.precise_observable_description,
        "confidence": round(vision.confidence, 4),
        "ood_ratio": round(vision.ood_ratio, 3) if vision.ood_ratio is not None else None,
        "uncertainty": list(vision.uncertainty),
        "rejections": list(vision.media_rejected_basis),
        "observable_evidence": list(vision.observable_evidence),
        "basis": list(vision.basis),
    }


def _run_video(path: Path, expected: str) -> dict[str, object]:
    analysis = analyze_report(
        video=path,
        description="real-world media probe (no citizen description supplied)",
        report_id=f"RW-VID-{path.stem}",
        timestamp=datetime.now(timezone.utc),
        vision_pipeline=_REAL_MEDIA_PIPELINE,
    )
    vision = analysis.vision
    return {
        "file": path.relative_to(REPO_ROOT).as_posix(),
        "kind": "video",
        "model_version": _REAL_MEDIA_MODEL,
        "expected_category": expected,
        "media_usable": vision.media_usable,
        "media_kind": vision.media_kind,
        "primary_category": vision.primary_category,
        "secondary_label": vision.secondary_label,
        "precise_observable_description": vision.precise_observable_description,
        "confidence": round(vision.confidence, 4),
        "ood_ratio": round(vision.ood_ratio, 3) if vision.ood_ratio is not None else None,
        "frames_selected": vision.frames_selected,
        "video_total_frames": vision.video_total_frames,
        "video_duration_s": round(vision.video_duration_s, 2) if vision.video_duration_s is not None else None,
        "video_fps": vision.video_fps,
        "uncertainty": list(vision.uncertainty),
        "rejections": list(vision.media_rejected_basis),
        "observable_evidence": list(vision.observable_evidence),
        "basis": list(vision.basis),
    }


def main() -> None:
    if not MANIFEST.exists():
        print(f"manifest not found: {MANIFEST}")
        return
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for folder in ("images", "videos"):
        for entry in manifest[folder]:
            path = REPO_ROOT / entry["file"]
            if not path.exists():
                print(f"skip (not downloaded yet): {entry['file']}")
                continue
            row = _run_video(path, entry["expected_category"]) if folder == "videos" else _run_image(
                path, entry["expected_category"]
            )
            row["source"] = entry["source_title"]
            row["license"] = entry["license"]
            rows.append(row)
    if not rows:
        print("no demo media present yet; nothing to analyse")
        return
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "real_world_predictions.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "rows": rows}, indent=2),
        encoding="utf-8",
    )
    _write_report(rows)
    _print_summary(rows)


def _verdict(row: dict[str, object]) -> str:
    if not row["media_usable"]:
        return "REJECTED"
    expected = str(row["expected_category"])
    if expected == "ood_control":
        return "OOD-FLAGGED" if row["ood_ratio"] is not None and float(row["ood_ratio"]) >= 2.0 else "OOD-NOT-FLAGGED"
    if row["primary_category"] == expected:
        return "correct"
    return "misclassified"


def _write_report(rows: list[dict[str, object]]) -> None:
    lines = [
        "# Real-world media probe — image/video analyser on real media",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()} by `python -m civitas_evaluation.real_world_probe`.",
        "",
        "This probe exercises the *real-media* vision path: citizen photos are natural",
        f"images, so the probe selects the zero-shot CLIP classifier ({_REAL_MEDIA_MODEL})",
        "when it is available (fallback: the deterministic k-NN). This report records",
        "what the analyser *honestly* says: verdict, confidence, out-of-distribution",
        "ratio, uncertainty notes, and structured rejections.",
        "",
        "## Per-file results",
        "",
        "| file | kind | expected | usable | verdict | category | conf | ood | frames | notes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        notes = " | ".join(row["uncertainty"][:2]) if row["uncertainty"] else ("; ".join(row["rejections"][:1]) if row["rejections"] else "")
        lines.append(
            f"| {row['file'].rsplit('/', 1)[-1]} | {row['kind']} | {row['expected_category']} | "
            f"{row['media_usable']} | {_verdict(row)} | {row['primary_category'] or '-'} | "
            f"{row['confidence']} | {row['ood_ratio'] if row['ood_ratio'] is not None else '-'} | "
            f"{row.get('frames_selected', '-')} | {notes} |"
        )
    correct = sum(1 for r in rows if _verdict(r) == "correct")
    flagged = sum(1 for r in rows if _verdict(r) in {"OOD-FLAGGED", "OOD-NOT-FLAGGED"})
    lines += [
        "",
        f"Totals: {len(rows)} media files — {correct} correct on real-world in-domain media "
        f"(model {_REAL_MEDIA_MODEL}), {flagged} out-of-domain controls evaluated for honest flagging.",
        "",
        "Sources and licenses: see `datasets/demo_data/manifest.json` — Wikimedia Commons",
        "(CC0 / CC BY / CC BY-SA / public domain) plus locally provided demo media whose",
        "license is not recorded.",
        "",
    ]
    (RESULTS / "real_world_report.md").write_text("\n".join(lines), encoding="utf-8")


def _print_summary(rows: list[dict[str, object]]) -> None:
    print(f"analysed {len(rows)} real-world media files")
    for row in rows:
        print(
            f"  [{_verdict(row):<14}] {row['file']:<60} -> {row['primary_category'] or 'rejected'} "
            f"(conf {row['confidence']}, ood {row['ood_ratio'] if row['ood_ratio'] is not None else '-'})"
        )


if __name__ == "__main__":
    main()
