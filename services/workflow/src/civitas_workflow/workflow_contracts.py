"""Serializable contracts for the first Civitas incident workflow."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from civitas_knowledge.contracts import KnowledgeResult
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    WAITING_FOR_HUMAN_REVIEW = "waiting_for_human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ABSTAINED = "abstained"
    FAILED = "failed"


class WorkflowContext(StrictModel):
    report_id: str
    incident_id: str
    description: str = ""
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    citizen_selected_category: str | None = None
    media: list[dict[str, str | None]] = Field(default_factory=list)
    clarification_answers: dict[str, str] = Field(default_factory=dict)
    existing_work_order_id: str | None = None
    existing_ml_available: bool = False


class StructuredEvidence(StrictModel):
    likely_category: str | None = None
    secondary_categories: list[str] = Field(default_factory=list)
    observed_facts: list[str] = Field(default_factory=list)
    citizen_reported_claims: list[str] = Field(default_factory=list)
    retrieved_facts: list[str] = Field(default_factory=list)
    inferred_facts: list[str] = Field(default_factory=list)
    hazards: list[str] = Field(default_factory=list)
    landmarks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


class ClarificationQuestion(StrictModel):
    question_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=1, max_length=500)
    decision_impact: list[
        Literal["classification", "duplicate", "severity", "priority", "routing", "safety"]
    ] = Field(min_length=1)
    required: bool = True


class ClarificationPlan(StrictModel):
    clarification_required: bool
    questions: list[ClarificationQuestion] = Field(default_factory=list, max_length=3)
    can_continue_without_answers: bool

    @model_validator(mode="after")
    def questions_match_requirement(self) -> ClarificationPlan:
        if self.clarification_required != bool(self.questions):
            raise ValueError("clarification_required must match whether questions are present")
        return self


class MLIntelligence(StrictModel):
    available: bool
    primary_category: str | None = None
    observable_evidence: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    duplicate_verdict: Literal["new", "duplicate", "unknown"] | None = None
    cluster_verdict: Literal["merged", "isolated", "unknown"] | None = None
    severity_score: int | None = Field(default=None, ge=0, le=100)
    severity_level: str | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    priority_level: str | None = None
    feature_contributions: list[str] = Field(default_factory=list)
    model_versions: list[str] = Field(default_factory=list)
    failure_reason: str | None = None


class RoutingDecision(StrictModel):
    primary_department: str
    secondary_departments: list[str] = Field(default_factory=list)
    escalation_required: bool
    rationale: list[str] = Field(default_factory=list)
    policy_references: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    review_required: bool = True


class OperationalPlan(StrictModel):
    summary: str = Field(min_length=1, max_length=2000)
    required_actions: list[str] = Field(default_factory=list)
    suggested_resources: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    estimated_window_min_hours: int | None = Field(default=None, ge=0)
    estimated_window_max_hours: int | None = Field(default=None, ge=0)
    missing_operational_information: list[str] = Field(default_factory=list)
    policy_references: list[str] = Field(default_factory=list)
    review_required: bool = True

    @model_validator(mode="after")
    def window_is_non_decreasing(self) -> OperationalPlan:
        if (
            self.estimated_window_min_hours is not None
            and self.estimated_window_max_hours is not None
            and self.estimated_window_min_hours > self.estimated_window_max_hours
        ):
            raise ValueError("estimated resolution window minimum cannot exceed maximum")
        return self


class CriticVerdict(StrEnum):
    PASS = "PASS"
    REVISE_ROUTING = "REVISE_ROUTING"
    REVISE_PLAN = "REVISE_PLAN"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    ABSTAIN = "ABSTAIN"


class CriticIssue(StrictModel):
    code: str
    message: str
    affected_node: Literal["routing", "operational_planning", "workflow"]
    reference_ids: list[str] = Field(default_factory=list)


class CriticResult(StrictModel):
    verdict: CriticVerdict
    issues: list[CriticIssue] = Field(default_factory=list)
    verification_references: list[str] = Field(default_factory=list)


class HumanReviewAction(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"
    REROUTE = "reroute"
    REJECT = "reject"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"


class HumanReviewDecision(StrictModel):
    action: HumanReviewAction
    notes: str | None = Field(default=None, max_length=2000)
    routing: RoutingDecision | None = None
    operational_plan: OperationalPlan | None = None


class CitizenCommunication(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    safety_advice_reference_ids: list[str] = Field(default_factory=list)


class WorkflowTraceEvent(StrictModel):
    node: str
    status: Literal["succeeded", "failed", "interrupted"]
    latency_ms: int = Field(ge=0)
    tool_or_model: str | None = None
    validation_outcome: str = "valid"
    knowledge_reference_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None


class CivitasWorkflowState(StrictModel):
    trace_id: str
    report_id: str
    status: WorkflowStatus = WorkflowStatus.RUNNING
    context: WorkflowContext | None = None
    evidence: StructuredEvidence | None = None
    clarifications: ClarificationPlan | None = None
    ml: MLIntelligence | None = None
    knowledge: KnowledgeResult | None = None
    routing: RoutingDecision | None = None
    operational_plan: OperationalPlan | None = None
    critic: CriticResult | None = None
    human_review: HumanReviewDecision | None = None
    citizen_communication: CitizenCommunication | None = None
    work_order_id: str | None = None
    revision_count: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    trace_events: list[WorkflowTraceEvent] = Field(default_factory=list)


class WorkflowCheckpoint(StrictModel):
    thread_id: str
    status: WorkflowStatus
    trace_id: str
