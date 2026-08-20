"""Unit and integration tests for omnichannel clarification formatting and reply ingestion."""

from fastapi.testclient import TestClient
from civitas_api.main import app
from civitas_workflow.clarification_channels import (
    format_channel_clarification_prompt,
    parse_channel_clarification_reply,
)

client = TestClient(app)


def test_format_channel_clarification_prompt():
    prompt = format_channel_clarification_prompt(
        question="Is water actively flooding electrical panels",
        options=["Yes, sparks visible", "No, water is near drain only", "Unsure"],
        incident_id="inc-test-99",
        channel="whatsapp",
    )
    assert "inc-test-99" in prompt.formatted_message
    assert "1️⃣" in prompt.formatted_message
    assert "2️⃣" in prompt.formatted_message
    assert "3️⃣" in prompt.formatted_message
    assert prompt.options[0] == "Yes, sparks visible"


def test_parse_channel_clarification_reply():
    opts = [
        "Yes, water is entering building",
        "No, localized street pooling",
        "Cannot verify safely",
    ]

    # Test digit parse
    r1 = parse_channel_clarification_reply("1", opts)
    assert r1.is_confident_match is True
    assert r1.selected_option_index == 0
    assert r1.selected_option_text == opts[0]

    # Test 'option 2'
    r2 = parse_channel_clarification_reply("option 2", opts)
    assert r2.is_confident_match is True
    assert r2.selected_option_index == 1

    # Test yes/no shortcut
    r3 = parse_channel_clarification_reply("yes", opts)
    assert r3.is_confident_match is True
    assert r3.selected_option_index == 0

    # Test keyword match
    r4 = parse_channel_clarification_reply("it is safely clear", opts)
    assert r4.is_confident_match is True
    assert r4.selected_option_index == 2


def test_get_clarification_prompt_endpoint():
    resp = client.get("/intake/clarify-prompt/inc-demo-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "prompt_text" in data["data"]
    assert "inc-demo-123" in data["data"]["prompt_text"]


def test_ingest_clarification_reply_endpoint():
    # First create an incident
    create_resp = client.post(
        "/open311/v2/requests.json",
        data={"service_code": "002", "description": "Pipe leaking near school"},
    )
    inc_id = create_resp.json()[0]["service_request_id"]

    reply_payload = {
        "report_id": inc_id,
        "channel": "whatsapp",
        "reply_text": "1",
    }
    resp = client.post("/intake/clarify-reply", json=reply_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["status"] == "CLARIFICATION_PROCESSED"
    assert data["data"]["is_confident_match"] is True
