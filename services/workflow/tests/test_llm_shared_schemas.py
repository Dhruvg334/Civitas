from __future__ import annotations

import json
from pathlib import Path

from civitas_workflow.llm.contracts import LLMCallMetadata

SCHEMAS = Path(__file__).resolve().parents[3] / "schemas" / "json"


def test_llm_metadata_schema_fields_match_python_contract() -> None:
    schema = json.loads((SCHEMAS / "llm-call-metadata.schema.json").read_text(encoding="utf-8"))
    assert set(schema["properties"]) == set(LLMCallMetadata.model_fields)
    assert set(schema["required"]) == {
        name for name, field in LLMCallMetadata.model_fields.items() if field.is_required()
    }
