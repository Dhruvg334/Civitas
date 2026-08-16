"""Local application adapters used by the test runtime and production bridge."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

from civitas_knowledge.backends import InMemoryKnowledgeBackend, KnowledgeBackend
from civitas_knowledge.contracts import (
    KnowledgeProvenance,
    KnowledgePurpose,
    KnowledgeQuery,
    KnowledgeRecord,
    KnowledgeResult,
    PolicyType,
)
from civitas_knowledge.retrieval import KnowledgeService
from civitas_workflow.agents import CivitasAgents
from civitas_workflow.graph import WorkflowDependencies, build_workflow
from civitas_workflow.llm import GroqLLMClient, LLMClient
from civitas_workflow.tools import (
    KnowledgeTool,
    MLIntelligenceTool,
    PersistenceTool,
    ReportContextTool,
    TraceTool,
)
from civitas_workflow.workflow_contracts import (
    ClarificationQuestion,
    MLIntelligence,
    OperationalPlan,
    RoutingDecision,
    WorkflowContext,
    WorkflowTraceEvent,
)
from langgraph.checkpoint.base import BaseCheckpointSaver

from civitas_api.operations import clarifications, policies, reports, routing, work_orders
from civitas_api.services.workflow_runtime import WorkflowRuntimeService


class LocalContext(ReportContextTool):
    def load(self, report_id: str) -> WorkflowContext:
        row = reports.get_incident(report_id)
        if row is None:
            raise LookupError(f"report {report_id} was not found")
        answers = {
            str(item["question_id"]): str(item["answer_text"])
            for item in clarifications.list_clarifications(report_id)
            if item.get("answer_text")
        }
        return WorkflowContext(
            report_id=report_id,
            incident_id=report_id,
            description=str(row.get("description") or ""),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            citizen_selected_category=row.get("category"),
            media=reports.list_media_for_incident(report_id),
            clarification_answers=answers,
            existing_work_order_id=row.get("assigned_work_order_id"),
        )


class LocalML(MLIntelligenceTool):
    def analyze(self, context: WorkflowContext, *, trace_id: str) -> MLIntelligence:
        from civitas_api.services.ml_runtime import analyze_persisted_report

        result = analyze_persisted_report(context.report_id, trace_id=trace_id)
        return MLIntelligence(
            available=True,
            primary_category=result.vision.primary_category,
            observable_evidence=result.vision.observable_evidence,
            uncertainty=[*result.vision.uncertainty, *result.basis],
            duplicate_verdict=result.duplicate.verdict,
            cluster_verdict=result.cluster.verdict,
            severity_score=result.severity.score,
            severity_level=result.severity.level,
            priority_score=result.priority.score,
            priority_level=result.priority.level,
            feature_contributions=[factor.factor for factor in result.severity.factors],
            model_versions=[model.model_version for model in result.models],
        )


class DatabaseKnowledgeBackend(KnowledgeBackend):
    """Read the canonical policy/playbook corpus directly from Civitas persistence."""

    def list_records(self, *, policy_type: PolicyType | None = None) -> list[KnowledgeRecord]:
        rows = policies.list_policies(kind=policy_type.value if policy_type else None, limit=200)
        return [
            KnowledgeRecord(
                record_id=str(row["policy_id"]),
                reference_id=str(row["code"]),
                title=str(row["title"]),
                policy_type=PolicyType(str(row["kind"])),
                text=str(row["body"]),
                categories=list(row.get("categories") or []),
                departments=list(row.get("departments") or []),
                jurisdiction=(str(row["jurisdiction"]) if row.get("jurisdiction") else None),
                required_actions=list(row.get("required_actions") or []),
                suggested_resources=list(row.get("suggested_resources") or []),
                severity_factors=list(row.get("severity_factors") or []),
                priority_factors=list(row.get("priority_factors") or []),
                provenance=KnowledgeProvenance(
                    backend="civitas_database",
                    source_identifier=str(row["policy_id"]),
                    source_path=f"policies/{row['code']}",
                    attributes={"reference_id": str(row["code"])},
                ),
            )
            for row in rows
        ]


class LocalKnowledge(KnowledgeTool):
    def __init__(self, service: KnowledgeService) -> None:
        self.service = service

    def retrieve(
        self, context: WorkflowContext, category: str | None, purposes: Sequence[KnowledgePurpose]
    ) -> KnowledgeResult:
        del context
        from civitas_knowledge.contracts import IncidentCategory

        return self.service.retrieve(
            KnowledgeQuery(
                category=IncidentCategory(category) if category else None,
                purposes=list(purposes),
                limit=20,
            )
        )


class LocalPersistence(PersistenceTool):
    def save_clarifications(
        self, incident_id: str, questions: Sequence[ClarificationQuestion]
    ) -> None:
        clarifications.ask_clarifications(
            incident_id,
            [question.model_dump(mode="json") for question in questions],
            asked_by="workflow",
        )

    def save_clarification_answers(self, incident_id: str, answers: dict[str, str]) -> None:
        for question_id, answer in answers.items():
            clarifications.answer_clarification(
                incident_id, question_id, answer, answered_by="workflow"
            )

    def ensure_routing(self, incident_id: str, decision: RoutingDecision) -> None:
        if not routing.list_routings_for_incident(incident_id):
            routing.create_routing_decision(
                incident_id=incident_id,
                primary_department=decision.primary_department,
                secondary_departments=decision.secondary_departments,
                escalation_required=decision.escalation_required,
                policy_references=decision.policy_references,
                decision_basis=decision.rationale,
                review_required=decision.review_required,
                workflow_version="workflow-v1",
                routed_by="workflow",
            )

    def ensure_work_order(
        self, incident_id: str, plan: OperationalPlan, decision: RoutingDecision
    ) -> str:
        row = reports.get_incident(incident_id)
        if row and row.get("assigned_work_order_id"):
            return str(row["assigned_work_order_id"])
        result = work_orders.create_work_order(
            incident_id=incident_id,
            summary=plan.summary,
            required_actions=plan.required_actions,
            suggested_resources=plan.suggested_resources,
            safety_notes=plan.safety_notes,
            primary_department=decision.primary_department,
            secondary_departments=decision.secondary_departments,
            escalation_required=decision.escalation_required,
            policy_references=plan.policy_references,
            estimated_window_min_hours=plan.estimated_window_min_hours,
            estimated_window_max_hours=plan.estimated_window_max_hours,
            created_by="workflow",
        )
        return str(result["work_order_id"])

    def apply_human_review(self, work_order_id: str, action: str) -> None:
        if action == "approve":
            work_orders.approve_work_order(work_order_id, reviewer_id="workflow-reviewer")
        elif action == "reject":
            work_orders.reject_work_order(work_order_id, reviewer_id="workflow-reviewer")


class LocalTrace(TraceTool):
    def record(self, incident_id: str, trace_id: str, event: WorkflowTraceEvent) -> None:
        with reports.get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO agent_traces "
                "(trace_id,incident_id,node,model_version,latency_ms,"
                "validation_outcome,created_at) "
                "VALUES (%(id)s,%(incident)s,%(node)s,%(model)s,%(latency)s,%(outcome)s,"
                "CURRENT_TIMESTAMP)",
                {
                    "id": f"{trace_id}-{event.node}-{uuid4().hex}",
                    "incident": incident_id,
                    "node": event.node,
                    "model": event.tool_or_model,
                    "latency": event.latency_ms,
                    "outcome": event.validation_outcome,
                },
            )
            conn.commit()


def create_test_runtime(
    llm: LLMClient, records: Sequence[KnowledgeRecord]
) -> WorkflowRuntimeService:
    return WorkflowRuntimeService(
        build_workflow(
            WorkflowDependencies(
                context_tool=LocalContext(),
                ml_tool=LocalML(),
                knowledge_tool=LocalKnowledge(KnowledgeService(InMemoryKnowledgeBackend(records))),
                persistence_tool=LocalPersistence(),
                trace_tool=LocalTrace(),
                agents=CivitasAgents(
                    llm, prompt_root=Path(__file__).resolve().parents[5] / "prompts"
                ),
            )
        )
    )


def create_production_runtime(
    checkpointer: BaseCheckpointSaver[Any],
) -> WorkflowRuntimeService:
    """Compose the deployed runtime in-process around one durable LangGraph saver."""
    return WorkflowRuntimeService(
        build_workflow(
            WorkflowDependencies(
                context_tool=LocalContext(),
                ml_tool=LocalML(),
                knowledge_tool=LocalKnowledge(KnowledgeService(DatabaseKnowledgeBackend())),
                persistence_tool=LocalPersistence(),
                trace_tool=LocalTrace(),
                agents=CivitasAgents(
                    GroqLLMClient(), prompt_root=Path(__file__).resolve().parents[5] / "prompts"
                ),
            ),
            checkpointer=checkpointer,
        )
    )
