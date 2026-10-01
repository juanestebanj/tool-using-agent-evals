"""Deterministic aggregation for multiple evaluated agent reports."""

from __future__ import annotations

from typing import Any

from evals.cases import EvalCase
from evals.graders import evaluate_report


def evaluate_suite(
    reports: dict[str, dict[str, Any]],
    cases: dict[str, EvalCase],
) -> dict[str, Any]:
    """Grade every named report and aggregate regression-suite status."""
    case_results: list[dict[str, Any]] = []

    for case_id, case in cases.items():
        report = reports.get(case_id)
        if report is None:
            case_results.append(
                {
                    "case_id": case_id,
                    "passed": False,
                    "error": "missing_report",
                }
            )
            continue

        if report.get("error"):
            case_results.append(
                {
                    "case_id": case_id,
                    "prompt": case.prompt,
                    "passed": False,
                    "error": report["error"],
                    "report": report,
                }
            )
            continue

        evaluation = evaluate_report(report, case)
        case_results.append(
            {
                "case_id": case_id,
                "prompt": case.prompt,
                "report": report,
                "evaluation": evaluation,
                "passed": evaluation["passed"],
            }
        )

    passed_count = sum(1 for result in case_results if result["passed"])
    total_count = len(case_results)

    return {
        "passed": passed_count == total_count,
        "passed_count": passed_count,
        "failed_count": total_count - passed_count,
        "total_count": total_count,
        "cases": case_results,
    }
