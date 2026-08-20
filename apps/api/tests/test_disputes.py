"""Unit and integration tests for citizen 72-hour dispute and resolution re-open."""

from fastapi.testclient import TestClient
from civitas_api.main import app
from civitas_api.operations.disputes import get_dispute_window_status, submit_citizen_dispute

client = TestClient(app)


def test_dispute_workflow_end_to_end():
    # 1. Create an incident
    create_resp = client.post(
        "/open311/v2/requests.json",
        data={"service_code": "001", "description": "Dangerous pothole outside metro"},
    )
    inc_id = create_resp.json()[0]["service_request_id"]

    # 2. Mark incident as resolved in DB
    from civitas_api.operations.reports import get_connection, _is_sqlite
    from datetime import datetime, UTC

    with get_connection() as conn, conn.cursor() as cur:
        now_iso = datetime.now(UTC).isoformat()
        if _is_sqlite():
            cur.execute("UPDATE incidents SET status = 'resolved', status_updated_at = ? WHERE incident_id = ?", (now_iso, inc_id))
        else:
            cur.execute("UPDATE incidents SET status = 'resolved', status_updated_at = %(now)s WHERE incident_id = %(id)s", {"now": datetime.now(UTC), "id": inc_id})
        conn.commit()

    # 3. Check dispute status
    status_resp = client.get(f"/resolutions/{inc_id}/dispute-status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["success"] is True
    assert data["data"]["is_disputable"] is True
    assert data["data"]["hours_remaining"] > 70.0

    # 4. Submit citizen dispute
    dispute_payload = {
        "dispute_reason": "Pothole was only filled with loose sand and collapsed after rain",
        "rebuttal_photo_url": "https://civitas-storage/dispute-rebuttal.jpg",
    }
    disp_resp = client.post(f"/resolutions/{inc_id}/dispute", json=dispute_payload)
    assert disp_resp.status_code == 200
    disp_data = disp_resp.json()
    assert disp_data["success"] is True
    assert disp_data["data"]["new_status"] == "reopened_disputed"
    assert "P1_CRITICAL" in disp_data["data"]["priority_escalation"]


def test_dispute_expired_window():
    # Create an incident resolved 100 hours ago
    create_resp = client.post(
        "/open311/v2/requests.json",
        data={"service_code": "001", "description": "Old resolved road repair"},
    )
    inc_id = create_resp.json()[0]["service_request_id"]

    from civitas_api.operations.reports import get_connection, _is_sqlite
    from datetime import datetime, timedelta, UTC

    stale_resolved = (datetime.now(UTC) - timedelta(hours=100)).isoformat()
    with get_connection() as conn, conn.cursor() as cur:
        if _is_sqlite():
            cur.execute("UPDATE incidents SET status = 'resolved', status_updated_at = ? WHERE incident_id = ?", (stale_resolved, inc_id))
        else:
            cur.execute("UPDATE incidents SET status = 'resolved', status_updated_at = %(now)s WHERE incident_id = %(id)s", {"now": stale_resolved, "id": inc_id})
        conn.commit()

    # Attempt dispute after 72h window
    disp_resp = client.post(f"/resolutions/{inc_id}/dispute", json={"dispute_reason": "Too late dispute attempt"})
    assert disp_resp.status_code == 400
    assert disp_resp.json()["detail"]["error"]["code"] == "DISPUTE_NOT_PERMITTED"
