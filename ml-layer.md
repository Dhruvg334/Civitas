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

## Phase 5 — Duplicate detection engine (COMMIT 288b1b8)

The 90-second version: three citizens report the same street problem within
75 minutes near Sunrise School — R1 "water leaking from the main pipe near
the school gate" at 10:30, R2 "flooding on the road in front of the school"
at 11:00, R3 "road surface breaking up after the water" at 11:45. The engine
retrieves all three as candidates (800 m / 24 h window), scores each pair,
explains every decision with a ✓ checklist, and merges the trio into one
incident (CL-018) instead of three. The two water reports count as "matching
categories"; the road-damage report is caught by *related categories*
(water damage erodes and washes out road surface) — the same physical
incident described from its effect, not its cause. Image similarity shows
the honest picture: 0.99 for two photos of the same leak, 0.93 for the
water photo vs the road-damage photo (the scenes share the same road and
background, so the model does not claim they are identical).

- `ml/duplicates/src/civitas_duplicates/detector.py` — `DuplicateDetector`,
  the first *engine* (operator-facing object) in the ML layer. It combines
  every earlier module: candidate window, per-pair features, weighted
  scoring, clustering, and now the evaluation harness. Constructor takes
  `landmark_index` for landmark anchoring and `density_records` for
  incident-density context; per-pair or per-cluster work, the demo and the
  evaluation harness all call the same object.
- `pair_features` (in `similarity.py`) with two new evidence families:
  - incident density — how busy the neighbourhood cell is (quiet cell here:
    0.03 of 1.0; a busy cell lowers confidence, it never overrides evidence).
  - related categories — water leak ↔ flooding, garbage ↔ water leak,
    pothole ↔ water leak are scored as *related* (0.5 weight, with an
    explicit note "water damage erodes and wash out the road surface")
    instead of either "match" or "unrelated". `RELATED_CATEGORIES` lives in
    `signals.py` with the same evidence-style documentation as the CV rules.
  - `duplicate_reasons` builds the ✓ checklist (GPS inside radius, time
    inside window, shared landmark anchoring, image/text similarity above
    evidence bar, matching or related categories, density context) — every
    score change is explainable line by line.
- `evaluation.py` — the measurable layer: deterministic `LabelledScenario`
  (seeded, 18 pairs: 6 same-incident, 6 genuinely distinct, 6 ambiguous
  co-located-but-different-category) and `evaluate_engine` which reports
  precision / recall / F1 / accuracy plus the two failure types people care
  about — false merges (auto-merged negatives) and false splits (positives
  not merged). Ambiguous pairs are **escalated to human review, never
  auto-merged**; the harness counts how many flagged pairs actually went to
  review. Current result on the labelled set: precision 1.000, recall
  1.000, F1 1.000, false merges 0, false splits 0, 6/6 ambiguous pairs sent
  to review.
- `cluster.py` — deterministic incident-id naming (`CL-001`, `CL-018`, ...)
  so clusters are addressable in the product and reproducible in the demo.
- Phase 4 embedding fix (recorded here because it surfaced during Phase 5
  testing): the classical image feature block was not feature-wise scaled,
  so highest-magnitude measurements (hue variance ~ 1e3-1e4) dominated the
  L2 norm and *visually different* images scored ~1.00. The 19 classical
  measurements are now standardized by population scale constants fitted on
  the synthetic benchmark set (5 categories x 8 seeds, documented in
  `embeddings._CLASSICAL_FEATURE_SCALES` as a known limitation); same-incident
  images still score 0.99, different-category images now score 0.93. Phase 4
  verification numbers stand except "rep-1 vs rep-3" now scores 0.31 (was
  0.34) — still correctly "different incident".
- Demo step 9 (`ml/demo_end_to_end.py`) walks the whole story above with
  real numbers: candidate retrieval, the three pair explanations, the
  CL-018 merge, and the full evaluation table. Division of labour with this
  file: `demo_end_to_end.py` is the narrated walk-through (one scenario,
  human-readable); `ml-layer.md` is the implementation record (what exists,
  where, verified how). Both must stay in sync when numbers move.

## Phase 6 — Severity feature engineering (COMMIT c177c39)

The 90-second version: the water leak outside Sunrise School is now ONE
incident (CL-018, three reports merged in Phase 5). Phase 6 asks the next
question: **how bad is it?** The incident feature engineer pulls the three
evidence families together — what the camera saw (standing water, ~49% of
the road surface flooded), where it is (at the school gate, 584 m from the
hospital, moderate traffic), and what the crowd says (3 neighbours reported
it in 75 minutes). That becomes typed features: `active_water_flow = 1`,
`water_coverage = 0.49`, `school_distance = 0 m`, `traffic_exposure =
moderate`, `report_count = 3`, `duration = 1.2 h`. The severity model turns
them into **Severity score 78 / level HIGH** with named contributing
factors — *active road flooding*, *slip hazard*, *significant affected
area*, *near school*, *crowd corroboration*, *protracted exposure* — each
with the points it earned and the evidence line that earned them. A
**separate priority model** then answers "how urgently do we respond?"
without reusing the severity model's internals: priority 68, tier P2, its
own contributing factors (children exposure to a school at the site,
hospital 584 m away, crowd pressure, time unresolved).

- `ml/risk/src/civitas_risk/incident_features.py` — the feature
  engineering layer (evidence only, no decisions):
  - `IncidentVisualEvidence` — what the CV pipeline observed on the
    incident's photo; `from_evidence` maps the evidence strings
    ("standing water", "water flowing across road") onto the typed
    `active_water_flow` 0/1 flag and carries the flooded-area share.
  - `ConsolidatedIncident` — the Phase 5 cluster as one typed object:
    category, visual evidence, `ExposureContext` from the geospatial
    layer, report count, duration (first to last report), rain context.
  - `IncidentFeatures` — the typed feature vector: `active_water_flow`,
    `water_coverage`, `school_distance_m`, `hospital_distance_m`,
    `traffic_exposure`, `junction_density_1km`, `report_count`,
    `duration_hours`, `rain_intensity_mm_h`, plus a `provenance` string
    per feature. Missing signals are `None` with "recorded as absent,
    never invented" provenance entries — a missing school distance never
    becomes a "school 1000 m away" guess.
- `severity_model.py` — `SeverityModel` (model_version `severity-model-v1`):
  deterministic points per contributing factor (documented constants:
  category base, active flow 12, significant coverage 8, slip hazard 5,
  near-school 10, traffic 5-7, crowd up to 9, duration up to 8, heavy rain
  5), diminishing-returns squash (scale 66) so the score stays 0-100, and
  level bands (<35 low, 35-59 medium, 60-79 high, >=80 critical). Every
  factor carries `(factor name, points, evidence)` — the demo shows all of
  them. The demo incident totals 100 points -> 78 HIGH.
- `priority_model.py` — `PriorityModel` (model_version `priority-model-v1`),
  a **separate object with separate weights and factors**: 0.45 severity +
  0.30 urgency (children/emergency-asset/traffic exposure) + 0.15 crowd
  pressure + 0.10 time unresolved, tiers P1 >= 80, P2 >= 60, P3 >= 40.
  Separateness is the point of the project requirement: severity says how
  bad, priority says how urgent, and neither model can answer for the
  other (changing one never silently changes the other).
- Demo step 10 (`ml/demo_end_to_end.py`) walks the whole story: the CV
  pipeline is re-run on R1's photo for the evidence strings, the landmark
  index supplies the exposure, and both models print their scores, levels
  and factor lists with evidence lines. Division of labour stays as in
  Phase 5: the demo is the narrated walk-through, this file is the record.

## Phase 7 — Priority feature engineering (COMMIT f5732c4)

The 90-second version: Phase 6 said **how bad** the leak is; Phase 7
answers **how urgently the municipality must respond** — with a feature
engineer and model of its own. The engineer takes the same consolidated
incident (CL-018) and builds a separate ten-signal vector: severity
verdict (one-way input), school proximity, hospital proximity, traffic
exposure, population exposure, repeated reports, incident duration,
nearby incident density, category urgency, time sensitivity. Missing
inputs are recorded as 0 with a "not computed" provenance line — a
missing exposure never becomes a guessed "moderate traffic".

The priority model blends ten weights (severity 0.25, school 0.18,
hospital 0.08, traffic 0.12, population 0.07, reports 0.10, duration
0.05, density 0.05, category 0.05, time 0.05; the sum is validated to
1.0) into a 0-100 score with named reasons, each citing the exact
evidence it saw. Levels: <40 low, 40-59 medium, 60-79 high, >=80
critical. Demo: CL-018 at noon scores **Priority 64 HIGH** — school at
0 m, 3 merged reports, moderate traffic, population proxy 0.25, water
leak, daytime peak. This v2 model **supersedes the Phase 6 v1 blend**
(0.45/0.30/0.15/0.10 weights, P1-P4 tiers); the severity model is untouched.

Honesty guardrail: the score is computed, never curated. "What if it were
worse?" is answered in demo section 11 as a **labelled sensitivity walk**
(heavy-traffic junction + rain + 6 reports -> 81 CRITICAL; multi-day worst
case, 9 reports -> 91 CRITICAL) — hypothetical contexts, printed as
what-ifs, never attributed to the observed incident. A CRITICAL verdict
still goes to a human reviewer.

- `ml/risk/src/civitas_risk/priority_features.py` — Phase 7 feature
  engineering:
  - `PriorityContext` — the engineer's typed input: the consolidated
    incident plus severity verdict, population-density proxy, nearby
    density norm and the scenario clock. `PriorityFeatures` — the typed
    ten-signal vector, one field per signal, with a `provenance` string
    per signal.
  - `build_priority_features` — same raw facts as severity engineering,
    different question; every signal cites its source ("school at 0 m",
    "3 merged report(s) -> independent-pressure 0.63", "12:00 — daytime
    peak activity window").
  - `category_urgency_signal` — urgency per category (garbage overflow
    0.8, water leak 0.6, streetlight 0.2; unknown categories get the
    neutral 0.4 with a "neutral for unknown category" entry).
  - `time_sensitivity_signal` — daytime peak 07:00-19:00 = 0.8, evening
    19-22 = 0.4, night = 0.2; heavy rain (>= 20 mm/h) raises the signal
    by 0.2 (capped); an unknown hour is neutral 0.5. Deliberately
    weekday-agnostic: no hidden school-holiday assumptions.
- `priority_model.py` — `PriorityModel` (model_version
  `priority-model-v2`): `WEIGHTS` (sum validated to 1.0),
  `assess()` -> `PriorityAssessment(score, level, reasons)` where each
  `PriorityReason` is `(factor, points, evidence)`, and
  `priority_level_for`. `PriorityLevel` reuses the severity level
  literal (low/medium/high/critical) so both models speak one language.
- `tests/test_phase7_priority.py` — the pinned demo scenario: severity
  78, school 37 m, hospital 584 m, moderate traffic, population proxy
  0.255, 3 reports, 1.2 h, density 0.10, water leak, noon -> **63 HIGH**;
  saturated corner (9 reports, 96 h, dense cell) -> **>= 85 CRITICAL**;
  band boundaries 39/40/59/60/79/80; missing signals stay neutral; rain
  escalates time sensitivity; determinism; score equals the weighted sum.
- Demo steps 10+11 (`ml/demo_end_to_end.py`): step 10 reruns the whole
  evidence chain (CV on R1's photo, landmark index, nearby density) and
  prints both models with evidence-citing reasons; step 11 prints the
  ten-signal table, the model verdict (Priority 64 HIGH on the real
  grid-cell values) and the labelled what-if walk.

## Phase 8 — Resolution verification (COMMIT <fill-on-commit>)

The 90-second version: the first seven phases understand the incident —
vision, duplicates, severity, priority — and then the municipality acts.
Phase 8 is the **second ML moment**: it checks that the action actually
worked. The system receives the BEFORE photo (taken at report time) and
the AFTER photo (taken by the inspector) and answers: **RESOLVED**,
**PARTIALLY RESOLVED**, **UNVERIFIABLE**, or **CONFLICTING**. Demo story:
before the fix the road had *water flowing across it*; after the fix
there is *no active flow but standing water remains* — so the verdict is
**PARTIALLY RESOLVED**, the work order reopens, and the field team goes
back. That is more meaningful than a classifier that just says "done" or
"not done": it catches half-finished fixes, restarted leaks, blurry
evidence and outright contradictions.

- `ml/resolution/src/civitas_resolution/evidence.py` — `ResolutionEvidence`
  types one side of the pair (incident, stage before/after, source, media
  usability, CV category, evidence strings, active-water-flow flag,
  water coverage). `from_vision` maps a `VisualClassificationResult` onto
  it; `from_evidence` builds it from evidence strings directly (tests and
  evidence-level checks). The flow flag derives only from *flowing*
  markers — a leftover puddle is tracked by `water_coverage`, because
  residual water is a partial, not an active flow.
- `model.py` — `ResolutionModel` (model_version `resolution-model-v1`), a
  deterministic comparison with the same house style (every reason cites
  the evidence it saw):
  - guards (fail fast, never guess): AFTER (or BEFORE) media rejected by
    the quality gate -> UNVERIFIABLE; AFTER shows a different hazard with
    its own evidence -> CONFLICTING;
  - per-signal tracks, built only from signals present BEFORE: active
    water flow (flow still observable -> unchanged/conflicting; gone ->
    resolved), standing-water coverage (`water_coverage >= 0.20` mirrors
    the vision evidence threshold; gone below -> resolved; coverage grew
    >10% -> worsened/conflicting; residual water remains -> partial),
    and for the other four categories a single hazard-marker track
    (present -> unchanged/conflicting; absent -> resolved);
  - outcome precedence (worst wins): unchanged/worsened -> CONFLICTING,
    reduced-but-present -> PARTIAL, everything gone -> RESOLVED.
- `tests/test_phase8_resolution.py` — 21 tests: unit level covers all four
  verdicts, thresholds (0.20 standing-water minimum, 1.10 growth ratio),
  media rejection, no-measurable-hazard, category mismatch, determinism;
  integration runs the real vision pipeline on the synthetic corpus
  (flow variant -> standing variant is exactly the user story) and pins
  the measured values (before coverage 0.481 with
  `['standing water', 'water flowing across road']`; after 0.491 with
  `['standing water']`).
- Demo step 12 (`ml/demo_end_to_end.py`): the work order closes as
  "resolved"; the model reopens it. Prints BEFORE/AFTER evidence, the
  PARTIALLY RESOLVED verdict with reasons, and three re-checks — a
  dry-road snapshot (RESOLVED, evidence-level with a recorded limitation:
  the synthetic corpus has no clean-road scene), a restarted leak
  (CONFLICTING) and a blurry photo (UNVERIFIABLE, quality gate rejects
  the media).

## Verification (all passing)

```bash
cd geospatial && python -m pytest tests          # 93 passed
cd geospatial && python -m ruff check src tests  # clean
cd geospatial && python -m mypy src              # clean (13 files)
cd ml/duplicates && python -m pytest tests       # 63 passed
cd ml/duplicates && python -m ruff check src tests  # clean
cd ml/duplicates && python -m mypy src           # clean (12 files)
cd ml/vision && python -m pytest tests           # 27 passed
cd ml/vision && python -m ruff check src tests   # clean
cd ml/vision && python -m mypy src               # clean (9 files)
cd ml/risk && python -m pytest tests             # 62 passed
cd ml/risk && python -m ruff check src tests     # clean
cd ml/risk && python -m mypy src/civitas_risk    # clean (12 files)
cd ml/resolution && python -m pytest tests       # 21 passed
cd ml/resolution && python -m ruff check src tests  # clean
cd ml/resolution && python -m mypy src/civitas_resolution  # clean (3 files)
python ml/demo_end_to_end.py                     # full trace incl. CV + Phases 4 + 5 + 6 + 7 + 8 steps
```

Note: `civitas-vision` is a regular dev dependency of the duplicates
package (`pip install -e "ml/vision[dev]"`); with it installed the
duplicates tests exercise the real image paths instead of skipping them.

## Commits on this branch

- `7cd21fe` Add ML intelligence layer: duplicate detection, geospatial reasoning, severity/priority
- `ce4af51` Phase 1/12 complete
- `32ff126` Track ML layer phase plan and progress notes
- `43c7f0a` Phase 2/12 completed
- `8d3fb95` Phase 3/12 completed
- `5aed379` Fix feature hash constants in phase notes
- `c7ca129` Phase 4/12 completed
- `f16faad` Record Phase 4 commit hash in progress notes
- `288b1b8` Phase 5/12 completed
- `c5ed976` Record Phase 5 commit hash in progress notes
- `c177c39` Phase 6/12 completed
- `c0bf9dd` Record Phase 6 commit hash in progress notes
- `f5732c4` Phase 7/12 completed