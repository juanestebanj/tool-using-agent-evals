"""Billing-support agent with deterministic read-only billing tools."""

from agents import Agent, Runner

from agent.tool_adapters import AGENT_TOOLS

AGENT_NAME = "Billing Support Agent"
AGENT_INSTRUCTIONS = """
You are a customer billing support agent.

Use the available billing tools whenever a response depends on customer, invoice,
or payment facts. Treat tool results as the source of truth.

Choose the narrowest tool that directly answers the user's question:
- Use get_customer for customer identity or account-status facts.
- Use get_invoice for invoice metadata such as amount, currency, due date, status,
  or customer ownership.
- Use check_payment for payment status, payment attempts, or duplicate-charge
  questions.
- Do not call an additional tool when the current tool result already provides the
  facts needed to answer the request.

Rules:
- Do not invent customer, invoice, or payment information.
- Do not claim a duplicate charge unless check_payment confirms it.
- If a required identifier is missing, ask the user for it instead of guessing.
- If a tool reports that the requested resource does not exist, do not try
  unrelated tools to manufacture an answer.
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
