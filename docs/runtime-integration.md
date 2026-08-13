# Runtime integration

Workflow routes create or reuse a `workflow_runs` row and use its stable `thread_id` for LangGraph checkpoints. Runtime status is operational metadata only; checkpoint contents belong to LangGraph. Clarification and review resumes use the same thread through `Command(resume=...)`. Production must initialize the PostgreSQL saver once at application startup; tests use memory checkpoints. Run `py -3.12 scripts/smoke_workflow.py REPORT_ID --token TOKEN` against a local authenticated API.
