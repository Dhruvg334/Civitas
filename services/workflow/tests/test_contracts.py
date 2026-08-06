from civitas_workflow.contracts import WorkflowInput


def test_workflow_input_contract() -> None:
    payload = WorkflowInput(report_id="RPT-001")
    assert payload.evidence == {}
