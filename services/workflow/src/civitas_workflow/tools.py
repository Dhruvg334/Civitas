"""Explicit workflow tool boundaries with deterministic in-memory implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from civitas_knowledge.contracts import (
    IncidentCategory,
    KnowledgePurpose,
    KnowledgeQuery,
    KnowledgeResult,
)
from civitas_knowledge.retrieval import KnowledgeService

from civitas_workflow.workflow_contracts import (
    ClarificationQuestion,
    MLIntelligence,
    OperationalPlan,
    RoutingDecision,
    WorkflowContext,
    WorkflowTraceEvent,
)


class ReportContextTool(ABC):
    @abstractmethod
    def load(self, report_id: str) -> WorkflowContext: ...


class MLIntelligenceTool(ABC):
    @abstractmethod
    def analyze(self, context: WorkflowContext, *, trace_id: str) -> MLIntelligence: ...


class KnowledgeTool(ABC):
    @abstractmethod
    def retrieve(
        self,
        context: WorkflowContext,
        category: str | None,
        purposes: Sequence[KnowledgePurpose],
    ) -> KnowledgeResult: ...


class PersistenceTool(ABC):
    @abstractmethod
    def save_clarifications(
        self, incident_id: str, questions: Sequence[ClarificationQuestion]
    ) -> None: ...

    @abstractmethod
    def save_clarification_answers(self, incident_id: str, answers: dict[str, str]) -> None: ...

    @abstractmethod
    def ensure_routing(self, incident_id: str, decision: RoutingDecision) -> None: ...

    @abstractmethod
    def ensure_work_order(
        self, incident_id: str, plan: OperationalPlan, routing: RoutingDecision
    ) -> str: ...

    @abstractmethod
    def apply_human_review(self, work_order_id: str, action: str) -> None: ...


class TraceTool(ABC):
    @abstractmethod
    def record(self, incident_id: str, trace_id: str, event: WorkflowTraceEvent) -> None: ...


class InMemoryReportContextTool(ReportContextTool):
    def __init__(self, contexts: Sequence[WorkflowContext]) -> None:
        self._contexts = {context.report_id: context.model_copy(deep=True) for context in contexts}

    def load(self, report_id: str) -> WorkflowContext:
        if report_id not in self._contexts:
            raise LookupError(f"report {report_id!r} was not found")
        return self._contexts[report_id].model_copy(deep=True)


class InMemoryMLIntelligenceTool(MLIntelligenceTool):
    def __init__(self, result: MLIntelligence | Exception) -> None:
        self.result = result
        self.calls = 0

    def analyze(self, context: WorkflowContext, *, trace_id: str) -> MLIntelligence:
        del context, trace_id
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result.model_copy(deep=True)


class ServiceKnowledgeTool(KnowledgeTool):
    def __init__(self, service: KnowledgeService) -> None:
        self.service = service

    def retrieve(
        self,
        context: WorkflowContext,
        category: str | None,
        purposes: Sequence[KnowledgePurpose],
    ) -> KnowledgeResult:
        del context
        return self.service.retrieve(
            KnowledgeQuery(
                category=IncidentCategory(category) if category else None,
                purposes=list(purposes),
                limit=20,
            )
        )


class InMemoryPersistenceTool(PersistenceTool):
    def __init__(self) -> None:
        self.clarifications: dict[str, dict[str, str]] = {}
        self.routes: dict[str, RoutingDecision] = {}
        self.work_orders: dict[str, tuple[OperationalPlan, RoutingDecision]] = {}
        self.review_actions: dict[str, str] = {}

    def save_clarifications(
        self, incident_id: str, questions: Sequence[ClarificationQuestion]
    ) -> None:
        self.clarifications.setdefault(incident_id, {})
        for question in questions:
            self.clarifications[incident_id].setdefault(question.question_id, "")

    def save_clarification_answers(self, incident_id: str, answers: dict[str, str]) -> None:
        self.clarifications.setdefault(incident_id, {}).update(answers)

    def ensure_routing(self, incident_id: str, decision: RoutingDecision) -> None:
        self.routes.setdefault(incident_id, decision.model_copy(deep=True))

    def ensure_work_order(
        self, incident_id: str, plan: OperationalPlan, routing: RoutingDecision
    ) -> str:
        work_order_id = f"wo-{incident_id}"
        self.work_orders.setdefault(
            work_order_id, (plan.model_copy(deep=True), routing.model_copy(deep=True))
        )
        return work_order_id

    def apply_human_review(self, work_order_id: str, action: str) -> None:
        self.review_actions[work_order_id] = action


class InMemoryTraceTool(TraceTool):
    def __init__(self) -> None:
        self.events: list[tuple[str, str, WorkflowTraceEvent]] = []

    def record(self, incident_id: str, trace_id: str, event: WorkflowTraceEvent) -> None:
        self.events.append((incident_id, trace_id, event.model_copy(deep=True)))
