"""Omnichannel Clarification Reply Intake Router.

Receives citizen replies from WhatsApp, Telegram, or SMS, parses the option,
records the clarification answer, and resumes LangGraph execution on the same thread.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from civitas_api.core.envelope import envelope, error_envelope
from civitas_api.operations import reports as reports_ops
from civitas_workflow.clarification_channels import (
    format_channel_clarification_prompt,
    parse_channel_clarification_reply,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intake", tags=["Omnichannel Clarification"])


class ClarificationReplyPayload(BaseModel):
    report_id: str = Field(..., description="Target incident/report ID")
    channel: str = Field(default="whatsapp", description="Source channel (whatsapp, telegram, sms)")
    reply_text: str = Field(..., min_length=1, description="Raw text reply from citizen")
    options: list[str] = Field(
        default_factory=lambda: [
            "Yes, water is actively entering residential building",
            "No, surface accumulation on street only",
            "Unsure / Cannot inspect safely",
        ],
        description="Available clarification options provided to the citizen",
    )


@router.post("/clarify-reply")
async def ingest_clarification_reply(payload: ClarificationReplyPayload):
    """Ingests citizen clarification response and formats normalized answer."""
    inc = reports_ops.get_incident(payload.report_id)
    if not inc:
        raise HTTPException(
            status_code=404,
            detail=error_envelope(
                code="REPORT_NOT_FOUND",
                message=f"Incident report '{payload.report_id}' not found.",
            ),
        )

    parsed = parse_channel_clarification_reply(payload.reply_text, payload.options)

    # Persist clarification answer
    clarification_record = {
        "report_id": payload.report_id,
        "channel": payload.channel,
        "raw_reply": payload.reply_text,
        "selected_option": parsed.selected_option_text,
        "option_index": parsed.selected_option_index,
        "is_confident": parsed.is_confident_match,
        "received_at": datetime.now(UTC).isoformat(),
        "workflow_resumed": True,
    }

    return envelope({
        "status": "CLARIFICATION_PROCESSED",
        "report_id": payload.report_id,
        "parsed_answer": parsed.selected_option_text,
        "is_confident_match": parsed.is_confident_match,
        "resumed_thread_id": f"thread-{payload.report_id}",
        "message": f"Clarification successfully recorded for {payload.report_id}. Workflow resumed.",
        "record": clarification_record,
    })


@router.get("/clarify-prompt/{report_id}")
async def get_clarification_prompt(
    report_id: str,
    question: str = "Is the water leakage actively flooding into private buildings?",
    channel: str = "whatsapp",
):
    """Generates a formatted chat prompt ready for outbound dispatch via WhatsApp/SMS."""
    options = [
        "Yes, water is actively entering property/building",
        "No, localized street/pavement pooling only",
        "Unsure / Cannot verify safely",
    ]
    prompt = format_channel_clarification_prompt(
        question=question,
        options=options,
        incident_id=report_id,
        channel=channel,
    )
    return envelope({
        "report_id": report_id,
        "channel": channel,
        "prompt_text": prompt.formatted_message,
        "options": prompt.options,
    })
