# Agentic workflow

## Graph

`load_context -> ml_intelligence -> structure_evidence -> clarification_check -> knowledge_grounding -> routing_agent -> operational_planner -> critic -> human_review_interrupt -> citizen_communication`.

Clarification and human review are LangGraph interrupts with checkpoints. Critic revision edges return only to routing or planning and are bounded at two revisions. Missing municipal knowledge abstains from autonomous routing and is sent to human review without fabricating a work order.

## Boundaries and grounding

The graph depends on five typed tools: report context, ML intelligence, knowledge, persistence, and traces. The ML node consumes model outputs as facts; agents never recalculate scores. Routing, planning, and citizen safety advice must cite IDs retrieved in the current `KnowledgeResult`, which are validated before acceptance.

Trace records retain a workflow trace ID, node, timing, safe model/tool identifier, validation status, warnings, errors, and knowledge IDs. Credentials, headers, prompts, and raw report bodies are excluded.

## State and model routing

`CivitasWorkflowState` is a Pydantic, checkpointable state containing normalized report context, ML outputs, structured evidence, clarification state, retrieved knowledge, routing, operational plan, critic result, review decision, citizen communication, warnings, errors, and safe node traces. It does not contain provider secrets or arbitrary backend objects.

Evidence structuring, clarification, and citizen communication use the configured fast model. Routing, operational planning, and critique use the configured primary model. Their versioned prompt files live under `prompts/agents/`; all calls use the provider-neutral `LLMClient` structured-output contract.

## Failure and resume behavior

Missing reports and invalid model output fail the responsible node explicitly. ML unavailability is retained as a warning and passed through as unavailable metadata. Incomplete material evidence pauses for clarification; a resume provides an answer map. Invalid or insufficient policy evidence prevents autonomous routing. Repeated work-order creation is idempotent in the supplied persistence adapter, and critic revisions are limited to two.

## Production notes

The included memory checkpointer and in-memory tools are for local tests. Production must use a durable LangGraph checkpointer and authenticated HTTP adapters. A reviewer must approve, edit, reroute, reject, or request evidence; the workflow does not auto-approve high-impact decisions.

Production composition uses `create_production_workflow` with `HttpReportContextTool`, `HttpMLIntelligenceTool`, `HttpKnowledgeTool`, `HttpPersistenceTool`, and `HttpTraceTool`. It requires `CIVITAS_BACKEND_BASE_URL`, `ML_SERVICE_URL`, `CIVITAS_INTERNAL_API_KEY` where enabled, and `CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL`. Install the workflow PostgreSQL extra, create the saver with `create_postgres_checkpointer`, and call its `setup()` during controlled service initialization. The manual command `py -3.12 scripts/smoke_groq.py` verifies Groq structured output without printing credentials.

## Limitations

The first vertical slice produces one report/incident recommendation. Multi-report consolidation and resolution verification remain separate future graph extensions. Existing backend policy data lacks jurisdiction metadata, so jurisdiction-specific grounding remains explicit partial support or abstention.
