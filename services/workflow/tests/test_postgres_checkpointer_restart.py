"""PostgreSQL checkpoint cross-process persistence and restart/resume test."""

import os
from pathlib import Path
from typing import Any
import pytest
from langgraph.types import Command

from civitas_knowledge.backends import InMemoryKnowledgeBackend
from civitas_knowledge.contracts import KnowledgeProvenance, KnowledgeRecord, PolicyType
from civitas_knowledge.retrieval import KnowledgeService
from civitas_workflow.agents import CivitasAgents
from civitas_workflow.graph import CivitasWorkflow, WorkflowDependencies, build_workflow
from civitas_workflow.llm import FakeLLMClient
from civitas_workflow.runtime import create_postgres_checkpointer
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
    HumanReviewAction,
    HumanReviewDecision,
    MLIntelligence,
    OperationalPlan,
    RoutingDecision,
    StructuredEvidence,
    WorkflowContext,
    WorkflowStatus,
)

PROMPT_ROOT = Path(__file__).resolve().parents[3] / "prompts"


def _build_test_graph(saver: Any) -> CivitasWorkflow:
    records = [
        KnowledgeRecord(
            record_id="ply-water-01",
            reference_id="PLAY-WATER-01",
            title="Water playbook",
            policy_type=PolicyType.PLAYBOOK,
            text="Primary WATER. Secondary DRAIN. Secure the road.",
            categories=["water_leakage"],
            departments=["water", "drain"],
            required_actions=["secure affected road", "isolate leak"],
            suggested_resources=["water crew"],
            provenance=KnowledgeProvenance(backend="test", source_identifier="ply-water-01"),
        ),
    ]
    knowledge = KnowledgeService(InMemoryKnowledgeBackend(records))
    outputs = {
        "StructuredEvidence": StructuredEvidence(
            likely_category="water_leakage",
            observed_facts=["standing water"],
            citizen_reported_claims=["active leak"],
            hazards=["slip"],
            landmarks=["school"],
        ),
        "ClarificationPlan": ClarificationPlan(
            clarification_required=False, can_continue_without_answers=True
        ),
        "RoutingDecision": RoutingDecision(
            primary_department="water",
            secondary_departments=["drain"],
            escalation_required=False,
            rationale=["Water playbook assigns water."],
            policy_references=["PLAY-WATER-01"],
            review_required=True,
        ),
        "OperationalPlan": OperationalPlan(
            summary="Inspect water leak.",
            required_actions=["secure affected road", "isolate leak"],
            suggested_resources=["water crew"],
            safety_notes=["Secure road."],
            dependencies=["field inspection"],
            policy_references=["PLAY-WATER-01"],
            review_required=True,
        ),
        "CriticResult": CriticResult(
            verdict=CriticVerdict.PASS, verification_references=["PLAY-WATER-01"]
        ),
        "CitizenCommunication": CitizenCommunication(
            message="Your report has been sent to the water team.",
            safety_advice_reference_ids=["PLAY-WATER-01"],
        ),
    }
    context = WorkflowContext(
        report_id="rpt-pg-1",
        incident_id="inc-pg-1",
        description="Water is pooling on the road.",
        latitude=20.3,
        longitude=85.8,
        citizen_selected_category="water_leakage",
    )
    ml_intel = MLIntelligence(
        available=True,
        primary_category="water_leakage",
        observable_evidence=["water pooling"],
        severity_score=70,
        severity_level="high",
        priority_score=75,
        priority_level="P2",
    )

    return build_workflow(
        WorkflowDependencies(
            context_tool=InMemoryReportContextTool([context]),
            ml_tool=InMemoryMLIntelligenceTool(ml_intel),
            knowledge_tool=ServiceKnowledgeTool(knowledge),
            persistence_tool=InMemoryPersistenceTool(),
            trace_tool=InMemoryTraceTool(),
            agents=CivitasAgents(FakeLLMClient(outputs), prompt_root=PROMPT_ROOT),
        ),
        checkpointer=saver,
    )


def test_postgres_checkpointer_process_restart_resumption() -> None:
    pg_url = os.getenv("TEST_POSTGRES_DATABASE_URL")
    if not pg_url:
        pytest.skip("TEST_POSTGRES_DATABASE_URL not configured")

    thread_id = "test-thread-cross-process-1234"
    config = {"configurable": {"thread_id": thread_id}}

    # Process 1: Create saver, setup tables, run graph to human review interrupt
    saver_1 = create_postgres_checkpointer(pg_url)
    saver_1.setup()

    graph_1 = _build_test_graph(saver_1)
    graph_1.graph.invoke(
        {"report_id": "rpt-pg-1", "trace_id": "trc-pg-1"},
        config,
    )
    state_before_restart = graph_1.graph.get_state(config)
    assert state_before_restart.next == ("human_review_interrupt",)

    # Simulate Process 1 Exit: close saver_1 connection
    if hasattr(saver_1, "conn") and saver_1.conn:
        saver_1.conn.close()

    # Process 2: Fresh process initializes new checkpointer from same DB
    saver_2 = create_postgres_checkpointer(pg_url)
    graph_2 = _build_test_graph(saver_2)

    # Verify state restores from PostgreSQL across process lifetime
    saved_state = graph_2.graph.get_state(config)
    assert saved_state.next == ("human_review_interrupt",)
    assert saved_state.values.get("report_id") == "rpt-pg-1"

    # Resume graph on Process 2 with human review decision
    decision = HumanReviewDecision(
        action=HumanReviewAction.APPROVE,
        notes="Supervisor approval after process restart",
    )
    graph_2.graph.invoke(
        Command(resume=decision.model_dump(mode="json", exclude_none=True)),
        config,
    )

    final_snapshot = graph_2.graph.get_state(config)
    assert final_snapshot.values.get("status") == WorkflowStatus.APPROVED
    assert "water team" in final_snapshot.values["citizen_communication"].message
    assert final_snapshot.next == ()

    if hasattr(saver_2, "conn") and saver_2.conn:
        saver_2.conn.close()
