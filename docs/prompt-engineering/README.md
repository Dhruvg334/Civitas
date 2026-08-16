# Prompt and Structured-Output Design

Civitas prompts are versioned runtime assets, not large strings embedded throughout application code. Each agent receives only the context required for its responsibility and returns a schema-validated result.

## Agent boundaries

The workflow separates language-model responsibilities into focused stages:

- evidence structuring,
- clarification planning,
- department routing,
- operational planning,
- critic/consistency review,
- citizen communication.

Deterministic context loading, ML inference, policy retrieval, persistence and workflow state transitions remain outside the LLM.

## Evidence discipline

Prompts require explicit distinction between:

- observed evidence,
- citizen-reported claims,
- retrieved policy,
- inference.

Unsupported causes, policy rules, resources, timelines, or visual facts are rejected by schema/grounding checks or surfaced for human review.

## Structured outputs

All operational LLM outputs are validated against typed Pydantic contracts. Invalid JSON, schema mismatches, unsupported knowledge references, provider failures, and exhausted retries are represented as typed errors instead of silently accepted text.

## Grounding

Policy-dependent outputs must cite valid knowledge identifiers returned by the knowledge layer. Reference validation detects fabricated IDs before routing or work-order recommendations are accepted.

## Critic stage

The critic checks evidence boundaries, routing consistency, work-order completeness, unsupported policy claims, unsupported resource/timeline statements, and human-review conditions. Its output is machine-readable and controls bounded revision or escalation paths without exposing hidden chain-of-thought.

## Reproducibility

Prompt versions are recorded by the evaluation system so baseline and Civitas runs can be compared against the exact prompt assets used for each execution.
