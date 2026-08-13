from __future__ import annotations

import jwt
from fastapi.testclient import TestClient


def test_golden_water_workflow_reaches_review_and_completes(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    from civitas_knowledge.contracts import KnowledgeProvenance, KnowledgeRecord, PolicyType
    from civitas_workflow.llm import FakeLLMClient
    from civitas_workflow.workflow_contracts import (
        CitizenCommunication,
        ClarificationPlan,
        CriticResult,
        CriticVerdict,
        OperationalPlan,
        RoutingDecision,
        StructuredEvidence,
    )

    from civitas_api.main import app
    from civitas_api.operations import workflow_runs
    from civitas_api.services.workflow_composition import create_test_runtime

    report = client.post(
        "/api/v1/reports",
        json={
            "description": "Water is flowing across the road near a school.",
            "location": {"latitude": 20.3, "longitude": 85.8},
            "citizen_selected_category": "water leak",
        },
        headers=auth_header,
    ).json()["data"]
    outputs = {
        "StructuredEvidence": StructuredEvidence(
            likely_category="water_leakage",
            observed_facts=["water across road"],
            citizen_reported_claims=["leak"],
            hazards=["slip risk"],
            landmarks=["school"],
        ),
        "ClarificationPlan": ClarificationPlan(
            clarification_required=False, can_continue_without_answers=True
        ),
        "RoutingDecision": RoutingDecision(
            primary_department="water",
            secondary_departments=["traffic"],
            escalation_required=False,
            policy_references=["PLAY-WATER-01"],
        ),
        "OperationalPlan": OperationalPlan(
            summary="Inspect and isolate water leak.",
            required_actions=["isolate leak"],
            suggested_resources=["water crew"],
            safety_notes=["secure road"],
            policy_references=["PLAY-WATER-01"],
        ),
        "CriticResult": CriticResult(
            verdict=CriticVerdict.PASS, verification_references=["PLAY-WATER-01"]
        ),
        "CitizenCommunication": CitizenCommunication(
            message="Your report has been sent to the water team."
        ),
    }
    record = KnowledgeRecord(
        record_id="water-playbook",
        reference_id="PLAY-WATER-01",
        title="Water playbook",
        policy_type=PolicyType.PLAYBOOK,
        text="Water routes to water department.",
        categories=["water_leakage"],
        departments=["water", "traffic"],
        required_actions=["isolate leak"],
        suggested_resources=["water crew"],
        provenance=KnowledgeProvenance(backend="test", source_identifier="water-playbook"),
    )
    app.state.workflow_runtime = create_test_runtime(FakeLLMClient(outputs), [record])
    started = client.post(f"/api/v1/reports/{report['report_id']}/workflow", headers=auth_header)
    assert started.status_code == 200, started.text
    workflow = started.json()["data"]
    assert workflow["status"] == "WAITING_FOR_REVIEW"
    row = workflow_runs.get(workflow["workflow_id"])
    assert row and row["thread_id"] == workflow["workflow_id"]
    reviewer = {
        "Authorization": f"Bearer {jwt.encode({'sub': 'reviewer', 'role': 'reviewer'}, 'test-secret-not-used-in-dev-mode', algorithm='HS256')}"
    }
    approved = client.post(
        f"/api/v1/workflows/{workflow['workflow_id']}/review",
        json={"action": "approve"},
        headers=reviewer,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["status"] == "COMPLETED"
    assert workflow_runs.get(workflow["workflow_id"])["thread_id"] == row["thread_id"]
    with (
        __import__(
            "civitas_api.operations.reports", fromlist=["get_connection"]
        ).get_connection() as conn,
        conn.cursor() as cur,
    ):
        cur.execute("SELECT COUNT(*) AS c FROM routing_decisions")
        assert cur.fetchone()["c"] == 1
        cur.execute("SELECT COUNT(*) AS c FROM work_orders")
        assert cur.fetchone()["c"] == 1
        cur.execute("SELECT COUNT(*) AS c FROM agent_traces")
        assert cur.fetchone()["c"] > 0
    repeat = client.post(f"/api/v1/reports/{report['report_id']}/workflow", headers=auth_header)
    assert repeat.json()["data"]["workflow_id"] == workflow["workflow_id"]
