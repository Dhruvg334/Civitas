"""Trace sink boundary; persistence remains owned by the API layer."""

from __future__ import annotations

from typing import Protocol

from civitas_workflow.llm.contracts import LLMTraceRecord


class LLMTraceSink(Protocol):
    def record(self, event: LLMTraceRecord) -> None: ...


class NullTraceSink:
    def record(self, event: LLMTraceRecord) -> None:
        del event


class InMemoryTraceSink:
    def __init__(self) -> None:
        self.events: list[LLMTraceRecord] = []

    def record(self, event: LLMTraceRecord) -> None:
        self.events.append(event)
