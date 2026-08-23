"""The backend adapter interface.

The ML module depends only on this interface — never directly on raw database
tables or internal endpoints. Two interchangeable implementations exist:

  - `MockBackendAdapter`  deterministic, runs fully offline on fixtures;
  - `RealBackendAdapter`  HTTP client for the backend API service.

Contract verification: `tests/test_phase10_adapters.py` validates both
implementations conform to this interface and produce identical
schema-valid answers (exercised through an injected HTTP transport).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from civitas_ml.contracts import (
    LandmarkSet,
    MediaReference,
    NearbyCandidatesRequest,
    NearbyCandidatesResponse,
)


class BackendAdapter(ABC):
    """Fetch what the ML pipeline needs: candidates, landmarks, media bytes."""

    @abstractmethod
    def fetch_nearby_candidates(self, request: NearbyCandidatesRequest) -> NearbyCandidatesResponse:
        """The spatial/temporal retrieval window (PostGIS lives in the backend)."""

    @abstractmethod
    def fetch_landmarks(self) -> LandmarkSet:
        """Landmark context for geo feature engineering (schools, hospitals, ...)."""

    @abstractmethod
    def fetch_media(self, reference: str) -> bytes:
        """Raw media bytes for one backend media reference (image/video).

        Callers must never assume resolution: bytes may be PNG/JPEG/H264,
        and the media validation step owns parsing and quality gating.
        """

    @abstractmethod
    def resolve_media_metadata(self, reference: str) -> MediaReference:
        """Backend-known metadata (kind, mime) for a media reference id."""