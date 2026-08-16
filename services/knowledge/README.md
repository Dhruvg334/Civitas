# Civitas Knowledge Service

`civitas_knowledge` retrieves municipal policy and playbook evidence for workflow decisions. It supplies attributable knowledge; routing, work-order generation, and review remain separate workflow responsibilities.

## Architecture

- `KnowledgeBackend` defines the storage boundary.
- `HttpKnowledgeBackend` consumes the authenticated policy API and validates Civitas envelopes.
- `InMemoryKnowledgeBackend` provides deterministic local/test execution.
- `KnowledgeService` applies exact filtering, keyword relevance, and stable reference-ID tie-breaking.

Queries cover department jurisdiction, routing, escalation, safety, required work-order fields, operational guidance, and citizen-communication restrictions across the supported incident taxonomy.

## Results and provenance

Every `KnowledgeResult` retains the policy identifier/code, relevant text, structured actions/resources, retrieval method, transparent ranking points, and backend source path. Ranking points are relevance signals, not confidence probabilities.

Grounding state is explicit:

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `INSUFFICIENT_KNOWLEDGE`

`validate_grounding_references` checks downstream citations against only the records retrieved for the current decision.

## Jurisdiction behavior

Jurisdiction-specific outputs require jurisdiction metadata in the retrieved corpus. When matching jurisdiction evidence is absent, the service returns partial support or insufficiency rather than inferring municipal authority from general model knowledge.

## Testing

```powershell
python -m pytest services/knowledge/tests
```

Tests use the in-memory backend or an injected HTTP transport and require neither a database nor internet access. The real HTTP adapter uses `CIVITAS_BACKEND_BASE_URL` and a backend-authorized bearer token.
