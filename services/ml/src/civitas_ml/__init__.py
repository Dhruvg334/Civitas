"""Civitas ML/CV intelligence service (Phases 9-10).

The stable, schema-validated surface Dhruv's agents and Utkarsh's API
consume. Two entry styles:

    analyze_report(...) / verify_resolution(...)   Phase 9 offline calls
    run_report(ReportInput, backend) / run_resolution(ResolutionInput, backend)
                                                   Phase 10 adapter-driven pipeline

Backend switching is configuration (CIVITAS_BACKEND_MODE=mock|real) —
the ML models never depend on how the backend is implemented.
"""

from civitas_ml.adapters import BackendAdapter, MockBackendAdapter, RealBackendAdapter
from civitas_ml.analyze import analyze_report
from civitas_ml.config import MODE_MOCK, MODE_REAL, BackendSettings, get_backend
from civitas_ml.contracts import (
    CandidateReport,
    ClusterSection,
    DuplicateCandidate,
    DuplicateSection,
    EmbeddingSection,
    ErrorPayload,
    FactorPoint,
    GeospatialSection,
    LandmarkInfo,
    LandmarkSet,
    MediaReference,
    ModelReference,
    NearbyCandidatesRequest,
    NearbyCandidatesResponse,
    PrioritySection,
    ReportAnalysis,
    ReportInput,
    ResolutionInput,
    ResolutionVerification,
    SeveritySection,
    VisionSection,
)
from civitas_ml.errors import (
    BackendAdapterError,
    MalformedResponseError,
    MLServiceError,
)
from civitas_ml.media import ResolvedMedia, resolve_media
from civitas_ml.pipeline import run_report, run_resolution
from civitas_ml.verify import verify_resolution

__all__ = [
    "MODE_MOCK",
    "MODE_REAL",
    "BackendAdapter",
    "BackendAdapterError",
    "BackendSettings",
    "CandidateReport",
    "ClusterSection",
    "DuplicateCandidate",
    "DuplicateSection",
    "EmbeddingSection",
    "ErrorPayload",
    "FactorPoint",
    "GeospatialSection",
    "LandmarkInfo",
    "LandmarkSet",
    "MLServiceError",
    "MalformedResponseError",
    "MediaReference",
    "MockBackendAdapter",
    "ModelReference",
    "NearbyCandidatesRequest",
    "NearbyCandidatesResponse",
    "PrioritySection",
    "RealBackendAdapter",
    "ReportAnalysis",
    "ReportInput",
    "ResolutionInput",
    "ResolutionVerification",
    "ResolvedMedia",
    "SeveritySection",
    "VisionSection",
    "analyze_report",
    "get_backend",
    "resolve_media",
    "run_report",
    "run_resolution",
    "verify_resolution",
]