from ai_dojo.flows.implementation_flow import ImplementationFlow


def test_implementation_flow_build_inputs_uses_expected_contract_keys():
    flow = ImplementationFlow()
    flow.state["issue"] = "Add contract testing for each crew factory"
    flow.state["current_year"] = "2026"

    assert flow._build_inputs() == {
        "issue": "Add contract testing for each crew factory",
        "idea": "Add contract testing for each crew factory",
        "topic": "Add contract testing for each crew factory",
        "current_year": "2026",
    }


def test_implementation_flow_defaults_to_revision_limit_and_state_dict():
    flow = ImplementationFlow()

    assert flow.max_revisions == 2
    assert isinstance(flow.state, dict)
