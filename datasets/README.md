# Datasets

Large datasets and media are not committed to Git. Commit only manifests, source references, label definitions, checksums, generation scripts, and small non-sensitive fixtures.

## What lives here

| Path | Contents |
|---|---|
| `generators/` | Deterministic seed-controlled dataset generators |
| `manifests/` | Committed manifests with row counts, columns and sha256 checksums |
| `generated/` | Output artifacts (gitignored; reproducible via the generators) |

## Generators

- `generate_duplicates.py` — synthetic labeled civic reports with
  ground-truth duplicate clusters plus detector pair evaluations for
  precision/recall benchmarking (see `generators/README.md`).
- `generate_risk_dataset.py` — 400 labeled severity samples (rule score +
  Gaussian noise) for the `ml/risk` ML calibration layer.
- `generate_landmarks.py` — deterministic demo-city landmark fixture for
  offline flows and PostGIS seeding.

## Verification

After regenerating, verify outputs against their manifests:

```bash
sha256sum datasets/generated/duplicate_pairs.jsonl
# must equal the sha256 recorded in datasets/manifests/duplicate_pairs.manifest.json
```

Update a manifest only when a generator's behavior or seed intentionally
changes.