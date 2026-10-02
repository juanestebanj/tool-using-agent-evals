"""Named evaluation cases for tool-using agent behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvalCase:
    """Expected deterministic trajectory and answer properties for one agent task."""

    id: str
    prompt: str
    required_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    expected_arguments: dict[str, dict[str, Any]]
    ordered_tools: tuple[str, ...]
    answer_required_evidence: tuple[tuple[str, ...], ...] = ()
    answer_forbidden_evidence: tuple[str, ...] = ()


DUPLICATE_CHARGE_CASE = EvalCase(
    id="duplicate-charge",
    prompt="I think invoice INV-1042 was charged twice.",
    required_tools=("check_payment",),
    forbidden_tools=("get_customer", "get_invoice"),
    expected_arguments={
        "check_payment": {"invoice_id": "INV-1042"},
    },
    ordered_tools=("check_payment",),
    answer_required_evidence=(
        ("INV-1042",),
        ("charged twice", "duplicate charge"),
        ("two successful", "2 successful"),
    ),
    answer_forbidden_evidence=("no duplicate", "not charged twice"),
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
    answer_required_evidence=(
        ("INV-2001",),
        ("one successful payment", "1 successful payment", "no duplicate"),
    ),
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
    answer_required_evidence=(
        ("INV-1043",),
        ("failed", "not successful", "no successful payment"),
    ),
    answer_forbidden_evidence=("payment was successful", "payment succeeded"),
)

MISSING_INVOICE_ID_CASE = EvalCase(
    id="missing-invoice-id",
    prompt="I think I was charged twice.",
    required_tools=(),
    forbidden_tools=("get_customer", "get_invoice", "check_payment"),
    expected_arguments={},
    ordered_tools=(),
    answer_required_evidence=(
        ("invoice id", "invoice number", "invoice identifier"),
    ),
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
    answer_required_evidence=(
        ("INV-9999",),
        ("not found", "couldn't find", "couldn’t find", "could not be found", "cannot find", "does not exist"),
    ),
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
    answer_required_evidence=(
        ("INV-1043",),
        ("2026-10-15", "October 15, 2026", "Oct 15, 2026"),
    ),
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
    answer_required_evidence=(
        ("CUST-001",),
        ("active",),
    ),
    answer_forbidden_evidence=("inactive",),
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
