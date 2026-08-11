# Dataset Generators

Deterministic, seed-controlled scripts that produce the labeled and fixture
datasets used by the ml layer. Generated files land in `datasets/generated/`
(not committed — see root `.gitignore`); manifests with checksums are
committed so output integrity is verifiable.

## Duplicate pairs (`generate_duplicates.py`)

Synthetic civic reports: 30 base incidents with 0-3 duplicates each (GPS
jitter, time offsets, paraphrased text, occasionally wrong/missing category)
plus 15 unrelated singletons. Also runs the duplicate detector over all
plausible pairs and stores `same_cluster` ground truth next to
`model_score` / `model_decision` for honest precision/recall benchmarking.

```bash
python datasets/generators/generate_duplicates.py
```

## Risk samples (`generate_risk_dataset.py`)

400 labeled severity samples across all five categories with randomized
school/hospital/traffic exposure, report pressure, longevity, weather and
electrical text markers. The label is the rule severity score plus Gaussian
noise (σ=0.05). Trains the ML calibration layer via
`python -m civitas_risk.train_severity`.

```bash
python datasets/generators/generate_risk_dataset.py
```

**Caveat:** labels are synthetic. They are fine for exercising the training
pipeline and measuring drift, but production calibration must be trained on
human-reviewed labels.

## Landmarks (`generate_landmarks.py`)

Exports the deterministic demo-city landmark set as JSONL for seeding the
PostGIS `landmarks` table and offline tests.

```bash
python datasets/generators/generate_landmarks.py
```

## Manifest contract

Every generator writes `datasets/manifests/<name>.manifest.json`:

```json
{ "schema_version": 1, "name": "...", "kind": "synthetic|fixture",
  "generator": "...", "generation_command": "...", "seed": <int>,
  "row_count": <int>, "generated_file": "...", "sha256": "<hex>",
  "columns": {...}, "usage": "..." }
```

Verify after regeneration: `sha256sum datasets/generated/<file>` must match
the manifest value; update the manifest only when the generator's behavior
(or seed) intentionally changes.