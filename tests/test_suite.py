from evals.cases import (
    CASES,
    CUSTOMER_STATUS_CASE,
    DUPLICATE_CHARGE_CASE,
    INVOICE_DUE_DATE_CASE,
    MISSING_INVOICE_ID_CASE,
    UNKNOWN_INVOICE_CASE,
)
from evals.suite import evaluate_suite


def _report(*calls, final_output: str):
    return {
        "final_output": final_output,
        "trajectory": [
            {
                "type": "tool_call",
                "name": name,
                "arguments": arguments,
                "call_id": f"call-{index}",
            }
            for index, (name, arguments) in enumerate(calls, start=1)
        ]
    }


def test_case_registry_contains_contrasting_routing_scenarios():
    assert set(CASES) == {
        "duplicate-charge",
        "single-charge",
        "failed-payment",
        "missing-invoice-id",
        "unknown-invoice",
        "invoice-due-date",
        "customer-status",
    }


def test_payment_case_uses_payment_tool_without_redundant_invoice_lookup():
    assert DUPLICATE_CHARGE_CASE.required_tools == ("check_payment",)
    assert "get_invoice" in DUPLICATE_CHARGE_CASE.forbidden_tools
    assert DUPLICATE_CHARGE_CASE.expected_arguments == {
        "check_payment": {"invoice_id": "INV-1042"}
    }


def test_missing_identifier_case_forbids_guessing_with_tools():
    assert MISSING_INVOICE_ID_CASE.required_tools == ()
    assert set(MISSING_INVOICE_ID_CASE.forbidden_tools) == {
        "get_customer",
        "get_invoice",
        "check_payment",
    }


def test_unknown_invoice_case_uses_payment_tool_and_stops_on_not_found():
    assert UNKNOWN_INVOICE_CASE.required_tools == ("check_payment",)
    assert set(UNKNOWN_INVOICE_CASE.forbidden_tools) == {
        "get_customer",
        "get_invoice",
    }


def test_invoice_metadata_case_routes_to_get_invoice():
    assert INVOICE_DUE_DATE_CASE.required_tools == ("get_invoice",)
    assert set(INVOICE_DUE_DATE_CASE.forbidden_tools) == {
        "get_customer",
        "check_payment",
    }


def test_customer_status_case_routes_to_get_customer():
    assert CUSTOMER_STATUS_CASE.required_tools == ("get_customer",)
    assert set(CUSTOMER_STATUS_CASE.forbidden_tools) == {
        "get_invoice",
        "check_payment",
    }


def test_evaluate_suite_aggregates_passing_cases():
    cases = {
        DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE,
        MISSING_INVOICE_ID_CASE.id: MISSING_INVOICE_ID_CASE,
    }
    reports = {
        "duplicate-charge": _report(
            ("check_payment", {"invoice_id": "INV-1042"}),
            final_output=(
                "Invoice INV-1042 was charged twice. "
                "Two successful payments were recorded."
            ),
        ),
        "missing-invoice-id": _report(
            final_output="Please provide the invoice ID."
        ),
    }

    result = evaluate_suite(reports, cases)

    assert result["passed"] is True
    assert result["passed_count"] == 2
    assert result["failed_count"] == 0


def test_evaluate_suite_marks_missing_report_as_failure():
    cases = {DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE}

    result = evaluate_suite({}, cases)

    assert result["passed"] is False
    assert result["failed_count"] == 1
    assert result["cases"][0]["error"] == "missing_report"


def test_evaluate_suite_marks_execution_error_as_failure():
    cases = {DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE}
    reports = {
        "duplicate-charge": {
            "prompt": DUPLICATE_CHARGE_CASE.prompt,
            "trajectory": [],
            "error": {"type": "RuntimeError", "message": "model unavailable"},
        }
    }

    result = evaluate_suite(reports, cases)

    assert result["passed"] is False
    assert result["cases"][0]["error"]["type"] == "RuntimeError"
