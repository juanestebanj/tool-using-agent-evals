"""Deterministic graders for captured agent trajectories."""

from __future__ import annotations

from typing import Any

from evals.cases import EvalCase


def _tool_calls(trajectory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in trajectory if item.get("type") == "tool_call"]


def grade_required_tools(
    trajectory: list[dict[str, Any]], required_tools: tuple[str, ...]
) -> dict[str, Any]:
    """Check that every required tool appears at least once."""
    actual = [call.get("name") for call in _tool_calls(trajectory)]
    missing = [name for name in required_tools if name not in actual]
    return {
        "passed": not missing,
        "expected": list(required_tools),
        "actual": actual,
        "missing": missing,
    }


def grade_forbidden_tools(
    trajectory: list[dict[str, Any]], forbidden_tools: tuple[str, ...]
) -> dict[str, Any]:
    """Check that forbidden tools are never called."""
    actual = [call.get("name") for call in _tool_calls(trajectory)]
    unexpected = [name for name in actual if name in forbidden_tools]
    return {
        "passed": not unexpected,
        "forbidden": list(forbidden_tools),
        "actual": actual,
        "unexpected": unexpected,
    }


def grade_exact_arguments(
    trajectory: list[dict[str, Any]],
    expected_arguments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Check that each named tool is called at least once with exact expected arguments."""
    calls = _tool_calls(trajectory)
    failures: list[dict[str, Any]] = []

    for tool_name, expected in expected_arguments.items():
        matching_calls = [call for call in calls if call.get("name") == tool_name]
        if not matching_calls:
            failures.append(
                {
                    "tool": tool_name,
                    "reason": "tool_not_called",
                    "expected": expected,
                    "actual": [],
                }
            )
            continue

        actual_arguments = [call.get("arguments") for call in matching_calls]
        if expected not in actual_arguments:
            failures.append(
                {
                    "tool": tool_name,
                    "reason": "arguments_mismatch",
                    "expected": expected,
                    "actual": actual_arguments,
                }
            )

    return {
        "passed": not failures,
        "expected": expected_arguments,
        "failures": failures,
    }


def grade_tool_order(
    trajectory: list[dict[str, Any]], ordered_tools: tuple[str, ...]
) -> dict[str, Any]:
    """Check that expected tools appear in order as a subsequence of tool calls."""
    actual = [call.get("name") for call in _tool_calls(trajectory)]

    cursor = 0
    for name in actual:
        if cursor < len(ordered_tools) and name == ordered_tools[cursor]:
            cursor += 1

    passed = cursor == len(ordered_tools)
    return {
        "passed": passed,
        "expected_order": list(ordered_tools),
        "actual": actual,
    }


def evaluate_report(report: dict[str, Any], case: EvalCase) -> dict[str, Any]:
    """Run all deterministic trajectory graders for one captured agent report."""
    trajectory = report.get("trajectory", [])

    checks = {
        "required_tools": grade_required_tools(trajectory, case.required_tools),
        "forbidden_tools": grade_forbidden_tools(trajectory, case.forbidden_tools),
        "exact_arguments": grade_exact_arguments(
            trajectory, case.expected_arguments
        ),
        "tool_order": grade_tool_order(trajectory, case.ordered_tools),
    }

    return {
        "case_id": case.id,
        "passed": all(check["passed"] for check in checks.values()),
        "checks": checks,
    }
