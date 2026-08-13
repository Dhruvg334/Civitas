from pathlib import Path

import pytest

from civitas_workflow.prompts import PromptLoader

PROMPT_ROOT = Path(__file__).resolve().parents[3] / "prompts"


def test_versioned_prompt_assets_are_loadable() -> None:
    text = PromptLoader(PROMPT_ROOT).load("knowledge/grounded-policy-use-v1.md")
    assert "INSUFFICIENT_KNOWLEDGE" in text
    assert "reference_id" in text


def test_prompt_loader_rejects_path_escape() -> None:
    with pytest.raises(ValueError):
        PromptLoader(PROMPT_ROOT).load("../README.md")
