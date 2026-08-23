-- 0003_incident_operations.sql
-- Incident lifecycle + cluster persistence + audit trail + assessments + media schema.
--
-- Module: Backend Operations
-- Pre-requisites: 0001_spatial_core.sql, 0002_incident_description.sql applied
-- Effect: 4 new tables + 3 new columns on incidents; all nullable or
--         default-populated; no row rewrites; no constraint violations
-- Reversible: DROP TABLE statements listed at bottom of file

ALTER TABLE incidents ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'submitted';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS source text NOT NULL DEFAULT 'citizen';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS status_updated_at timestamptz;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS last_assessment_model text;

UPDATE incidents SET status_updated_at = reported_at WHERE status_updated_at IS NULL;

CREATE TABLE IF NOT EXISTS incident_links (
    link_id          text PRIMARY KEY,
    incident_id      text NOT NULL REFERENCES incidents(incident_id),
    report_id        text NOT NULL REFERENCES incidents(incident_id),
    source           text NOT NULL DEFAULT 'duplicate_detector',
    confidence       double precision,
    basis            jsonb,
    created_at       timestamptz NOT NULL DEFAULT now(),
    created_by       text,
    UNIQUE (incident_id, report_id)
);
CREATE INDEX IF NOT EXISTS incident_links_incident_idx ON incident_links (incident_id);
CREATE INDEX IF NOT EXISTS incident_links_report_idx ON incident_links (report_id);

CREATE TABLE IF NOT EXISTS media (
    media_id         text PRIMARY KEY,
    incident_id      text NOT NULL REFERENCES incidents(incident_id),
    kind             text NOT NULL CHECK (kind IN ('image', 'video')),
    mime_type        text NOT NULL,
    storage_path     text NOT NULL,
    bytes_size       bigint NOT NULL,
    width            integer,
    height           integer,
    duration_s       double precision,
    captured_at      timestamptz,
    uploaded_at      timestamptz NOT NULL DEFAULT now(),
    uploaded_by      text
);
CREATE INDEX IF NOT EXISTS media_incident_idx ON media (incident_id);

CREATE TABLE IF NOT EXISTS incident_assessments (
    assessment_id    text PRIMARY KEY,
    incident_id      text NOT NULL REFERENCES incidents(incident_id),
    severity_score   integer CHECK (severity_score BETWEEN 0 AND 100),
    severity_level   text,
    severity_factors jsonb,
    priority_score   integer CHECK (priority_score BETWEEN 0 AND 100),
    priority_level   text,
    priority_factors jsonb,
    uncertainties    jsonb,
    review_required  boolean NOT NULL DEFAULT false,
    model_version    text,
    assessed_at      timestamptz NOT NULL DEFAULT now(),
    assessed_by      text
);
CREATE INDEX IF NOT EXISTS incident_assessments_incident_idx
    ON incident_assessments (incident_id, assessed_at DESC);

CREATE TABLE IF NOT EXISTS agent_traces (
    trace_id         text PRIMARY KEY,
    incident_id      text NOT NULL REFERENCES incidents(incident_id),
    node             text NOT NULL,
    model_version    text,
    prompt_version   text,
    input            jsonb,
    output           jsonb,
    latency_ms       integer,
    tokens_in        integer,
    tokens_out       integer,
    validation_outcome text,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS agent_traces_incident_idx
    ON agent_traces (incident_id, created_at);

-- Reversal (uncomment to roll back):
-- DROP TABLE IF EXISTS agent_traces;
-- DROP TABLE IF EXISTS incident_assessments;
-- DROP TABLE IF EXISTS media;
-- DROP TABLE IF EXISTS incident_links;
-- ALTER TABLE incidents DROP COLUMN IF EXISTS last_assessment_model;
-- ALTER TABLE incidents DROP COLUMN IF EXISTS status_updated_at;
-- ALTER TABLE incidents DROP COLUMN IF EXISTS source;
-- ALTER TABLE incidents DROP COLUMN IF EXISTS status;
