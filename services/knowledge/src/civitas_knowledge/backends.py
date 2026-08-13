"""Backend boundary for the existing Civitas policy/playbook API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Protocol, cast

from pydantic import ValidationError

from civitas_knowledge.contracts import KnowledgeProvenance, KnowledgeRecord, PolicyType
from civitas_knowledge.errors import KnowledgeBackendError, KnowledgeMalformedResponseError


class KnowledgeBackend(ABC):
    @abstractmethod
    def list_records(self, *, policy_type: PolicyType | None = None) -> list[KnowledgeRecord]: ...


class InMemoryKnowledgeBackend(KnowledgeBackend):
    def __init__(self, records: Sequence[KnowledgeRecord]) -> None:
        self._records = tuple(record.model_copy(deep=True) for record in records)

    def list_records(self, *, policy_type: PolicyType | None = None) -> list[KnowledgeRecord]:
        records = self._records
        if policy_type is not None:
            records = tuple(record for record in records if record.policy_type == policy_type)
        return [record.model_copy(deep=True) for record in records]


class KnowledgeHTTPTransport(Protocol):
    def get_json(
        self, url: str, *, headers: dict[str, str], timeout_seconds: float
    ) -> tuple[int, object]: ...


class UrllibKnowledgeTransport:
    def get_json(
        self, url: str, *, headers: dict[str, str], timeout_seconds: float
    ) -> tuple[int, object]:
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8")
                return response.status, _json_body(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return exc.code, _json_body(body)
        except TimeoutError as exc:
            raise KnowledgeBackendError("knowledge backend request timed out") from exc
        except urllib.error.URLError as exc:
            raise KnowledgeBackendError(f"knowledge backend is unreachable: {exc.reason}") from exc


class HttpKnowledgeBackend(KnowledgeBackend):
    """Consumes the current GET /api/v1/policies success-envelope contract."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str | None = None,
        timeout_seconds: float = 10.0,
        transport: KnowledgeHTTPTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport or UrllibKnowledgeTransport()
        self.headers = {"Accept": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def list_records(self, *, policy_type: PolicyType | None = None) -> list[KnowledgeRecord]:
        params: dict[str, str | int] = {"limit": 200}
        if policy_type is not None:
            params["kind"] = policy_type.value
        path = "/api/v1/policies"
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        status, payload = self.transport.get_json(
            url, headers=self.headers, timeout_seconds=self.timeout_seconds
        )
        if status != 200:
            raise KnowledgeBackendError(
                f"knowledge backend returned HTTP {status}",
                details={"path": path, "status_code": status},
            )
        rows = _policy_rows(payload)
        try:
            return [_record_from_api(row, path) for row in rows]
        except (KeyError, TypeError, ValidationError, ValueError) as exc:
            raise KnowledgeMalformedResponseError(
                f"policy response does not match the knowledge contract: {exc}",
                details={"path": path},
            ) from exc


def _json_body(body: str) -> object:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body


def _policy_rows(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise KnowledgeMalformedResponseError("expected a Civitas success envelope")
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("policies"), list):
        raise KnowledgeMalformedResponseError("success envelope is missing data.policies")
    rows = data["policies"]
    if not all(isinstance(row, dict) for row in rows):
        raise KnowledgeMalformedResponseError("data.policies contains a non-object record")
    return cast(list[dict[str, Any]], rows)


def _record_from_api(row: dict[str, Any], source_path: str) -> KnowledgeRecord:
    record_id = str(row["policy_id"])
    reference_id = str(row["code"])
    return KnowledgeRecord(
        record_id=record_id,
        reference_id=reference_id,
        title=str(row["title"]),
        policy_type=PolicyType(str(row["kind"])),
        text=str(row["body"]),
        categories=_string_list(row.get("categories")),
        departments=_string_list(row.get("departments")),
        jurisdiction=(str(row["jurisdiction"]) if row.get("jurisdiction") is not None else None),
        required_actions=_string_list(row.get("required_actions")),
        suggested_resources=_string_list(row.get("suggested_resources")),
        severity_factors=_object_list(row.get("severity_factors")),
        priority_factors=_object_list(row.get("priority_factors")),
        provenance=KnowledgeProvenance(
            backend="civitas_api",
            source_identifier=record_id,
            source_path=f"{source_path}/{urllib.parse.quote(reference_id)}",
            attributes={"reference_id": reference_id},
        ),
    )


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("expected a list of strings")
    return list(value)


def _object_list(value: object) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("expected a list of objects")
    return [dict(item) for item in value]
