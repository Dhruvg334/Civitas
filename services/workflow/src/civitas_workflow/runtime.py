"""Canonical production and deterministic workflow composition."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from civitas_workflow.agents import CivitasAgents
from civitas_workflow.graph import CivitasWorkflow, WorkflowDependencies, build_workflow
from civitas_workflow.http_adapters import (
    HTTPAdapterSettings,
    HttpKnowledgeTool,
    HttpMLIntelligenceTool,
    HttpPersistenceTool,
    HttpReportContextTool,
    HttpTraceTool,
)
from civitas_workflow.llm import GroqLLMClient, LLMClient


def create_production_workflow(
    *, checkpointer: BaseCheckpointSaver[Any], prompt_root: Path
) -> CivitasWorkflow:
    """Wire the one production graph; callers must provide a durable saver."""
    settings = HTTPAdapterSettings(
        backend_base_url=_required_env("CIVITAS_BACKEND_BASE_URL"),
        ml_base_url=_required_env("ML_SERVICE_URL"),
        internal_api_key=os.getenv("CIVITAS_INTERNAL_API_KEY") or None,
        timeout_seconds=float(os.getenv("CIVITAS_WORKFLOW_HTTP_TIMEOUT_SECONDS", "10")),
        max_retries=int(os.getenv("CIVITAS_WORKFLOW_HTTP_MAX_RETRIES", "2")),
    )
    return _compose(
        llm=GroqLLMClient(),
        prompt_root=prompt_root,
        checkpointer=checkpointer,
        settings=settings,
    )


def create_test_workflow(
    *,
    llm: LLMClient,
    dependencies: WorkflowDependencies,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CivitasWorkflow:
    """Single graph logic for offline tests; no network or Groq configuration."""
    del llm  # Agents are already present in deterministic dependency composition.
    return build_workflow(dependencies, checkpointer=checkpointer or MemorySaver())


def _compose(
    *,
    llm: LLMClient,
    prompt_root: Path,
    checkpointer: BaseCheckpointSaver[Any],
    settings: HTTPAdapterSettings,
) -> CivitasWorkflow:
    return build_workflow(
        WorkflowDependencies(
            context_tool=HttpReportContextTool(settings),
            ml_tool=HttpMLIntelligenceTool(settings),
            knowledge_tool=HttpKnowledgeTool(settings),
            persistence_tool=HttpPersistenceTool(settings),
            trace_tool=HttpTraceTool(settings),
            agents=CivitasAgents(llm, prompt_root=prompt_root),
        ),
        checkpointer=checkpointer,
    )


def create_postgres_checkpointer(database_url: str) -> BaseCheckpointSaver[Any]:
    """Create LangGraph's PostgreSQL saver when its optional dependency is installed."""
    try:
        from langgraph.checkpoint.postgres import PostgresSaver  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on deployment extra
        raise RuntimeError(
            "PostgreSQL checkpointing requires langgraph-checkpoint-postgres; "
            "install the workflow production extra."
        ) from exc
    return cast(BaseCheckpointSaver[Any], PostgresSaver.from_conn_string(database_url))


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required for the production workflow")
    return value
