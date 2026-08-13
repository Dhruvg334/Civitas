# Shared Schemas

This folder is the cross-module contract boundary. JSON Schema files are canonical until generated language-specific types are introduced.

Breaking changes require:
1. a versioned schema change,
2. contract tests in every affected module,
3. migration notes,
4. explicit integration review.

Knowledge grounding adds `knowledge-query`, `knowledge-reference`, and
`knowledge-result`. Structured model calls expose `llm-call-metadata`.
Their Python counterparts live in `civitas_knowledge.contracts` and
`civitas_workflow.llm.contracts`; contract tests keep required fields and
enum values aligned.
