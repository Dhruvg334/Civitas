-- Operational metadata only; LangGraph checkpoint contents remain in its own tables.
CREATE TABLE IF NOT EXISTS workflow_runs (
    workflow_id text PRIMARY KEY,
    thread_id text NOT NULL UNIQUE,
    report_id text NOT NULL REFERENCES incidents(incident_id),
    incident_id text,
    trace_id text NOT NULL,
    status text NOT NULL,
    interrupt_type text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);
CREATE INDEX IF NOT EXISTS workflow_runs_report_active_idx ON workflow_runs (report_id, status);
