"""Shared pytest fixtures.

The default pytest run uses SQLite + monkeypatched operations so tests
pass in CI without a live database. When `DATABASE_URL` points at a
real Postgres, the integration tests exercise the full path.

Auth is bypassed in tests via the `dev_token` fixture, which yields a
JWT-signed token. The auth dependency is invoked against the configured
secret (empty in tests → dev mode → accept unsigned).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _sqlite_schema() -> str:
    return """
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id TEXT PRIMARY KEY,
        category TEXT,
        reported_at TEXT,
        duplicates_seen INTEGER DEFAULT 1,
        description TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT NOT NULL DEFAULT 'submitted',
        source TEXT NOT NULL DEFAULT 'citizen',
        status_updated_at TEXT,
        last_assessment_model TEXT,
        assigned_department TEXT,
        assigned_work_order_id TEXT,
        resolution_class TEXT
    );
    CREATE TABLE IF NOT EXISTS incident_links (
        link_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        report_id TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'duplicate_detector',
        confidence REAL,
        basis TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT,
        UNIQUE (incident_id, report_id)
    );
    CREATE TABLE IF NOT EXISTS media (
        media_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        bytes_size INTEGER NOT NULL,
        width INTEGER,
        height INTEGER,
        duration_s REAL,
        captured_at TEXT,
        uploaded_at TEXT NOT NULL,
        uploaded_by TEXT
    );
    CREATE TABLE IF NOT EXISTS incident_assessments (
        assessment_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        severity_score INTEGER,
        severity_level TEXT,
        severity_factors TEXT,
        priority_score INTEGER,
        priority_level TEXT,
        priority_factors TEXT,
        uncertainties TEXT,
        review_required INTEGER NOT NULL DEFAULT 0,
        model_version TEXT,
        assessed_at TEXT NOT NULL,
        assessed_by TEXT
    );
    CREATE TABLE IF NOT EXISTS agent_traces (
        trace_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        node TEXT NOT NULL,
        model_version TEXT,
        prompt_version TEXT,
        input TEXT,
        output TEXT,
        latency_ms INTEGER,
        tokens_in INTEGER,
        tokens_out INTEGER,
        validation_outcome TEXT,
        created_at TEXT NOT NULL
    );
    -- 0004 additions
    CREATE TABLE IF NOT EXISTS work_orders (
        work_order_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        summary TEXT NOT NULL,
        required_actions TEXT,
        suggested_resources TEXT,
        safety_notes TEXT,
        estimated_window_min_hours INTEGER,
        estimated_window_max_hours INTEGER,
        non_binding INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'awaiting_review',
        primary_department TEXT,
        secondary_departments TEXT,
        escalation_required INTEGER NOT NULL DEFAULT 0,
        policy_references TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT,
        reviewed_by TEXT,
        reviewed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS clarifications (
        clarification_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        question_id TEXT NOT NULL,
        question_text TEXT NOT NULL,
        decision_impact TEXT,
        required INTEGER NOT NULL DEFAULT 0,
        asked_at TEXT NOT NULL,
        answered_at TEXT,
        answer_text TEXT,
        answered_by TEXT
    );
    CREATE TABLE IF NOT EXISTS routing_decisions (
        routing_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        primary_department TEXT NOT NULL,
        secondary_departments TEXT,
        escalation_required INTEGER NOT NULL DEFAULT 0,
        policy_references TEXT,
        decision_basis TEXT,
        review_required INTEGER NOT NULL DEFAULT 1,
        workflow_version TEXT NOT NULL DEFAULT 'routing-v1',
        routed_at TEXT NOT NULL,
        routed_by TEXT
    );
    CREATE TABLE IF NOT EXISTS resolution_submissions (
        resolution_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        classification TEXT NOT NULL,
        resolved_evidence TEXT,
        remaining_evidence TEXT,
        uncertainties TEXT,
        model_version TEXT,
        submitted_at TEXT NOT NULL,
        submitted_by TEXT,
        reviewed_by TEXT,
        reviewed_at TEXT,
        review_action TEXT
    );
    CREATE TABLE IF NOT EXISTS policies (
        policy_id TEXT PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        categories TEXT,
        departments TEXT,
        severity_factors TEXT,
        priority_factors TEXT,
        required_actions TEXT,
        suggested_resources TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS workflow_runs (
        workflow_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL UNIQUE,
        report_id TEXT NOT NULL,
        incident_id TEXT,
        trace_id TEXT NOT NULL,
        status TEXT NOT NULL,
        interrupt_type TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT
    );
    """


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Per-test ephemeral SQLite DB unless DATABASE_URL points at real PG."""
    from civitas_api.core import config as cfg

    cfg.get_settings.cache_clear()

    if os.environ.get("DATABASE_URL", "").startswith("postgresql"):
        yield
        cfg.get_settings.cache_clear()
        return

    db = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("CIVITAS_POSTGIS_DSN", f"sqlite:///{db}")
    cfg.get_settings.cache_clear()

    conn = sqlite3.connect(db)
    conn.executescript(_sqlite_schema())
    conn.commit()
    conn.close()

    yield
    cfg.get_settings.cache_clear()


@pytest.fixture
def dev_token() -> str:
    """A JWT with role supervisor; auth runs in dev mode (no secret)."""
    import jwt as pyjwt

    # PyJWT requires a non-empty HMAC key even when verification is off
    # in production. The auth dependency ignores the signature when
    # SUPABASE_JWT_SECRET is unset (dev mode), so the key value is
    # irrelevant — we just need something HMAC-shaped for PyJWT.
    return pyjwt.encode(
        {"sub": "test-user", "role": "supervisor"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


@pytest.fixture
def auth_header(dev_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {dev_token}"}


@pytest.fixture
def storage_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Local-disk storage under a fresh tmp dir for each test."""
    root = tmp_path / "storage"
    monkeypatch.setenv("CIVITAS_STORAGE_ROOT", str(root))
    from civitas_api.core import storage
    storage.reset_storage_for_tests()
    return root


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient wrapping the live app."""
    from civitas_api.main import app as _app
    return TestClient(_app)
