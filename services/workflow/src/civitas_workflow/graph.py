"""Checkpointed LangGraph workflow for a single Civitas incident."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal

from civitas_knowledge.contracts import GroundingStatus, KnowledgePurpose
from civitas_knowledge.grounding import validate_grounding_references
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from civitas_workflow.agents import CivitasAgents
from civitas_workflow.tools import (
    KnowledgeTool,
    MLIntelligenceTool,
    PersistenceTool,
    ReportContextTool,
    TraceTool,
)
from civitas_workflow.workflow_contracts import (
    CivitasWorkflowState,
    ClarificationPlan,
    ClarificationQuestion,
    CriticVerdict,
    HumanReviewAction,
    HumanReviewDecision,
    MLIntelligence,
    WorkflowContext,
    WorkflowStatus,
    WorkflowTraceEvent,
)

MAX_REVISIONS = 2


@dataclass(frozen=True)
class WorkflowDependencies:
    context_tool: ReportContextTool
    ml_tool: MLIntelligenceTool
    knowledge_tool: KnowledgeTool
    persistence_tool: PersistenceTool
    trace_tool: TraceTool
    agents: CivitasAgents


class CivitasWorkflow:
    def __init__(self, dependencies: WorkflowDependencies) -> None:
        self.dependencies = dependencies
        self.checkpointer = MemorySaver()
        self.graph = self._build().compile(checkpointer=self.checkpointer)

    def _build(self) -> StateGraph[CivitasWorkflowState]:
        graph = StateGraph(CivitasWorkflowState)
        graph.add_node("load_context", self._load_context)
        graph.add_node("ml_intelligence", self._ml_intelligence)
        graph.add_node("structure_evidence", self._structure_evidence)
        graph.add_node("clarification_check", self._clarification_check)
        graph.add_node("clarification_interrupt", self._clarification_interrupt)
        graph.add_node("knowledge_grounding", self._knowledge_grounding)
        graph.add_node("routing_agent", self._routing_agent)
        graph.add_node("operational_planner", self._operational_planner)
        graph.add_node("critic", self._critic)
        graph.add_node("prepare_human_review", self._prepare_human_review)
        graph.add_node("human_review_interrupt", self._human_review_interrupt)
        graph.add_node("citizen_communication", self._citizen_communication)
        graph.add_edge(START, "load_context")
        graph.add_conditional_edges(
            "load_context", self._after_load, {"ml_intelligence": "ml_intelligence", "end": END}
        )
        graph.add_edge("ml_intelligence", "structure_evidence")
        graph.add_edge("structure_evidence", "clarification_check")
        graph.add_conditional_edges(
            "clarification_check",
            self._after_clarification_check,
            {
                "clarification_interrupt": "clarification_interrupt",
                "knowledge_grounding": "knowledge_grounding",
                "end": END,
            },
        )
        graph.add_edge("clarification_interrupt", "knowledge_grounding")
        graph.add_edge("knowledge_grounding", "routing_agent")
        graph.add_conditional_edges(
            "routing_agent",
            self._after_routing,
            {
                "operational_planner": "operational_planner",
                "prepare_human_review": "prepare_human_review",
                "end": END,
            },
        )
        graph.add_conditional_edges(
            "operational_planner", self._after_plan, {"critic": "critic", "end": END}
        )
        graph.add_conditional_edges(
            "critic",
            self._after_critic,
            {
                "routing_agent": "routing_agent",
                "operational_planner": "operational_planner",
                "prepare_human_review": "prepare_human_review",
                "end": END,
            },
        )
        graph.add_edge("prepare_human_review", "human_review_interrupt")
        graph.add_conditional_edges(
            "human_review_interrupt",
            self._after_human_review,
            {
                "citizen_communication": "citizen_communication",
                "routing_agent": "routing_agent",
                "clarification_interrupt": "clarification_interrupt",
                "end": END,
            },
        )
        graph.add_edge("citizen_communication", END)
        return graph

    def _load_context(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        try:
            context = self.dependencies.context_tool.load(state.report_id)
            return self._update(
                state,
                context=context,
                status=WorkflowStatus.RUNNING,
                event=self._event("load_context", started, "ReportContextTool"),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "load_context", started, exc, "ReportContextTool")

    def _ml_intelligence(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert state.context is not None
        try:
            ml = self.dependencies.ml_tool.analyze(state.context, trace_id=state.trace_id)
            return self._update(
                state, ml=ml, event=self._event("ml_intelligence", started, "MLIntelligenceTool")
            )
        except Exception as exc:  # noqa: BLE001
            unavailable = MLIntelligence(available=False, failure_reason=str(exc))
            return self._update(
                state,
                ml=unavailable,
                warnings=[*state.warnings, f"ML intelligence unavailable: {exc}"],
                event=self._event(
                    "ml_intelligence", started, "MLIntelligenceTool", status="failed", error=exc
                ),
            )

    def _structure_evidence(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert state.context is not None
        try:
            evidence = self.dependencies.agents.structure_evidence(
                state.context, state.ml, state.trace_id
            )
            return self._update(
                state,
                evidence=evidence,
                event=self._event("structure_evidence", started, "fast_llm"),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "structure_evidence", started, exc, "fast_llm")

    def _clarification_check(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert state.context is not None and state.evidence is not None
        try:
            plan = self.dependencies.agents.clarify(state.context, state.evidence, state.trace_id)
            if plan.clarification_required:
                self.dependencies.persistence_tool.save_clarifications(
                    state.context.incident_id, plan.questions
                )
            return self._update(
                state,
                clarifications=plan,
                status=(
                    WorkflowStatus.WAITING_FOR_CLARIFICATION
                    if plan.clarification_required and not plan.can_continue_without_answers
                    else WorkflowStatus.RUNNING
                ),
                event=self._event("clarification_check", started, "fast_llm"),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "clarification_check", started, exc, "fast_llm")

    def _clarification_interrupt(self, state: CivitasWorkflowState) -> dict[str, object]:
        assert state.context is not None and state.clarifications is not None
        self.dependencies.trace_tool.record(
            state.context.incident_id,
            state.trace_id,
            WorkflowTraceEvent(
                node="clarification_interrupt",
                status="interrupted",
                latency_ms=0,
                tool_or_model="LangGraph",
                validation_outcome="valid",
            ),
        )
        answers = interrupt(
            {
                "kind": "clarification",
                "trace_id": state.trace_id,
                "report_id": state.report_id,
                "questions": [
                    question.model_dump(mode="json") for question in state.clarifications.questions
                ],
            }
        )
        if not isinstance(answers, dict) or not all(
            isinstance(value, str) for value in answers.values()
        ):
            return self._update(
                state,
                status=WorkflowStatus.FAILED,
                errors=[
                    *state.errors,
                    "clarification resume must be an object of question IDs to answers",
                ],
            )
        self.dependencies.persistence_tool.save_clarification_answers(
            state.context.incident_id, answers
        )
        context = state.context.model_copy(
            update={"clarification_answers": {**state.context.clarification_answers, **answers}}
        )
        return self._update(state, context=context, status=WorkflowStatus.RUNNING)

    def _knowledge_grounding(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert state.context is not None and state.evidence is not None
        category = state.evidence.likely_category or (
            state.ml.primary_category if state.ml else None
        )
        try:
            knowledge = self.dependencies.knowledge_tool.retrieve(
                state.context,
                category,
                [
                    KnowledgePurpose.DEPARTMENT_JURISDICTION,
                    KnowledgePurpose.ROUTING_POLICY,
                    KnowledgePurpose.ESCALATION_RULES,
                    KnowledgePurpose.SAFETY_GUIDANCE,
                    KnowledgePurpose.REQUIRED_WORK_ORDER_FIELDS,
                    KnowledgePurpose.OPERATIONAL_GUIDANCE,
                    KnowledgePurpose.CITIZEN_COMMUNICATION_RESTRICTIONS,
                ],
            )
            warnings = list(state.warnings)
            if knowledge.status != GroundingStatus.SUPPORTED:
                warnings.append(knowledge.abstention_reason or "municipal knowledge is partial")
            references = [item.reference.reference_id for item in knowledge.evidence]
            return self._update(
                state,
                knowledge=knowledge,
                warnings=warnings,
                event=self._event(
                    "knowledge_grounding", started, "KnowledgeTool", references=references
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "knowledge_grounding", started, exc, "KnowledgeTool")

    def _routing_agent(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert state.evidence is not None and state.ml is not None and state.knowledge is not None
        if state.knowledge.status == GroundingStatus.INSUFFICIENT_KNOWLEDGE:
            return self._update(
                state,
                status=WorkflowStatus.ABSTAINED,
                warnings=[
                    *state.warnings,
                    "Routing abstained: municipal knowledge is insufficient.",
                ],
                event=self._event("routing_agent", started, "primary_llm", status="interrupted"),
            )
        try:
            routing = self.dependencies.agents.route(
                state.evidence, state.ml, state.knowledge, state.trace_id
            )
            validation = validate_grounding_references(routing.policy_references, state.knowledge)
            if not validation.valid:
                raise ValueError(
                    f"routing cited unavailable knowledge IDs: {validation.invalid_reference_ids}"
                )
            return self._update(
                state,
                routing=routing,
                event=self._event(
                    "routing_agent", started, "primary_llm", references=routing.policy_references
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "routing_agent", started, exc, "primary_llm")

    def _operational_planner(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert (
            state.evidence is not None
            and state.ml is not None
            and state.knowledge is not None
            and state.routing is not None
        )
        try:
            plan = self.dependencies.agents.plan(
                state.evidence, state.ml, state.routing, state.knowledge, state.trace_id
            )
            validation = validate_grounding_references(plan.policy_references, state.knowledge)
            if not validation.valid:
                raise ValueError(
                    f"operational plan cited unavailable knowledge IDs: {validation.invalid_reference_ids}"
                )
            return self._update(
                state,
                operational_plan=plan,
                event=self._event(
                    "operational_planner", started, "primary_llm", references=plan.policy_references
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "operational_planner", started, exc, "primary_llm")

    def _critic(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert (
            state.evidence
            and state.ml
            and state.knowledge
            and state.routing
            and state.operational_plan
        )
        try:
            critic = self.dependencies.agents.critique(
                state.evidence,
                state.ml,
                state.knowledge,
                state.routing,
                state.operational_plan,
                state.trace_id,
            )
            references = [
                *critic.verification_references,
                *(reference for issue in critic.issues for reference in issue.reference_ids),
            ]
            validation = validate_grounding_references(references, state.knowledge)
            if not validation.valid:
                raise ValueError(
                    f"critic cited unavailable knowledge IDs: {validation.invalid_reference_ids}"
                )
            revisions = state.revision_count + (
                1
                if critic.verdict in {CriticVerdict.REVISE_ROUTING, CriticVerdict.REVISE_PLAN}
                else 0
            )
            return self._update(
                state,
                critic=critic,
                revision_count=revisions,
                event=self._event("critic", started, "primary_llm", references=references),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "critic", started, exc, "primary_llm")

    def _prepare_human_review(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert state.context
        try:
            if state.routing is None or state.operational_plan is None:
                return self._update(
                    state,
                    status=WorkflowStatus.WAITING_FOR_HUMAN_REVIEW,
                    event=self._event(
                        "prepare_human_review", started, "PersistenceTool", status="interrupted"
                    ),
                )
            self.dependencies.persistence_tool.ensure_routing(
                state.context.incident_id, state.routing
            )
            work_order_id = (
                state.work_order_id
                or self.dependencies.persistence_tool.ensure_work_order(
                    state.context.incident_id, state.operational_plan, state.routing
                )
            )
            return self._update(
                state,
                work_order_id=work_order_id,
                status=WorkflowStatus.WAITING_FOR_HUMAN_REVIEW,
                event=self._event(
                    "prepare_human_review",
                    started,
                    "PersistenceTool",
                    references=state.routing.policy_references,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "prepare_human_review", started, exc, "PersistenceTool")

    def _human_review_interrupt(self, state: CivitasWorkflowState) -> dict[str, object]:
        assert state.context
        self.dependencies.trace_tool.record(
            state.context.incident_id,
            state.trace_id,
            WorkflowTraceEvent(
                node="human_review_interrupt",
                status="interrupted",
                latency_ms=0,
                tool_or_model="LangGraph",
                validation_outcome="valid",
            ),
        )
        raw = interrupt(
            {
                "kind": "human_review",
                "trace_id": state.trace_id,
                "incident_id": state.context.incident_id,
                "work_order_id": state.work_order_id,
                "routing": state.routing.model_dump(mode="json") if state.routing else None,
                "operational_plan": state.operational_plan.model_dump(mode="json")
                if state.operational_plan
                else None,
            }
        )
        decision = HumanReviewDecision.model_validate(raw)
        if state.work_order_id:
            self.dependencies.persistence_tool.apply_human_review(
                state.work_order_id, decision.action.value
            )
        update: dict[str, object] = {"human_review": decision}
        if decision.routing:
            update["routing"] = decision.routing
        if decision.operational_plan:
            update["operational_plan"] = decision.operational_plan
        if decision.action == HumanReviewAction.APPROVE:
            update["status"] = WorkflowStatus.APPROVED
        elif decision.action == HumanReviewAction.REJECT:
            update["status"] = WorkflowStatus.REJECTED
        elif decision.action == HumanReviewAction.REQUEST_MORE_EVIDENCE:
            question = ClarificationQuestion(
                question_id="human_requested_evidence",
                text=decision.notes or "Please provide additional evidence.",
                reason="Human reviewer requested more evidence.",
                decision_impact=["safety"],
                required=True,
            )
            self.dependencies.persistence_tool.save_clarifications(
                state.context.incident_id, [question]
            )
            update["clarifications"] = ClarificationPlan(
                clarification_required=True,
                questions=[question],
                can_continue_without_answers=False,
            )
            update["status"] = WorkflowStatus.WAITING_FOR_CLARIFICATION
        return {**update, "trace_events": list(state.trace_events)}

    def _citizen_communication(self, state: CivitasWorkflowState) -> dict[str, object]:
        started = time.perf_counter()
        assert (
            state.context
            and state.evidence
            and state.routing
            and state.operational_plan
            and state.knowledge
        )
        try:
            communication = self.dependencies.agents.communicate(
                state.context,
                state.evidence,
                state.routing,
                state.operational_plan,
                state.knowledge,
                state.trace_id,
            )
            validation = validate_grounding_references(
                communication.safety_advice_reference_ids, state.knowledge
            )
            if not validation.valid:
                raise ValueError(
                    f"communication cited unavailable knowledge IDs: {validation.invalid_reference_ids}"
                )
            return self._update(
                state,
                citizen_communication=communication,
                event=self._event(
                    "citizen_communication",
                    started,
                    "fast_llm",
                    references=communication.safety_advice_reference_ids,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return self._failed(state, "citizen_communication", started, exc, "fast_llm")

    @staticmethod
    def _after_load(state: CivitasWorkflowState) -> Literal["ml_intelligence", "end"]:
        return "end" if state.status == WorkflowStatus.FAILED else "ml_intelligence"

    @staticmethod
    def _after_clarification_check(
        state: CivitasWorkflowState,
    ) -> Literal["clarification_interrupt", "knowledge_grounding", "end"]:
        if state.status == WorkflowStatus.FAILED:
            return "end"
        if (
            state.clarifications
            and state.clarifications.clarification_required
            and not state.clarifications.can_continue_without_answers
        ):
            return "clarification_interrupt"
        return "knowledge_grounding"

    @staticmethod
    def _after_routing(
        state: CivitasWorkflowState,
    ) -> Literal["operational_planner", "prepare_human_review", "end"]:
        if state.status == WorkflowStatus.FAILED:
            return "end"
        if state.status == WorkflowStatus.ABSTAINED:
            return "prepare_human_review"
        return "operational_planner"

    @staticmethod
    def _after_plan(state: CivitasWorkflowState) -> Literal["critic", "end"]:
        return "end" if state.status == WorkflowStatus.FAILED else "critic"

    @staticmethod
    def _after_critic(
        state: CivitasWorkflowState,
    ) -> Literal["routing_agent", "operational_planner", "prepare_human_review", "end"]:
        if state.status == WorkflowStatus.FAILED:
            return "end"
        assert state.critic is not None
        if (
            state.critic.verdict == CriticVerdict.REVISE_ROUTING
            and state.revision_count < MAX_REVISIONS
        ):
            return "routing_agent"
        if (
            state.critic.verdict == CriticVerdict.REVISE_PLAN
            and state.revision_count < MAX_REVISIONS
        ):
            return "operational_planner"
        return "prepare_human_review"

    @staticmethod
    def _after_human_review(
        state: CivitasWorkflowState,
    ) -> Literal["citizen_communication", "routing_agent", "clarification_interrupt", "end"]:
        assert state.human_review is not None
        if (
            state.human_review.action == HumanReviewAction.APPROVE
            and state.routing
            and state.operational_plan
        ):
            return "citizen_communication"
        if state.human_review.action == HumanReviewAction.REROUTE:
            return "routing_agent"
        if state.human_review.action == HumanReviewAction.REQUEST_MORE_EVIDENCE:
            return "clarification_interrupt"
        return "end"

    def _update(
        self, state: CivitasWorkflowState, event: WorkflowTraceEvent | None = None, **values: object
    ) -> dict[str, object]:
        events = list(state.trace_events)
        if event:
            events.append(event)
            updated_context = values.get("context")
            if isinstance(updated_context, WorkflowContext):
                incident_id = updated_context.incident_id
            else:
                incident_id = state.context.incident_id if state.context else state.report_id
            self.dependencies.trace_tool.record(incident_id, state.trace_id, event)
        return {**values, "trace_events": events}

    def _failed(
        self, state: CivitasWorkflowState, node: str, started: float, exc: Exception, tool: str
    ) -> dict[str, object]:
        return self._update(
            state,
            status=WorkflowStatus.FAILED,
            errors=[*state.errors, f"{node}: {exc}"],
            event=self._event(node, started, tool, status="failed", error=exc),
        )

    @staticmethod
    def _event(
        node: str,
        started: float,
        tool: str,
        *,
        status: Literal["succeeded", "failed", "interrupted"] = "succeeded",
        references: list[str] | None = None,
        error: Exception | None = None,
    ) -> WorkflowTraceEvent:
        return WorkflowTraceEvent(
            node=node,
            status=status,
            latency_ms=max(0, round((time.perf_counter() - started) * 1000)),
            tool_or_model=tool,
            validation_outcome="valid" if status == "succeeded" else "invalid",
            knowledge_reference_ids=references or [],
            error_code=type(error).__name__ if error else None,
        )


def build_workflow(dependencies: WorkflowDependencies) -> CivitasWorkflow:
    return CivitasWorkflow(dependencies)
