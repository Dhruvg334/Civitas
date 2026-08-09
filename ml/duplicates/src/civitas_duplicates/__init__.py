"""Civitas duplicate detection engine."""

from civitas_duplicates.cluster import ScoredPair, UnionFind, cluster_reports, evidence_strength
from civitas_duplicates.contracts import (
    DuplicateResult,
    IncidentCluster,
    PairFeatures,
    ReportLike,
)
from civitas_duplicates.detector import DuplicateDetector
from civitas_duplicates.embeddings import (
    HashNgramEmbedder,
    ProviderEmbedder,
    cosine_similarity,
)
from civitas_duplicates.similarity import (
    DEFAULT_WEIGHTS,
    ScoringConfig,
    composite_score,
    decide_duplicate,
)

__all__ = [
    "ScoredPair",
    "UnionFind",
    "cluster_reports",
    "evidence_strength",
    "DuplicateResult",
    "IncidentCluster",
    "PairFeatures",
    "ReportLike",
    "DuplicateDetector",
    "HashNgramEmbedder",
    "ProviderEmbedder",
    "cosine_similarity",
    "DEFAULT_WEIGHTS",
    "ScoringConfig",
    "composite_score",
    "decide_duplicate",
]