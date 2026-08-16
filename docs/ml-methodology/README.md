# ML Methodology

Civitas treats ML as a set of inspectable components that feed a larger decision workflow. Each model boundary exposes typed outputs, basis fields, version metadata, and explicit uncertainty rather than only a final label.

## Vision

The vision package supports image and selected video-frame analysis. Classification combines CLIP-compatible semantic representations with deterministic image features used by downstream duplicate and resolution components. Media quality and low-confidence outcomes remain visible to the workflow.

## Duplicate intelligence

Duplicate detection combines multiple signals:

- text similarity,
- visual similarity,
- geographic distance,
- temporal proximity,
- category agreement,
- landmark/context overlap.

No single feature is treated as sufficient for every case. The duplicate layer exposes per-signal evidence so clustering decisions can be inspected and evaluated against hard-negative cases.

## Clustering

Reports that satisfy duplicate and proximity criteria can be grouped into one operational incident while preserving every source report. This reduces ticket inflation without discarding evidence contributed by individual residents.

## Severity and priority

Severity and priority are separate model contracts:

- **Severity** represents harm or hazard magnitude.
- **Priority** represents operational urgency after spatial and contextual factors are considered.

The risk layer records contributing factors rather than presenting a score without basis.

## Geospatial context

PostGIS supplies spatial evidence such as distance to schools, hospitals, transport corridors and nearby reports. These values are computed deterministically and remain separate from language-model inference.

## Resolution verification

Resolution verification compares original and post-work evidence and returns one of four explicit outcomes: resolved, partially resolved, unverifiable, or conflicting. Ambiguous evidence remains reviewable rather than being coerced into a binary closure decision.

## Evaluation discipline

Component evaluation is kept separate from workflow evaluation. ML reports record the dataset/corpus used, sample count, label provenance, failure cases, and the specific model or rule version under test. Synthetic or rule-derived labels are identified as such and are not presented as independent real-world calibration.

## Runtime integration

The unified ML service exposes a `ReportAnalysis` contract containing vision, duplicate, cluster, severity, priority, model metadata, basis information, warnings, and trace identifiers. The LangGraph workflow consumes this contract directly and does not ask the LLM to recalculate deterministic ML outputs.
