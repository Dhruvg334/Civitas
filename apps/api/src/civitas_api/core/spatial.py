"""Spatial layer adapters for the FastAPI backend.

Wraps Pavit's `civitas_geo` library with the backend's `PostgresExecutor`,
and exposes typed dataclasses/result handlers for HTTP routes.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make Pavit's geospatial package importable as `civitas_geo` from the
# vendored copy under services/spatial/src.  We do NOT install it as a
# package because the team has not vendored it into the api pyproject yet;
# a sys.path shim is the minimum-friction integration for the hackathon.
_SPATIAL_SRC = Path(__file__).resolve().parents[2] / "spatial" / "src"
if str(_SPATIAL_SRC) not in sys.path:
    sys.path.insert(0, str(_SPATIAL_SRC))

from civitas_geo.aggregates import DensityAggregator  # noqa: E402
from civitas_geo.boundary import DEFAULT_BOUNDARY  # noqa: E402
from civitas_geo.candidates import CandidateRetriever  # noqa: E402
from civitas_geo.landmarks import LandmarkIndex  # noqa: E402
from civitas_geo.models import (  # noqa: E402
    CandidateSearchSpec,
    DensityAggregateResult,
    GeoPoint,
    LandmarkDistance,
    NearbyIncidentsResult,
    SpatialSearchSpec,
)
from civitas_geo.retrieval import NearbyRetriever  # noqa: E402

from civitas_api.core.database import PostgresExecutor  # noqa: E402

__all__ = [
    "CandidateRetriever",
    "DensityAggregator",
    "DEFAULT_BOUNDARY",
    "GeoPoint",
    "LandmarkDistance",
    "LandmarkIndex",
    "NearbyRetriever",
    "PostgresExecutor",
    "SpatialSearchSpec",
    "CandidateSearchSpec",
    "DensityAggregateResult",
    "NearbyIncidentsResult",
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