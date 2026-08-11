"""Generate a deterministic labeled duplicate-pairs dataset for Civitas.

Produces synthetic but realistic civic reports: base incidents with 0-3
duplicate reports (GPS jitter, temporal offset, paraphrased text, sometimes
wrong category) plus unrelated singletons, and evaluates the duplicate
detector end-to-end, emitting pair-level ground truth and model outputs.

Usage:
    python datasets/generators/generate_duplicates.py
Outputs:
    datasets/generated/duplicate_pairs.jsonl   (labeled dataset + model rows)
    datasets/manifests/duplicate_pairs.manifest.json
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml" / "duplicates" / "src"))
sys.path.insert(0, str(REPO / "geospatial" / "src"))

from civitas_duplicates import DuplicateDetector, ReportLike  # noqa: E402
from civitas_geo import distance as geo  # noqa: E402

OUT_DIR = REPO / "datasets" / "generated"
MANIFEST_DIR = REPO / "datasets" / "manifests"
OUT_FILE = OUT_DIR / "duplicate_pairs.jsonl"
MANIFEST_FILE = MANIFEST_DIR / "duplicate_pairs.manifest.json"

SEED = 2026
T0 = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)
BASE_COUNT = 25
SINGLETON_COUNT = 15

CATEGORY_TEMPLATES: dict[str, list[str]] = {
    "pothole": [
        "deep pothole near the school gate {loc}",
        "big pothole before the school {loc} causing two wheelers to slip",
        "road damage with a large pothole {loc}",
        "pothole outside the school entrance {loc}, cars are braking suddenly",
    ],
    "water_leak": [
        "water leakage at {loc}, road is flooding",
        "burst pipe leaking water {loc}",
        "water flowing from a broken main {loc}",
        "flooding {loc}, water pipe burst",
    ],
    "garbage": [
        "garbage overflowing at {loc}",
        "waste pile {loc} not collected for days",
        "trash overflowing {loc}, bad smell",
    ],
    "streetlight": [
        "streetlight not working {loc}",
        "broken street light {loc}",
        "dark stretch {loc}, light pole damaged",
    ],
    "fallen_tree": [
        "fallen tree blocking the pathway {loc}",
        "tree down across the path {loc}",
        "uprooted tree blocking the footpath {loc}, walkers cannot pass",
    ],
}

LOCATION_TERMS = {
    "school gate": "near sunrise school",
    "kingsway junction": "at kingsway junction",
    "old bazaar market": "at old bazaar market",
    "civic centre metro": "outside civic centre metro",
    "central hospital road": "on central hospital road",
}

ANCHORS: list[dict[str, object]] = [
    {"name": "school gate", "lat": 28.6139, "lon": 77.2090, "landmark_ids": ["lm-school-01", "lm-path-01"]},
    {"name": "kingsway junction", "lat": 28.6160, "lon": 77.2130, "landmark_ids": ["lm-junction-01"]},
    {"name": "old bazaar market", "lat": 28.6120, "lon": 77.2180, "landmark_ids": ["lm-market-01"]},
    {"name": "civic centre metro", "lat": 28.6190, "lon": 77.2165, "landmark_ids": ["lm-metro-01"]},
    {"name": "central hospital road", "lat": 28.6100, "lon": 77.2050, "landmark_ids": ["lm-hosp-01"]},
]


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(row_count: int, columns: dict[str, str]) -> None:
    manifest = {
        "schema_version": 1,
        "name": "duplicate_pairs",
        "description": "Synthetic labeled civic reports with ground-truth duplicate "
        "clusters; model pair evaluations included for detector benchmarking.",
        "kind": "synthetic",
        "generator": "datasets/generators/generate_duplicates.py",
        "generation_command": "python datasets/generators/generate_duplicates.py",
        "seed": SEED,
        "row_count": row_count,
        "generated_file": "datasets/generated/duplicate_pairs.jsonl",
        "sha256": sha256_hex(OUT_FILE),
        "columns": columns,
        "usage": "Benchmark duplicate precision/recall; calibrate ScoringConfig "
        "thresholds. Do not use as production training signal without "
        "human-review labels.",
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def paraphrase(rng: random.Random, category: str, variation: int, location_term: str) -> str:
    pool = CATEGORY_TEMPLATES[category]
    return pool[(variation) % len(pool)].format(loc=location_term)


def make_report(
    rng: random.Random,
    report_id: str,
    category: str,
    anchor: dict[str, object],
    jitter_m: float,
    offset_h: float,
    drop_or_flip_category: bool,
    true_cluster: str,
    role: str,
) -> dict[str, object]:
    lat0 = float(anchor["lat"])
    lon0 = float(anchor["lon"])
    lat, lon = geo.offset_point(lat0, lon0, jitter_m, jitter_m * 0.6)
    cat = category
    if drop_or_flip_category and rng.random() < 0.12:
        cat = None if rng.random() < 0.4 else rng.choice(
            [c for c in CATEGORY_TEMPLATES if c != category]
        )
    submitted_at = T0 + timedelta(hours=offset_h)
    location_term = LOCATION_TERMS[str(anchor["name"])]
    return {
        "report_id": report_id,
        "description": paraphrase(rng, category, rng.randint(0, 3), location_term),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "submitted_at": submitted_at.isoformat(),
        "category": cat,
        "landmark_ids": list(anchor["landmark_ids"]),
        "true_cluster_id": true_cluster,
        "role": role,
    }


def main() -> None:
    rng = random.Random(SEED)
    reports: list[dict[str, object]] = []
    clusters: dict[str, bool] = {}

    for i in range(BASE_COUNT):
        # Congruent cycling: category = i mod 5, anchor = (i // 5) mod 5.
        # Same category => different anchor, so distinct incidents never
        # collide at the same spot in the synthetic world.
        category = list(CATEGORY_TEMPLATES)[i % len(CATEGORY_TEMPLATES)]
        anchor = ANCHORS[(i // len(CATEGORY_TEMPLATES)) % len(ANCHORS)]
        cluster_id = f"inc-{i:03d}"
        clusters[cluster_id] = True
        base_id = f"r-{i:04d}-base"
        reports.append(
            make_report(rng, base_id, category, anchor, jitter_m=5.0, offset_h=0.0,
                        drop_or_flip_category=False, true_cluster=cluster_id, role="base")
        )
        dup_count = rng.choice([0, 1, 1, 2, 3])
        for d in range(dup_count):
            dup_id = f"r-{i:04d}-dup{d}"
            reports.append(
                make_report(
                    rng, dup_id, category, anchor,
                    jitter_m=rng.uniform(10.0, 70.0),
                    offset_h=rng.uniform(0.5, 36.0),
                    drop_or_flip_category=True,
                    true_cluster=cluster_id,
                    role="duplicate",
                )
            )

    for k in range(SINGLETON_COUNT):
        sid = f"s-{k:04d}"
        # Category from cycle offset, but anchor intentionally DIFFERENT so
        # singletons are spatially separated from same-category bases.
        category = list(CATEGORY_TEMPLATES)[(BASE_COUNT + k) % len(CATEGORY_TEMPLATES)]
        anchor = ANCHORS[(BASE_COUNT + k + 2) % len(ANCHORS)]
        reports.append(
            make_report(
                rng, sid, category, anchor,
                jitter_m=rng.uniform(300.0, 900.0),
                offset_h=rng.uniform(1.0, 100.0),
                drop_or_flip_category=True,
                true_cluster=sid,
                role="singleton",
            )
        )

    detector = DuplicateDetector()
    model_rows: list[dict[str, object]] = []
    cluster_of = {str(r["report_id"]): str(r["true_cluster_id"]) for r in reports}
    by_id: dict[str, ReportLike] = {}
    for rec in reports:
        by_id[str(rec["report_id"])] = ReportLike(
            report_id=str(rec["report_id"]),
            description=str(rec["description"]),
            latitude=float(rec["latitude"]),
            longitude=float(rec["longitude"]),
            submitted_at=datetime.fromisoformat(str(rec["submitted_at"])),
            category=rec["category"],
            landmark_ids=list(rec["landmark_ids"]),
        )
    ordered = list(by_id.values())
    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            a, b = ordered[i], ordered[j]
            if abs(
                (a.submitted_at - b.submitted_at).total_seconds()
            ) > 100 * 3600 and geo.haversine_m(a.latitude, a.longitude, b.latitude, b.longitude) > 3000:
                continue
            res = detector.evaluate_pair(a, b)
            model_rows.append(
                {
                    "a": a.report_id,
                    "b": b.report_id,
                    "same_cluster": cluster_of[a.report_id] == cluster_of[b.report_id],
                    "model_score": res.score,
                    "model_decision": res.is_duplicate,
                    "model_review": res.requires_review,
                }
            )

    rows = reports + [
        {
            "kind": "duplicate_evaluation",
            **{k: row[k] for k in ("a", "b", "same_cluster", "model_score", "model_decision")},
        }
        for row in model_rows
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    truth = sum(1 for r in model_rows if r["same_cluster"])
    tp = sum(1 for r in model_rows if r["same_cluster"] and r["model_decision"])
    model_pos = sum(1 for r in model_rows if r["model_decision"])
    flagged = sum(1 for r in model_rows if r["model_review"])
    review_recall = sum(
        1 for r in model_rows if r["same_cluster"] and (r["model_decision"] or r["model_review"])
    )
    precision = (tp / model_pos) if model_pos else 0.0
    recall = (tp / truth) if truth else 0.0
    write_manifest(
        len(rows),
        {
            "reports": "report_id, description, latitude, longitude, submitted_at, "
            "category, landmark_ids, true_cluster_id, role",
            "duplicate_evaluation": "a, b, same_cluster, model_score, model_decision, model_review",
        },
    )
    print(
        f"wrote {len(reports)} reports, {len(model_rows)} evaluated pairs to {OUT_FILE}\n"
        f"duplicate detection: precision={precision:.1%} recall={recall:.1%} "
        f"({tp}/{truth} true pairs recovered); {flagged} pairs flagged for review "
        f"(auto+review recall={review_recall / truth:.1%})"
    )


if __name__ == "__main__":
    main()