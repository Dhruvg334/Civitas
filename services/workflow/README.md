# Civitas workflow service

The workflow service orchestrates one civic incident using LangGraph. It consumes typed adapters for report context, ML intelligence, knowledge retrieval, persistence, and tracing; graph nodes do not import backend operations or model implementations.

The graph loads context, runs deterministic ML analysis, structures evidence, asks only material clarifications, retrieves policy evidence, proposes routing and an operational plan, runs a bounded critic loop, persists a reviewable work order, pauses for human review, and then writes citizen communication after approval.

All agent calls go through `LLMClient`. Fast model routing is used for evidence, clarification, and citizen communication; the primary model is used for routing, planning, and critique. The LangGraph memory checkpointer is suitable for local development and tests. Production needs a durable checkpointer and HTTP adapters bound to authenticated API routes.

```powershell
py -3.12 -m pytest services/workflow/tests
```

No test calls Groq or any external LLM.
