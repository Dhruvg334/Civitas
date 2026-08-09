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

## Phase 3 — Computer vision pipeline (COMMIT 8d3fb95)

- `ml/vision` package (`civitas-vision`, numpy + Pillow + optional OpenCV):
  - `quality` — blur gate via variance-of-Laplacian (calibrated threshold
    0.001 on [0,1] grayscale), exposure, resolution, saturation checks.
  - `frames` — video frame extraction + deterministic key-frame selection by
    sharpness/exposure.
  - `features` — 19 real classical measurements (Laplacian variance, edge
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

## Phase 4 — Embeddings and the same-incident layer (COMMIT c7ca129)

Product question this phase answers: "do these two reports describe the same
real-world incident?" — NOT "do these two sentences look similar?".

- `ml/duplicates` — per-report embeddings combining both modalities and the
  raw geospatial signals:
  - `embeddings.ClassicalImageEmbedder` — deterministic image embedding:
    the 19 civitas-vision pixel measurements + 32-bin hue + 32-bin
    saturation histogram, L2-normalized (dim 83). Method and basis are
    recorded on every `ImageEmbedding`; missing civitas-vision degrades to a
    colour-only vector (recorded, never fabricated). `ProviderEmbedder`
    remains the swap-in point for CLIP-class models.
  - `embeddings.build_report_embeddings` / `ReportEmbeddings` — one record
    per report fusing text embedding, image embedding, GPS, timestamp,
    category and landmark ids.
  - `similarity.incident_gate` — hard geospatial gate: the same-incident
    claim must be physically plausible first (distance <= 2000 m AND time
    delta <= 72 h) using only observed geospatial signals; language and
    pixels are never consulted outside the gate.
  - `similarity.incident_similarity` — the Phase 4 answer: gate -> fused
    weighted score (text/image embeddings + category + GPS + time +
    landmark) -> threshold decision with near-threshold and conflicting-
    category escalations to human review. Missing GPS/timestamp -> answered
    "cannot confirm" and escalated, never guessed. `INCIDENT_ANCHORED_WEIGHTS`
    preset (geospatial + temporal dominate) sits beside the balanced default.
  - `benchmark` — synthetic same-incident pairs (same cell, burst window,
    category, landmarks; different descriptions and photo variants) vs
    genuinely distinct pairs; precision/recall/F1/accuracy report.
- `civitas_geo.aggregates` — reports-per-cell transactional density history:
  - `reports_per_cell_sql` — ST_SnapToGrid grouping (metres -> degrees via
    cell_size / 111320), recency `since` + boundary envelope filters, one row
    per (cell, category).
  - `reports_per_cell_memory` / `DensityAggregator` — identical floor-anchored
    math offline; same cell_id as PostGIS mode (grid origin (0, 0));
    mode labels geometry provenance ("postgis"/"memory"/"unavailable").
  - Feature wiring: `cell_report_density_norm = min(1, cell_count / 50)` with
    provenance; absent density is recorded as absent, not invented
    (`raw.cell_report_density_cell_count = -1`).
- Verified: 93 geospatial + 42 duplicates + 27 vision tests (162 total);
  ruff + mypy clean (13 + 11 + 9 files); demo steps 7 (embedding +
  same-incident answers, 20/20 synthetic pairs correct) and 8 (density
  aggregates); duplicate pair "rep-1 vs rep-2" scores 0.88,
  "rep-1 vs rep-3" 0.34 — both answered with the gate visible in the basis.

## Verification (all passing)

```bash
cd geospatial && python -m pytest tests          # 93 passed
cd geospatial && python -m ruff check src tests  # clean
cd geospatial && python -m mypy src              # clean (13 files)
cd ml/duplicates && python -m pytest tests       # 42 passed
cd ml/duplicates && python -m ruff check src tests  # clean
cd ml/duplicates && python -m mypy src           # clean (11 files)
cd ml/vision && python -m pytest tests           # 27 passed
cd ml/vision && python -m ruff check src tests   # clean
cd ml/vision && python -m mypy src               # clean (9 files)
python ml/demo_end_to_end.py                     # full trace incl. CV + Phase 4 steps
```

## Commits on this branch

- `7cd21fe` Add ML intelligence layer: duplicate detection, geospatial reasoning, severity/priority
- `ce4af51` Phase 1/12 complete
- `32ff126` Track ML layer phase plan and progress notes
- `43c7f0a` Phase 2/12 completed
- `8d3fb95` Phase 3/12 completed
- `5aed379` Fix feature hash constants in phase notes