"""Deterministic billing tools.

These functions contain no model calls and no external I/O. Keeping them pure makes
their behavior cheap, repeatable, and easy to isolate from agent-orchestration errors.
"""

from copy import deepcopy
from typing import Any

from agent.data import CUSTOMERS, INVOICES, PAYMENTS


def _not_found(resource: str, identifier_name: str, identifier: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": f"{resource}_not_found",
        identifier_name: identifier,
    }


def get_customer(customer_id: str) -> dict[str, Any]:
    """Return a customer record by ID, or a stable not-found result."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return _not_found("customer", "customer_id", customer_id)

    return {
        "ok": True,
        "customer": deepcopy(customer),
    }


def get_invoice(invoice_id: str) -> dict[str, Any]:
    """Return an invoice record by ID, or a stable not-found result."""
    invoice = INVOICES.get(invoice_id)
    if invoice is None:
        return _not_found("invoice", "invoice_id", invoice_id)

    return {
        "ok": True,
        "invoice": deepcopy(invoice),
    }


def check_payment(invoice_id: str) -> dict[str, Any]:
    """Summarize payment activity for an invoice and flag duplicate successful charges.

    A duplicate charge is detected when more than one successful payment matches the
    invoice amount and currency. Failed payments do not count toward the duplicate.
    """
    invoice = INVOICES.get(invoice_id)
    if invoice is None:
        return _not_found("invoice", "invoice_id", invoice_id)

    invoice_payments = [
        deepcopy(payment)
        for payment in PAYMENTS
        if payment["invoice_id"] == invoice_id
    ]

    successful_matches = [
        payment
        for payment in invoice_payments
        if payment["status"] == "succeeded"
        and payment["amount_cents"] == invoice["amount_cents"]
        and payment["currency"] == invoice["currency"]
    ]

    return {
        "ok": True,
        "invoice_id": invoice_id,
        "payments": invoice_payments,
        "successful_matching_payments": len(successful_matches),
        "total_successful_cents": sum(
            payment["amount_cents"] for payment in successful_matches
        ),
        "duplicate_charge_detected": len(successful_matches) > 1,
    }
