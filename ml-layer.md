# Civitas ML and Geospatial Intelligence

The Civitas intelligence layer combines computer vision, duplicate detection, spatial context, severity/priority assessment, and resolution verification behind typed service contracts. Each component exposes inspectable evidence and model metadata so downstream workflow decisions remain attributable.

## Package layout

```text
geospatial/                 PostGIS/geospatial operations
ml/vision/                  Image/video understanding
ml/duplicates/              Similarity, duplicate decisions and clustering
ml/risk/                    Severity and priority models
ml/resolution/              Before/after resolution verification
services/ml/                Unified runtime contracts and composition
services/evaluation/        Component and workflow evaluation
```

## Unified runtime contract

`services/ml` exposes a stable `ReportAnalysis` result containing:

- vision/media intelligence,
- duplicate candidates,
- cluster result,
- severity,
- priority,
- model metadata,
- basis/evidence fields,
- uncertainty/warnings,
- trace identifier.

The workflow consumes this contract directly. Language-model agents do not recalculate deterministic ML outputs.

## Vision

The vision layer supports still images and selected video frames. It provides:

- incident-category classification,
- model/version metadata,
- confidence margin,
- out-of-distribution ratio,
- media-quality/rejection state,
- structured evidence strings used by downstream logic.

CLIP-compatible semantic representations are used for real-media classification where the neural-model extra is available. Deterministic image features remain available for duplicate and resolution analysis.

### Media integrity

Unreadable, missing, unsupported, or low-quality media is represented as an explicit rejection/uncertainty state. The pipeline does not force a category when the media contract cannot support one.

## Duplicate detection

Duplicate intelligence combines independent signals rather than relying on one similarity score:

- text similarity,
- visual similarity,
- geographic distance,
- temporal proximity,
- category agreement,
- landmark/context overlap.

Per-signal evidence remains available for inspection and evaluation. Hard-negative cases—nearby but distinct incidents—are part of the evaluation corpus because false merges can be operationally costly.

## Incident clustering

Duplicate decisions can be composed into report clusters while preserving every source report. Cluster membership reduces ticket inflation without discarding additional evidence contributed by residents.

The cluster output is consumed by workflow and risk logic as context; source reports remain separately traceable for audit and citizen communication.

## Geospatial intelligence

The `civitas_geo` package/PostGIS queries provide deterministic spatial evidence, including:

- nearby incident candidates,
- nearby landmarks,
- distance to schools/hospitals/transport corridors,
- incident density,
- proximity features used by duplicate and priority logic.

Spatial calculations remain separate from LLM inference. Coordinates and derived exposure signals are persisted or traced through typed contracts.

## Severity

Severity measures the magnitude of harm or hazard indicated by the report and model evidence. The output includes:

- numeric/ordinal severity,
- contributing factors,
- factor citations/basis,
- model/version metadata.

Severity is not used as a synonym for operational urgency.

## Priority

Priority estimates response urgency after contextual factors are considered. Relevant signals can include:

- pedestrian/road exposure,
- school or hospital proximity,
- accessibility impact,
- public-health implications,
- number of corroborating reports,
- duration and spatial context.

Keeping severity and priority separate allows a moderate but high-exposure incident to receive urgent operational attention without misrepresenting its hazard magnitude.

## Resolution verification

`verify_resolution` compares original and post-work evidence and returns:

- `resolved`,
- `partially_resolved`,
- `unverifiable`,
- or `conflicting`.

The result includes structured evidence, reasons, confidence/basis fields, and model metadata. Uncertain or conflicting evidence remains reviewable rather than being coerced into a closure decision.

## Service failure behavior

The unified ML boundary uses explicit errors for malformed backend payloads, missing operational files, unsupported media, and contract violations. Missing dependency data is not silently converted into an empty candidate set or a guessed model output.

## Evaluation methodology

Civitas separates three forms of evaluation:

1. **Synthetic regression evaluation** for deterministic model and contract behavior.
2. **Real-media probe evaluation** for open/licensed civic photographs and videos.
3. **Workflow evaluation** for Baseline A, Baseline B, and the full LangGraph decision system.

Evaluation outputs preserve sample counts, dataset/version context, and failure cases. Synthetic/rule-derived labels are described as implementation/regression evidence rather than external real-world calibration.

### Vision/media evaluation

The frozen component corpus exercises supported civic categories, media-quality cases, ambiguous/OOD inputs, and real-media probes. Results are stored under the evaluation result directories together with per-case outputs.

### Duplicate/clustering evaluation

Duplicate evaluation tracks precision, recall, false merges, false splits, and hard-negative behavior. Clustering evaluation keeps scenario-level correctness separate from pairwise merge behavior so operational failure modes remain visible.

### Severity/priority evaluation

Risk evaluation checks agreement with the published scoring/rule contracts and validates factor/basis output. Rule-derived labels are treated as implementation-faithfulness tests, not independent calibration claims.

### Resolution evaluation

Resolution evaluation covers resolved, partial, unverifiable, and conflicting evidence outcomes, including edge/borderline cases that should remain review candidates.

## Golden civic scenario

The seeded water-leak scenario combines multiple citizen reports, media, wrong/ambiguous category input, school/traffic spatial context, duplicate clustering, risk assessment, policy-grounded routing, work-order generation, human review, and resolution evidence.

The golden scenario is used as an end-to-end integration trail. It is kept separate from component performance claims.

## Operational transparency

The ML layer records:

- model/version identifiers,
- inputs required for the decision,
- structured basis/evidence,
- uncertainty/rejection state,
- evaluation corpus/version where applicable,
- trace identifiers for runtime correlation.

This keeps model behavior inspectable by the workflow, reviewers, and evaluation harness without exposing hidden reasoning or unstructured internal state.
