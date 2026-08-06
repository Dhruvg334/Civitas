# Civitas Repository Instructions

## Product boundary
Civitas is an evidence-backed civic incident intelligence platform. Keep observable evidence, retrieved knowledge, model output, inference, and human decisions distinct.

## Architecture boundaries
- `apps/web`: product interfaces only.
- `apps/api`: public API, validation, persistence adapters, auth, and operational state.
- `services/workflow`: agent graph and orchestration.
- `services/knowledge`: policy/playbook retrieval and grounding.
- `services/evaluation`: baseline and workflow evaluation.
- `services/ml`: inference interfaces and ML service composition.
- `ml/*`: model-specific implementation, training, and experiments.
- `schemas`: versioned shared contracts. Breaking changes require explicit review.
- `database`: migrations and seed data only.

## Engineering rules
- Do not place secrets in source control.
- Do not fabricate metrics or model confidence.
- Add tests for normal, boundary, and failure behavior.
- Keep public interfaces typed and schema validated.
- Prefer small, reviewable changes over broad rewrites.
- Preserve human review for high-impact routing, work-order, and closure decisions.
- Record known limitations rather than hiding them.

## Before completing a coding task
Run the relevant lint, type-check, tests, and build commands. Report commands used, concrete test values, expected results, and remaining limitations.
