-- 0002_incident_description.sql
-- Adds the `description` column the FastAPI backend writes on POST /api/v1/reports.
-- Mirrors the citizen-text column already implied by the API contract.
--
-- Module: Backend Operations
-- Pre-requisites: 0001_spatial_core.sql applied
-- Effect: ALTER TABLE incidents ADD COLUMN description text NULL
-- Backwards-compatible: existing rows get NULL, no NOT NULL violation
-- Reversible: ALTER TABLE incidents DROP COLUMN description;

ALTER TABLE incidents ADD COLUMN IF NOT EXISTS description text;