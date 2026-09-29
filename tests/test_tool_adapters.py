from agent.tool_adapters import AGENT_TOOLS


def test_tool_adapters_have_stable_names():
    assert [tool.name for tool in AGENT_TOOLS] == [
        "get_customer",
        "get_invoice",
        "check_payment",
    ]


def test_tool_adapters_have_descriptions_for_model_selection():
    for tool in AGENT_TOOLS:
        assert tool.description
        assert len(tool.description.strip()) > 20
