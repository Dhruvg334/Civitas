from pathlib import Path

from civitas_evaluation.workflow_eval import CASES, evaluate, write_results


def test_dataset_has_all_five_categories_and_unique_ids() -> None:
    assert len(CASES) == 25
    assert len({case.case_id for case in CASES}) == len(CASES)
    assert len({case.category for case in CASES}) == 5


def test_offline_comparison_is_serializable(tmp_path: Path) -> None:
    result = evaluate("civitas")
    assert result["case_count"] == 25
    comparison = write_results(tmp_path / "workflow")
    assert comparison["mode"] == "offline_deterministic_contract"
