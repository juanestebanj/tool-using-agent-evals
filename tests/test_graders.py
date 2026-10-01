from evals.cases import DUPLICATE_CHARGE_CASE
from evals.graders import (
    evaluate_report,
    grade_exact_arguments,
    grade_forbidden_tools,
    grade_required_tools,
    grade_tool_order,
)


def _trajectory(*calls):
    return [
        {
            "type": "tool_call",
            "name": name,
            "arguments": arguments,
            "call_id": f"call-{index}",
        }
        for index, (name, arguments) in enumerate(calls, start=1)
    ]


def test_duplicate_charge_case_passes_expected_trajectory():
    report = {
        "trajectory": _trajectory(
            ("check_payment", {"invoice_id": "INV-1042"}),
        )
    }

    result = evaluate_report(report, DUPLICATE_CHARGE_CASE)

    assert result["passed"] is True
    assert all(check["passed"] for check in result["checks"].values())


def test_required_tools_reports_missing_tool():
    result = grade_required_tools(
        _trajectory(("get_invoice", {"invoice_id": "INV-1042"})),
        ("get_invoice", "check_payment"),
    )

    assert result["passed"] is False
    assert result["missing"] == ["check_payment"]


def test_forbidden_tools_detects_unnecessary_customer_lookup():
    result = grade_forbidden_tools(
        _trajectory(
            ("get_invoice", {"invoice_id": "INV-1042"}),
            ("get_customer", {"customer_id": "CUST-001"}),
        ),
        ("get_customer",),
    )

    assert result["passed"] is False
    assert result["unexpected"] == ["get_customer"]


def test_exact_arguments_detects_wrong_invoice_id():
    result = grade_exact_arguments(
        _trajectory(("check_payment", {"invoice_id": "INV-1043"})),
        {"check_payment": {"invoice_id": "INV-1042"}},
    )

    assert result["passed"] is False
    assert result["failures"][0]["reason"] == "arguments_mismatch"


def test_tool_order_detects_reversed_calls():
    result = grade_tool_order(
        _trajectory(
            ("check_payment", {"invoice_id": "INV-1042"}),
            ("get_invoice", {"invoice_id": "INV-1042"}),
        ),
        ("get_invoice", "check_payment"),
    )

    assert result["passed"] is False


def test_tool_order_allows_unrelated_non_forbidden_calls_between_expected_tools():
    result = grade_tool_order(
        _trajectory(
            ("get_invoice", {"invoice_id": "INV-1042"}),
            ("some_other_tool", {}),
            ("check_payment", {"invoice_id": "INV-1042"}),
        ),
        ("get_invoice", "check_payment"),
    )

    assert result["passed"] is True
