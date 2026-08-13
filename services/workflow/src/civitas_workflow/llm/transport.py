"""Minimal injectable HTTP transport for Groq's OpenAI-compatible endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol

from civitas_workflow.llm.contracts import TransportResponse


class LLMTransport(Protocol):
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> TransportResponse: ...


class UrllibLLMTransport:
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> TransportResponse:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8")
                return _response(response.status, body, dict(response.headers.items()))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return _response(exc.code, body, dict(exc.headers.items()) if exc.headers else {})
        except TimeoutError as exc:
            raise TimeoutError("Groq request timed out") from exc
        except urllib.error.URLError as exc:
            raise ConnectionError(f"Groq request failed: {exc.reason}") from exc


def _response(status: int, body: str, headers: dict[str, str]) -> TransportResponse:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return TransportResponse(status_code=status, raw_body=body, headers=headers)
    return TransportResponse(
        status_code=status,
        payload=payload if isinstance(payload, dict) else None,
        raw_body=body,
        headers=headers,
    )
