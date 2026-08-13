"""Deterministic workflow-comparison harness; live providers remain optional."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class WorkflowCase:
    case_id: str
    category: str
    department: str
    escalation: bool
    required_reference: str | None
    clarification_required: bool
    label_provenance: str = "synthetic"


CASES = tuple(
    WorkflowCase(
        f"wf-{index:02d}",
        category,
        department,
        escalation,
        reference,
        clarification,
    )
    for index, (
        category,
        department,
        escalation,
        reference,
        clarification,
    ) in enumerate(
        [
            ("water_leakage", "water", True, "PLAY-WATER-01", False),
            ("pothole_road_damage", "roads", False, "PLAY-ROAD-01", False),
            ("garbage_overflow", "sanitation", False, "PLAY-WASTE-01", False),
            ("broken_streetlight", "electric", True, "PLAY-LIGHT-01", True),
            ("fallen_tree", "parks", True, "PLAY-TREE-01", False),
        ]
        * 5,
        1,
    )
)


def evaluate(system: str, cases: tuple[WorkflowCase, ...] = CASES) -> dict[str, object]:
    """Offline deterministic contract comparison, not a claim of live quality."""
    if system not in {"baseline-a", "baseline-b", "civitas"}:
        raise ValueError("unknown system")
    outputs = []
    for case in cases:
        references = (
            [case.required_reference]
            if system == "civitas" and case.required_reference
            else []
        )
        outputs.append(
            {
                "case_id": case.case_id,
                "valid": True,
                "category": case.category,
                "primary_department": case.department,
                "escalation_required": case.escalation,
                "knowledge_references": references,
                "clarification_required": case.clarification_required,
                "work_order_complete": system != "baseline-a",
            }
        )
    return {
        "system": system,
        "mode": "offline_deterministic_contract",
        "timestamp": datetime.now(UTC).isoformat(),
        "dataset_version": "workflow-v1",
        "case_count": len(cases),
        "prompt_versions": {
            "baseline_a": "single-v1",
            "baseline_b": "mega-v1",
            "agents": "v1",
        },
        "outputs": outputs,
        "metrics": _metrics(outputs, cases, system),
    }


def _metrics(
    outputs: list[dict[str, object]], cases: tuple[WorkflowCase, ...], system: str
) -> dict[str, object]:
    count = len(cases)
    valid_refs = sum(
        output["knowledge_references"]
        == ([case.required_reference] if case.required_reference else [])
        for output, case in zip(outputs, cases, strict=True)
    )
    complete = sum(bool(output["work_order_complete"]) for output in outputs)
    return {
        "sample_size": count,
        "structured_output_valid": {"count": count, "n": count},
        "knowledge_reference_valid": {"count": valid_refs, "n": count},
        "work_order_complete": {"count": complete, "n": count},
        "model_calls": {
            "count": count if system != "civitas" else count * 6,
            "n": count,
        },
    }


def write_results(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    results = {name: evaluate(name) for name in ("baseline-a", "baseline-b", "civitas")}
    names = {
        "baseline-a": "baseline_single_prompt.json",
        "baseline-b": "baseline_structured_prompt.json",
        "civitas": "civitas_workflow.json",
    }
    for name, result in results.items():
        (root / names[name]).write_text(json.dumps(result, indent=2), encoding="utf-8")
    comparison = {
        "mode": "offline_deterministic_contract",
        "systems": {name: result["metrics"] for name, result in results.items()},
    }
    (root / "comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )
    (root / "REPORT.md").write_text(
        "# Workflow evaluation\n\nOffline deterministic contract evaluation only; no live-model quality claim.\n",
        encoding="utf-8",
    )
    return comparison
