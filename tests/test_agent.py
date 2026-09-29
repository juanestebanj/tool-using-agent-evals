from agent.agent import AGENT_INSTRUCTIONS, AGENT_NAME, build_agent


def test_build_agent_has_expected_identity():
    agent = build_agent()
    assert agent.name == AGENT_NAME
    assert agent.name == "Billing Support Agent"


def test_agent_registers_expected_tools():
    agent = build_agent()
    tool_names = {tool.name for tool in agent.tools}

    assert tool_names == {"get_customer", "get_invoice", "check_payment"}


def test_agent_instructions_require_grounded_tool_use():
    instructions = AGENT_INSTRUCTIONS.lower()

    assert "source of truth" in instructions
    assert "do not invent" in instructions
    assert "do not claim a duplicate charge unless" in instructions
    assert "read-only" in instructions
