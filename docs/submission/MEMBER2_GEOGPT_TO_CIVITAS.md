# Member 2 — Technical Narrative: from GeoGPT to Civitas

*Why this document exists:* Civitas Phase 12 deliberately changes **no ML
code**. Its single goal is to make a technical journey understandable to a
judge: the previous geospatial-ML project (GeoGPT) was the hands-on
foundation; Civitas is the new, broader multimodal civic-intelligence
system; and this member's contribution is the engineering bridge between
the two — using geospatial feature engineering as one part of a larger
pipeline, not as a renamed copy of the old project. Everything in this
narrative is verifiable from the actual repositories; measured claims are
kept strictly separate from prior-project claims.

---

## 1. The 90-second answer (interview / presentation paragraph)

> My previous GeoGPT project gave me hands-on experience building an
> end-to-end geospatial ML pipeline where I engineered spatial features and
> used machine-learning models to predict geographical risk. In Civitas, I
> extended that approach from environmental/geographical risk to hyperlocal
> civic incidents. Instead of looking only at spatial data, Civitas combines
> visual evidence from citizen images/videos, text embeddings, GPS, time,
> landmark and contextual features to determine whether multiple reports
> belong to the same incident and to estimate separate severity and
> priority. The same geospatial-ML mindset from GeoGPT is therefore being
> reused, but the problem, features, models and outputs are redesigned for
> civic incident intelligence.

## 2. Rules of evidence used in this narrative

1. **GeoGPT claims** cite files and measured outputs in the GeoGPT
   repository (`github.com/pavitagrawal/DTM_NatGeo_Project_GeoGPT` — prior
   work, referenced only as prior work).
2. **Civitas claims** cite the Civitas repository and the Phase 11/12
   evaluation artifacts (`services/evaluation/results/REPORT.md`,
   `METRICS.json`, the sha256-pinned frozen test set under
   `services/evaluation/test_data/`, and the golden evidence trail).
3. **No crossover:** GeoGPT metrics are never presented as Civitas metrics,
   and GeoGPT results are never evidence that Civitas models work.

## 3. GeoGPT — the actual prior project (verified inventory)

GeoGPT ("Intelligent Hydro-DTM", National Geo-AI Challenge, IIT Bombay) is
an environmental-risk ML pipeline: it turns SVAMITVA-style drone LiDAR
point clouds into waterlogging/flood-risk intelligence for rural villages.
It is a *static flood-risk analysis of a village from a single survey*, not
an incident-reporting system. What is genuinely implemented there:

| Capability | Implementation in the GeoGPT repository |
|---|---|
| End-to-end geospatial ML workflow | `LAZ → ground classification → DTM → terrain analysis → hydrology → ML risk → drainage design → government reports` (`src/hydro_dtm/`, 16 modules; `HACKATHON_TECHNICAL_REPORT.md` §3.1) |
| Point-cloud ingestion & preprocessing | `point_cloud_processor.py` (laspy: `LASFileValidator`, `LASFileReader`), `point_cloud_operations.py` (statistical/radius/LOF noise filters via scikit-learn), `pdal_preprocessor.py` (a real PDAL JSON pipeline executed through `pdal.Pipeline`) |
| Terrain/geographical feature processing | `hydrology_analyzer.py`: D8 & D∞ flow direction, Planchon–Darboux depression filling, flow accumulation, stream extraction, watersheds, slope, aspect, TWI (`ln(a/tan β)`), curvature, depression detection |
| ML feature engineering for risk | `waterlogging_predictor.py` `extract_features` (15+ features: elevation, slope, aspect, TWI, flow accumulation and its log, distance-to-streams, TPI, local relief, convergence index, relative elevation, slope position, interactions) |
| ML-based risk prediction | Random Forest (classifier for 4-class waterlogging risk Low/Medium/High/Critical + regressor for flood duration) **and** XGBoost, selectable via `model_type='rf'\|'xgb'\|'ensemble'`; an `EnsembleClassifier` majority-vote wrapper; ground classification via CSF + RF/XGBoost refinement (`ground_classifier.py`) |
| Spatial data handling | Real Parampur Gram Panchayat input: `209311SAJOI_209312PARAMPUR.laz` (97,104,031 points, EPSG:32643) + orthophoto GeoTIFF; raster I/O via `rasterio`; vector/shapefile export via `geopandas`/`shapely` |
| PostGIS usage | `docker-compose.yml` PostGIS 15 (postgis/postgis:15-3.3); `database.py` defines 9 SQLAlchemy/geoalchemy2 tables with SRID 4326 geometry columns and `CREATE EXTENSION postgis`. Scope note: ORM scaffolding was defined; the pipeline itself runs on files (LAZ/GeoTIFF) |
| Measurable model outputs | Reproducible demo outputs under `demo_outputs/`: ground classification CSF 78.0% / ML 61.8% (synthetic-label limitations; 50,000 pts, 52.73 s); waterlogging risk model accuracy 0.9% with risk split Low 29.6% / Medium 35.0% / High 22.8% / Critical 12.7% (synthetic labels); real-data sample run: 100,000-point sample → DTM 100×100 in 3.71 s, High-risk areas 0.0%; village hydrology run: 512 depressions, 4 critical zones |

**What GeoGPT did NOT implement** (verified by repo-wide inspection — this
narrative does not claim otherwise): duplicate detection between reports,
civic-incident severity or priority scoring, before/after resolution
verification, and a comparison experiment of Random Forest vs XGBoost
(both are wired in and selectable, but no comparison artifacts exist).
README-level numbers such as "95%+ accuracy" and "0.15 m RMSE" are
presentation copy, **not** measured outputs, and are excluded from this
narrative. The genuinely measured values above are the ones that carry the
"experience" story.

## 4. Civitas — the new problem: hyperlocal civic incident intelligence

Citizens report civic incidents (water leakage, potholes, garbage
overflow, broken streetlights, fallen trees) with images/video + text +
GPS + timestamp. Civitas must decide, from observational evidence: *is
this the same physical incident as earlier reports?* (duplicate detection
+ clustering), *how dangerous is it?* (severity), *how urgent is
municipal action?* (priority), and later *was it actually resolved?*
(resolution verification). Unlike GeoGPT's static raster grid, inputs are
populated, multimodal, real-time reports — so the intelligence layer is
per-report and multiplayer, with the same emphasis on turning raw
observations into engineered features and measurable predictions.

## 5. Before versus now

| | GeoGPT (previous project) | Civitas (Member 2 contribution) |
|---|---|---|
| Input | Drone LiDAR point cloud + orthophoto (97 M points, Parampur GP) | Citizen image/video + text + GPS + timestamp per report |
| Processing | PDAL + CSF ground classification, DTM, D8 hydrology | Media preprocessing (quality gate) + computer vision + text/image embeddings |
| Features | Terrain/hydrology features: slope, aspect, TWI, flow accumulation, distance-to-streams, TPI, relief, curvature | Geospatial/time/context features: GPS distance, temporal delta, landmark proximity, incident density, category agreement — combined with vision + text similarity |
| Model | Random Forest / XGBoost waterlogging risk (Low–Critical), ground classification | Duplicate scoring + incident clustering; separate severity and priority models; resolution verification models |
| Output | Village waterlogging risk map + drainage plan + government report | Per-report duplicate/severity/priority intelligence, incident clusters, work-order verification for the municipal workflow |
| Evaluation | Reproducible demo outputs (`demo_outputs/`), synthetic-label limitations recorded | Frozen test set (68 files, sha256-pinned), Phase 11/12 metrics, failure analysis, golden evidence trail |

The important progression is **not** "I used Random Forest before and now
use another model." It is that the earlier project gave practical
experience in turning complex spatial information into structured ML
features and measurable predictions — and Civitas extends that discipline
into a multimodal civic-intelligence system whose models, features and
outputs are redesigned for the incident domain.

## 6. The core idea, adapted

The idea that transfers from GeoGPT to Civitas is the pipeline shape:
**raw spatial information → engineered geographic/contextual features →
ML → measurable risk-oriented output**.

In GeoGPT the spatial problem was geographical/environmental risk
(waterlogging of a village terrain). In Civitas the problem is civic
incidents: spatial intelligence is combined with visual and textual
evidence to determine whether reports refer to the same physical incident,
and how severe and how urgent that incident is. The Civitas features that
genuinely derive from this geospatial-thinking approach (defined in the
Civitas design, `ml/duplicates/src/civitas_duplicates/contracts.py`
`PairFeatures` and `ml/duplicates/src/civitas_duplicates/` modules):

- **Geographic distance between reports** — `gps_distance_m`,
  `gps_similarity` (`geo_features.py`, haversine-based, caps at
  `max_reasonable_distance_m=2000.0`)
- **Temporal proximity** — `time_delta_h`, `time_similarity`,
  burst-window semantics (`time_features.py`)
- **Landmark/context proximity** — `landmark_similarity`
  (`landmark_features.py`, school/hospital proximity is also used by the
  severity layer via `civitas_risk/features.py`
  `school_proximity_signal` / `hospital_proximity_signal`)
- **Incident density / number of nearby reports** — `incident_density`
  (normalized reports-per-cell, `geospatial/src/civitas_geo/aggregates.py`
  `reports_per_cell_*`), plus `repeated_report_signal` in
  `civitas_risk/features.py`
- **Category agreement and evidence overlaps** — `category_agreement`,
  `category_relation_note`, text and image similarity

Not every Civitas feature came from GeoGPT; vision, embeddings, category
semantics and explanation/evidence constraints are newly built for the
civic domain. The claim is only that the *habit of spatial feature
engineering and measurable ML* came from the GeoGPT experience.

## 7. The role of geospatial intelligence in Civitas (precisely bounded)

- **Duplicates:** geospatial information does **not** independently decide
  whether two reports are duplicates. The verdict combines image
  similarity + text similarity + geographic distance + temporal proximity
  + category agreement + landmark/context overlap (all fields of
  `PairFeatures`; frozen threshold 0.70 in `ScoringConfig`).
- **Severity and priority:** geospatial/contextual signals contribute to,
  but do not independently determine, severity or priority — the risk
  layer fuses spatial/contextual evidence (school/hospital proximity,
  traffic, repeated reports, longevity, weather escalation) with visual
  incident evidence (category and vision output) and documented rule
  tables (`civitas_risk/features.py`, `incident_features.py`,
  `priority_features.py`).
- **Backend boundary:** PostGIS/backend spatial retrieval (ward boundary
  checks, nearby-report candidate queries, aggregates) belongs to the
  Civitas **backend module** — that implementation is another member's
  contribution and is not claimed here. This member's contribution
  **consumes** the resulting candidate/context payloads (the typed
  `NearbyCandidatesRequest/Response` and `ReportLike` contracts in
  `services/ml/src/civitas_ml/contracts.py`) and performs the ML feature
  engineering and intelligence layer on top.

## 8. Evidence separation: two scorecards, kept apart

| | GeoGPT measured outputs | Civitas Phase 11/12 measured results |
|---|---|---|
| Where | `demo_outputs/*` in the GeoGPT repo | `services/evaluation/results/*` in Civitas |
| What | CSF 78.0% / ML 61.8% ground classification (synthetic labels); risk accuracy 0.9%; real-data DTM sample 100×100 in 3.71 s | Vision accuracy 1.0 (50/50); media-quality verdicts 14/14 correct; duplicates recall 1.0, precision 0.667 with 4 review escalations (2 hard) and recorded failure cases; clustering 7 same-incident pairs merged / 8 different pairs separated; severity 12/12 kappa 1.0 with 49 factor citations and 0 explanation violations; priority 12/12 kappa 1.0 with 3/3 critical recall; resolution accuracy 0.875, kappa 0.833 |
| Purpose | Prior experience evidence | Current system evidence |

Civitas results are produced by **one documented command**
(`cd services/evaluation && python run_all.py`) against a frozen,
sha256-pinned test set that `run_all.py check` refuses to run unless the
manifest hash matches — the dataset path is closed: generate once, freeze,
evaluate, never regenerate. The golden very-scenario (three water-leak
citizen reports → one incident CL-1000, severity HIGH, priority MEDIUM,
work order verified RESOLVED at 0.63 confidence; `results/golden/
evidence_trail.json`) walks the composed chain as a *product* walkthrough
and is explicitly separated from model-performance evidence. Recorded
limitations (two duplicate false merges, two clustering misses, severity's
unreachable low band, synthetic labels) stay visible.

## 9. Member 2 contribution summary — the full progression

```
GeoGPT experience                       prior geospatial ML project: LiDAR → terrain/hydrology
  → geospatial feature-engineering      features (slope, aspect, TWI, flow accumulation, ...)
     foundation                         and RF/XGBoost risk prediction, measured demo outputs
  → Civitas media preprocessing         quality gate: blur/tiny/dark/bright/ambiguous/unsupported
     and vision                         → vision classifier (5 categories) with honest confidence
  → image/text embeddings               classical-CV + n-gram embeddings with provenance
  → geospatial/time/context features    GPS distance · time delta · landmark proximity ·
                                         incident density · category agreement
  → duplicate scoring and clustering    DuplicateDetector (frozen 0.70 threshold), incident
                                         clusters, per-feature contributions + reasons
  → separate severity and priority      severity (danger, rule-table factors w/ citations) vs
                                         priority (urgency, 10-signal semantics), both kappa 1.0
  → municipal workflow consumption      typed service contracts consumed by agents/backend
  → before/after resolution             before/after evidence verification (RESOLVED 0.63)
     verification
  → measurable evaluation               frozen test set (68 files, sha256 manifest), Phase 11/12
                                         metrics, failure analysis, golden evidence trail
```

Every stage above is demonstrated by code or measured output in the Civitas
repository (`ml/`, `geospatial/`, `services/ml/`, `services/evaluation/`,
`ml/demo_end_to_end.py`), and the same standard of evidence is applied to
the GeoGPT side of the story.

## 10. References

- GeoGPT (prior work, reference only): `https://github.com/pavitagrawal/DTM_NatGeo_Project_GeoGPT` — "Intelligent Hydro-DTM", an end-to-end geospatial ML pipeline (LiDAR → DTM → hydrology → ML waterlogging risk → drainage/government outputs). It is prior technical experience and a foundation for thinking about geospatial ML, **not** a prior implementation of Civitas' duplicate detection, severity, priority, or civic-incident intelligence.
- Civitas (this repository): `ml/`, `geospatial/`, `services/ml/`, `services/evaluation/`, `ml-layer.md`, `ml/demo_end_to_end.py`.