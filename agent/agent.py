"""Billing-support agent with deterministic read-only billing tools."""

from agents import Agent, Runner

from agent.tool_adapters import AGENT_TOOLS

AGENT_NAME = "Billing Support Agent"
AGENT_INSTRUCTIONS = """
You are a customer billing support agent.

Use the available billing tools whenever a response depends on customer, invoice,
or payment facts. Treat tool results as the source of truth.

Rules:
- Do not invent customer, invoice, or payment information.
- If the user provides an invoice ID, inspect the relevant invoice before making
  factual claims about it.
- For duplicate-charge questions, inspect payment activity before concluding that a
  duplicate exists.
- Do not claim a duplicate charge unless the tool result confirms it.
- If a required identifier is missing, ask the user for it instead of guessing.
- The available tools are read-only. Do not imply that you changed billing state,
  issued a refund, or performed another write action.

Be concise and factual.
""".strip()


def build_agent() -> Agent:
    """Create the tool-using billing support agent without executing a model call."""
    return Agent(
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        tools=AGENT_TOOLS,
    )


def main() -> None:
    """Run one live tool-using interaction. Requires OPENAI_API_KEY."""
    agent = build_agent()
    result = Runner.run_sync(
        agent,
        "I think invoice INV-1042 was charged twice.",
    )
    print(result.final_output)


if __name__ == "__main__":
    main()
