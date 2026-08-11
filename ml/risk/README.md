# Severity and Priority (ml/risk)

Separate, explainable assessment of **severity** (how dangerous) and
**priority** (how urgently to respond), built on engineered features that
combine the geospatial layer with report pressure.

## Feature engineering (`features.py`)

All features are normalized to [0, 1] with per-feature provenance strings:
`assemble_feature_vector(ctx)` returns `(features, provenance)`.

| Feature | Inputs | Meaning |
|---|---|---|
| `category_base` | canonical category | static base hazard (pothole 0.55, water 0.50, garbage 0.45, streetlight 0.35, fallen tree 0.65) |
| `school_proximity` | `ExposureContext.nearest_school_m` | children exposure: ≤300 m → 1.0, ≤1 km → 0.5 |
| `hospital_proximity` | `ExposureContext.nearest_hospital_m` | emergency asset proximity → urgency |
| `traffic` | `ExposureContext.traffic_exposure` | road class / junction density from map reasoning |
| `electrical` | text markers + explicit flag | electrocution hazard (labelled inference) |
| `public_health` | category + rain | garbage overflow / contamination / flooding |
| `accessibility` | explicit flag + pathway landmark | blocked pedestrian/emergency access |
| `repeated_reports` | duplicate-cluster size | `1 - exp(-k/2)` pressure |
| `longevity` | hours open | `tanh(h/336)` time-unresolved pressure |
| `weather` | rain intensity | escalation for water/fallen-tree only |

## Severity (rules + optional ML calibration)

- `rule_severity()`: base + bounded additive modifiers (electrical +0.15,
  school ≤300 m +0.15, public health +0.15, accessibility +0.10, high
  traffic +0.10, rain +0.10, hospital ≤500 m +0.05), clamped; buckets
  low < 0.35 ≤ medium < 0.60 ≤ high < 0.80 ≤ critical.
- `LogisticCalibrator`: a dependency-free logistic regression that learns a
  calibration layer on the synthetic labeled dataset. `SeverityAssessor`
  blends it explicitly (`ml_blend_weight`), and the rule score always
  participates — the ML layer corrects, never replaces, the rules.
- Training: `python -m civitas_risk.train_severity --dataset <risk_samples.jsonl>`
  writes `ml/risk/artifacts/severity_coefficients.json` with train/heldout
  RMSE. Metrics on synthetic labels; production versions must be trained on
  reviewed labels (see Known limitations).

## Priority (separate decision)

`PriorityAssessor`:
`priority = 0.45·severity + 0.35·urgency + 0.15·reports + 0.05·longevity`,
where urgency = 0.45·school + 0.30·traffic + 0.25·hospital. Tiers:
P1 ≥ 0.80, P2 ≥ 0.60, P3 ≥ 0.40, P4. Every outcome lists the weight
composition and each contributing factor with provenance.

## Why severity ≠ priority

A streetlight outage next to a hospital is low severity but elevated
priority; a garbage overflow behind a market is medium severity and P3/P4.
The two scores are produced and explained independently.

## Run

```bash
pip install -e "./ml/risk[dev]" -e "./geospatial[dev]"
pytest ml/risk
python -m civitas_risk.train_severity --dataset datasets/generated/risk_samples.jsonl
```

## Known limitations

- Training labels are synthetic (generated from the rule scorer + noise);
  the ML blend must be re-trained on human-reviewed labels before production
  use and its blend weight kept conservative until then.
- No real-time traffic or weather feeds yet; `rain_intensity_mm_h` and road
  data are external inputs fed through `RiskContext`/`ExposureContext`.
- `junction_density_1km` is a landmark-count heuristic, not a road-graph
  measurement.