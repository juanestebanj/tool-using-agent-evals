"""Minimal billing-support agent used as the baseline for later tool-use evals."""

from agents import Agent, Runner

AGENT_NAME = "Billing Support Agent"
AGENT_INSTRUCTIONS = """
You are a customer billing support agent.

Help customers resolve billing and payment questions.
Be concise and factual.
Do not invent customer, invoice, or payment information.
""".strip()


def build_agent() -> Agent:
    """Create the baseline agent without executing a model call."""
    return Agent(name=AGENT_NAME, instructions=AGENT_INSTRUCTIONS)


def main() -> None:
    """Run one live baseline interaction. Requires OPENAI_API_KEY."""
    agent = build_agent()
    result = Runner.run_sync(
        agent,
        "Hello. I think I was charged twice for an invoice.",
    )
    print(result.final_output)


if __name__ == "__main__":
    main()
