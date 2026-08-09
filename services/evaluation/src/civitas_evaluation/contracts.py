"""Evaluation contracts (Phase 11/12).

Types for the frozen test sets, per-component predictions and the
aggregated metric records. Everything saved to `results/` validates
against these models so a judge can verify the artifacts directly.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    case_id: str
    input_payload: dict[str, Any]
    expected_output: dict[str, Any]
    tags: list[str] = Field(default_factory=list)


class LabeledExample(BaseModel):
    """One frozen test-set row: input + ground-truth label + provenance."""

    case_id: str
    label: str
    hard: bool = Field(default=False, description="hard-negative / adversarial intent")
    source: str = "synthetic (procedural generator), see dataset manifest"
    details: dict[str, Any] = Field(default_factory=dict)


class ConfusionMatrixRecord(BaseModel):
    classes: list[str]
    matrix: list[list[int]]  # rows = true, cols = predicted
    row_sums: list[int] = Field(default_factory=list)


class ClassMetrics(BaseModel):
    class_name: str
    tp: int = 0
    fp: int = 0
    fn: int = 0
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None


class ComponentMetrics(BaseModel):
    component: str
    model_version: str | None = None
    thresholds: dict[str, float | str] = Field(default_factory=dict)
    test_set: str
    n: int = 0
    metrics: dict[str, float] = Field(default_factory=dict)
    class_wise: list[ClassMetrics] = Field(default_factory=list)
    confusion: ConfusionMatrixRecord | None = None
    notes: list[str] = Field(default_factory=list)


class FailureRecord(BaseModel):
    failure_id: str
    component: str
    test_case: str
    input_summary: str
    expected: str
    actual: str
    model_version: str | None = None
    feature_evidence: list[str] = Field(default_factory=list)
    likely_reason: str
    acceptable: bool
    improvement: str


class GoldenStep(BaseModel):
    step: str
    payload: dict[str, Any]
    output: dict[str, Any]


class GoldenScenario(BaseModel):
    scenario_id: str = "golden-water-leak"
    steps: list[GoldenStep] = Field(default_factory=list)
    model_evidence: bool = False  # golden demo is NOT model-performance evidence


class EvaluationReport(BaseModel):
    project: str = "civitas"
    phase: str = "Phase 11/12"
    components: list[ComponentMetrics] = Field(default_factory=list)
    failures: list[FailureRecord] = Field(default_factory=list)
    golden: list[GoldenScenario] = Field(default_factory=list)
    dataset_manifest: dict[str, Any] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    thresholds: dict[str, dict[str, float | str]] = Field(default_factory=dict)
    worked: list[str] = Field(default_factory=list)