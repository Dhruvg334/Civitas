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
    ClassicalImageEmbedder,
    HashNgramEmbedder,
    ImageEmbedding,
    ProviderEmbedder,
    ReportEmbeddings,
    build_report_embeddings,
    cosine_similarity,
)
from civitas_duplicates.similarity import (
    DEFAULT_WEIGHTS,
    INCIDENT_ANCHORED_WEIGHTS,
    IncidentGateResult,
    IncidentSimilarityResult,
    ScoringConfig,
    composite_score,
    decide_duplicate,
    duplicate_reasons,
    incident_gate,
    incident_similarity,
    make_pair,
)
from civitas_duplicates.evaluation import (
    EngineEvaluation,
    LabelledPair,
    PairRow,
    build_labelled_pairs,
    evaluate_engine,
)
from civitas_duplicates.signals import RELATED_CATEGORIES

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
    "ClassicalImageEmbedder",
    "HashNgramEmbedder",
    "ImageEmbedding",
    "ProviderEmbedder",
    "ReportEmbeddings",
    "build_report_embeddings",
    "cosine_similarity",
    "DEFAULT_WEIGHTS",
    "INCIDENT_ANCHORED_WEIGHTS",
    "IncidentGateResult",
    "IncidentSimilarityResult",
    "ScoringConfig",
    "composite_score",
    "decide_duplicate",
    "duplicate_reasons",
    "incident_gate",
    "incident_similarity",
    "make_pair",
    "EngineEvaluation",
    "LabelledPair",
    "PairRow",
    "build_labelled_pairs",
    "evaluate_engine",
    "RELATED_CATEGORIES",
]