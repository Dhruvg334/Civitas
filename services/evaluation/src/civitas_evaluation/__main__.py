"""Phase 11/12 evaluation runner - the one documented command.

Usage (from services/evaluation):
    python run_all.py              run the full evaluation over the frozen test set
    python run_all.py check        verify the frozen test-set manifest hashes
    python run_all.py regenerate-testset   bootstrap the test set (refused if results exist)

Every metric in results/ is produced by this run from saved predictions;
nothing is invented, estimated or reused from other work.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]

_PACKAGE_SOURCES = [
    HERE / "src",
    REPO_ROOT / "ml" / "vision" / "src",
    REPO_ROOT / "ml" / "duplicates" / "src",
    REPO_ROOT / "ml" / "risk" / "src",
    REPO_ROOT / "ml" / "resolution" / "src",
    REPO_ROOT / "geospatial" / "src",
    REPO_ROOT / "services" / "ml" / "src",
]
for _src in _PACKAGE_SOURCES:
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))


def check_manifest() -> bool:
    from civitas_evaluation import datasets

    manifest_path = datasets.TEST_DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        print("test_data/manifest.json missing - run: python run_all.py regenerate-testset")
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ok = True
    for relative, expected in manifest["files"].items():
        path = datasets.TEST_DATA_DIR / relative
        if not path.exists():
            print(f"MISSING {relative}")
            ok = False
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            print(f"HASH MISMATCH {relative}")
            ok = False
    if ok:
        print(f"frozen test set intact: {len(manifest['files'])} files verified against manifest")
    return ok


def regenerate() -> None:
    from civitas_evaluation import datasets

    try:
        manifest: dict[str, Any] = datasets.generate_test_set()
    except RuntimeError as exc:
        print(f"refused: {exc}")
        sys.exit(1)
    print(f"test set generated: {len(manifest['files'])} files written to test_data/ (frozen from now on)")


def run_all() -> int:
    if not check_manifest():
        print("aborting: frozen test set missing or corrupt")
        return 1

    from civitas_evaluation import datasets

    datasets.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    from civitas_duplicates.contracts import DuplicateResult  # noqa: F401
    from civitas_evaluation import (
        clustering_eval,
        duplicate_eval,
        failures,
        golden,
        media_quality_eval,
        report,
        resolution_eval,
        risk_eval,
        vision_eval,
    )
    from civitas_evaluation.contracts import ComponentMetrics, EvaluationReport

    components: list[ComponentMetrics] = []

    print("[1/8] vision classifier evaluation (50 frozen images)")
    vision_metrics, vision_predictions = vision_eval.run()
    components.append(vision_metrics)

    print("[2/8] media-quality gate evaluation (14 cases)")
    media_metrics, media_rows = media_quality_eval.run()
    components.append(media_metrics)

    print("[3/8] duplicate-detection evaluation (15 labelled pairs)")
    dup_metrics, dup_artifacts = duplicate_eval.run()
    components.append(dup_metrics)

    print("[4/8] incident-clustering evaluation (4 scenarios)")
    cluster_metrics, cluster_rows = clustering_eval.run()
    components.append(cluster_metrics)

    print("[5/8] severity + priority evaluation (12 + 12 labelled cases)")
    risk_metrics, risk_rows_raw = risk_eval.run()
    risk_rows: dict[str, Any] = dict(risk_rows_raw)
    components.extend(risk_metrics)

    print("[6/8] resolution-verification evaluation (16 before/after cases)")
    res_metrics, res_rows = resolution_eval.run()
    components.append(res_metrics)

    print("[7/8] golden water-leak scenario (evidence trail only)")
    golden_scenario = golden.run()

    print("[8/8] failure analysis + final report")
    severity_violations = json.loads(
        (datasets.RESULTS_DIR / "severity_consistency_checks.json").read_text(encoding="utf-8")
    )
    priority_violations = json.loads(
        (datasets.RESULTS_DIR / "priority_consistency_checks.json").read_text(encoding="utf-8")
    )
    failure_records = failures.run(
        vision_predictions=vision_predictions,
        media_rows=media_rows,
        duplicate_artifacts=dup_artifacts,
        cluster_rows=cluster_rows,
        resolution_rows=res_rows,
        severity_rows=risk_rows["severity"],
        priority_rows=risk_rows["priority"],
        severity_violations=severity_violations,
        priority_violations=priority_violations,
    )
    failures.save(failure_records)

    model_versions = {
        "vision-classifier": "vision-knn-v1",
        "media-quality-gate": "vision-knn-v1 + civitas-ml media resolution",
        "duplicate-detection": "duplicates-engine-v1",
        "incident-clustering": "duplicates-engine-v1",
        "severity-model": "severity-model-v1",
        "priority-model": "priority-model-v2",
        "resolution-verification": "resolution-model-v1",
    }
    thresholds = {
        component.component: component.thresholds for component in components
    }
    evaluation = EvaluationReport(
        components=components,  # type: ignore[arg-type]
        failures=failure_records,
        golden=[golden_scenario],
        model_versions=model_versions,
        thresholds=thresholds,
    )
    report.write_all(evaluation, components, failure_records, [golden_scenario])  # type: ignore[arg-type]

    print("\ndone: results/REPORT.md, METRICS.json, failures.json, golden/evidence_trail.json")
    return 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "run-all"
    if command == "regenerate-testset":
        regenerate()
        return 0
    if command == "check":
        return 0 if check_manifest() else 1
    return run_all()


if __name__ == "__main__":
    sys.exit(main())