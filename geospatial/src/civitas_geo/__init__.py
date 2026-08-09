"""Civitas geospatial intelligence package."""

from civitas_geo import (
    boundary,
    candidates,
    distance,
    feature_engineering,
    landmarks,
    queries,
    reasoning,
    retrieval,
    validation,
)
from civitas_geo.boundary import DEFAULT_BOUNDARY
from civitas_geo.candidates import (
    CandidateRetriever,
    enrich_landmark_context,
    retrieve_candidates_memory,
    retrieve_candidates_postgis,
)
from civitas_geo.feature_engineering import (
    CivicIncidentContext,
    GeospatialFeatureEngine,
    GeospatialFeatureVector,
)
from civitas_geo.models import (
    CandidateListResult,
    CandidateRecord,
    CandidateSearchSpec,
    ExposureContext,
    GeoPoint,
    Landmark,
    LandmarkDistance,
    LocationValidationResult,
    NearbyIncident,
    NearbyIncidentsResult,
    OperationalBoundary,
    PipelineGateDecision,
    SpatialSearchSpec,
)
from civitas_geo.validation import gate_for_pipeline

__all__ = [
    "boundary",
    "candidates",
    "distance",
    "feature_engineering",
    "landmarks",
    "queries",
    "reasoning",
    "retrieval",
    "validation",
    "DEFAULT_BOUNDARY",
    "CandidateRetriever",
    "enrich_landmark_context",
    "retrieve_candidates_memory",
    "retrieve_candidates_postgis",
    "CivicIncidentContext",
    "GeospatialFeatureEngine",
    "GeospatialFeatureVector",
    "CandidateListResult",
    "CandidateRecord",
    "CandidateSearchSpec",
    "ExposureContext",
    "GeoPoint",
    "Landmark",
    "LandmarkDistance",
    "LocationValidationResult",
    "NearbyIncident",
    "NearbyIncidentsResult",
    "OperationalBoundary",
    "PipelineGateDecision",
    "SpatialSearchSpec",
    "gate_for_pipeline",
]