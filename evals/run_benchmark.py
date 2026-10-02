"""Run repeated live trials for every configured agent evaluation case."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from evals.benchmark import build_benchmark_report, evaluate_trial
from evals.cases import CASES, EvalCase
from evals.run_case import run_case
from evals.semantic_grader import judge_report


DEFAULT_TRIALS_PER_CASE = 5


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("trials must be at least 1")
    return parsed


def run_live_benchmark(
    *,
    trials_per_case: int = DEFAULT_TRIALS_PER_CASE,
    cases: dict[str, EvalCase] = CASES,
    run_case_fn: Callable[[str], dict[str, Any]] = run_case,
    judge_report_fn: Callable[[dict[str, Any]], dict[str, Any]] = judge_report,
) -> dict[str, Any]:
    """Execute repeated trials and return a reliability-oriented benchmark."""
    if trials_per_case < 1:
        raise ValueError("trials_per_case must be at least 1")

    trial_results: dict[str, list[dict[str, Any]]] = {}

    for case_id, case in cases.items():
        trials: list[dict[str, Any]] = []
        for trial_number in range(1, trials_per_case + 1):
            print(
                f"Running {case_id} trial {trial_number}/{trials_per_case}: "
                f"{case.prompt}",
                flush=True,
            )
            try:
                report = run_case_fn(case.prompt)
                try:
                    report["semantic_judgment"] = judge_report_fn(report)
                except Exception as exc:
                    report["semantic_judgment"] = {
                        "passed": False,
                        "error": {
                            "type": type(exc).__name__,
                            "message": str(exc),
                        },
                    }
            except Exception as exc:
                report = {
                    "prompt": case.prompt,
                    "trajectory": [],
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }

            trials.append(
                evaluate_trial(
                    case=case,
                    trial_number=trial_number,
                    report=report,
                )
            )

        trial_results[case_id] = trials

    return build_benchmark_report(
        trial_results,
        cases,
        trials_per_case=trials_per_case,
    )


def write_benchmark_report(report: dict[str, Any], output_path: Path) -> None:
    """Persist the benchmark report before reporting pass/fail."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trials",
        type=_positive_int,
        default=DEFAULT_TRIALS_PER_CASE,
        help="Number of independent live trials to run for each eval case.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/repeated-trial-benchmark.json"),
        help="Path for the complete repeated-trial benchmark report.",
    )
    args = parser.parse_args()

    report = run_live_benchmark(trials_per_case=args.trials)
    write_benchmark_report(report, args.output)

    print(
        "Repeated-trial benchmark: "
        f"{report['passed_trials']}/{report['total_trials']} trials passed "
        f"({report['pass_rate']:.1%})",
        flush=True,
    )

    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
