# Knowledge Grounding

The Civitas knowledge layer supplies policy and operational evidence to routing, planning, critique, and communication stages. Its primary purpose is to keep municipal rules attributable to stored records instead of allowing the language model to invent them.

## Retrieval contract

A knowledge query can constrain retrieval by category, department, jurisdiction, policy type, and operational purpose. Results contain:

- stable record identifier,
- title/type,
- category and department metadata,
- jurisdiction when present,
- relevant rule/playbook text,
- retrieval method and score,
- provenance,
- warnings,
- sufficiency state.

## Retrieval order

The default strategy is deterministic-first:

1. exact metadata constraints,
2. category/department/purpose filtering,
3. keyword/token relevance,
4. stable identifier tie-breaking.

This keeps the small policy corpus reproducible and avoids requiring an external vector service for core routing behavior.

## Sufficiency states

Knowledge results report one of:

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `INSUFFICIENT_KNOWLEDGE`

A missing policy does not become an inferred municipal rule. Downstream workflow logic can narrow the recommendation, request review, or abstain.

## Reference validation

Policy-dependent LLM output must cite knowledge IDs returned by the retrieval layer. `validate_grounding_references` rejects invented or unavailable identifiers before a routing/work-order result is accepted.

## Backend adapter

The HTTP adapter consumes the existing policy API and preserves the Civitas success/error envelope. An in-memory backend supplies deterministic tests without changing retrieval behavior.

## Corpus scope

The seeded corpus covers department jurisdiction, routing policy, escalation conditions, safety guidance, work-order requirements, operational playbooks, and citizen-communication constraints across the supported civic categories. Jurisdiction-specific claims remain evidence-dependent; absence of jurisdiction metadata produces an explicit sufficiency result rather than a guessed location rule.
