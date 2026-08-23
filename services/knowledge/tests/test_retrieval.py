from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas_knowledge.backends import InMemoryKnowledgeBackend
from civitas_knowledge.contracts import (
    GroundingStatus,
    KnowledgePurpose,
    KnowledgeQuery,
    KnowledgeRecord,
    RetrievalMethod,
)
from civitas_knowledge.grounding import validate_grounding_references
from civitas_knowledge.retrieval import KnowledgeService


def test_exact_category_retrieval(service: KnowledgeService) -> None:
    result = service.retrieve(KnowledgeQuery(category="water_leakage"))
    assert result.status == GroundingStatus.SUPPORTED
    assert result.records[0].reference_id == "PLAY-WATER-01"
    assert result.retrieval_method == RetrievalMethod.EXACT_FILTER


@pytest.mark.parametrize(
    ("category", "reference_id"),
    [
        ("pothole_road_damage", "PLAY-POTHOLE-01"),
        ("water_leakage", "PLAY-WATER-01"),
        ("garbage_overflow", "PLAY-WASTE-01"),
        ("broken_streetlight", "PLAY-LIGHT-01"),
        ("fallen_tree", "PLAY-TREE-01"),
    ],
)
def test_all_core_categories_have_exact_retrieval(
    service: KnowledgeService, category: str, reference_id: str
) -> None:
    result = service.retrieve(KnowledgeQuery(category=category))
    assert result.records[0].reference_id == reference_id


def test_department_retrieval_returns_all_exact_matches(service: KnowledgeService) -> None:
    result = service.retrieve(
        KnowledgeQuery(department="road", purposes=[KnowledgePurpose.DEPARTMENT_JURISDICTION])
    )
    assert {record.reference_id for record in result.records} == {
        "PLAY-POTHOLE-01",
        "PLAY-TREE-01",
    }


def test_escalation_policy_retrieval(service: KnowledgeService) -> None:
    result = service.retrieve(
        KnowledgeQuery(category="water_leakage", purposes=[KnowledgePurpose.ESCALATION_RULES])
    )
    assert result.records[0].reference_id == "PLAY-WATER-01"
    assert "escalate" in result.records[0].text.casefold()


def test_multiple_matching_records(service: KnowledgeService) -> None:
    result = service.retrieve(KnowledgeQuery(purposes=[KnowledgePurpose.SAFETY_GUIDANCE], limit=10))
    assert len(result.records) >= 2


def test_no_matching_policy_returns_abstention(service: KnowledgeService) -> None:
    result = service.retrieve(KnowledgeQuery(department="aviation"))
    assert result.status == GroundingStatus.INSUFFICIENT_KNOWLEDGE
    assert result.sufficient_evidence is False
    assert result.records == []
    assert result.abstention_reason


def test_missing_jurisdiction_is_insufficient(service: KnowledgeService) -> None:
    result = service.retrieve(KnowledgeQuery(jurisdiction="Ward 17"))
    assert result.status == GroundingStatus.INSUFFICIENT_KNOWLEDGE
    assert "jurisdiction evidence for Ward 17" in result.missing_information
    assert "not inferred" in result.warnings[0]


def test_invalid_category_is_rejected() -> None:
    with pytest.raises(ValidationError):
        KnowledgeQuery(category="sinkhole")


def test_provenance_and_reference_are_retained(service: KnowledgeService) -> None:
    result = service.retrieve(KnowledgeQuery(category="pothole_road_damage"))
    record = result.records[0]
    evidence = result.evidence[0]
    assert record.record_id == "ply-pothole-01"
    assert record.provenance.source_path == "/api/v1/policies/PLAY-POTHOLE-01"
    assert evidence.reference.reference_id == "PLAY-POTHOLE-01"
    assert evidence.relevant_policy_text == record.text


def test_ranking_is_deterministic(service: KnowledgeService) -> None:
    query = KnowledgeQuery(purposes=[KnowledgePurpose.OPERATIONAL_GUIDANCE])
    first = [record.reference_id for record in service.retrieve(query).records]
    second = [record.reference_id for record in service.retrieve(query).records]
    assert first == second


def test_in_memory_backend_returns_copies(knowledge_records: list[KnowledgeRecord]) -> None:
    backend = InMemoryKnowledgeBackend(knowledge_records)
    first = backend.list_records()
    first[0].title = "mutated"
    assert backend.list_records()[0].title != "mutated"


def test_grounding_reference_validation(service: KnowledgeService) -> None:
    result = service.retrieve(KnowledgeQuery(category="water_leakage"))
    validation = validate_grounding_references(
        ["PLAY-WATER-01", "ply-water-01", "INVENTED-01"], result
    )
    assert validation.valid is False
    assert validation.valid_reference_ids == ["PLAY-WATER-01", "ply-water-01"]
    assert validation.invalid_reference_ids == ["INVENTED-01"]


def test_partial_support_names_missing_purpose(service: KnowledgeService) -> None:
    result = service.retrieve(
        KnowledgeQuery(
            category="water_leakage",
            purposes=[
                KnowledgePurpose.ROUTING_POLICY,
                KnowledgePurpose.CITIZEN_COMMUNICATION_RESTRICTIONS,
            ],
            limit=1,
        )
    )
    assert result.status == GroundingStatus.PARTIALLY_SUPPORTED
    assert any("citizen_communication_restrictions" in item for item in result.missing_information)


@pytest.mark.parametrize(
    ("purpose", "expected_reference"),
    [
        (KnowledgePurpose.DEPARTMENT_JURISDICTION, "PLAY-WATER-01"),
        (KnowledgePurpose.ROUTING_POLICY, "PLAY-WATER-01"),
        (KnowledgePurpose.ESCALATION_RULES, "PLAY-WATER-01"),
        (KnowledgePurpose.SAFETY_GUIDANCE, "PLAY-WATER-01"),
        (KnowledgePurpose.REQUIRED_WORK_ORDER_FIELDS, "PLAY-POTHOLE-01"),
        (KnowledgePurpose.OPERATIONAL_GUIDANCE, "PLAY-WATER-01"),
        (KnowledgePurpose.CITIZEN_COMMUNICATION_RESTRICTIONS, "POL-GEN-04"),
    ],
)
def test_supported_knowledge_use_cases(
    service: KnowledgeService,
    purpose: KnowledgePurpose,
    expected_reference: str,
) -> None:
    result = service.retrieve(KnowledgeQuery(purposes=[purpose], limit=10))
    assert expected_reference in {record.reference_id for record in result.records}
