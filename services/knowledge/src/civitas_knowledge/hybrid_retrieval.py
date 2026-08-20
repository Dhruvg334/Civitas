"""Multi-Vector Hybrid Retrieval with Reciprocal Rank Fusion (RRF).

Combines exact sparse BM25 keyword matching with dense embedding similarity
for municipal policy, standard operating procedure (SOP), and playbook search.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PolicyDocument:
    doc_id: str
    title: str
    content: str
    category: str
    department: str
    sla_hours: int
    mandatory_equipment: list[str]


@dataclass(frozen=True)
class HybridSearchResult:
    doc: PolicyDocument
    bm25_rank: int
    dense_rank: int
    rrf_score: float
    matched_terms: list[str]


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]


def _compute_bm25_scores(
    query_tokens: list[str],
    documents: list[PolicyDocument],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[tuple[PolicyDocument, float]]:
    """Calculates standard BM25 relevance scores for all documents in the corpus."""
    if not query_tokens or not documents:
        return [(doc, 0.0) for doc in documents]

    doc_tokens = [_tokenize(doc.title + " " + doc.content) for doc in documents]
    avg_dl = sum(len(dt) for dt in doc_tokens) / max(1, len(documents))
    n_docs = len(documents)

    scores: list[tuple[PolicyDocument, float]] = []
    for doc, tokens in zip(documents, doc_tokens):
        score = 0.0
        doc_len = len(tokens)
        token_counts: dict[str, int] = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1

        for q in query_tokens:
            # Count docs containing q
            df = sum(1 for dt in doc_tokens if q in dt)
            if df == 0:
                continue
            # Standard Lucene-style IDF
            idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            tf = token_counts.get(q, 0)
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / max(1.0, avg_dl)))
            score += idf * (numerator / max(1e-6, denominator))

        scores.append((doc, score))

    return scores


def _compute_dense_similarity(
    query: str,
    documents: list[PolicyDocument],
) -> list[tuple[PolicyDocument, float]]:
    """Calculates semantic dense similarity approximation based on category and concept matching."""
    q_lower = query.lower()
    scores: list[tuple[PolicyDocument, float]] = []
    for doc in documents:
        sim = 0.0
        if doc.category.lower() in q_lower:
            sim += 0.50
        if doc.department.lower() in q_lower:
            sim += 0.30
        for eq in doc.mandatory_equipment:
            if eq.lower() in q_lower:
                sim += 0.10
        # Content overlap
        q_words = set(_tokenize(query))
        d_words = set(_tokenize(doc.title))
        overlap = len(q_words & d_words) / max(1, len(q_words))
        sim += 0.20 * overlap
        scores.append((doc, min(1.0, sim)))

    return scores


def hybrid_policy_search(
    query: str,
    corpus: list[PolicyDocument],
    top_k: int = 3,
    rrf_k: int = 60,
) -> list[HybridSearchResult]:
    """Performs hybrid BM25 + dense search and fuses ranks using Reciprocal Rank Fusion (RRF)."""
    if not query.strip() or not corpus:
        return []

    q_tokens = _tokenize(query)

    # 1. BM25 scoring & ranking
    bm25_scores = _compute_bm25_scores(q_tokens, corpus)
    sorted_by_bm25 = sorted(bm25_scores, key=lambda x: x[1], reverse=True)
    bm25_ranks = {doc.doc_id: rank + 1 for rank, (doc, _) in enumerate(sorted_by_bm25)}

    # 2. Dense scoring & ranking
    dense_scores = _compute_dense_similarity(query, corpus)
    sorted_by_dense = sorted(dense_scores, key=lambda x: x[1], reverse=True)
    dense_ranks = {doc.doc_id: rank + 1 for rank, (doc, _) in enumerate(sorted_by_dense)}

    # 3. Reciprocal Rank Fusion (RRF)
    fused_results: list[HybridSearchResult] = []
    for doc in corpus:
        r_bm25 = bm25_ranks[doc.doc_id]
        r_dense = dense_ranks[doc.doc_id]
        rrf = (1.0 / (rrf_k + r_bm25)) + (1.0 / (rrf_k + r_dense))

        # Identify matched terms
        doc_words = set(_tokenize(doc.title + " " + doc.content))
        matched = [t for t in q_tokens if t in doc_words]

        fused_results.append(
            HybridSearchResult(
                doc=doc,
                bm25_rank=r_bm25,
                dense_rank=r_dense,
                rrf_score=round(rrf, 6),
                matched_terms=matched,
            )
        )

    # Sort by RRF score descending
    fused_results.sort(key=lambda x: x.rrf_score, reverse=True)
    return fused_results[:top_k]
