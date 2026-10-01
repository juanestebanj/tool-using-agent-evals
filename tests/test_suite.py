from evals.cases import (
    CASES,
    DUPLICATE_CHARGE_CASE,
    MISSING_INVOICE_ID_CASE,
    UNKNOWN_INVOICE_CASE,
)
from evals.suite import evaluate_suite


def _report(*calls):
    return {
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


def test_case_registry_contains_contrasting_scenarios():
    assert set(CASES) == {
        "duplicate-charge",
        "single-charge",
        "failed-payment",
        "missing-invoice-id",
        "unknown-invoice",
    }


def test_missing_identifier_case_forbids_guessing_with_tools():
    assert MISSING_INVOICE_ID_CASE.required_tools == ()
    assert set(MISSING_INVOICE_ID_CASE.forbidden_tools) == {
        "get_customer",
        "get_invoice",
        "check_payment",
    }


def test_unknown_invoice_case_stops_after_invoice_lookup():
    assert UNKNOWN_INVOICE_CASE.required_tools == ("get_invoice",)
    assert "check_payment" in UNKNOWN_INVOICE_CASE.forbidden_tools


def test_evaluate_suite_aggregates_passing_cases():
    cases = {
        DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE,
        MISSING_INVOICE_ID_CASE.id: MISSING_INVOICE_ID_CASE,
    }
    reports = {
        "duplicate-charge": _report(
            ("get_invoice", {"invoice_id": "INV-1042"}),
            ("check_payment", {"invoice_id": "INV-1042"}),
        ),
        "missing-invoice-id": _report(),
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
