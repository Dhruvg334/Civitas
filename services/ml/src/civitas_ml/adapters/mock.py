"""Deterministic mock backend adapter (Phase 10).

Simulates the backend contract (nearby-candidate retrieval, landmarks,
media bytes) entirely from local JSON fixtures plus deterministic
seeded image generation — no network, no database, no Utkarsh.

Design rules:
- returns only schema-valid payloads that the pipeline validates anyway;
- contributes no scoring knowledge: the adapter never decides anything,
  it only *fetches* — mock-specific assumptions cannot leak into the
  ML algorithms because the pipeline consumes the same validated
  contract objects regardless of adapter;
- deterministic: same request -> same answer in every run;
- supports positive (R2, R3), negative (N1, N2) and ambiguous (A1)
  candidate cases.

Failure injection for tests only: setting `malformed_paths` makes the
adapter answer with payloads that violate the contract, so the pipeline
fails *structured* (MalformedResponseError) instead of guessing.
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from civitas_ml.adapters.base import BackendAdapter
from civitas_ml.contracts import (
    CandidateReport,
    LandmarkInfo,
    LandmarkSet,
    MediaReference,
    NearbyCandidatesRequest,
    NearbyCandidatesResponse,
)
from civitas_ml.errors import MalformedResponseError

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures"
MEDIA_DIR = FIXTURES_DIR / "media"


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        {key: value for key, value in item.items() if value is not None}
        for item in raw
    ]


def _generate_media_bytes(spec: str) -> bytes:
    """Materialize a fixture media spec into PNG bytes (seeded, stable).

    Spec format: `{category}@{seed}[:{variant}]` e.g. `water_leakage@7101:flow`.
    """
    from civitas_vision.benchmark import make_image

    category_and_seed, _, variant = spec.partition(":")
    category, seed = category_and_seed.split("@")
    buffer = BytesIO()
    make_image(category, int(seed), variant=variant or None).save(buffer, format="PNG")
    return buffer.getvalue()


class MockBackendAdapter(BackendAdapter):
    """Offline adapter: local fixtures + seeded deterministic media."""

    def __init__(
        self,
        *,
        candidates_file: Path | None = None,
        landmarks_file: Path | None = None,
        malformed_paths: set[str] | None = None,
    ) -> None:
        self._candidates_file = candidates_file or (FIXTURES_DIR / "mock_candidates.json")
        self._landmarks_file = landmarks_file or (FIXTURES_DIR / "mock_landmarks.json")
        self._malformed_paths: set[str] = set(malformed_paths or set())

    def fetch_nearby_candidates(self, request: NearbyCandidatesRequest) -> NearbyCandidatesResponse:
        path = self._candidates_file or (FIXTURES_DIR / "mock_candidates.json")
        raw = _load_fixture(path)
        if f"candidates:{request.report_id}" in self._malformed_paths:
            raw = _malformed_candidates(raw)
        try:
            candidates = [CandidateReport.model_validate(item) for item in raw]
        except ValidationError as exc:
            raise MalformedResponseError(
                f"mock fixture payload does not match the contract: {exc}",
                details={"fixture": path.name},
            ) from exc
        basis = [
            f"mock adapter: deterministic fixture {path.name}; "
            "spatial + temporal trim is the backend's job (PostGIS later)",
            f"requested radius {request.radius_m:.0f} m / window {request.time_window_h:.0f} h; "
            "fixture returns its full deterministic set",
        ]
        return NearbyCandidatesResponse(
            request=request,
            candidates=candidates,
            count=len(candidates),
            basis=basis,
        )

    def fetch_landmarks(self) -> LandmarkSet:
        path = self._landmarks_file or (FIXTURES_DIR / "mock_landmarks.json")
        raw = _load_fixture(path)
        if "landmarks" in self._malformed_paths:
            raw = _malformed_landmarks(raw)
        try:
            landmarks = [LandmarkInfo.model_validate(item) for item in raw]
        except ValidationError as exc:
            raise MalformedResponseError(
                f"mock fixture payload does not match the contract: {exc}",
                details={"fixture": path.name},
            ) from exc
        return LandmarkSet(
            landmarks=landmarks,
            basis=["mock adapter: deterministic landmark fixture (mirrors DEMO_LANDMARKS)"],
        )

    def fetch_media(self, reference: str) -> bytes:
        if reference.startswith("fixture:"):
            return _generate_media_bytes(reference.removeprefix("fixture:"))
        if reference.startswith("mock:"):
            path = MEDIA_DIR / reference.removeprefix("mock:")
            if not path.exists():
                raise FileNotFoundError(f"mock media fixture missing: {path}")
            return path.read_bytes()
        raise FileNotFoundError(f"unknown mock media reference {reference!r}")

    def resolve_media_metadata(self, reference: str) -> MediaReference:
        if reference.startswith("fixture:"):
            return MediaReference(
                media_id=reference,
                kind="image",
                mime_type="image/png",
                note="mock fixture media (deterministic generated sample)",
            )
        raise FileNotFoundError(f"unknown mock media reference {reference!r}")


def _malformed_candidates(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a payload that violates the CandidateReport contract."""
    if not raw:
        return [{"report_id": 123, "latitude": "not-a-number"}]  # type: ignore[list-item]
    broken = dict(raw[0])
    broken["latitude"] = "NaN"
    return [broken, *raw[1:]]


def _malformed_landmarks(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a payload that violates the LandmarkInfo contract."""
    if not raw:
        return [{"name": "NaN", "latitude": "not-a-number"}]  # type: ignore[list-item]
    broken = dict(raw[0])
    broken["latitude"] = "NaN"
    return [broken, *raw[1:]]


__all__ = ["MockBackendAdapter"]