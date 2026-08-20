"""Omnichannel conversational clarification formatter and parser.

Translates LangGraph clarification interrupts into natural SMS/WhatsApp/Telegram
interactive prompts and parses citizen responses into normalized graph inputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClarificationPrompt:
    channel: str
    incident_id: str
    formatted_message: str
    options: list[str]


@dataclass(frozen=True)
class ParsedClarificationReply:
    selected_option_index: int | None
    selected_option_text: str
    is_confident_match: bool
    raw_reply: str


def format_channel_clarification_prompt(
    question: str,
    options: list[str],
    incident_id: str,
    channel: str = "whatsapp",
) -> ClarificationPrompt:
    """Formats an interactive conversational prompt for citizen chat channels."""
    clean_q = question.strip()
    if not clean_q.endswith("?"):
        clean_q += "?"

    lines = [
        f"🏛️ *Civitas Municipal Triage* (Ref: `{incident_id}`)",
        "",
        clean_q,
        "",
    ]
    for idx, opt in enumerate(options, 1):
        lines.append(f"*{idx}️⃣* {opt}")

    lines.append("")
    lines.append("👉 _Please reply with the number or brief text corresponding to your answer._")

    return ClarificationPrompt(
        channel=channel,
        incident_id=incident_id,
        formatted_message="\n".join(lines),
        options=options,
    )


def parse_channel_clarification_reply(
    reply_text: str,
    options: list[str],
) -> ParsedClarificationReply:
    """Parses a citizen's conversational reply into a structured option choice."""
    text = reply_text.strip().lower()

    # 1. Match direct digit (e.g. "1", "2", "#1", "option 1")
    digit_match = re.search(r"\b([1-9])\b", text)
    if digit_match:
        idx = int(digit_match.group(1)) - 1
        if 0 <= idx < len(options):
            return ParsedClarificationReply(
                selected_option_index=idx,
                selected_option_text=options[idx],
                is_confident_match=True,
                raw_reply=reply_text,
            )

    # 2. Match yes/no shortcuts
    if text in ("yes", "y", "true", "correct", "yep", "yeah") and len(options) >= 1:
        # Check if first option is an affirmative
        first_opt = options[0].lower()
        if "yes" in first_opt or "is" in first_opt or "active" in first_opt or "blocked" in first_opt:
            return ParsedClarificationReply(
                selected_option_index=0,
                selected_option_text=options[0],
                is_confident_match=True,
                raw_reply=reply_text,
            )

    if text in ("no", "n", "false", "nope", "negative") and len(options) >= 2:
        second_opt = options[1].lower()
        if "no" in second_opt or "not" in second_opt or "clear" in second_opt:
            return ParsedClarificationReply(
                selected_option_index=1,
                selected_option_text=options[1],
                is_confident_match=True,
                raw_reply=reply_text,
            )

    # 3. Match keyword substring
    for idx, opt in enumerate(options):
        words = [w for w in re.findall(r"\w+", opt.lower()) if len(w) > 3]
        if any(w in text for w in words):
            return ParsedClarificationReply(
                selected_option_index=idx,
                selected_option_text=opt,
                is_confident_match=True,
                raw_reply=reply_text,
            )

    # 4. Fallback: treat raw text as custom answer for option 0 or custom response
    fallback_text = reply_text.strip()
    return ParsedClarificationReply(
        selected_option_index=None,
        selected_option_text=fallback_text,
        is_confident_match=False,
        raw_reply=reply_text,
    )
