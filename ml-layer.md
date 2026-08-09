# Civitas ML Layer — Implemented Work

Branch: `ml-layer`. This file records only implemented, verified work.

## Phase 1 — Geospatial feature engineering (COMMIT ce4af51)

- `geospatial/src/civitas_geo/feature_engineering.py` — evidence-only
  `GeospatialFeatureVector`: 24+ normalized `[0,1]` features, per-feature
  provenance, warnings, basis; no decision fields.
- Blocks: location validity, school/hospital/traffic/junction exposure,
  population proxy, neighbourhood report stats, hour/weekend temporality,
  canonical category one-hot.
- Tests, exports, demo step 2b, README.

## Phase 2 — Spatial foundation (COMMIT 43c7f0a)

- `civitas_geo.boundary` + `OperationalBoundary` — PostGIS Boundary shared by
  validation and retrieval (envelope pre-filter `&& ST_MakeEnvelope`).
- `civitas_geo.candidates` — candidate windows for the duplicate engine:
  radius X m, recency Y h, category, boundary; `CandidateRecord` carries
  coordinates, timestamps, category, duplicates_seen, window flag and
  nearest-landmark context; `CandidateRetriever` (PostGIS/memory).
- `civitas_geo.queries.candidate_incidents_sql` — parameterized window query
  (`ST_DWithin` + `make_interval(hours)` + boundary + `hours_since_reported`).
- `civitas_geo.validation.gate_for_pipeline` — rejects malformed, placeholder
  and off-coverage coordinates before the spatial pipeline (explicit reasons).
- `database/migrations/0001_spatial_core.sql`, `database/seed/0001_demo_landmarks.sql`.
- Tests (78 package), demo step 2c (gate -> candidates -> duplicate engine).

## Phase 3 — Computer vision pipeline (COMMIT <pending>)

- `ml/vision` package (`civitas-vision`, numpy + Pillow + optional OpenCV):
  - `quality` — blur gate via variance-of-Laplacian (calibrated threshold
    0.001 on [0,1] grayscale), exposure, resolution, saturation checks.
  - `frames` — video frame extraction + deterministic key-frame selection by
    sharpness/exposure.
  - `features` — 18 real classical measurements (Laplacian variance, edge
    density, vertical/flow/banding ratios, blue/green dominance, dark
    low-texture share, bright-peak geometry, color scatter, ...).
  - `classifier` — k-NN (k=3) over z-scored features with softmax
    confidence and per-frame vote merge; secondary categories at proba >= 0.25.
  - `evidence` — observable-evidence strings from measurement rules
    (standing/flowing water, pothole cavity, waste pile, streetlight bulb,
    fallen trunk) with documented thresholds.
  - `detector` — `VisualIntelligencePipeline`: media -> quality -> frames ->
    classify -> evidence -> the product JSON
    (primary_category, secondary_categories, observable_evidence, confidence).
  - `benchmark` — deterministic synthetic scene corpus (5 categories, flow
    variant, blur negatives) + evaluation report (accuracy, macro-F1,
    per-class metrics, confusion matrix).
- Verified: 27 tests; ruff + mypy clean; benchmark accuracy 1.000 /
  macro-F1 1.000 on 40 held-out synthetic images (69 earlier runs > 0.85);
  demo steps 5 and 6.

## Verification (all passing)

```bash
cd geospatial && python -m pytest tests          # 78 passed
cd ml/vision && python -m pytest tests           # 27 passed
cd ml/vision && python -m ruff check src tests   # clean
cd ml/vision && python -m mypy src               # clean (9 files)
python ml/demo_end_to_end.py                     # full trace incl. CV steps
```

## Commits on this branch

- `7cd21fe` Add ML intelligence layer: duplicate detection, geospatial reasoning, severity/priority
- `ce4af51` Phase 1/12 complete
- `32ff126` Track ML layer phase plan and progress notes
- `43c7f0a` Phase 2/12 completed
- `8d3fb95` Phase 3/12 completed