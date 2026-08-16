"""Tests for the clarifications module."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_report(client: TestClient, auth_header: dict[str, str]) -> str:
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "test report for clarifications",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["report_id"]


def _triage_token() -> str:
    import jwt as pyjwt
    return pyjwt.encode(
        {"sub": "triage-1", "role": "triage"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _triage_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {_triage_token()}"}


def _citizen_header() -> dict[str, str]:
    return {
        "Authorization": "Bearer "
        + __import__("jwt").encode(
            {"sub": "citizen-1", "role": "citizen"},
            "test-secret-not-used-in-dev-mode",
            algorithm="HS256",
        )
    }


def test_ask_clarifications_advances_state(client: TestClient) -> None:
    auth = _triage_header()
    rid = _create_report(client, auth)
    r = client.post(
        f"/api/v1/reports/{rid}/clarifications",
        json={
            "questions": [
                {"question_id": "q1", "text": "Any electrical contact?", "required": True},
            ]
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["count"] == 1
    assert data["clarifications"][0]["question_id"] == "q1"
    assert data["clarifications"][0]["answered_at"] is None

    det = client.get(f"/api/v1/incidents/{rid}", headers=auth).json()["data"]
    assert det["status"] == "awaiting_clarification"


def test_ask_validates_nonempty(client: TestClient) -> None:
    auth = _triage_header()
    rid = _create_report(client, auth)
    r = client.post(
        f"/api/v1/reports/{rid}/clarifications",
        json={"questions": []},
        headers=auth,
    )
    assert r.status_code == 422


def test_answer_clarification_persists(client: TestClient) -> None:
    auth = _triage_header()
    rid = _create_report(client, auth)
    client.post(
        f"/api/v1/reports/{rid}/clarifications",
        json={"questions": [{"question_id": "q1", "text": "Any electrical contact?", "required": True}]},
        headers=auth,
    )
    r = client.post(
        f"/api/v1/reports/{rid}/clarifications/q1/answer",
        json={"answer": "No electrical equipment visible"},
        headers=_citizen_header(),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["answer_text"] == "No electrical equipment visible"
    assert data["answered_at"] is not None
    # Last required Q answered -> back to under_analysis
    det = client.get(f"/api/v1/incidents/{rid}", headers=auth).json()["data"]
    assert det["status"] == "under_analysis"


def test_optional_unanswered_does_not_advance(client: TestClient) -> None:
    auth = _triage_header()
    rid = _create_report(client, auth)
    client.post(
        f"/api/v1/reports/{rid}/clarifications",
        json={
            "questions": [
                {"question_id": "qreq", "text": "required?", "required": True},
                {"question_id": "qopt", "text": "optional?", "required": False},
            ]
        },
        headers=auth,
    )
    # Answer only the optional one
    client.post(
        f"/api/v1/reports/{rid}/clarifications/qopt/answer",
        json={"answer": "skip"},
        headers=_citizen_header(),
    )
    det = client.get(f"/api/v1/incidents/{rid}", headers=auth).json()["data"]
    # Still waiting because qreq unanswered
    assert det["status"] == "awaiting_clarification"


def test_reasking_open_question_is_noop(client: TestClient) -> None:
    auth = _triage_header()
    rid = _create_report(client, auth)
    client.post(
        f"/api/v1/reports/{rid}/clarifications",
        json={"questions": [{"question_id": "q1", "text": "first?", "required": False}]},
        headers=auth,
    )
    # Re-asking same q1 should NOT create a duplicate row.
    r = client.post(
        f"/api/v1/reports/{rid}/clarifications",
        json={"questions": [{"question_id": "q1", "text": "first?", "required": False}]},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    # Second ask should add zero rows
    assert r.json()["data"]["count"] == 0


def test_list_clarifications(client: TestClient) -> None:
    auth = _triage_header()
    rid = _create_report(client, auth)
    client.post(
        f"/api/v1/reports/{rid}/clarifications",
        json={"questions": [
            {"question_id": "q1", "text": "one"},
            {"question_id": "q2", "text": "two"},
        ]},
        headers=auth,
    )
    r = client.get(f"/api/v1/reports/{rid}/clarifications", headers=auth)
    assert r.status_code == 200
    assert r.json()["data"]["count"] == 2