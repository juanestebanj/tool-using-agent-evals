from agent.agent import (
    AGENT_INSTRUCTIONS,
    AGENT_NAME,
    DEFAULT_AGENT_MODEL,
    build_agent,
)


def test_build_agent_has_expected_identity():
    agent = build_agent()
    assert agent.name == AGENT_NAME
    assert agent.name == "Billing Support Agent"


def test_agent_uses_pinned_default_model():
    agent = build_agent()

    assert agent.model == DEFAULT_AGENT_MODEL
    assert agent.model == "gpt-6-luna"


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
    assert "do not invent external support channels" in instructions


def test_agent_instructions_define_tool_responsibilities():
    instructions = " ".join(AGENT_INSTRUCTIONS.lower().split())

    assert "narrowest tool" in instructions
    assert "get_customer for customer" in instructions
    assert "get_invoice for invoice metadata" in instructions
    assert "check_payment for payment" in instructions
    assert "verifies whether the invoice exists" in instructions
    assert "do not preflight payment questions with get_invoice" in instructions
    assert "do not call an additional tool" in instructions



def test_agent_instructions_define_concise_response_policy():
    instructions = " ".join(AGENT_INSTRUCTIONS.lower().split())

    assert "minimum wording needed" in instructions
    assert "prefer one sentence" in instructions
    assert "at most two short sentences" in instructions
    assert "do not restate the user's question" in instructions
    assert "repeat supporting facts that are not needed" in instructions
