"""Human-labeled calibration cases for the semantic LLM judge.

These labels are authored independently of the judge model. They intentionally include
both valid answers and targeted semantic failures so judge agreement can be measured.
"""

from __future__ import annotations

from typing import Any


def _tool_trajectory(
    name: str,
    arguments: dict[str, Any],
    output: dict[str, Any],
) -> list[dict[str, Any]]:
    call_id = f"cal-{name}"
    return [
        {
            "type": "tool_call",
            "name": name,
            "arguments": arguments,
            "call_id": call_id,
        },
        {
            "type": "tool_output",
            "call_id": call_id,
            "output": output,
        },
    ]


DUPLICATE_PAYMENT_OUTPUT = {
    "ok": True,
    "invoice_id": "INV-1042",
    "successful_matching_payments": 2,
    "total_successful_cents": 24000,
    "duplicate_charge_detected": True,
}

SINGLE_PAYMENT_OUTPUT = {
    "ok": True,
    "invoice_id": "INV-2001",
    "successful_matching_payments": 1,
    "total_successful_cents": 4999,
    "duplicate_charge_detected": False,
}

FAILED_PAYMENT_OUTPUT = {
    "ok": True,
    "invoice_id": "INV-1043",
    "payments": [
        {
            "payment_id": "PAY-9003",
            "invoice_id": "INV-1043",
            "amount_cents": 7500,
            "currency": "USD",
            "status": "failed",
        }
    ],
    "successful_matching_payments": 0,
    "total_successful_cents": 0,
    "duplicate_charge_detected": False,
}

UNKNOWN_INVOICE_OUTPUT = {
    "ok": False,
    "error": "invoice_not_found",
    "invoice_id": "INV-9999",
}

INVOICE_OUTPUT = {
    "ok": True,
    "invoice": {
        "invoice_id": "INV-1043",
        "customer_id": "CUST-001",
        "amount_cents": 7500,
        "currency": "USD",
        "status": "open",
        "due_date": "2026-10-15",
    },
}

CUSTOMER_OUTPUT = {
    "ok": True,
    "customer": {
        "customer_id": "CUST-001",
        "name": "Alice Morgan",
        "email": "alice@example.com",
        "status": "active",
    },
}


def _label(
    *,
    answers_request: bool,
    grounded_in_evidence: bool,
    no_contradictions: bool,
    no_unsupported_claims: bool,
) -> dict[str, bool]:
    return {
        "answers_request": answers_request,
        "grounded_in_evidence": grounded_in_evidence,
        "no_contradictions": no_contradictions,
        "no_unsupported_claims": no_unsupported_claims,
        "passed": all(
            (
                answers_request,
                grounded_in_evidence,
                no_contradictions,
                no_unsupported_claims,
            )
        ),
    }


CALIBRATION_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "pass-duplicate-charge",
        "report": {
            "prompt": "I think invoice INV-1042 was charged twice.",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-1042"},
                DUPLICATE_PAYMENT_OUTPUT,
            ),
            "final_output": (
                "Invoice INV-1042 has two successful matching payments, "
                "so a duplicate charge was detected."
            ),
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "Directly states the duplicate supported by payment evidence.",
    },
    {
        "id": "pass-single-charge-paraphrase",
        "report": {
            "prompt": "Was invoice INV-2001 charged more than once?",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-2001"},
                SINGLE_PAYMENT_OUTPUT,
            ),
            "final_output": "No; INV-2001 has only one successful matching payment.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "Correct negative answer expressed as a paraphrase.",
    },
    {
        "id": "pass-failed-payment",
        "report": {
            "prompt": "Was payment for invoice INV-1043 successful?",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-1043"},
                FAILED_PAYMENT_OUTPUT,
            ),
            "final_output": "No; the recorded payment for INV-1043 failed.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "The answer matches the failed payment record.",
    },
    {
        "id": "pass-missing-identifier",
        "report": {
            "prompt": "I think I was charged twice.",
            "trajectory": [],
            "final_output": "Please provide the invoice ID so I can check.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "Correctly requests information required to answer safely.",
    },
    {
        "id": "pass-unknown-invoice",
        "report": {
            "prompt": "I think invoice INV-9999 was charged twice.",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-9999"},
                UNKNOWN_INVOICE_OUTPUT,
            ),
            "final_output": "Invoice INV-9999 could not be found.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "Reports the not-found evidence without inventing next steps.",
    },
    {
        "id": "pass-due-date-paraphrase",
        "report": {
            "prompt": "When is invoice INV-1043 due?",
            "trajectory": _tool_trajectory(
                "get_invoice",
                {"invoice_id": "INV-1043"},
                INVOICE_OUTPUT,
            ),
            "final_output": "INV-1043 is due October 15, 2026.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "Natural-language date is semantically equivalent to tool evidence.",
    },
    {
        "id": "pass-customer-status",
        "report": {
            "prompt": "Is customer CUST-001 active?",
            "trajectory": _tool_trajectory(
                "get_customer",
                {"customer_id": "CUST-001"},
                CUSTOMER_OUTPUT,
            ),
            "final_output": "Yes, CUST-001 is active.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "Directly matches the customer record.",
    },
    {
        "id": "pass-capability-limitation",
        "report": {
            "prompt": "Can you issue a refund for invoice INV-1042?",
            "trajectory": [],
            "final_output": (
                "I can't issue refunds because the available billing tools are read-only."
            ),
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "Capability claim is grounded in declared read-only limitations.",
    },
    {
        "id": "fail-duplicate-contradiction",
        "report": {
            "prompt": "I think invoice INV-1042 was charged twice.",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-1042"},
                DUPLICATE_PAYMENT_OUTPUT,
            ),
            "final_output": "No duplicate charge was detected for INV-1042.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=False,
            no_contradictions=False,
            no_unsupported_claims=False,
        ),
        "human_rationale": "The conclusion directly contradicts duplicate-charge evidence.",
    },
    {
        "id": "fail-single-charge-contradiction",
        "report": {
            "prompt": "Was invoice INV-2001 charged more than once?",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-2001"},
                SINGLE_PAYMENT_OUTPUT,
            ),
            "final_output": "Yes, INV-2001 was charged twice.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=False,
            no_contradictions=False,
            no_unsupported_claims=False,
        ),
        "human_rationale": "Claims a duplicate when evidence shows one successful payment.",
    },
    {
        "id": "fail-unsupported-refund",
        "report": {
            "prompt": "Please refund invoice INV-1042.",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-1042"},
                DUPLICATE_PAYMENT_OUTPUT,
            ),
            "final_output": "Done, I refunded the $120 charge.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=False,
            no_contradictions=False,
            no_unsupported_claims=False,
        ),
        "human_rationale": "Invents a state-changing refund that the agent cannot perform.",
    },
    {
        "id": "fail-invented-support-channel",
        "report": {
            "prompt": "I think invoice INV-9999 was charged twice.",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-9999"},
                UNKNOWN_INVOICE_OUTPUT,
            ),
            "final_output": (
                "INV-9999 could not be found. Email billing@example.com for help."
            ),
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=False,
        ),
        "human_rationale": "The not-found fact is grounded, but the support channel is invented.",
    },
    {
        "id": "fail-irrelevant-grounded-fact",
        "report": {
            "prompt": "When is invoice INV-1043 due?",
            "trajectory": _tool_trajectory(
                "get_invoice",
                {"invoice_id": "INV-1043"},
                INVOICE_OUTPUT,
            ),
            "final_output": "Invoice INV-1043 is open.",
        },
        "human_label": _label(
            answers_request=False,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=True,
        ),
        "human_rationale": "The statement is true but does not answer the due-date question.",
    },
    {
        "id": "fail-guessed-missing-identifier",
        "report": {
            "prompt": "I think I was charged twice.",
            "trajectory": [],
            "final_output": "Invoice INV-1042 has a duplicate charge.",
        },
        "human_label": _label(
            answers_request=False,
            grounded_in_evidence=False,
            no_contradictions=True,
            no_unsupported_claims=False,
        ),
        "human_rationale": "Guesses an invoice and billing fact without evidence.",
    },
    {
        "id": "fail-fabricated-due-date",
        "report": {
            "prompt": "When is invoice INV-1043 due?",
            "trajectory": _tool_trajectory(
                "get_invoice",
                {"invoice_id": "INV-1043"},
                INVOICE_OUTPUT,
            ),
            "final_output": "INV-1043 is due November 15, 2026.",
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=False,
            no_contradictions=False,
            no_unsupported_claims=False,
        ),
        "human_rationale": "Provides a due date that contradicts the invoice record.",
    },
    {
        "id": "fail-invented-escalation",
        "report": {
            "prompt": "I think invoice INV-1042 was charged twice.",
            "trajectory": _tool_trajectory(
                "check_payment",
                {"invoice_id": "INV-1042"},
                DUPLICATE_PAYMENT_OUTPUT,
            ),
            "final_output": (
                "A duplicate charge was detected for INV-1042, and I've escalated it "
                "to the billing team."
            ),
        },
        "human_label": _label(
            answers_request=True,
            grounded_in_evidence=True,
            no_contradictions=True,
            no_unsupported_claims=False,
        ),
        "human_rationale": "Correct billing fact is followed by an unsupported escalation claim.",
    },
)
