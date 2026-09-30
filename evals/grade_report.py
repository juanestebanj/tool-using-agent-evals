"""Grade a captured live-run JSON report against a named eval case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.cases import CASES
from evals.graders import evaluate_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=sorted(CASES))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = evaluate_report(report, CASES[args.case])
    print(json.dumps(result, indent=2, sort_keys=True))

    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
