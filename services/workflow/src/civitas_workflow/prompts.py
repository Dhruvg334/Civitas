"""Safe loader for versioned prompt assets."""

from __future__ import annotations

from pathlib import Path


class PromptLoader:
    def __init__(self, prompt_root: Path) -> None:
        self.prompt_root = prompt_root.resolve()

    def load(self, relative_path: str) -> str:
        target = (self.prompt_root / relative_path).resolve()
        if target != self.prompt_root and self.prompt_root not in target.parents:
            raise ValueError("prompt path must remain inside the configured prompt root")
        if target.suffix != ".md":
            raise ValueError("prompt assets must be Markdown files")
        return target.read_text(encoding="utf-8")
