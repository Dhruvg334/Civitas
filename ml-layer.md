# Civitas ML Layer — Implemented Work

Branch: `ml-layer`. This file records only implemented, verified work.

## Phase 1 — Geospatial feature engineering (COMMIT ce4af51)

- `geospatial/src/civitas_geo/feature_engineering.py` — evidence-only
  `GeospatialFeatureVector`: 24+ normalized `[0,1]` features, per-feature
  provenance, warnings, basis; no decision fields.
- Blocks: location validity, school/hospital/traffic/junction exposure,
  population proxy, neighbourhood report stats, hour/weekend temporality,
  canonical category one-hot.
- `geospatial/tests/test_feature_engineering.py` + exports + demo step 2b
  + README documentation.

## Phase 2 — Spatial foundation (PostGIS boundary, candidate retrieval, gate)

- `geospatial/src/civitas_geo/boundary.py` + `OperationalBoundary` in
  `models.py` — the shared PostGIS Boundary consumed by validation and every
  retrieval query (envelope pre-filter as `&& ST_MakeEnvelope`).
- `geospatial/src/civitas_geo/candidates.py` + `CandidateSearchSpec` /
  `CandidateRecord` / `CandidateListResult` — retrieval windows for the ML
  duplicate engine: reports within X metres and Y hours, category filter,
  exclusions, boundary; ordered by distance; every candidate carries
  coordinates, timestamps, category, `duplicates_seen`, time-window flag and
  nearest-landmark context per kind (`enrich_landmark_context`).
- `geospatial/src/civitas_geo/queries.py::candidate_incidents_sql()` —
  parameterized PostGIS window query: `ST_DWithin` + recency
  `make_interval(hours)` + boundary envelope + `hours_since_reported`.
- `geospatial/src/civitas_geo/validation.py::gate_for_pipeline()` — detects
  missing/malformed, placeholder and off-coverage coordinates and blocks them
  from the spatial pipeline (reasons: `rejected_malformed`,
  `rejected_placeholder`, `rejected_out_of_coverage`, `rejected_implausible`).
- `database/migrations/0001_spatial_core.sql` (PostGIS + incidents + landmarks
  + GIST indexes) and `database/seed/0001_demo_landmarks.sql` (matches
  `DEMO_LANDMARKS`).
- `geospatial/tests/test_boundary_candidates.py` (20 tests; package 78
  passing) + demo step 2c (gate -> candidate list -> duplicate engine).
- `CandidateRetriever` prefers PostGIS when an executor is supplied; memory
  mode is labeled `mode="memory"` and reports untimestamped records in
  `basis`.

## Verification (all passing)

```bash
cd geospatial
python -m pytest tests            # 78 passed
python -m ruff check src tests    # clean
python -m mypy src                # clean (12 files)
python ml/demo_end_to_end.py      # full trace incl. gate + candidate list
```

## Commits on this branch

- `7cd21fe` Add ML intelligence layer: duplicate detection, geospatial reasoning, severity/priority
- `ce4af51` Phase 1/12 complete
- `32ff126` Track ML layer phase plan and progress notes
- `PHASE2` Phase 2/12 completed