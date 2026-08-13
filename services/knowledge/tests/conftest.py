from __future__ import annotations

import pytest

from civitas_knowledge.backends import InMemoryKnowledgeBackend
from civitas_knowledge.contracts import KnowledgeProvenance, KnowledgeRecord, PolicyType
from civitas_knowledge.retrieval import KnowledgeService


def _record(
    record_id: str,
    code: str,
    title: str,
    text: str,
    *,
    kind: PolicyType = PolicyType.PLAYBOOK,
    categories: list[str] | None = None,
    departments: list[str] | None = None,
    actions: list[str] | None = None,
    resources: list[str] | None = None,
) -> KnowledgeRecord:
    return KnowledgeRecord(
        record_id=record_id,
        reference_id=code,
        title=title,
        policy_type=kind,
        text=text,
        categories=categories or [],
        departments=departments or [],
        required_actions=actions or [],
        suggested_resources=resources or [],
        provenance=KnowledgeProvenance(
            backend="fixture",
            source_identifier=record_id,
            source_path=f"/api/v1/policies/{code}",
        ),
    )


@pytest.fixture
def knowledge_records() -> list[KnowledgeRecord]:
    return [
        _record(
            "ply-water-01",
            "PLAY-WATER-01",
            "Water leakage playbook",
            "Primary WATER. Secondary DRAIN and TRAFFIC. Escalate ELECTRIC for electrical contact.",
            categories=["water_leakage", "road_flooding"],
            departments=["water", "drain", "traffic", "electric"],
            actions=["secure affected road section", "isolate leak source"],
            resources=["water maintenance crew", "road barriers"],
        ),
        _record(
            "ply-pothole-01",
            "PLAY-POTHOLE-01",
            "Pothole playbook",
            "Primary ROAD; secondary TRAFFIC. Required work-order fields include location and lane.",
            categories=["pothole", "pothole_road_damage"],
            departments=["road"],
            actions=["inspect damage", "set temporary safety markers", "schedule repair"],
            resources=["road maintenance crew", "safety cones"],
        ),
        _record(
            "ply-tree-01",
            "PLAY-TREE-01",
            "Fallen tree playbook",
            "Primary PARKS; secondary ROAD or TRAFFIC. Escalate ELECTRIC when wires are involved.",
            categories=["fallen_tree"],
            departments=["parks", "road", "traffic", "electric"],
            actions=["secure area", "remove or stabilize tree"],
            resources=["parks crew", "traffic cones"],
        ),
        _record(
            "ply-waste-01",
            "PLAY-WASTE-01",
            "Garbage overflow playbook",
            "Primary WASTE; secondary TRAFFIC if the road is obstructed.",
            categories=["garbage_overflow"],
            departments=["waste", "traffic"],
            actions=["remove accumulated waste", "clean affected public surface"],
            resources=["waste collection crew", "hazard tape"],
        ),
        _record(
            "ply-light-01",
            "PLAY-LIGHT-01",
            "Broken streetlight playbook",
            "Primary LIGHT; secondary ELECTRIC when exposed wiring is visible.",
            categories=["broken_streetlight"],
            departments=["light", "electric"],
            actions=["inspect power and fixture", "secure exposed electrical area"],
            resources=["electrical maintenance crew"],
        ),
        _record(
            "pol-gen-02",
            "POL-GEN-02",
            "Electrical exposure escalates routing",
            "When water contacts electrical infrastructure, routing must include electrical review or escalation.",
            kind=PolicyType.POLICY,
            departments=["electric"],
        ),
        _record(
            "pol-gen-04",
            "POL-GEN-04",
            "No exact completion promise",
            "Work orders must use non-binding resolution windows. Promising a specific completion time to citizens is forbidden.",
            kind=PolicyType.POLICY,
        ),
    ]


@pytest.fixture
def service(knowledge_records: list[KnowledgeRecord]) -> KnowledgeService:
    return KnowledgeService(InMemoryKnowledgeBackend(knowledge_records))
