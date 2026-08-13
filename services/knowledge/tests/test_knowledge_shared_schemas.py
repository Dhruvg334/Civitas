from __future__ import annotations

import json
from pathlib import Path

from civitas_knowledge.contracts import (
    GroundingStatus,
    IncidentCategory,
    KnowledgeQuery,
    KnowledgeResult,
)

SCHEMAS = Path(__file__).resolve().parents[3] / "schemas" / "json"


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_knowledge_query_category_enum_matches_python_contract() -> None:
    schema = _schema("knowledge-query.schema.json")
    values = set(schema["properties"]["category"]["enum"])
    assert values == {category.value for category in IncidentCategory} | {None}
    assert set(KnowledgeQuery.model_fields) == set(schema["properties"])


def test_knowledge_result_status_enum_matches_python_contract() -> None:
    schema = _schema("knowledge-result.schema.json")
    assert set(schema["properties"]["status"]["enum"]) == {
        status.value for status in GroundingStatus
    }
    assert set(schema["properties"]) == set(KnowledgeResult.model_fields)
    assert set(schema["required"]) == {
        name for name, field in KnowledgeResult.model_fields.items() if field.is_required()
    }


def test_knowledge_reference_required_fields_match_python_contract() -> None:
    schema = _schema("knowledge-reference.schema.json")
    assert set(schema["required"]) == {
        "record_id",
        "reference_id",
        "title",
        "source_identifier",
    }
