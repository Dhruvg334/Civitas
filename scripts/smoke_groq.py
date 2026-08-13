"""Manual structured-output smoke check. Never run from automated tests."""

from __future__ import annotations

import sys

from civitas_workflow.llm import GroqLLMClient, LLMMessage, ModelTier
from pydantic import BaseModel


class SmokeResponse(BaseModel):
    ready: bool


def main() -> int:
    try:
        result = GroqLLMClient().generate_structured(
            [LLMMessage(role="user", content='Return JSON: {"ready": true}.')],
            SmokeResponse,
            model_tier=ModelTier.FAST,
        )
    except Exception as exc:  # noqa: BLE001 - CLI reports safe error type only
        print(f"Groq smoke test failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(
        f"provider={result.provider} model={result.model} latency_ms={result.latency_ms} usage={result.usage}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
