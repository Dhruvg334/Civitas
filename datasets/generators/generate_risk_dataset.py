"""Generate a deterministic labeled severity dataset for Civitas.

Synthetic samples across categories, exposure levels, report pressure and
weather. Labels are the rule severity score plus controlled noise so the ML
calibration layer learns to approximate-and-correct the rules. Labels are
explicitly synthetic; production calibration requires human-reviewed labels.

Usage:
    python datasets/generators/generate_risk_dataset.py
Outputs:
    datasets/generated/risk_samples.jsonl
    datasets/manifests/risk_samples.manifest.json
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml" / "risk" / "src"))
sys.path.insert(0, str(REPO / "geospatial" / "src"))

from civitas_geo.models import ExposureContext
from civitas_risk.contracts import RiskContext
from civitas_risk.features import (
    FEATURE_KEYS,
    assemble_feature_vector,
    normalize_category,
)
from civitas_risk.severity import rule_severity, severity_level

OUT_DIR = REPO / "datasets" / "generated"
MANIFEST_DIR = REPO / "datasets" / "manifests"
OUT_FILE = OUT_DIR / "risk_samples.jsonl"
MANIFEST_FILE = MANIFEST_DIR / "risk_samples.manifest.json"

SEED = 7
N_SAMPLES = 400
NOISE_SIGMA = 0.05

CATEGORIES = ["pothole", "water_leak", "garbage", "streetlight", "fallen_tree"]
TRAFFIC = ["low", "moderate", "high"]
DESCRIPTIONS = {
    "pothole": ["deep pothole causing accidents", "road damage on main road", "pothole near market"],
    "water_leak": ["water pipe burst on road", "leakage flooding the footpath", "water on road"],
    "garbage": ["garbage overflowing", "waste pile at market", "trash not collected"],
    "streetlight": ["streetlight flickering", "light not working at night", "dark stretch at metro"],
    "fallen_tree": ["tree fallen across path", "uprooted tree on footpath", "tree blocking road"],
}
ELECTRIC_TEXT = ["electric wire hanging", "broken pole with live wire"]
ACCESS_TEXT = ["blocks the school pathway entrance"]


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(row_count: int) -> None:
    manifest = {
        "schema_version": 1,
        "name": "risk_samples",
        "description": "Synthetic labeled severity/priority samples for ML "
        "calibration training. Labels = rule severity + Gaussian noise.",
        "kind": "synthetic",
        "generator": "datasets/generators/generate_risk_dataset.py",
        "generation_command": "python datasets/generators/generate_risk_dataset.py",
        "seed": SEED,
        "row_count": row_count,
        "generated_file": "datasets/generated/risk_samples.jsonl",
        "sha256": sha256_hex(OUT_FILE),
        "columns": {
            "report_id": "str", "category": "canonical category", "description": "str",
            "features": f"normalized features: {FEATURE_KEYS}",
            "rule_severity": "rule scorer output", "severity_label": "rule + noise target",
            "severity_level": "label level", "open_hours": "float", "repeated_reports": "int",
        },
        "usage": "Train ml/risk logistic calibration (train_severity.py). Synthetic "
        "labels only; swap for human-reviewed labels before production.",
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def random_exposure(rng: random.Random, i: int) -> ExposureContext:
    # Deterministic per-index variety
    school_m = rng.choice([None, 60.0, 120.0, 350.0, 800.0, 2000.0, 5000.0])
    hospital_m = rng.choice([None, 250.0, 700.0, 1500.0, 4000.0])
    traffic = rng.choice(TRAFFIC)
    junction = rng.choice([0.0, 0.3, 1.2, 2.5, 4.0])
    pathway = rng.random() < 0.2
    return ExposureContext(
        nearest_school_m=school_m,
        nearest_hospital_m=hospital_m,
        junction_density_1km=junction,
        nearest_waterbody_m=rng.choice([None, 400.0, 1500.0]),
        pathway_proximity=pathway,
        traffic_exposure=traffic,  # type: ignore[arg-type]
        sources=[f"generator-{i}"],
        inference=[],
    )


def make_sample(rng: random.Random, i: int) -> dict[str, object]:
    category = CATEGORIES[i % len(CATEGORIES)]
    desc = rng.choice(DESCRIPTIONS[category])
    if rng.random() < 0.15:
        desc += " " + rng.choice(ELECTRIC_TEXT)
    if category == "fallen_tree" and rng.random() < 0.25:
        desc += " " + rng.choice(ACCESS_TEXT)
    ctx = RiskContext(
        report_id=f"syn-{i:04d}",
        category=category,
        description=desc,
        exposure=random_exposure(rng, i),
        repeated_reports=rng.choice([1, 1, 2, 3, 5, 8]),
        open_hours=rng.choice([0.5, 6.0, 30.0, 120.0, 400.0, 800.0]),
        rain_intensity_mm_h=rng.choice([None, None, 3.0, 15.0, 30.0, 70.0]),
        electrical_risk_text=False,  # text markers already in desc
        accessibility_blocked=False,
    )
    features, _ = assemble_feature_vector(ctx)
    rule_score, _, _ = rule_severity(ctx)
    label = max(0.0, min(1.0, rule_score + rng.gauss(0.0, NOISE_SIGMA)))
    return {
        "kind": "risk_sample",
        "report_id": ctx.report_id,
        "category": normalize_category(ctx.category),
        "description": ctx.description,
        "features": features,
        "rule_severity": round(rule_score, 4),
        "severity_label": round(label, 4),
        "severity_level": severity_level(rule_score),
        "open_hours": ctx.open_hours,
        "repeated_reports": ctx.repeated_reports,
    }


def main() -> None:
    rng = random.Random(SEED)
    samples = [make_sample(rng, i) for i in range(N_SAMPLES)]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as fh:
        for row in samples:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_manifest(len(samples))
    print(f"wrote {len(samples)} risk samples to {OUT_FILE}")


if __name__ == "__main__":
    main()