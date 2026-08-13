# Knowledge grounding and structured LLM foundation

## Responsibility

This foundation separates two concerns:

1. `services/knowledge` retrieves traceable policy and playbook records.
2. `services/workflow/civitas_workflow/llm` obtains schema-validated model output through a provider-neutral interface.

It does not implement the agent graph.

## Knowledge retrieval order

The retriever loads the small curated corpus through `KnowledgeBackend`, applies category, department, jurisdiction, and policy-type constraints, scores query and purpose token overlap, and uses policy reference ID plus record ID as a deterministic final tie-break. A no-match result is explicit and contains an abstention reason.

The HTTP adapter uses the existing `/api/v1/policies` endpoint. The in-memory adapter supplies the same typed records for offline tests. Source IDs, exact text, structured actions, and source paths survive retrieval so a later agent can answer “What evidence supports this decision?” without reconstructing provenance.

## LLM provider boundary

`LLMClient.generate_structured` is the only interface workflow code needs. `GroqLLMClient` sends a JSON-Schema response request to Groq's OpenAI-compatible endpoint; `FakeLLMClient` is deterministic and offline. Model names, API key, timeout, retries, temperature, and strict-schema mode come from environment configuration. No model name is an architectural constant. Strict mode defaults off because Groq limits it to selected models and requires every schema field to be required; Pydantic validation is always applied locally regardless of mode.

Every successful call returns validated Pydantic output with model, measured latency, token usage when supplied, trace ID, retry count, warnings, and safe provider metadata. Configuration, timeout, provider, malformed JSON, schema-validation, and exhausted-retry failures have distinct exception types. Invalid output is never returned as a successful value.

The trace sink boundary emits fields supported by the existing agent trace infrastructure without importing API persistence code or recording credentials, authorization headers, prompts, or report bodies.

## Future agent usage

A later workflow node should retrieve knowledge, require sufficient grounding for policy-dependent statements, pass only relevant evidence into the structured model request, and validate every generated policy reference with `validate_grounding_references`. Partial or insufficient results should remain available for human review.

## Limitations and next steps

- The backend currently omits jurisdiction metadata.
- No semantic ranker is enabled; deterministic exact/keyword retrieval is adequate for the initial corpus.
- A later integration phase must provide an API-owned trace sink that persists LLM trace events against an incident and must build the LangGraph workflow around these interfaces.
