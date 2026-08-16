"""Export the deterministic demo landmark set as a data artifact.

Usage:
    python datasets/generators/generate_landmarks.py
Outputs:
    datasets/generated/landmarks.jsonl
    datasets/manifests/landmarks.manifest.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "geospatial" / "src"))

from civitas_geo.landmarks import DEMO_LANDMARKS

OUT_DIR = REPO / "datasets" / "generated"
MANIFEST_DIR = REPO / "datasets" / "manifests"
OUT_FILE = OUT_DIR / "landmarks.jsonl"
MANIFEST_FILE = MANIFEST_DIR / "landmarks.manifest.json"


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    rows = [lm.model_dump() for lm in DEMO_LANDMARKS]
    with OUT_FILE.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {
        "schema_version": 1,
        "name": "landmarks",
        "description": "Deterministic demo-city landmark set backing offline "
        "duplicate/severity flows. Production landmarks come from the PostGIS "
        "landmarks table (see geospatial/README.md).",
        "kind": "fixture",
        "generator": "datasets/generators/generate_landmarks.py",
        "generation_command": "python datasets/generators/generate_landmarks.py",
        "row_count": len(rows),
        "generated_file": "datasets/generated/landmarks.jsonl",
        "sha256": sha256_hex(OUT_FILE),
        "columns": {"landmark_id": "str", "name": "str", "kind": "school|hospital|junction|market|park|waterbody|metro_station|pathway", "latitude": "float", "longitude": "float", "radius_m": "float"},
        "usage": "Seed the PostGIS landmarks table and offline tests.",
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} landmarks to {OUT_FILE}")


if __name__ == "__main__":
    main()