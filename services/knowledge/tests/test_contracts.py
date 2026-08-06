from civitas_knowledge.contracts import PolicyReference


def test_policy_reference_contract() -> None:
    policy = PolicyReference(policy_id="POL-001", title="Water leaks", excerpt="Route to water services.", source="playbook")
    assert policy.policy_id == "POL-001"
