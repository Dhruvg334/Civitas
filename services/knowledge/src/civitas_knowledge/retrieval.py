"""Deterministic-first hybrid retrieval for the small curated policy corpus."""

from __future__ import annotations

import re
from dataclasses import dataclass

from civitas_knowledge.backends import KnowledgeBackend
from civitas_knowledge.contracts import (
    GroundingStatus,
    KnowledgeEvidence,
    KnowledgePurpose,
    KnowledgeQuery,
    KnowledgeRecord,
    KnowledgeReference,
    KnowledgeResult,
    RetrievalMethod,
)

_TOKEN = re.compile(r"[a-z0-9]+")
_PURPOSE_TERMS: dict[KnowledgePurpose, frozenset[str]] = {
    KnowledgePurpose.DEPARTMENT_JURISDICTION: frozenset(
        {"primary", "secondary", "department", "road", "water", "waste", "parks", "light"}
    ),
    KnowledgePurpose.ROUTING_POLICY: frozenset({"route", "routing", "primary", "secondary"}),
    KnowledgePurpose.ESCALATION_RULES: frozenset(
        {"escalate", "escalation", "critical", "electrical", "review", "approval"}
    ),
    KnowledgePurpose.SAFETY_GUIDANCE: frozenset(
        {"safety", "secure", "hazard", "barrier", "cones", "wires", "electrical"}
    ),
    KnowledgePurpose.REQUIRED_WORK_ORDER_FIELDS: frozenset(
        {"required", "work", "order", "fields", "location", "action"}
    ),
    KnowledgePurpose.OPERATIONAL_GUIDANCE: frozenset(
        {"inspect", "repair", "remove", "isolate", "crew", "resources", "action"}
    ),
    KnowledgePurpose.CITIZEN_COMMUNICATION_RESTRICTIONS: frozenset(
        {"citizen", "promise", "promising", "forbidden", "completion", "non", "binding"}
    ),
}


@dataclass(frozen=True)
class _Ranked:
    record: KnowledgeRecord
    exact_count: int
    matched_terms: tuple[str, ...]
    purpose_matches: frozenset[KnowledgePurpose]

    @property
    def score(self) -> float:
        """Transparent relevance points, not probability or confidence."""
        return float(self.exact_count * 10 + len(self.matched_terms))


class KnowledgeService:
    def __init__(self, backend: KnowledgeBackend) -> None:
        self.backend = backend

    def retrieve(self, query: KnowledgeQuery) -> KnowledgeResult:
        candidates = self.backend.list_records(policy_type=query.policy_type)
        ranked = [rank for record in candidates if (rank := _rank(record, query)) is not None]
        ranked.sort(
            key=lambda item: (
                -item.exact_count,
                -len(item.purpose_matches),
                -len(item.matched_terms),
                item.record.reference_id,
                item.record.record_id,
            )
        )
        selected = ranked[: query.limit]
        warnings: list[str] = []
        missing: list[str] = []
        if query.jurisdiction and (
            not selected or any(item.record.jurisdiction is None for item in selected)
        ):
            missing.append(f"jurisdiction evidence for {query.jurisdiction}")
            warnings.append(
                "The current backend policy contract has no jurisdiction field; jurisdiction was not inferred."
            )

        covered_purposes = frozenset(
            purpose for item in selected for purpose in item.purpose_matches
        )
        missing_purposes = [
            purpose.value for purpose in query.purposes if purpose not in covered_purposes
        ]
        missing.extend(f"policy evidence for {purpose}" for purpose in missing_purposes)

        if not selected:
            status = GroundingStatus.INSUFFICIENT_KNOWLEDGE
            sufficient = False
            abstention = "No stored policy or playbook matched the supplied retrieval criteria."
            method = RetrievalMethod.DETERMINISTIC_FALLBACK
        elif missing:
            status = GroundingStatus.PARTIALLY_SUPPORTED
            sufficient = False
            abstention = "Stored evidence does not cover every requested criterion."
            method = _result_method(selected)
        else:
            status = GroundingStatus.SUPPORTED
            sufficient = True
            abstention = None
            method = _result_method(selected)

        return KnowledgeResult(
            query=query,
            records=[item.record for item in selected],
            evidence=[_evidence(item) for item in selected],
            status=status,
            sufficient_evidence=sufficient,
            retrieval_method=method,
            missing_information=missing,
            abstention_reason=abstention,
            warnings=warnings,
        )


def _rank(record: KnowledgeRecord, query: KnowledgeQuery) -> _Ranked | None:
    exact_count = 0
    restrictive_match = False
    if query.category:
        category = query.category.value
        if category in record.categories:
            exact_count += 1
            restrictive_match = True
        elif record.categories:
            return None
    if query.department:
        department = query.department.casefold()
        if department in {item.casefold() for item in record.departments}:
            exact_count += 1
            restrictive_match = True
        elif record.departments:
            return None
    if query.jurisdiction and record.jurisdiction:
        if query.jurisdiction.casefold() != record.jurisdiction.casefold():
            return None
        exact_count += 1
        restrictive_match = True
    if query.policy_type:
        exact_count += 1
        restrictive_match = True

    document_tokens = _record_tokens(record)
    query_tokens = _tokens(query.text or "")
    purpose_matches = frozenset(
        purpose
        for purpose in query.purposes
        if _PURPOSE_TERMS[purpose] & document_tokens or _purpose_structured_match(purpose, record)
    )
    purpose_terms = frozenset(
        term for purpose in query.purposes for term in _PURPOSE_TERMS[purpose]
    )
    matched_terms = tuple(sorted((query_tokens | purpose_terms) & document_tokens))

    has_signal = restrictive_match or bool(query_tokens & document_tokens) or bool(purpose_matches)
    if not has_signal:
        return None
    return _Ranked(record, exact_count, matched_terms, purpose_matches)


def _purpose_structured_match(purpose: KnowledgePurpose, record: KnowledgeRecord) -> bool:
    if purpose == KnowledgePurpose.DEPARTMENT_JURISDICTION:
        return bool(record.departments)
    if purpose == KnowledgePurpose.REQUIRED_WORK_ORDER_FIELDS:
        return (
            bool(record.required_actions) or "required work-order fields" in record.text.casefold()
        )
    if purpose == KnowledgePurpose.OPERATIONAL_GUIDANCE:
        return bool(record.required_actions or record.suggested_resources)
    return False


def _record_tokens(record: KnowledgeRecord) -> frozenset[str]:
    structured = " ".join(
        [
            record.title,
            record.text,
            *record.categories,
            *record.departments,
            *record.required_actions,
            *record.suggested_resources,
        ]
    )
    return _tokens(structured)


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.casefold()))


def _evidence(item: _Ranked) -> KnowledgeEvidence:
    method = RetrievalMethod.EXACT_FILTER if item.exact_count else RetrievalMethod.KEYWORD
    return KnowledgeEvidence(
        reference=KnowledgeReference(
            record_id=item.record.record_id,
            reference_id=item.record.reference_id,
            title=item.record.title,
            source_identifier=item.record.provenance.source_identifier,
        ),
        relevant_policy_text=item.record.text,
        retrieval_method=method,
        retrieval_score=item.score,
        matched_terms=list(item.matched_terms),
    )


def _result_method(items: list[_Ranked]) -> RetrievalMethod:
    return (
        RetrievalMethod.EXACT_FILTER
        if any(item.exact_count for item in items)
        else RetrievalMethod.KEYWORD
    )
