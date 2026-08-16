# Database Migrations

PostgreSQL & PostGIS schema definitions executed in ascending order:

| File | Purpose |
| :--- | :--- |
| `0001_spatial_core.sql` | PostGIS extension enablement, spatial indexes, wards table, geography helper functions. |
| `0002_incident_description.sql` | Report and incident base structures, description columns, geospatial point geometry. |
| `0003_incident_operations.sql` | Operational status enums, work orders, media attachments, and role-based access constraints. |
| `0004_workflow_core.sql` | Verification tables, clarification history, department routing, and audit logs. |
| `0005_seed_policies.sql` | Municipal resolution playbooks, triage policies, department matrices, and grounding rules. |
| `0006_workflow_runs.sql` | Application-level workflow run metadata (workflow ID, thread ID, trace ID, execution status, interrupt type). |

> **Note on LangGraph Persistence**:
> Application operational metadata is stored in `workflow_runs`. The low-level LangGraph checkpoint state (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`) is managed and initialized directly by LangGraph's PostgreSQL checkpointer (`PostgresSaver.setup()`).
