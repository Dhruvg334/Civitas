-- 0004_workflow_core.sql
-- Work-orders, clarifications, routing decisions, resolution submissions, and policies schema.
--
-- Module: Backend Operations
-- Pre-requisites: 0001_spatial_core.sql, 0002_incident_description.sql,
--                 0003_incident_operations.sql applied
-- Effect: 5 new tables + 3 new columns on incidents. All additive.
--         New columns have safe defaults so existing rows are valid.
--         No new FK constraints on existing tables.
-- Reversible: DROP TABLE / DROP COLUMN statements at the bottom.

-- ---------------------------------------------------------------------------
-- incidents: extend with assignment + resolution-class fields
-- assigned_work_order_id is intentionally NOT a foreign key — see
-- docs/api/STATE_MACHINE.md. It points to the active WO; multiple WOs
-- may exist per incident over its lifecycle. Application enforces
-- existence + ownership on write.
-- ---------------------------------------------------------------------------

ALTER TABLE incidents
    ADD COLUMN IF NOT EXISTS assigned_department text;

ALTER TABLE incidents
    ADD COLUMN IF NOT EXISTS assigned_work_order_id text;

ALTER TABLE incidents
    ADD COLUMN IF NOT EXISTS resolution_class text;

CREATE INDEX IF NOT EXISTS incidents_assigned_wo_idx
    ON incidents (assigned_work_order_id);

-- ---------------------------------------------------------------------------
-- work_orders
-- Status values are intentionally restricted to those named in the
-- contract (ref/04 §13) plus the lifecycle values that follow from the
-- incident state machine. 'rejected' is NOT a work-order status — when
-- a supervisor rejects a work order, the WO stays in 'awaiting_review'
-- (closed-but-not-approved) and the incident moves to 'rejected'.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id              text PRIMARY KEY,
    incident_id                text NOT NULL REFERENCES incidents(incident_id),
    summary                    text NOT NULL,
    required_actions           jsonb NOT NULL DEFAULT '[]'::jsonb,
    suggested_resources        jsonb NOT NULL DEFAULT '[]'::jsonb,
    safety_notes               jsonb NOT NULL DEFAULT '[]'::jsonb,
    estimated_window_min_hours integer,
    estimated_window_max_hours integer,
    non_binding                boolean NOT NULL DEFAULT true,
    status                     text NOT NULL DEFAULT 'awaiting_review'
                               CHECK (status IN (
                                   'awaiting_review',
                                   'approved',
                                   'assigned',
                                   'in_progress',
                                   'resolution_submitted',
                                   'verification_pending',
                                   'resolved',
                                   'partially_resolved',
                                   'reopened'
                               )),
    primary_department         text,
    secondary_departments      text[] NOT NULL DEFAULT '{}'::text[],
    escalation_required        boolean NOT NULL DEFAULT false,
    policy_references          text[] NOT NULL DEFAULT '{}'::text[],
    created_at                 timestamptz NOT NULL DEFAULT now(),
    created_by                 text,
    reviewed_by                text,
    reviewed_at                timestamptz
);

CREATE INDEX IF NOT EXISTS work_orders_incident_idx
    ON work_orders (incident_id);
CREATE INDEX IF NOT EXISTS work_orders_status_idx
    ON work_orders (status);

-- ---------------------------------------------------------------------------
-- clarifications
-- (incident_id, question_id) is intentionally NOT unique. The same
-- question may legitimately be re-asked after an incident is reopened
-- (ref/04 §3 lists 'reopened' as a valid status). Application enforces
-- "at most one OPEN clarification per (incident, question)" — see
-- docs/api/STATE_MACHINE.md.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS clarifications (
    clarification_id  text PRIMARY KEY,
    incident_id       text NOT NULL REFERENCES incidents(incident_id),
    question_id       text NOT NULL,
    question_text     text NOT NULL,
    decision_impact   text[] NOT NULL DEFAULT '{}'::text[],
    required          boolean NOT NULL DEFAULT false,
    asked_at          timestamptz NOT NULL DEFAULT now(),
    answered_at       timestamptz,
    answer_text       text,
    answered_by       text
);

CREATE INDEX IF NOT EXISTS clarifications_incident_idx
    ON clarifications (incident_id, asked_at);
CREATE INDEX IF NOT EXISTS clarifications_unanswered_idx
    ON clarifications (incident_id, question_id) WHERE answered_at IS NULL;

-- ---------------------------------------------------------------------------
-- routing_decisions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS routing_decisions (
    routing_id            text PRIMARY KEY,
    incident_id           text NOT NULL REFERENCES incidents(incident_id),
    primary_department    text NOT NULL,
    secondary_departments text[] NOT NULL DEFAULT '{}'::text[],
    escalation_required   boolean NOT NULL DEFAULT false,
    policy_references     text[] NOT NULL DEFAULT '{}'::text[],
    decision_basis        jsonb NOT NULL DEFAULT '[]'::jsonb,
    review_required       boolean NOT NULL DEFAULT true,
    workflow_version      text NOT NULL DEFAULT 'routing-v1',
    routed_at             timestamptz NOT NULL DEFAULT now(),
    routed_by             text
);

CREATE INDEX IF NOT EXISTS routing_decisions_incident_idx
    ON routing_decisions (incident_id, routed_at DESC);

-- ---------------------------------------------------------------------------
-- resolution_submissions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS resolution_submissions (
    resolution_id      text PRIMARY KEY,
    incident_id        text NOT NULL REFERENCES incidents(incident_id),
    classification     text NOT NULL CHECK (classification IN (
        'resolved',
        'partially_resolved',
        'unverifiable',
        'conflicting_evidence'
    )),
    resolved_evidence  jsonb NOT NULL DEFAULT '[]'::jsonb,
    remaining_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    uncertainties      jsonb NOT NULL DEFAULT '[]'::jsonb,
    model_version      text,
    submitted_at       timestamptz NOT NULL DEFAULT now(),
    submitted_by       text,
    reviewed_by        text,
    reviewed_at        timestamptz,
    review_action      text
);

CREATE INDEX IF NOT EXISTS resolution_submissions_incident_idx
    ON resolution_submissions (incident_id, submitted_at DESC);

-- ---------------------------------------------------------------------------
-- policies
-- Seed data lives in 0005_seed_policies.sql so this migration stays
-- schema-only.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS policies (
    policy_id           text PRIMARY KEY,
    code                text NOT NULL UNIQUE,
    kind                text NOT NULL CHECK (kind IN ('policy', 'playbook')),
    title               text NOT NULL,
    body                text NOT NULL,
    categories          text[] NOT NULL DEFAULT '{}'::text[],
    departments         text[] NOT NULL DEFAULT '{}'::text[],
    severity_factors    jsonb NOT NULL DEFAULT '[]'::jsonb,
    priority_factors    jsonb NOT NULL DEFAULT '[]'::jsonb,
    required_actions    text[] NOT NULL DEFAULT '{}'::text[],
    suggested_resources text[] NOT NULL DEFAULT '{}'::text[],
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS policies_kind_idx ON policies (kind);
CREATE INDEX IF NOT EXISTS policies_categories_idx ON policies USING GIN (categories);
CREATE INDEX IF NOT EXISTS policies_departments_idx ON policies USING GIN (departments);

-- ---------------------------------------------------------------------------
-- Reversal (uncomment to roll back):
-- DROP TABLE IF EXISTS policies;
-- DROP TABLE IF EXISTS resolution_submissions;
-- DROP TABLE IF EXISTS routing_decisions;
-- DROP TABLE IF EXISTS clarifications;
-- DROP TABLE IF EXISTS work_orders;
-- DROP INDEX IF EXISTS incidents_assigned_wo_idx;
-- ALTER TABLE incidents DROP COLUMN IF EXISTS resolution_class;
-- ALTER TABLE incidents DROP COLUMN IF EXISTS assigned_work_order_id;
-- ALTER TABLE incidents DROP COLUMN IF EXISTS assigned_department;
-- ---------------------------------------------------------------------------