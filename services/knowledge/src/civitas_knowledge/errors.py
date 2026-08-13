"""Typed knowledge layer failures."""

from __future__ import annotations

from typing import Any


class KnowledgeError(Exception):
    code = "knowledge_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class KnowledgeConfigurationError(KnowledgeError):
    code = "knowledge_configuration_error"


class KnowledgeBackendError(KnowledgeError):
    code = "knowledge_backend_error"


class KnowledgeMalformedResponseError(KnowledgeBackendError):
    code = "knowledge_malformed_response"
