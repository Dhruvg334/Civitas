"""Spatial layer adapters for the FastAPI backend.

Wraps the `civitas_geo` library with the backend's `PostgresExecutor`,
and exposes typed dataclasses/result handlers for HTTP routes.
"""

from __future__ import annotations

from civitas_geo.aggregates import DensityAggregator
from civitas_geo.boundary import DEFAULT_BOUNDARY
from civitas_geo.candidates import CandidateRetriever
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import (
    CandidateSearchSpec,
    DensityAggregateResult,
    GeoPoint,
    LandmarkDistance,
    NearbyIncidentsResult,
    SpatialSearchSpec,
)
from civitas_geo.retrieval import NearbyRetriever

from civitas_api.core.database import PostgresExecutor

__all__ = [
    "DEFAULT_BOUNDARY",
    "CandidateRetriever",
    "CandidateSearchSpec",
    "DensityAggregateResult",
    "DensityAggregator",
    "GeoPoint",
    "LandmarkDistance",
    "LandmarkIndex",
    "NearbyIncidentsResult",
    "NearbyRetriever",
    "PostgresExecutor",
    "SpatialSearchSpec",
]


def get_executor() -> PostgresExecutor:
    return PostgresExecutor()


def _is_sqlite_mode() -> bool:
    from civitas_api.core.config import get_settings

    return get_settings().database_url.startswith("sqlite:///")


def get_nearby_retriever() -> NearbyRetriever:
    """Return a NearbyRetriever backed by PostGIS, or memory-mode if sqlite."""
    if _is_sqlite_mode():
        return NearbyRetriever(executor=None)
    return NearbyRetriever(executor=get_executor())


def get_candidate_retriever() -> CandidateRetriever:
    if _is_sqlite_mode():
        return CandidateRetriever(executor=None)
    return CandidateRetriever(executor=get_executor())


def get_density_aggregator() -> DensityAggregator:
    if _is_sqlite_mode():
        # PostGIS-required; surface as unavailable in sqlite mode.
        return DensityAggregator(executor=None)
    return DensityAggregator(executor=get_executor())


def get_landmark_index() -> LandmarkIndex:
    """Offline landmark index; used when no PostGIS landmark table is loaded."""
    return LandmarkIndex()