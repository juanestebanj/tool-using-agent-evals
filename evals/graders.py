"""Deterministic graders for captured agent trajectories and outcomes."""

from __future__ import annotations

import unicodedata
from typing import Any

from evals.cases import EvalCase


def _tool_calls(trajectory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in trajectory if item.get("type") == "tool_call"]


def _normalize_text(value: str) -> str:
    """Normalize answer text enough for stable evidence matching."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.replace("’", "'").replace("‘", "'")
    return " ".join(normalized.split())


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


def grade_answer_outcome(
    final_output: Any,
    required_evidence: tuple[tuple[str, ...], ...],
    forbidden_evidence: tuple[str, ...],
) -> dict[str, Any]:
    """Check narrow factual evidence in the final natural-language answer.

    Each required evidence group is an OR condition: at least one phrase in the group
    must appear. Every group must pass. Forbidden phrases must not appear.
    """
    text = final_output if isinstance(final_output, str) else ""
    normalized = _normalize_text(text)

    missing_groups: list[list[str]] = []
    for alternatives in required_evidence:
        normalized_alternatives = [_normalize_text(item) for item in alternatives]
        if not any(item in normalized for item in normalized_alternatives):
            missing_groups.append(list(alternatives))

    found_forbidden = [
        phrase
        for phrase in forbidden_evidence
        if _normalize_text(phrase) in normalized
    ]

    return {
        "passed": bool(text) and not missing_groups and not found_forbidden,
        "required_evidence": [list(group) for group in required_evidence],
        "missing_evidence_groups": missing_groups,
        "forbidden_evidence": list(forbidden_evidence),
        "found_forbidden_evidence": found_forbidden,
    }


def evaluate_report(report: dict[str, Any], case: EvalCase) -> dict[str, Any]:
    """Run deterministic trajectory and outcome graders for one captured report."""
    trajectory = report.get("trajectory", [])

    checks = {
        "required_tools": grade_required_tools(trajectory, case.required_tools),
        "forbidden_tools": grade_forbidden_tools(trajectory, case.forbidden_tools),
        "exact_arguments": grade_exact_arguments(
            trajectory, case.expected_arguments
        ),
        "tool_order": grade_tool_order(trajectory, case.ordered_tools),
        "answer_outcome_smoke": grade_answer_outcome(
            report.get("final_output"),
            case.answer_required_evidence,
            case.answer_forbidden_evidence,
        ),
    }

    semantic_judgment = report.get("semantic_judgment")
    if semantic_judgment is not None:
        checks["semantic_outcome"] = semantic_judgment

    gating_check_names = [
        "required_tools",
        "forbidden_tools",
        "exact_arguments",
        "tool_order",
    ]

    if semantic_judgment is not None:
        gating_check_names.append("semantic_outcome")
    else:
        # Offline deterministic grading still has a useful fallback when no live
        # semantic judge result is available.
        gating_check_names.append("answer_outcome_smoke")

    return {
        "case_id": case.id,
        "passed": all(checks[name]["passed"] for name in gating_check_names),
        "gating_checks": gating_check_names,
        "checks": checks,
    }
