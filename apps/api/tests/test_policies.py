"""Tests for the policies + playbooks module."""

from __future__ import annotations

import jwt as pyjwt
from fastapi.testclient import TestClient

from civitas_api.main import app


def _triage_token() -> str:
    return pyjwt.encode(
        {"sub": "tri-1", "role": "triage"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _hdr() -> dict[str, str]:
    return {"Authorization": f"Bearer {_triage_token()}"}


def _seed_policies() -> None:
    """Seed the SQLite test profile with the same rows 0005 puts in PG."""
    from civitas_api.operations import policies as pol_ops
    pol_ops.upsert_policy(
        code="PLAY-WATER-01", kind="playbook",
        title="Water playbook",
        body="Primary WATER, secondary DRAIN.",
        categories=["water_leakage", "road_flooding"],
        departments=["water", "drain"],
        severity_factors=[{"name": "active_flow"}],
        priority_factors=[{"name": "school_proximity"}],
        required_actions=["secure area", "isolate leak"],
        suggested_resources=["water crew"],
    )
    pol_ops.upsert_policy(
        code="PLAY-POTHOLE-01", kind="playbook",
        title="Pothole playbook",
        body="Primary ROAD.",
        categories=["pothole"],
        departments=["road"],
        severity_factors=[{"name": "depth"}],
        priority_factors=[{"name": "traffic_exposure"}],
        required_actions=["inspect"],
        suggested_resources=["road crew"],
    )
    pol_ops.upsert_policy(
        code="POL-GEN-01", kind="policy",
        title="Routing uses observable evidence",
        body="...",
        categories=[], departments=[],
        severity_factors=[], priority_factors=[],
        required_actions=[], suggested_resources=[],
    )


def test_list_all_policies(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    _seed_policies()
    r = client.get("/api/v1/policies", headers=auth_header)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["count"] >= 3


def test_filter_by_kind(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    _seed_policies()
    r = client.get(
        "/api/v1/policies", params={"kind": "playbook"}, headers=auth_header
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["count"] == 2
    for p in data["policies"]:
        assert p["kind"] == "playbook"


def test_filter_by_category(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    _seed_policies()
    r = client.get(
        "/api/v1/policies", params={"category": "water_leakage"}, headers=auth_header
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["count"] == 1
    assert data["policies"][0]["code"] == "PLAY-WATER-01"


def test_filter_by_department(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    _seed_policies()
    r = client.get(
        "/api/v1/policies", params={"department": "road"}, headers=auth_header
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["count"] == 1
    assert data["policies"][0]["code"] == "PLAY-POTHOLE-01"


def test_get_policy_by_code(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    _seed_policies()
    r = client.get("/api/v1/policies/PLAY-WATER-01", headers=auth_header)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["code"] == "PLAY-WATER-01"
    assert data["kind"] == "playbook"
    assert "water_leakage" in data["categories"]


def test_get_policy_404(client: TestClient, auth_header: dict[str, str]) -> None:
    r = client.get("/api/v1/policies/PLAY-NOPE", headers=auth_header)
    assert r.status_code == 404


def test_requires_triage_role(client: TestClient) -> None:
    citizen_tok = pyjwt.encode(
        {"sub": "c-1", "role": "citizen"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )
    r = client.get(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {citizen_tok}"},
    )
    assert r.status_code == 403