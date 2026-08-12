"""Real backend adapter (Phase 10): thin HTTP client for Utkarsh's API.

This adapter is the ONLY code that changes when the real backend ships.
It implements exactly the `BackendAdapter` interface, talking HTTP to
endpoints derived from `CIVITAS_BACKEND_BASE_URL`; authentication, timeouts
and endpoint paths are configuration, never hard-coded credentials or URLs.

The endpoint contract (what Utkarsh must implement) is documented in
`services/ml/docs/CONTRACT.md`; this client is the reference consumer.

`httpx` is an optional extra (`pip install -e "services/ml[http]"`): a
clear structured error is raised if it is missing, and no local execution
path requires a live backend.
"""

from __future__ import annotations

from typing import Any

from civitas_ml.adapters.base import BackendAdapter
from civitas_ml.contracts import (
    LandmarkSet,
    MediaReference,
    NearbyCandidatesRequest,
    NearbyCandidatesResponse,
)
from civitas_ml.errors import (
    CODE_DEPENDENCY_MISSING,
    BackendAdapterError,
    MalformedResponseError,
    MLServiceError,
)

_ENDPOINT_NEARBY = "/api/v1/ml/nearby-candidates"
_ENDPOINT_LANDMARKS = "/api/v1/ml/landmarks"
_ENDPOINT_MEDIA = "/api/v1/ml/media/{reference}"
_ENDPOINT_MEDIA_METADATA = "/api/v1/ml/media/{reference}/metadata"


class RealBackendAdapter(BackendAdapter):
    """HTTP client for the Civitas backend ML endpoints (schema-validated)."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str | None = None,
        timeout_seconds: float = 10.0,
        extra_headers: dict[str, str] | None = None,
        _transport: Any = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds
        self._headers: dict[str, str] = dict(extra_headers or {})
        if token:
            self._headers["Authorization"] = f"Bearer {token}"
        self._transport = _transport  # injectable for contract tests only

    @property
    def _client(self) -> Any:
        try:
            import httpx  # type: ignore[import-not-found]
        except ImportError:
            raise MLServiceError(
                "RealBackendAdapter needs httpx: pip install -e \"services/ml[http]\"",
                code=CODE_DEPENDENCY_MISSING,
            ) from None
        return httpx.Client(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self.timeout_seconds,
            transport=self._transport,
        )

    def _get_json(self, path: str) -> dict[str, Any]:
        try:
            with self._client as client:
                response = client.get(path)
        except Exception as exc:  # noqa: BLE001 - network/timeout -> structured error
            raise BackendAdapterError(
                f"backend unreachable at {self.base_url}{path}: {exc}",
                details={"path": path},
            ) from exc
        if response.status_code != 200:
            raise BackendAdapterError(
                f"backend returned HTTP {response.status_code} for {path}",
                details={"path": path, "status_code": response.status_code},
            )
        try:
            payload = response.json()
        except Exception as exc:  # noqa: BLE001 - non-JSON body
            raise MalformedResponseError(
                f"backend returned non-JSON body for {path}", details={"path": path}
            ) from exc
        if not isinstance(payload, dict):
            raise MalformedResponseError(
                f"backend returned a non-object payload for {path}", details={"path": path}
            )
        if "success" in payload:
            if payload.get("success") is not True:
                raise BackendAdapterError(
                    f"backend returned an error envelope for {path}",
                    details={"path": path, "error": payload.get("error")},
                )
            data = payload.get("data")
            if not isinstance(data, dict):
                raise MalformedResponseError(
                    f"backend success envelope has non-object data for {path}", details={"path": path}
                )
            return data
        return payload

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            with self._client as client:
                response = client.post(path, json=body)
        except Exception as exc:  # noqa: BLE001
            raise BackendAdapterError(
                f"backend unreachable at {self.base_url}{path}: {exc}", details={"path": path}
            ) from exc
        if response.status_code != 200:
            raise BackendAdapterError(
                f"backend returned HTTP {response.status_code} for {path}",
                details={"path": path, "status_code": response.status_code},
            )
        try:
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            raise MalformedResponseError(f"backend returned non-JSON body for {path}", details={"path": path}) from exc
        if not isinstance(payload, dict):
            raise MalformedResponseError(f"backend returned a non-object payload for {path}", details={"path": path})
        if "success" in payload:
            if payload.get("success") is not True:
                raise BackendAdapterError(f"backend returned an error envelope for {path}", details={"path": path})
            payload = payload.get("data")
        if not isinstance(payload, dict):
            raise MalformedResponseError(f"backend response data is not an object for {path}", details={"path": path})
        return payload

    def fetch_nearby_candidates(self, request: NearbyCandidatesRequest) -> NearbyCandidatesResponse:
        payload = self._post_json(_ENDPOINT_NEARBY, request.model_dump(mode="json"))
        try:
            return NearbyCandidatesResponse.model_validate(payload)
        except Exception as exc:  # noqa: BLE001 - validation failure -> structured error
            raise MalformedResponseError(
                f"nearby-candidates response does not match the contract: {exc}",
                details={"path": _ENDPOINT_NEARBY},
            ) from exc

    def fetch_landmarks(self) -> LandmarkSet:
        payload = self._get_json(_ENDPOINT_LANDMARKS)
        try:
            return LandmarkSet.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            raise MalformedResponseError(
                f"landmarks response does not match the contract: {exc}",
                details={"path": _ENDPOINT_LANDMARKS},
            ) from exc

    def fetch_media(self, reference: str) -> bytes:
        try:
            with self._client as client:
                response = client.get(_ENDPOINT_MEDIA.format(reference=reference))
        except Exception as exc:  # noqa: BLE001
            raise BackendAdapterError(
                f"backend media fetch failed for {reference}: {exc}", details={"media_reference": reference}
            ) from exc
        if response.status_code != 200:
            raise BackendAdapterError(
                f"backend returned HTTP {response.status_code} for media {reference}",
                details={"media_reference": reference, "status_code": response.status_code},
            )
        return response.content

    def resolve_media_metadata(self, reference: str) -> MediaReference:
        payload = self._get_json(_ENDPOINT_MEDIA_METADATA.format(reference=reference))
        try:
            return MediaReference.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            raise MalformedResponseError(
                f"media metadata response does not match the contract: {exc}",
                details={"media_reference": reference},
            ) from exc


__all__ = ["RealBackendAdapter"]