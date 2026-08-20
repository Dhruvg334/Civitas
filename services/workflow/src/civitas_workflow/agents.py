"""Structured agents; all model invocation stays behind ``LLMClient``."""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

from civitas_knowledge.contracts import KnowledgeResult
from pydantic import BaseModel

from civitas_workflow.llm import LLMClient, LLMMessage, ModelTier
from civitas_workflow.prompts import PromptLoader
from civitas_workflow.workflow_contracts import (
    CitizenCommunication,
    ClarificationPlan,
    CriticResult,
    MLIntelligence,
    OperationalPlan,
    RoutingDecision,
    StructuredEvidence,
    WorkflowContext,
)

OutputT = TypeVar("OutputT", bound=BaseModel)


def sanitize_ai_input_text(text: str, max_chars: int = 10000) -> str:
    """Sanitize user-provided text for LLM ingestion by stripping control characters and bounding length."""
    if not isinstance(text, str):
        return text
    # Strip null bytes and non-printable control characters (except newline, tab, carriage return)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return cleaned[:max_chars]


def sanitize_payload(payload: Any) -> Any:
    """Recursively sanitize string values in dictionaries, lists, and Pydantic models."""
    if isinstance(payload, str):
        return sanitize_ai_input_text(payload)
    if isinstance(payload, dict):
        return {k: sanitize_payload(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    if isinstance(payload, BaseModel):
        return sanitize_payload(payload.model_dump(mode="json"))
    return payload


class CivitasAgents:
    def __init__(self, llm: LLMClient, *, prompt_root: Path) -> None:
        self.llm = llm
        self.prompts = PromptLoader(prompt_root)

    def structure_evidence(
        self, context: WorkflowContext, ml: MLIntelligence | None, trace_id: str
    ) -> StructuredEvidence:
        return self._call(
            "agents/evidence/evidence-v1.md",
            StructuredEvidence,
            {"context": context, "ml": ml},
            ModelTier.FAST,
            trace_id,
        )

    def clarify(
        self, context: WorkflowContext, evidence: StructuredEvidence, trace_id: str
    ) -> ClarificationPlan:
        return self._call(
            "agents/clarification/clarification-v1.md",
            ClarificationPlan,
            {"context": context, "evidence": evidence},
            ModelTier.FAST,
            trace_id,
        )

    def route(
        self,
        evidence: StructuredEvidence,
        ml: MLIntelligence,
        knowledge: KnowledgeResult,
        trace_id: str,
    ) -> RoutingDecision:
        return self._call(
            "agents/routing/routing-v1.md",
            RoutingDecision,
            {"evidence": evidence, "ml": ml, "knowledge": knowledge},
            ModelTier.PRIMARY,
            trace_id,
        )

    def plan(
        self,
        evidence: StructuredEvidence,
        ml: MLIntelligence,
        routing: RoutingDecision,
        knowledge: KnowledgeResult,
        trace_id: str,
    ) -> OperationalPlan:
        return self._call(
            "agents/operational_planning/operational-planning-v1.md",
            OperationalPlan,
            {"evidence": evidence, "ml": ml, "routing": routing, "knowledge": knowledge},
            ModelTier.PRIMARY,
            trace_id,
        )

    def critique(
        self,
        evidence: StructuredEvidence,
        ml: MLIntelligence,
        knowledge: KnowledgeResult,
        routing: RoutingDecision,
        plan: OperationalPlan,
        trace_id: str,
    ) -> CriticResult:
        return self._call(
            "agents/critic/critic-v1.md",
            CriticResult,
            {
                "evidence": evidence,
                "ml": ml,
                "knowledge": knowledge,
                "routing": routing,
                "plan": plan,
            },
            ModelTier.PRIMARY,
            trace_id,
        )

    def communicate(
        self,
        context: WorkflowContext,
        evidence: StructuredEvidence,
        routing: RoutingDecision,
        plan: OperationalPlan,
        knowledge: KnowledgeResult,
        trace_id: str,
    ) -> CitizenCommunication:
        return self._call(
            "agents/citizen_communication/citizen-communication-v1.md",
            CitizenCommunication,
            {
                "context": context,
                "evidence": evidence,
                "routing": routing,
                "plan": plan,
                "knowledge": knowledge,
            },
            ModelTier.FAST,
            trace_id,
        )

    def _call(
        self,
        prompt_path: str,
        output_type: type[OutputT],
        payload: object,
        tier: ModelTier,
        trace_id: str,
    ) -> OutputT:
        prompt = self.prompts.load(prompt_path)
        sanitized = sanitize_payload(payload)
        result = self.llm.generate_structured(
            [
                LLMMessage(role="system", content=prompt),
                LLMMessage(role="user", content=json.dumps(sanitized, default=_dump, sort_keys=True)),
            ],
            output_type,
            model_tier=tier,
            trace_id=trace_id,
        )
        return result.output


def _dump(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"cannot serialize {type(value)!r}")
