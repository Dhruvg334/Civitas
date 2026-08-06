from civitas_evaluation.contracts import EvaluationCase


def test_evaluation_case_contract() -> None:
    case = EvaluationCase(case_id="CASE-001", input_payload={}, expected_output={})
    assert case.tags == []
