# Civitas knowledge service

`civitas_knowledge` retrieves municipal policy and playbook evidence for later workflow decisions. It does not decide routing or create work orders, and it never fills missing policy with general model knowledge.

## Architecture

- `KnowledgeBackend` is the storage boundary.
- `HttpKnowledgeBackend` consumes the existing authenticated `GET /api/v1/policies` API and validates its success envelope.
- `InMemoryKnowledgeBackend` provides deterministic local and unit-test operation.
- `KnowledgeService` applies exact filtering first, then keyword relevance, then a stable reference-ID tie-break. No external vector service is required.

Queries can request the five MVP incident categories and the supported purposes: department jurisdiction, routing, escalation, safety, work-order fields, operational guidance, and citizen communication restrictions.

## Results and provenance

Every `KnowledgeResult` retains the backend `policy_id`, public policy `code`, exact policy text, structured actions/resources, retrieval method, transparent relevance points, and backend source path. Relevance points are ranking signals, not confidence probabilities.

The grounding state is one of `SUPPORTED`, `PARTIALLY_SUPPORTED`, or `INSUFFICIENT_KNOWLEDGE`. Missing jurisdiction or purpose coverage is explicit. `validate_grounding_references` checks downstream citations against only the records retrieved for that decision.

## Local testing

```powershell
python -m pytest services/knowledge/tests
```

Tests use the in-memory backend or an injected HTTP transport and need neither a database nor internet access. A real adapter requires `CIVITAS_BACKEND_BASE_URL` and a bearer token authorized for the backend policy routes.

## Limitations

- The current backend policy entity has no jurisdiction field. Jurisdiction-specific queries therefore abstain or return partial support and never infer jurisdiction.
- Keyword relevance is intentionally simple for the small curated corpus. A future semantic ranker may be added behind an interface without changing result contracts.
- The service retrieves evidence; authorized humans remain responsible for high-impact routing, work-order, and closure decisions.
