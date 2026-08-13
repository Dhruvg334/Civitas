"""Authenticated HTTP implementations of the workflow tool boundaries.

They intentionally consume the public Civitas envelopes, keeping the graph
independent of FastAPI internals and ML implementation modules.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from civitas_knowledge.backends import HttpKnowledgeBackend
from civitas_knowledge.contracts import (
    IncidentCategory,
    KnowledgePurpose,
    KnowledgeQuery,
    KnowledgeResult,
)
from civitas_knowledge.retrieval import KnowledgeService
from pydantic import BaseModel, ValidationError

from civitas_workflow.tools import (
    KnowledgeTool,
    MLIntelligenceTool,
    PersistenceTool,
    ReportContextTool,
    TraceTool,
)
from civitas_workflow.workflow_contracts import (
    ClarificationQuestion,
    MLIntelligence,
    OperationalPlan,
    RoutingDecision,
    WorkflowContext,
    WorkflowTraceEvent,
)


class WorkflowHTTPError(RuntimeError):
    """Typed, secret-free error returned by a Civitas runtime dependency."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class HTTPTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> tuple[int, bytes]: ...


class UrllibHTTPTransport:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> tuple[int, bytes]:
        try:
            with urlopen(
                Request(url, data=body, headers=dict(headers), method=method), timeout=timeout
            ) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, exc.read()
        except URLError as exc:
            raise WorkflowHTTPError(
                "DEPENDENCY_UNAVAILABLE", str(exc.reason), retryable=True
            ) from exc


@dataclass(frozen=True)
class HTTPAdapterSettings:
    backend_base_url: str
    ml_base_url: str
    internal_api_key: str | None = None
    timeout_seconds: float = 10.0
    max_retries: int = 2


class _HTTPBase:
    def __init__(
        self, settings: HTTPAdapterSettings, transport: HTTPTransport | None = None
    ) -> None:
        self.settings = settings
        self.transport = transport or UrllibHTTPTransport()

    def _request(
        self,
        method: str,
        base_url: str,
        path: str,
        payload: object | None = None,
        *,
        trace_id: str | None = None,
    ) -> Any:
        body = json.dumps(payload, default=_json_default).encode() if payload is not None else None
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.settings.internal_api_key:
            headers["X-Civitas-Internal-Key"] = self.settings.internal_api_key
        if trace_id:
            headers["X-Civitas-Trace-Id"] = trace_id
        url = f"{base_url.rstrip('/')}{path}"
        last_error: WorkflowHTTPError | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                status, raw = self.transport.request(
                    method, url, headers=headers, body=body, timeout=self.settings.timeout_seconds
                )
                parsed = json.loads(raw or b"{}")
                if 200 <= status < 300 and isinstance(parsed, dict) and parsed.get("success", True):
                    return parsed.get("data", parsed)
                detail = (
                    parsed.get("detail", parsed) if isinstance(parsed, dict) else "invalid response"
                )
                retryable = status >= 500
                last_error = WorkflowHTTPError("HTTP_ERROR", str(detail), retryable=retryable)
                if not retryable or attempt == self.settings.max_retries:
                    raise last_error
            except (json.JSONDecodeError, ValidationError) as exc:
                raise WorkflowHTTPError(
                    "MALFORMED_RESPONSE", "runtime dependency returned invalid JSON"
                ) from exc
            except WorkflowHTTPError as exc:
                last_error = exc
                if not exc.retryable or attempt == self.settings.max_retries:
                    raise
        raise last_error or WorkflowHTTPError("HTTP_ERROR", "request failed")


class _ReportPayload(BaseModel):
    report_id: str
    description: str = ""
    latitude: float | None = None
    longitude: float | None = None
    category: str | None = None


class HttpReportContextTool(_HTTPBase, ReportContextTool):
    def load(self, report_id: str) -> WorkflowContext:
        report = _ReportPayload.model_validate(
            self._request("GET", self.settings.backend_base_url, f"/api/v1/reports/{report_id}")
        )
        media = self._request(
            "GET", self.settings.backend_base_url, f"/api/v1/reports/{report_id}/media"
        )
        clarifications = self._request(
            "GET", self.settings.backend_base_url, f"/api/v1/reports/{report_id}/clarifications"
        )
        answers = {
            str(row["question_id"]): str(row["answer_text"])
            for row in clarifications.get("clarifications", [])
            if row.get("answered_at") and row.get("answer_text")
        }
        return WorkflowContext(
            report_id=report.report_id,
            incident_id=report.report_id,
            description=report.description,
            latitude=report.latitude,
            longitude=report.longitude,
            citizen_selected_category=report.category,
            media=media.get("media", []),
            clarification_answers=answers,
        )


class HttpMLIntelligenceTool(_HTTPBase, MLIntelligenceTool):
    """Consumes the backend's thin internal bridge to ReportAnalysis."""

    def analyze(self, context: WorkflowContext, *, trace_id: str) -> MLIntelligence:
        result = self._request(
            "POST",
            self.settings.ml_base_url,
            "/api/v1/ml/analyze",
            {"report_id": context.report_id, "trace_id": trace_id},
            trace_id=trace_id,
        )
        vision = result.get("vision", {})
        severity = result.get("severity", {})
        priority = result.get("priority", {})
        duplicate = result.get("duplicate", {})
        cluster = result.get("cluster", {})
        return MLIntelligence(
            available=True,
            primary_category=vision.get("predicted_category"),
            observable_evidence=vision.get("basis", []),
            uncertainty=[*vision.get("media_rejected_basis", []), *result.get("basis", [])],
            duplicate_verdict=duplicate.get("verdict"),
            cluster_verdict=cluster.get("verdict"),
            severity_score=severity.get("score"),
            severity_level=severity.get("level"),
            priority_score=priority.get("score"),
            priority_level=priority.get("level"),
            feature_contributions=[item.get("factor", "") for item in severity.get("factors", [])],
            model_versions=[item.get("model_version", "") for item in result.get("models", [])],
        )


class HttpKnowledgeTool(_HTTPBase, KnowledgeTool):
    """Uses the existing policy/playbook API through the knowledge service."""

    def retrieve(
        self, context: WorkflowContext, category: str | None, purposes: Sequence[KnowledgePurpose]
    ) -> KnowledgeResult:
        del context
        service = KnowledgeService(
            HttpKnowledgeBackend(
                base_url=self.settings.backend_base_url,
                token=self.settings.internal_api_key,
                timeout_seconds=self.settings.timeout_seconds,
            )
        )
        return service.retrieve(
            KnowledgeQuery(
                category=IncidentCategory(category) if category else None,
                purposes=list(purposes),
                limit=20,
            )
        )


class HttpPersistenceTool(_HTTPBase, PersistenceTool):
    def save_clarifications(
        self, incident_id: str, questions: Sequence[ClarificationQuestion]
    ) -> None:
        self._request(
            "POST",
            self.settings.backend_base_url,
            f"/api/v1/reports/{incident_id}/clarifications",
            {"questions": [item.model_dump(mode="json") for item in questions]},
        )

    def save_clarification_answers(self, incident_id: str, answers: dict[str, str]) -> None:
        for question_id, answer in answers.items():
            self._request(
                "POST",
                self.settings.backend_base_url,
                f"/api/v1/reports/{incident_id}/clarifications/{question_id}/answer",
                {"answer": answer},
            )

    def ensure_routing(self, incident_id: str, decision: RoutingDecision) -> None:
        existing = self._request(
            "GET", self.settings.backend_base_url, f"/api/v1/incidents/{incident_id}/route"
        )
        if not existing.get("routings"):
            self._request(
                "POST",
                self.settings.backend_base_url,
                f"/api/v1/incidents/{incident_id}/route",
                decision.model_dump(mode="json"),
            )

    def ensure_work_order(
        self, incident_id: str, plan: OperationalPlan, routing: RoutingDecision
    ) -> str:
        incident = self._request(
            "GET", self.settings.backend_base_url, f"/api/v1/incidents/{incident_id}"
        )
        if incident.get("assigned_work_order_id"):
            return str(incident["assigned_work_order_id"])
        payload = {
            **plan.model_dump(mode="json"),
            **routing.model_dump(mode="json"),
            "summary": plan.summary,
        }
        row = self._request(
            "POST",
            self.settings.backend_base_url,
            f"/api/v1/incidents/{incident_id}/work-orders",
            payload,
        )
        return str(row["work_order_id"])

    def apply_human_review(self, work_order_id: str, action: str) -> None:
        if action == "approve":
            self._request(
                "POST",
                self.settings.backend_base_url,
                f"/api/v1/work-orders/{work_order_id}/approve",
                {},
            )
        elif action == "reject":
            self._request(
                "POST",
                self.settings.backend_base_url,
                f"/api/v1/work-orders/{work_order_id}/reject",
                {},
            )


class HttpTraceTool(_HTTPBase, TraceTool):
    def record(self, incident_id: str, trace_id: str, event: WorkflowTraceEvent) -> None:
        self._request(
            "POST",
            self.settings.backend_base_url,
            f"/api/v1/incidents/{incident_id}/trace",
            {"workflow_trace_id": trace_id, **event.model_dump(mode="json")},
            trace_id=trace_id,
        )


def _json_default(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    raise TypeError(f"not JSON serializable: {type(value)!r}")
