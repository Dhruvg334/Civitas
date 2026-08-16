# Evaluation

Civitas evaluates the decision architecture at two levels: component behavior and end-to-end workflow behavior. Offline and live-provider runs are intentionally separated so deterministic contract verification is not presented as live model-quality evidence.

## Three-system comparison

The workflow evaluator runs the same case corpus through three executable systems:

1. **Single-prompt baseline** — one competent structured LLM call.
2. **Structured mega-prompt baseline** — one LLM call with explicit evidence, grounding, abstention, routing, planning, and validation instructions.
3. **Civitas workflow** — the real LangGraph graph with specialized stages, ML tools, knowledge retrieval, critique, and human-review semantics.

All systems use the same case identifiers and canonical normalized output shape. Expected labels are stored separately from model inputs.

## Offline deterministic mode

Offline mode uses `FakeLLMClient` so the evaluation can execute without external credentials. It validates:

- prompt and schema contracts,
- real graph execution,
- baseline call counts,
- result normalization,
- metric calculation,
- fabricated-reference detection,
- prohibited-promise detection,
- serialization and report generation.

Saved offline artifacts are labelled `OFFLINE DETERMINISTIC ARCHITECTURE EVALUATION`.

## Live provider mode

The same runner can use the production LLM abstraction with Groq. Live outputs are stored separately from deterministic artifacts and record model configuration, prompt versions, latency, token usage where returned, case count, failures, and timestamp.

## Corpus

The workflow corpus contains privacy-safe civic cases spanning the supported incident categories and decision conditions such as straightforward reports, ambiguity, missing information, wrong citizen category, duplicate and non-duplicate proximity cases, school/traffic exposure, escalation, insufficient policy evidence, conflicting evidence, weak/no media, multi-department routing, unsupported timeline/resource traps, human-review requirements, and abstention.

Label provenance is recorded as human-authored, policy-derived, synthetic, or model-derived where applicable.

## Metrics

Programmatic metrics include:

- structured-output validity,
- category accuracy,
- primary/secondary department correctness,
- escalation correctness,
- valid and fabricated knowledge-reference rates,
- unsupported municipal-rule rate,
- work-order completeness,
- unsupported timeline/resource-claim rates,
- citizen-message compliance,
- clarification usefulness/unnecessary clarification,
- human-review correctness,
- abstention correctness,
- workflow failure rate,
- model-call count,
- latency,
- token usage when available.

Aggregate percentages are reported with sample count `N`.

## Result artifacts

Generated workflow results are stored under `services/evaluation/results/workflow/`:

- `baseline_single_prompt.json`
- `baseline_structured_prompt.json`
- `civitas_workflow.json`
- `comparison.json`
- `REPORT.md`

The files include dataset version, execution mode, prompt versions, model/provider metadata, case-level outputs, aggregate metrics, failures, and limitations of the evaluation mode.
