"""Civitas ML service (Phase 9): one clean internal ML interface.

The stable, predictable surface LangGraph agents consume instead of
talking to the ML packages directly:

    analyze_report(image, video, description, latitude, longitude,
                   timestamp) -> ReportAnalysis
                     {vision, embeddings, duplicate, severity, priority}

    verify_resolution(before_media, after_media) -> ResolutionVerification
                     {status, confidence, evidence}
"""

from civitas_ml.analyze import analyze_report
from civitas_ml.contracts import (
    DuplicateCandidate,
    DuplicateSection,
    EmbeddingSection,
    FactorPoint,
    PrioritySection,
    ReportAnalysis,
    ResolutionVerification,
    SeveritySection,
    VisionSection,
)
from civitas_ml.verify import verify_resolution

__all__ = [
    "DuplicateCandidate",
    "DuplicateSection",
    "EmbeddingSection",
    "FactorPoint",
    "PrioritySection",
    "ReportAnalysis",
    "ResolutionVerification",
    "SeveritySection",
    "VisionSection",
    "analyze_report",
    "verify_resolution",
]