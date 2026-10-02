"""Run the complete live agent eval set and grade it as a regression suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evals.cases import CASES
from evals.run_case import run_case
from evals.semantic_grader import judge_report
from evals.suite import evaluate_suite


def run_live_suite() -> dict[str, Any]:
    """Execute every configured eval case and return the graded suite report."""
    reports: dict[str, dict[str, Any]] = {}

    for case_id, case in CASES.items():
        print(f"Running {case_id}: {case.prompt}", flush=True)
        try:
            report = run_case(case.prompt)
            try:
                report["semantic_judgment"] = judge_report(report)
            except Exception as exc:
                report["semantic_judgment"] = {
                    "passed": False,
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }
            reports[case_id] = report
        except Exception as exc:
            reports[case_id] = {
                "prompt": case.prompt,
                "trajectory": [],
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            }

    return evaluate_suite(reports, CASES)


def write_suite_report(report: dict[str, Any], output_path: Path) -> None:
    """Persist the suite report before the process reports pass/fail to CI."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/regression-suite.json"),
        help="Path for the complete regression-suite report.",
    )
    args = parser.parse_args()

    report = run_live_suite()
    write_suite_report(report, args.output)

    print(
        f"Regression suite: {report['passed_count']}/{report['total_count']} passed",
        flush=True,
    )

    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
