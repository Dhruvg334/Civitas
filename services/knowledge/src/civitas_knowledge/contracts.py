"""Public contracts for deterministic policy and playbook grounding."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IncidentCategory(StrEnum):
    POTHOLE_ROAD_DAMAGE = "pothole_road_damage"
    WATER_LEAKAGE = "water_leakage"
    GARBAGE_OVERFLOW = "garbage_overflow"
    BROKEN_STREETLIGHT = "broken_streetlight"
    FALLEN_TREE = "fallen_tree"


class PolicyType(StrEnum):
    POLICY = "policy"
    PLAYBOOK = "playbook"


class KnowledgePurpose(StrEnum):
    DEPARTMENT_JURISDICTION = "department_jurisdiction"
    ROUTING_POLICY = "routing_policy"
    ESCALATION_RULES = "escalation_rules"
    SAFETY_GUIDANCE = "safety_guidance"
    REQUIRED_WORK_ORDER_FIELDS = "required_work_order_fields"
    OPERATIONAL_GUIDANCE = "operational_guidance"
    CITIZEN_COMMUNICATION_RESTRICTIONS = "citizen_communication_restrictions"


class GroundingStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT_KNOWLEDGE = "INSUFFICIENT_KNOWLEDGE"


class RetrievalMethod(StrEnum):
    EXACT_FILTER = "exact_filter"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


class KnowledgeQuery(StrictModel):
    category: IncidentCategory | None = None
    department: str | None = Field(default=None, min_length=1, max_length=100)
    jurisdiction: str | None = Field(default=None, min_length=1, max_length=200)
    policy_type: PolicyType | None = None
    purposes: list[KnowledgePurpose] = Field(default_factory=list)
    text: str | None = Field(default=None, min_length=2, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)

    @model_validator(mode="after")
    def require_retrieval_signal(self) -> KnowledgeQuery:
        if not any(
            (
                self.category,
                self.department,
                self.jurisdiction,
                self.policy_type,
                self.purposes,
                self.text,
            )
        ):
            raise ValueError("at least one knowledge retrieval criterion is required")
        return self


class KnowledgeProvenance(StrictModel):
    backend: str
    source_identifier: str
    source_path: str | None = None
    attributes: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class KnowledgeRecord(StrictModel):
    record_id: str
    reference_id: str
    title: str
    policy_type: PolicyType
    text: str
    categories: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    jurisdiction: str | None = None
    required_actions: list[str] = Field(default_factory=list)
    suggested_resources: list[str] = Field(default_factory=list)
    severity_factors: list[dict[str, Any]] = Field(default_factory=list)
    priority_factors: list[dict[str, Any]] = Field(default_factory=list)
    provenance: KnowledgeProvenance


class KnowledgeReference(StrictModel):
    record_id: str
    reference_id: str
    title: str
    source_identifier: str


class KnowledgeEvidence(StrictModel):
    reference: KnowledgeReference
    relevant_policy_text: str
    retrieval_method: RetrievalMethod
    retrieval_score: float | None = Field(default=None, ge=0)
    matched_terms: list[str] = Field(default_factory=list)


class KnowledgeResult(StrictModel):
    query: KnowledgeQuery
    records: list[KnowledgeRecord]
    evidence: list[KnowledgeEvidence]
    status: GroundingStatus
    sufficient_evidence: bool
    retrieval_method: RetrievalMethod
    missing_information: list[str]
    abstention_reason: str | None = None
    warnings: list[str]


class GroundingReferenceValidation(StrictModel):
    valid: bool
    valid_reference_ids: list[str] = Field(default_factory=list)
    invalid_reference_ids: list[str] = Field(default_factory=list)


class PolicyReference(StrictModel):
    """Backward-compatible compact reference used by existing consumers."""

    policy_id: str
    title: str
    excerpt: str
    source: str
    tags: list[str] = Field(default_factory=list)
