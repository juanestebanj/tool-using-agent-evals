"""Deterministic aggregation for repeated live evaluation trials."""

from __future__ import annotations

from typing import Any

from evals.cases import EvalCase
from evals.graders import evaluate_report
from evals.metrics import aggregate_benchmark_metrics


def evaluate_trial(
    *,
    case: EvalCase,
    trial_number: int,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Grade one captured trial while preserving execution failures."""
    if report.get("error"):
        return {
            "trial": trial_number,
            "passed": False,
            "error": report["error"],
            "report": report,
        }

    evaluation = evaluate_report(report, case)
    return {
        "trial": trial_number,
        "passed": evaluation["passed"],
        "evaluation": evaluation,
        "report": report,
    }


def build_benchmark_report(
    trial_results: dict[str, list[dict[str, Any]]],
    cases: dict[str, EvalCase],
    *,
    trials_per_case: int,
) -> dict[str, Any]:
    """Aggregate repeated trials by case and across the entire benchmark."""
    case_results: list[dict[str, Any]] = []
    all_trials: list[dict[str, Any]] = []

    for case_id, case in cases.items():
        trials = trial_results.get(case_id, [])
        all_trials.extend(trials)
        passed_trials = sum(1 for trial in trials if trial.get("passed") is True)
        total_trials = len(trials)

        case_results.append(
            {
                "case_id": case_id,
                "prompt": case.prompt,
                "passed_trials": passed_trials,
                "failed_trials": total_trials - passed_trials,
                "total_trials": total_trials,
                "pass_rate": round(passed_trials / total_trials, 4)
                if total_trials
                else 0.0,
                "all_trials_passed": total_trials == trials_per_case
                and passed_trials == total_trials,
                "metrics": aggregate_benchmark_metrics(trials),
                "trials": trials,
            }
        )

    passed_trials = sum(1 for trial in all_trials if trial.get("passed") is True)
    total_trials = len(all_trials)

    return {
        "passed": bool(case_results)
        and all(result["all_trials_passed"] for result in case_results),
        "case_count": len(case_results),
        "trials_per_case": trials_per_case,
        "passed_trials": passed_trials,
        "failed_trials": total_trials - passed_trials,
        "total_trials": total_trials,
        "pass_rate": round(passed_trials / total_trials, 4)
        if total_trials
        else 0.0,
        "metrics": aggregate_benchmark_metrics(all_trials),
        "cases": case_results,
    }
