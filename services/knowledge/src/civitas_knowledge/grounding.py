"""Validate that generated policy citations refer to retrieved knowledge."""

from __future__ import annotations

from collections.abc import Iterable

from civitas_knowledge.contracts import GroundingReferenceValidation, KnowledgeResult


def validate_grounding_references(
    claimed_reference_ids: Iterable[str], result: KnowledgeResult
) -> GroundingReferenceValidation:
    available = {record.reference_id for record in result.records} | {
        record.record_id for record in result.records
    }
    claimed = list(dict.fromkeys(claimed_reference_ids))
    valid = [reference for reference in claimed if reference in available]
    invalid = [reference for reference in claimed if reference not in available]
    return GroundingReferenceValidation(
        valid=not invalid,
        valid_reference_ids=valid,
        invalid_reference_ids=invalid,
    )
