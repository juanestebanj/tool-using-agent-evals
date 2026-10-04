"""Compare two repeated-trial benchmark artifacts deterministically."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _delta(candidate: Any, baseline: Any) -> float | None:
    c = _number(candidate)
    b = _number(baseline)
    if c is None or b is None:
        return None
    return round(c - b, 6)


def _percent_change(candidate: Any, baseline: Any) -> float | None:
    c = _number(candidate)
    b = _number(baseline)
    if c is None or b is None or b == 0:
        return None
    return round((c - b) / b * 100, 3)


def _agent_token_means(report: dict[str, Any]) -> dict[str, float | None]:
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    samples = 0

    for case in report.get("cases", []):
        for trial in case.get("trials", []):
            captured = trial.get("report")
            if not isinstance(captured, dict):
                continue
            usage = captured.get("usage_metrics")
            if not isinstance(usage, dict):
                continue

            input_tokens += int(usage.get("input_tokens", 0) or 0)
            output_tokens += int(usage.get("output_tokens", 0) or 0)
            total_tokens += int(usage.get("total_tokens", 0) or 0)
            samples += 1

    if not samples:
        return {
            "sample_count": 0,
            "mean_input_tokens": None,
            "mean_output_tokens": None,
            "mean_total_tokens": None,
        }

    return {
        "sample_count": samples,
        "mean_input_tokens": round(input_tokens / samples, 3),
        "mean_output_tokens": round(output_tokens / samples, 3),
        "mean_total_tokens": round(total_tokens / samples, 3),
    }


def _headline_metrics(report: dict[str, Any]) -> dict[str, Any]:
    metrics = report.get("metrics") or {}
    agent = metrics.get("agent") or {}
    judge = metrics.get("judge") or {}
    evaluation = metrics.get("evaluation") or {}
    latency = agent.get("latency_seconds") or {}
    agent_cost = agent.get("estimated_cost_usd") or {}
    judge_cost = judge.get("estimated_cost_usd") or {}
    tokens = _agent_token_means(report)

    return {
        "pass_rate": _number(report.get("pass_rate")),
        "passed_trials": int(report.get("passed_trials", 0) or 0),
        "failed_trials": int(report.get("failed_trials", 0) or 0),
        "total_trials": int(report.get("total_trials", 0) or 0),
        "agent_latency_seconds": {
            "mean": _number(latency.get("mean")),
            "p50": _number(latency.get("p50")),
            "p95": _number(latency.get("p95")),
        },
        "agent_tokens": tokens,
        "agent_cost_usd": {
            "mean_per_measured_trial": _number(
                agent_cost.get("mean_per_measured_trial")
            ),
            "per_successful_trial": _number(
                agent_cost.get("per_successful_trial")
            ),
            "total": _number(agent_cost.get("total")),
        },
        "judge_cost_usd": {
            "mean_per_measured_trial": _number(
                judge_cost.get("mean_per_measured_trial")
            ),
            "total": _number(judge_cost.get("total")),
        },
        "evaluation_cost_usd": {
            "total": _number(evaluation.get("estimated_total_cost_usd")),
        },
    }


def _compare_value(candidate: Any, baseline: Any) -> dict[str, Any]:
    return {
        "baseline": baseline,
        "candidate": candidate,
        "delta": _delta(candidate, baseline),
        "percent_change": _percent_change(candidate, baseline),
    }


def _case_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("case_id")): case
        for case in report.get("cases", [])
        if case.get("case_id") is not None
    }


def compare_benchmarks(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Compare benchmark quality, serving metrics, and per-case reliability."""
    b = _headline_metrics(baseline)
    c = _headline_metrics(candidate)

    baseline_cases = _case_map(baseline)
    candidate_cases = _case_map(candidate)
    shared_ids = sorted(set(baseline_cases) & set(candidate_cases))
    baseline_only = sorted(set(baseline_cases) - set(candidate_cases))
    candidate_only = sorted(set(candidate_cases) - set(baseline_cases))

    case_comparisons: list[dict[str, Any]] = []
    regressions: list[str] = []
    improvements: list[str] = []

    for case_id in shared_ids:
        baseline_case = baseline_cases[case_id]
        candidate_case = candidate_cases[case_id]
        baseline_rate = _number(baseline_case.get("pass_rate"))
        candidate_rate = _number(candidate_case.get("pass_rate"))
        delta_pp = (
            round((candidate_rate - baseline_rate) * 100, 3)
            if baseline_rate is not None and candidate_rate is not None
            else None
        )

        status = "unchanged"
        if delta_pp is not None and delta_pp < 0:
            status = "regression"
            regressions.append(case_id)
        elif delta_pp is not None and delta_pp > 0:
            status = "improvement"
            improvements.append(case_id)

        case_comparisons.append(
            {
                "case_id": case_id,
                "baseline": {
                    "passed_trials": int(
                        baseline_case.get("passed_trials", 0) or 0
                    ),
                    "total_trials": int(
                        baseline_case.get("total_trials", 0) or 0
                    ),
                    "pass_rate": baseline_rate,
                },
                "candidate": {
                    "passed_trials": int(
                        candidate_case.get("passed_trials", 0) or 0
                    ),
                    "total_trials": int(
                        candidate_case.get("total_trials", 0) or 0
                    ),
                    "pass_rate": candidate_rate,
                },
                "pass_rate_delta_percentage_points": delta_pp,
                "status": status,
            }
        )

    b_latency = b["agent_latency_seconds"]
    c_latency = c["agent_latency_seconds"]
    b_tokens = b["agent_tokens"]
    c_tokens = c["agent_tokens"]
    b_agent_cost = b["agent_cost_usd"]
    c_agent_cost = c["agent_cost_usd"]
    b_judge_cost = b["judge_cost_usd"]
    c_judge_cost = c["judge_cost_usd"]
    b_eval_cost = b["evaluation_cost_usd"]
    c_eval_cost = c["evaluation_cost_usd"]

    pass_rate_delta_pp = (
        round((c["pass_rate"] - b["pass_rate"]) * 100, 3)
        if c["pass_rate"] is not None and b["pass_rate"] is not None
        else None
    )

    return {
        "baseline": b,
        "candidate": c,
        "comparison": {
            "pass_rate_delta_percentage_points": pass_rate_delta_pp,
            "agent_latency_seconds": {
                "mean": _compare_value(c_latency["mean"], b_latency["mean"]),
                "p50": _compare_value(c_latency["p50"], b_latency["p50"]),
                "p95": _compare_value(c_latency["p95"], b_latency["p95"]),
            },
            "agent_tokens": {
                "mean_input_tokens": _compare_value(
                    c_tokens["mean_input_tokens"],
                    b_tokens["mean_input_tokens"],
                ),
                "mean_output_tokens": _compare_value(
                    c_tokens["mean_output_tokens"],
                    b_tokens["mean_output_tokens"],
                ),
                "mean_total_tokens": _compare_value(
                    c_tokens["mean_total_tokens"],
                    b_tokens["mean_total_tokens"],
                ),
            },
            "agent_cost_usd": {
                "mean_per_measured_trial": _compare_value(
                    c_agent_cost["mean_per_measured_trial"],
                    b_agent_cost["mean_per_measured_trial"],
                ),
                "per_successful_trial": _compare_value(
                    c_agent_cost["per_successful_trial"],
                    b_agent_cost["per_successful_trial"],
                ),
                "total": _compare_value(
                    c_agent_cost["total"],
                    b_agent_cost["total"],
                ),
            },
            "judge_cost_usd": {
                "mean_per_measured_trial": _compare_value(
                    c_judge_cost["mean_per_measured_trial"],
                    b_judge_cost["mean_per_measured_trial"],
                ),
                "total": _compare_value(
                    c_judge_cost["total"],
                    b_judge_cost["total"],
                ),
            },
            "evaluation_cost_usd": {
                "total": _compare_value(
                    c_eval_cost["total"],
                    b_eval_cost["total"],
                ),
            },
        },
        "cases": case_comparisons,
        "regressions": regressions,
        "improvements": improvements,
        "baseline_only_cases": baseline_only,
        "candidate_only_cases": candidate_only,
    }


def _fmt_number(value: Any, digits: int = 3) -> str:
    return "n/a" if value is None else f"{float(value):,.{digits}f}"


def _fmt_percent(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):+.1f}%"


def _fmt_pp(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):+.1f} pp"


def _fmt_usd(value: Any) -> str:
    return "n/a" if value is None else f"${float(value):.8f}"


def render_comparison_markdown(
    comparison: dict[str, Any],
    *,
    baseline_label: str = "Baseline",
    candidate_label: str = "Candidate",
) -> str:
    """Render a comparison without deciding a universal winner."""
    b = comparison["baseline"]
    c = comparison["candidate"]
    delta = comparison["comparison"]

    rows = [
        (
            "Observed pass rate",
            f"{b['pass_rate'] * 100:.1f}%" if b["pass_rate"] is not None else "n/a",
            f"{c['pass_rate'] * 100:.1f}%" if c["pass_rate"] is not None else "n/a",
            _fmt_pp(delta["pass_rate_delta_percentage_points"]),
        ),
        (
            "Agent mean latency",
            f"{_fmt_number(b['agent_latency_seconds']['mean'])} s",
            f"{_fmt_number(c['agent_latency_seconds']['mean'])} s",
            _fmt_percent(
                delta["agent_latency_seconds"]["mean"]["percent_change"]
            ),
        ),
        (
            "Agent p50 latency",
            f"{_fmt_number(b['agent_latency_seconds']['p50'])} s",
            f"{_fmt_number(c['agent_latency_seconds']['p50'])} s",
            _fmt_percent(
                delta["agent_latency_seconds"]["p50"]["percent_change"]
            ),
        ),
        (
            "Agent p95 latency",
            f"{_fmt_number(b['agent_latency_seconds']['p95'])} s",
            f"{_fmt_number(c['agent_latency_seconds']['p95'])} s",
            _fmt_percent(
                delta["agent_latency_seconds"]["p95"]["percent_change"]
            ),
        ),
        (
            "Mean input tokens",
            _fmt_number(b["agent_tokens"]["mean_input_tokens"], 1),
            _fmt_number(c["agent_tokens"]["mean_input_tokens"], 1),
            _fmt_percent(
                delta["agent_tokens"]["mean_input_tokens"]["percent_change"]
            ),
        ),
        (
            "Mean output tokens",
            _fmt_number(b["agent_tokens"]["mean_output_tokens"], 1),
            _fmt_number(c["agent_tokens"]["mean_output_tokens"], 1),
            _fmt_percent(
                delta["agent_tokens"]["mean_output_tokens"]["percent_change"]
            ),
        ),
        (
            "Mean total tokens",
            _fmt_number(b["agent_tokens"]["mean_total_tokens"], 1),
            _fmt_number(c["agent_tokens"]["mean_total_tokens"], 1),
            _fmt_percent(
                delta["agent_tokens"]["mean_total_tokens"]["percent_change"]
            ),
        ),
        (
            "Agent mean cost / trial",
            _fmt_usd(b["agent_cost_usd"]["mean_per_measured_trial"]),
            _fmt_usd(c["agent_cost_usd"]["mean_per_measured_trial"]),
            _fmt_percent(
                delta["agent_cost_usd"]["mean_per_measured_trial"][
                    "percent_change"
                ]
            ),
        ),
        (
            "Agent cost / successful trial",
            _fmt_usd(b["agent_cost_usd"]["per_successful_trial"]),
            _fmt_usd(c["agent_cost_usd"]["per_successful_trial"]),
            _fmt_percent(
                delta["agent_cost_usd"]["per_successful_trial"][
                    "percent_change"
                ]
            ),
        ),
        (
            "Total evaluation cost",
            _fmt_usd(b["evaluation_cost_usd"]["total"]),
            _fmt_usd(c["evaluation_cost_usd"]["total"]),
            _fmt_percent(
                delta["evaluation_cost_usd"]["total"]["percent_change"]
            ),
        ),
    ]

    lines = [
        "# Baseline vs Candidate Evaluation",
        "",
        "This report presents measured tradeoffs and does not automatically declare a winner.",
        "",
        f"| Metric | {baseline_label} | {candidate_label} | Change |",
        "| --- | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| {metric} | {baseline_value} | {candidate_value} | {change} |"
        for metric, baseline_value, candidate_value, change in rows
    )

    lines.extend([
        "",
        "## Per-case reliability",
        "",
        "| Case | Baseline | Candidate | Δ pass rate | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ])

    for case in comparison["cases"]:
        b_case = case["baseline"]
        c_case = case["candidate"]
        lines.append(
            f"| {case['case_id']} | "
            f"{b_case['passed_trials']}/{b_case['total_trials']} | "
            f"{c_case['passed_trials']}/{c_case['total_trials']} | "
            f"{_fmt_pp(case['pass_rate_delta_percentage_points'])} | "
            f"{case['status']} |"
        )

    lines.extend(["", "## Reliability changes", ""])
    if comparison["regressions"]:
        lines.append(
            "**Regressions:** " + ", ".join(comparison["regressions"])
        )
    else:
        lines.append("**Regressions:** none observed in shared cases.")

    if comparison["improvements"]:
        lines.append(
            "**Improvements:** " + ", ".join(comparison["improvements"])
        )
    else:
        lines.append("**Improvements:** none observed in shared cases.")

    if comparison["baseline_only_cases"]:
        lines.append(
            "**Baseline-only cases:** "
            + ", ".join(comparison["baseline_only_cases"])
        )
    if comparison["candidate_only_cases"]:
        lines.append(
            "**Candidate-only cases:** "
            + ", ".join(comparison["candidate_only_cases"])
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "Use quality, latency, and cost together. A faster or cheaper candidate can still "
        "be unacceptable if reliability regresses; conversely, a more reliable candidate "
        "may justify higher serving cost. Acceptance policy belongs outside this comparison "
        "utility so product and engineering teams can define the tradeoff explicitly.",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/benchmark-comparison.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("results/benchmark-comparison.md"),
    )
    parser.add_argument("--baseline-label", default="Baseline")
    parser.add_argument("--candidate-label", default="Candidate")
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    comparison = compare_benchmarks(baseline, candidate)

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(comparison, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(
        render_comparison_markdown(
            comparison,
            baseline_label=args.baseline_label,
            candidate_label=args.candidate_label,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
