"""Integration tests for Omnichannel citizen intake endpoints."""

import io
from fastapi.testclient import TestClient
from civitas_api.main import app

client = TestClient(app)


def test_whatsapp_webhook_verification_success():
    resp = client.get(
        "/intake/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "challenge_123456",
            "hub.verify_token": "civitas_whatsapp_verify_2026",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "challenge_123456"


def test_whatsapp_webhook_verification_mismatch():
    resp = client.get(
        "/intake/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "challenge_123456",
            "hub.verify_token": "wrong_token",
        },
    )
    assert resp.status_code == 403


def test_whatsapp_webhook_incoming_message():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "15550192834"},
                            "messages": [
                                {
                                    "from": "15550192834",
                                    "id": "wamid.HBgL...",
                                    "timestamp": "1724180000",
                                    "type": "text",
                                    "text": {"body": "Water leaking rapidly near school entrance"},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    resp = client.post("/intake/whatsapp", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["processed"] == 1
    assert len(data["data"]["reports"]) == 1


def test_telegram_webhook_incoming():
    payload = {
        "update_id": 10001,
        "message": {
            "message_id": 42,
            "from": {"id": 999123, "is_bot": False, "first_name": "Citizen", "username": "citizen_john"},
            "chat": {"id": 999123, "type": "private"},
            "date": 1724180000,
            "text": "Huge pothole on 5th Avenue causing traffic hazard",
        },
    }
    resp = client.post("/intake/telegram", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["status"] == "processed"
    assert data["data"]["sender"] == "citizen_john"


def test_audio_voice_intake():
    # Construct minimal valid OGG audio header
    fake_ogg = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00" + b"\x00" * 50
    files = {"file": ("voicenote.ogg", fake_ogg, "audio/ogg")}
    data = {"latitude": "20.29614", "longitude": "85.82451", "category": "water_leakage"}

    resp = client.post("/intake/audio", data=data, files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "intake_complete"
    assert "report_id" in body["data"]


def test_simulate_omnichannel_intake():
    payload = {
        "channel": "whatsapp",
        "sender_id": "+919876543210",
        "text": "Simulated broken streetlight sparking at main gate",
        "category": "broken_streetlight",
        "latitude": 28.6139,
        "longitude": 77.2090,
    }
    resp = client.post("/intake/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["channel"] == "whatsapp"
    assert data["data"]["status"] == "INTAKE_ACCEPTED"
    assert "inc-" in data["data"]["incident_id"]
    assert "civitas-web.vercel.app" in data["data"]["tracking_url"]


def test_audio_voice_intake_invalid_header():
    fake_bad_audio = b"NOT_REAL_AUDIO_DATA_BYTES"
    files = {"file": ("voicenote.ogg", fake_bad_audio, "audio/ogg")}
    resp = client.post("/intake/audio", data={"latitude": "20.29614", "longitude": "85.82451"}, files=files)
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["error"]["code"] == "INVALID_AUDIO_HEADER"


def test_audio_voice_intake_unsupported_mime():
    files = {"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")}
    resp = client.post("/intake/audio", data={"latitude": "20.29614", "longitude": "85.82451"}, files=files)
    assert resp.status_code == 415
    body = resp.json()
    assert body["detail"]["error"]["code"] == "UNSUPPORTED_AUDIO_FORMAT"


def test_whatsapp_webhook_empty_payload():
    resp = client.post("/intake/whatsapp", json={"object": "whatsapp_business_account", "entry": []})
    assert resp.status_code == 200
    assert resp.json()["data"]["processed"] == 0


def test_telegram_webhook_empty_message():
    resp = client.post("/intake/telegram", json={"update_id": 10002})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ignored"

