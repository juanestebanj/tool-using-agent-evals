"""Named evaluation cases for tool-using agent behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvalCase:
    """Expected deterministic trajectory properties for one agent task."""

    id: str
    prompt: str
    required_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    expected_arguments: dict[str, dict[str, Any]]
    ordered_tools: tuple[str, ...]


DUPLICATE_CHARGE_CASE = EvalCase(
    id="duplicate-charge",
    prompt="I think invoice INV-1042 was charged twice.",
    required_tools=("check_payment",),
    forbidden_tools=("get_customer", "get_invoice"),
    expected_arguments={
        "check_payment": {"invoice_id": "INV-1042"},
    },
    ordered_tools=("check_payment",),
)

SINGLE_CHARGE_CASE = EvalCase(
    id="single-charge",
    prompt="Was invoice INV-2001 charged more than once?",
    required_tools=("check_payment",),
    forbidden_tools=("get_customer", "get_invoice"),
    expected_arguments={
        "check_payment": {"invoice_id": "INV-2001"},
    },
    ordered_tools=("check_payment",),
)

FAILED_PAYMENT_CASE = EvalCase(
    id="failed-payment",
    prompt="Was payment for invoice INV-1043 successful?",
    required_tools=("check_payment",),
    forbidden_tools=("get_customer", "get_invoice"),
    expected_arguments={
        "check_payment": {"invoice_id": "INV-1043"},
    },
    ordered_tools=("check_payment",),
)

MISSING_INVOICE_ID_CASE = EvalCase(
    id="missing-invoice-id",
    prompt="I think I was charged twice.",
    required_tools=(),
    forbidden_tools=("get_customer", "get_invoice", "check_payment"),
    expected_arguments={},
    ordered_tools=(),
)

UNKNOWN_INVOICE_CASE = EvalCase(
    id="unknown-invoice",
    prompt="I think invoice INV-9999 was charged twice.",
    required_tools=("check_payment",),
    forbidden_tools=("get_customer", "get_invoice"),
    expected_arguments={
        "check_payment": {"invoice_id": "INV-9999"},
    },
    ordered_tools=("check_payment",),
)

INVOICE_DUE_DATE_CASE = EvalCase(
    id="invoice-due-date",
    prompt="When is invoice INV-1043 due?",
    required_tools=("get_invoice",),
    forbidden_tools=("get_customer", "check_payment"),
    expected_arguments={
        "get_invoice": {"invoice_id": "INV-1043"},
    },
    ordered_tools=("get_invoice",),
)

CUSTOMER_STATUS_CASE = EvalCase(
    id="customer-status",
    prompt="Is customer CUST-001 active?",
    required_tools=("get_customer",),
    forbidden_tools=("get_invoice", "check_payment"),
    expected_arguments={
        "get_customer": {"customer_id": "CUST-001"},
    },
    ordered_tools=("get_customer",),
)

CASES: dict[str, EvalCase] = {
    case.id: case
    for case in (
        DUPLICATE_CHARGE_CASE,
        SINGLE_CHARGE_CASE,
        FAILED_PAYMENT_CASE,
        MISSING_INVOICE_ID_CASE,
        UNKNOWN_INVOICE_CASE,
        INVOICE_DUE_DATE_CASE,
        CUSTOMER_STATUS_CASE,
    )
}
