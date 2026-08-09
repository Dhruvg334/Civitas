# Civitas Geospatial Intelligence

Geospatial layer for Civitas: PostGIS spatial queries, nearby-incident
retrieval, landmark grounding, location validation and map-based exposure
reasoning. This is the dependency of the `ml/duplicates` (GPS/landmark
signals) and `ml/features` (normalized geospatial evidence vector) packages.

## Modules

| Module | Responsibility |
|---|---|
| `civitas_geo.boundary` | PostGIS Boundary: operational-area definition shared by validation and retrieval |
| `civitas_geo.candidates` | Candidate retrieval for the ML duplicate engine: X-metre/Y-hour windows, category, boundary, landmark context |
| `civitas_geo.distance` | Pure-Python WGS84 great-circle distance, bearing, bbox, offsets |
| `civitas_geo.landmarks` | Landmark index, nearest/within/overlap lookup, keyword extraction |
| `civitas_geo.validation` | Location validation: range, city coverage, heuristics, suggestions + pipeline gate |
| `civitas_geo.queries` | Parameterized PostGIS SQL builders (ST_DWithin, KNN, clustering, candidate windows) |
| `civitas_geo.retrieval` | Nearby-incident retrieval with identical PostGIS/memory contracts |
| `civitas_geo.reasoning` | Map-based reasoning -> exposure features for severity/priority |
| `civitas_geo.feature_engineering` | Normalized evidence feature vector for ML (validity, proximity, neighbourhood, temporal, category) |
| `civitas_geo.db` | Optional psycopg3 client (extra: `civitas-geospatial[postgres]`) |

## Contracts

All cross-module outputs are typed pydantic models in `civitas_geo.models`
(`GeoPoint`, `Landmark`, `LocationValidationResult`, `NearbyIncidentsResult`,
`ExposureContext`, `SpatialSearchSpec`, plus Phase 2 contracts:
`OperationalBoundary`, `CandidateSearchSpec`, `CandidateRecord`,
`CandidateListResult`, `PipelineGateDecision`) and the feature-engineering
contract `GeospatialFeatureVector` / input `CivicIncidentContext` in
`civitas_geo.feature_engineering`. Observable geography, retrieved
context and inference are kept on separate fields (`sources` vs `inference`)
so callers can attribute each signal.

## Spatial pipeline (Phase 2)

For every new incident the spatial stage runs:

    Current report -> location-validation gate -> PostGIS/memory candidate
    windows (X m radius, Y h recency, category, boundary) -> candidate list
    enriched with landmark context -> ML duplicate engine.

- `gate_for_pipeline()` (validation) rejects missing, malformed, placeholder
  `(0,0)` and off-coverage coordinates before they enter retrieval; rejected
  reports go to a human-fix queue with an explicit `reason`.
- `CandidateSearchSpec` defines the retrieval windows (radius X metres,
  `within_hours` Y); `candidate_incidents_sql()` executes them on PostGIS with
  `ST_DWithin` + recency `make_interval` + boundary envelope (`&&`
  `ST_MakeEnvelope`), all bound parameters.
- Every `CandidateRecord` carries coordinates, distance, timestamps,
  category, `duplicates_seen`, time-window flag and nearest-landmark context
  per kind — the complete field set the duplicate/exposure models consume.
- `CandidateRetriever` prefers PostGIS when an executor is configured and
  falls back to a deterministic memory scan labeled `mode="memory"`.
- The database artifacts live in `database/migrations/0001_spatial_core.sql`
  and `database/seed/0001_demo_landmarks.sql` (matching `DEMO_LANDMARKS`).

## PostGIS setup (production mode)

The database must expose `incidents` and `landmarks` tables with
`geometry(Point, 4326)` columns and GIST indexes:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS incidents (
  incident_id    text PRIMARY KEY,
  category       text,
  reported_at    timestamptz,
  duplicates_seen int DEFAULT 1,
  location_geom  geometry(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS incidents_location_geom_gix
  ON incidents USING GIST (location_geom);

CREATE TABLE IF NOT EXISTS landmarks (
  landmark_id text PRIMARY KEY,
  name        text NOT NULL,
  kind        text NOT NULL,
  radius_m    double precision DEFAULT 100,
  geom        geometry(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS landmarks_geom_gix
  ON landmarks USING GIST (geom);
```

`ensure_postgis_sql()` and `bbox_gist_index_sql()` are provided in
`civitas_geo.queries` for automated provisioning. Connection is via the
`CIVITAS_POSTGIS_DSN` environment variable only; never hard-code secrets.

Without a database, `NearbyRetriever` falls back to deterministic memory-mode
retrieval (marked `mode="memory"` in results).

## Design notes

- Every query builder returns `(sql, params)`; user values are always bound
  parameters, identifiers are validated against `[a-z0-9_]`.
- Distances use `geography` casts so ST_DWithin/ST_Distance return metres on
  the spheroid, matching `civitas_geo.distance.haversine_m`.
- Location validation separates hard range checks from labelled heuristics
  (marine bands, `(0,0)` placeholder, exact-duplicate GPS across reports).
- Map reasoning emits `ExposureContext` with explicit `sources` and
  `inference` lists — never asserted facts.
- `GeospatialFeatureEngine` returns a `GeospatialFeatureVector`: all features
  are normalized to `[0, 1]`, every feature carries a `provenance` entry
  naming its evidence source, `basis` records the supporting observations,
  and no decision fields (severity/priority/tier) appear anywhere — the ML
  layer decides.
- Feature-engineering limits on purpose: landmark datasets cover schools,
  hospitals, metros, junctions and no-fly/road buffers; anything else is
  `0` (no fabrication). Seeded thresholds are visible in
  `civitas_geo.feature_engineering` and are calibration candidates for
  Phase 6.
- The denoised feature vector and full raw statistics are produced by
  `GeospatialFeatureEngine.compute_for_point()` which automatically runs
  location validation and nearby-incident retrieval.
- The operational boundary is observable configuration (see
  `civitas_geo.boundary.DEFAULT_BOUNDARY`), never model inference; both the
  validation gate and candidate SQL consume the same `OperationalBoundary`
  so coverage is enforced identically in memory and PostGIS mode.
- Memory-mode candidate retrieval keeps records that lack timestamps but
  states this in `basis`; PostGIS mode always enforces recency because
  `reported_at` is `NOT NULL` in the migration.

## Run

```bash
pip install -e "./geospatial[dev]"
pytest geospatial
```