from __future__ import annotations

from pathlib import Path

from civitas_knowledge.backends import InMemoryKnowledgeBackend
from civitas_knowledge.contracts import KnowledgeProvenance, KnowledgeRecord, PolicyType
from civitas_knowledge.retrieval import KnowledgeService
from langgraph.types import Command

from civitas_workflow.agents import CivitasAgents
from civitas_workflow.graph import WorkflowDependencies, build_workflow
from civitas_workflow.llm import FakeLLMClient
from civitas_workflow.tools import (
    InMemoryMLIntelligenceTool,
    InMemoryPersistenceTool,
    InMemoryReportContextTool,
    InMemoryTraceTool,
    ServiceKnowledgeTool,
)
from civitas_workflow.workflow_contracts import (
    CitizenCommunication,
    ClarificationPlan,
    CriticResult,
    CriticVerdict,
    MLIntelligence,
    OperationalPlan,
    RoutingDecision,
    StructuredEvidence,
    WorkflowContext,
    WorkflowStatus,
)

PROMPT_ROOT = Path(__file__).resolve().parents[3] / "prompts"


def _knowledge() -> KnowledgeService:
    records = [
        KnowledgeRecord(
            record_id="ply-water-01",
            reference_id="PLAY-WATER-01",
            title="Water playbook",
            policy_type=PolicyType.PLAYBOOK,
            text="Primary WATER. Secondary DRAIN and TRAFFIC. Escalate ELECTRIC for electrical contact. Secure the affected road. Water maintenance crew.",
            categories=["water_leakage"],
            departments=["water", "drain", "traffic", "electric"],
            required_actions=["secure affected road", "isolate leak"],
            suggested_resources=["water maintenance crew", "road barriers"],
            provenance=KnowledgeProvenance(backend="test", source_identifier="ply-water-01"),
        ),
        KnowledgeRecord(
            record_id="pol-gen-04",
            reference_id="POL-GEN-04",
            title="No exact completion promise",
            policy_type=PolicyType.POLICY,
            text="Promising a specific completion time to citizens is forbidden.",
            provenance=KnowledgeProvenance(backend="test", source_identifier="pol-gen-04"),
        ),
    ]
    return KnowledgeService(InMemoryKnowledgeBackend(records))


def _workflow(
    *, clarification: ClarificationPlan | None = None, routing: RoutingDecision | None = None
):
    outputs = {
        "StructuredEvidence": StructuredEvidence(
            likely_category="water_leakage",
            observed_facts=["standing water is visible"],
            citizen_reported_claims=["resident reports an active leak"],
            hazards=["slip risk"],
            landmarks=["school"],
        ),
        "ClarificationPlan": clarification
        or ClarificationPlan(clarification_required=False, can_continue_without_answers=True),
        "RoutingDecision": routing
        or RoutingDecision(
            primary_department="water",
            secondary_departments=["traffic"],
            escalation_required=False,
            rationale=["Water playbook assigns WATER."],
            policy_references=["PLAY-WATER-01"],
            review_required=True,
        ),
        "OperationalPlan": OperationalPlan(
            summary="Inspect and isolate the reported water leak.",
            required_actions=["secure affected road", "isolate leak"],
            suggested_resources=["water maintenance crew", "road barriers"],
            safety_notes=["Secure the affected road."],
            dependencies=["field inspection"],
            policy_references=["PLAY-WATER-01"],
            review_required=True,
        ),
        "CriticResult": CriticResult(
            verdict=CriticVerdict.PASS, verification_references=["PLAY-WATER-01"]
        ),
        "CitizenCommunication": CitizenCommunication(
            message="Your report has been reviewed and sent to the water team for follow-up.",
            safety_advice_reference_ids=["PLAY-WATER-01"],
        ),
    }
    context = WorkflowContext(
        report_id="rpt-water-1",
        incident_id="inc-water-1",
        description="Water is flowing across the road near a school.",
        latitude=20.3,
        longitude=85.8,
        citizen_selected_category="water_leakage",
    )
    persistence = InMemoryPersistenceTool()
    traces = InMemoryTraceTool()
    dependencies = WorkflowDependencies(
        context_tool=InMemoryReportContextTool([context]),
        ml_tool=InMemoryMLIntelligenceTool(
            MLIntelligence(
                available=True,
                primary_category="water_leakage",
                observable_evidence=["standing water"],
                duplicate_verdict="duplicate",
                cluster_verdict="merged",
                severity_score=60,
                severity_level="high",
                priority_score=80,
                priority_level="high",
                feature_contributions=["school proximity"],
                model_versions=["risk-v1"],
            )
        ),
        knowledge_tool=ServiceKnowledgeTool(_knowledge()),
        persistence_tool=persistence,
        trace_tool=traces,
        agents=CivitasAgents(FakeLLMClient(outputs), prompt_root=PROMPT_ROOT),
    )
    return build_workflow(dependencies), persistence, traces


def _state(workflow, config: dict):
    return workflow.graph.get_state(config).values


def test_happy_path_reaches_real_human_review_interrupt() -> None:
    workflow, persistence, traces = _workflow()
    config = {"configurable": {"thread_id": "happy-water"}}
    workflow.graph.invoke({"trace_id": "wf-water-1", "report_id": "rpt-water-1"}, config)
    state = _state(workflow, config)
    assert state["status"] == WorkflowStatus.WAITING_FOR_HUMAN_REVIEW
    assert state["work_order_id"] == "wo-inc-water-1"
    assert len(persistence.work_orders) == 1
    assert {event[2].node for event in traces.events} >= {
        "load_context",
        "knowledge_grounding",
        "critic",
    }


def test_human_approval_resumes_to_citizen_communication() -> None:
    workflow, persistence, _ = _workflow()
    config = {"configurable": {"thread_id": "approve-water"}}
    workflow.graph.invoke({"trace_id": "wf-water-2", "report_id": "rpt-water-1"}, config)
    workflow.graph.invoke(Command(resume={"action": "approve"}), config)
    state = _state(workflow, config)
    assert state["status"] == WorkflowStatus.APPROVED
    assert "water team" in state["citizen_communication"].message
    assert persistence.review_actions["wo-inc-water-1"] == "approve"


def test_missing_safety_information_interrupts_for_clarification_then_resumes() -> None:
    clarification = ClarificationPlan(
        clarification_required=True,
        questions=[
            {
                "question_id": "electrical_contact",
                "text": "Is water touching any wires, poles, or electrical boxes?",
                "reason": "Electrical contact changes escalation and safety routing.",
                "decision_impact": ["routing", "safety"],
            }
        ],
        can_continue_without_answers=False,
    )
    workflow, persistence, _ = _workflow(clarification=clarification)
    config = {"configurable": {"thread_id": "clarify-water"}}
    workflow.graph.invoke({"trace_id": "wf-water-3", "report_id": "rpt-water-1"}, config)
    assert persistence.clarifications["inc-water-1"]["electrical_contact"] == ""
    workflow.graph.invoke(Command(resume={"electrical_contact": "No."}), config)
    state = _state(workflow, config)
    assert state["status"] == WorkflowStatus.WAITING_FOR_HUMAN_REVIEW
    assert persistence.clarifications["inc-water-1"]["electrical_contact"] == "No."


def test_fabricated_routing_reference_is_rejected() -> None:
    workflow, _, _ = _workflow(
        routing=RoutingDecision(
            primary_department="water",
            escalation_required=False,
            policy_references=["INVENTED-99"],
            review_required=True,
        )
    )
    config = {"configurable": {"thread_id": "bad-reference"}}
    workflow.graph.invoke({"trace_id": "wf-water-4", "report_id": "rpt-water-1"}, config)
    state = _state(workflow, config)
    assert state["status"] == WorkflowStatus.FAILED
    assert "unavailable knowledge IDs" in state["errors"][-1]


def test_repeated_invocation_does_not_create_duplicate_work_order() -> None:
    workflow, persistence, _ = _workflow()
    config = {"configurable": {"thread_id": "idempotent-water"}}
    workflow.graph.invoke({"trace_id": "wf-water-5", "report_id": "rpt-water-1"}, config)
    workflow.graph.invoke(None, config)
    assert len(persistence.work_orders) == 1
