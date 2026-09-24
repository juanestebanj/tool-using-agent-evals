from agent.agent import AGENT_INSTRUCTIONS, AGENT_NAME, build_agent


def test_build_agent_has_expected_identity():
    agent = build_agent()
    assert agent.name == AGENT_NAME
    assert agent.name == "Billing Support Agent"


def test_baseline_instructions_require_factual_behavior():
    instructions = AGENT_INSTRUCTIONS.lower()
    assert "do not invent" in instructions
    assert "billing" in instructions
