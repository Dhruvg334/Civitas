-- 0001_spatial_core: Civitas spatial persistence (Phase 2)
-- PostGIS extension + incidents + landmarks tables with GIST indexes.
-- Mirrors the schema contracts in geospatial/src/civitas_geo/queries.py and
-- the README provisioning SQL. Immutable once applied; append a new
-- migration for any change.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS incidents (
    incident_id     text PRIMARY KEY,
    category        text,
    reported_at     timestamptz NOT NULL,
    duplicates_seen int DEFAULT 1,
    location_geom   geometry(Point, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS incidents_location_geom_gix
    ON incidents USING GIST (location_geom);
CREATE INDEX IF NOT EXISTS incidents_reported_at_idx
    ON incidents (reported_at DESC);

CREATE TABLE IF NOT EXISTS landmarks (
    landmark_id text PRIMARY KEY,
    name        text NOT NULL,
    kind        text NOT NULL,
    radius_m    double precision DEFAULT 100,
    geom        geometry(Point, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS landmarks_geom_gix
    ON landmarks USING GIST (geom);
CREATE INDEX IF NOT EXISTS landmarks_kind_idx
    ON landmarks (kind);
