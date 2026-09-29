"""LLM-facing adapters for deterministic billing functions.

This module is intentionally thin: it exposes deterministic business logic from
`agent.tools` to the OpenAI Agents SDK without moving business rules into the
probabilistic orchestration layer.
"""

from typing import Any

from agents.decorators import tool

from agent import tools as billing_tools


@tool
def get_customer(customer_id: str) -> dict[str, Any]:
    """Look up a customer by customer ID.

    Use this when a billing request depends on customer identity or account status.
    """
    return billing_tools.get_customer(customer_id)


@tool
def get_invoice(invoice_id: str) -> dict[str, Any]:
    """Look up an invoice by invoice ID.

    Use this when a request depends on invoice ownership, amount, currency, due date,
    or invoice status.
    """
    return billing_tools.get_invoice(invoice_id)


@tool
def check_payment(invoice_id: str) -> dict[str, Any]:
    """Inspect payments for an invoice and detect duplicate successful charges.

    Use this for questions about whether an invoice was paid, charged more than once,
    or has failed payment attempts.
    """
    return billing_tools.check_payment(invoice_id)


AGENT_TOOLS = [get_customer, get_invoice, check_payment]
