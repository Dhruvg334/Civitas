# Civitas Geospatial Intelligence

Geospatial layer for Civitas: PostGIS spatial queries, nearby-incident
retrieval, landmark grounding, location validation and map-based exposure
reasoning. This is the dependency of the `ml/duplicates` (GPS/landmark
signals) and `ml/risk` (school/hospital/traffic exposure features) packages.

## Modules

| Module | Responsibility |
|---|---|
| `civitas_geo.distance` | Pure-Python WGS84 great-circle distance, bearing, bbox, offsets |
| `civitas_geo.landmarks` | Landmark index, nearest/within/overlap lookup, keyword extraction |
| `civitas_geo.validation` | Location validation: range, city coverage, heuristics, suggestions |
| `civitas_geo.queries` | Parameterized PostGIS SQL builders (ST_DWithin, KNN, clustering) |
| `civitas_geo.retrieval` | Nearby-incident retrieval with identical PostGIS/memory contracts |
| `civitas_geo.reasoning` | Map-based reasoning -> exposure features for severity/priority |
| `civitas_geo.db` | Optional psycopg3 client (extra: `civitas-geospatial[postgres]`) |

## Contracts

All cross-module outputs are typed pydantic models in `civitas_geo.models`
(`GeoPoint`, `Landmark`, `LocationValidationResult`, `NearbyIncidentsResult`,
`ExposureContext`, `SpatialSearchSpec`). Observable geography, retrieved
context and inference are kept on separate fields (`sources` vs `inference`)
so callers can attribute each signal.

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

## Run

```bash
pip install -e "./geospatial[dev]"
pytest geospatial
```