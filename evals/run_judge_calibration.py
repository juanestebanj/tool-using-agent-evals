"""Run the semantic judge on the committed human-labeled calibration set."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from evals.judge_calibration import (
    build_calibration_report,
    render_calibration_markdown,
)
from evals.judge_calibration_cases import CALIBRATION_CASES
from evals.semantic_grader import judge_report


def run_calibration(
    *,
    calibration_cases: tuple[dict[str, Any], ...] | list[dict[str, Any]] = CALIBRATION_CASES,
    judge_fn: Callable[..., dict[str, Any]] = judge_report,
    model: str | None = None,
) -> dict[str, Any]:
    """Execute judge calls while preserving individual execution failures."""
    judgments: dict[str, dict[str, Any]] = {}

    for case in calibration_cases:
        case_id = str(case["id"])
        print(f"Calibrating semantic judge: {case_id}")
        try:
            judgments[case_id] = judge_fn(case["report"], model=model)
        except Exception as exc:
            judgments[case_id] = {
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
            }

    return build_calibration_report(calibration_cases, judgments)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/judge-calibration.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("results/judge-calibration.md"),
    )
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    report = run_calibration(model=args.model)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(
        render_calibration_markdown(report),
        encoding="utf-8",
    )

    accuracy = report["overall_pass_label"]["accuracy"]
    print(
        "Semantic judge calibration: "
        f"{report['comparable_cases']}/{report['case_count']} comparable cases, "
        f"accuracy={accuracy if accuracy is not None else 'n/a'}, "
        f"false_positives={len(report['false_positive_cases'])}, "
        f"false_negatives={len(report['false_negative_cases'])}"
    )

    # Label disagreement is a calibration result, not an infrastructure failure.
    # Only judge execution errors make this command fail.
    if report["execution_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
