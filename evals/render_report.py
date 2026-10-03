"""Render a repeated-trial benchmark JSON artifact as a human-readable Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _pct(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value * 100:.1f}%"


def _seconds(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value:.3f} s"


def _number(value: Any, *, digits: int = 1) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value:,.{digits}f}"


def _usd(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"${value:.8f}"


def _tool_trajectory(report: dict[str, Any]) -> str:
    names = [
        item.get("name")
        for item in report.get("trajectory", [])
        if item.get("type") == "tool_call" and item.get("name")
    ]
    return " → ".join(str(name) for name in names) if names else "(no tool calls)"


def _failed_checks(trial: dict[str, Any]) -> list[str]:
    evaluation = trial.get("evaluation")
    if not isinstance(evaluation, dict):
        return []

    checks = evaluation.get("checks")
    gating = evaluation.get("gating_checks")
    if not isinstance(checks, dict) or not isinstance(gating, list):
        return []

    return [
        str(name)
        for name in gating
        if isinstance(checks.get(name), dict)
        and checks[name].get("passed") is not True
    ]


def _render_failure_section(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    for case in report.get("cases", []):
        case_id = str(case.get("case_id", "unknown-case"))
        for trial in case.get("trials", []):
            if trial.get("passed") is True:
                continue

            trial_number = trial.get("trial", "?")
            execution_error = trial.get("error")
            captured = trial.get("report")
            captured_report = captured if isinstance(captured, dict) else {}

            details: list[str] = []
            if isinstance(execution_error, dict):
                error_type = execution_error.get("type", "Error")
                message = execution_error.get("message", "")
                details.append(f"execution error: {error_type}: {message}".rstrip())

            failed_checks = _failed_checks(trial)
            if failed_checks:
                details.append(f"failed checks: {', '.join(failed_checks)}")

            details.append(f"tool trajectory: {_tool_trajectory(captured_report)}")
            failures.append(
                f"- **{case_id}, trial {trial_number}:** " + "; ".join(details)
            )

    if failures:
        return failures

    return ["No failed trials were observed in this benchmark run."]


def render_benchmark_report(
    report: dict[str, Any],
    *,
    source_label: str | None = None,
    source_url: str | None = None,
    commit_sha: str | None = None,
) -> str:
    """Return a deterministic Markdown summary of a repeated-trial benchmark."""
    metrics = report.get("metrics") or {}
    agent = metrics.get("agent") or {}
    judge = metrics.get("judge") or {}
    evaluation = metrics.get("evaluation") or {}

    agent_latency = agent.get("latency_seconds") or {}
    judge_latency = judge.get("latency_seconds") or {}
    agent_cost = agent.get("estimated_cost_usd") or {}
    judge_cost = judge.get("estimated_cost_usd") or {}

    passed_trials = int(report.get("passed_trials", 0) or 0)
    total_trials = int(report.get("total_trials", 0) or 0)
    failed_trials = int(report.get("failed_trials", total_trials - passed_trials) or 0)
    case_count = int(report.get("case_count", len(report.get("cases", []))) or 0)
    trials_per_case = int(report.get("trials_per_case", 0) or 0)

    lines = [
        "# Evaluation Report",
        "",
        "## Executive summary",
        "",
        f"- **Observed pass rate:** {_pct(report.get('pass_rate'))} "
        f"({passed_trials}/{total_trials} live trials)",
        f"- **Cases:** {case_count}",
        f"- **Trials per case:** {trials_per_case}",
        f"- **Failed trials:** {failed_trials}",
        f"- **Agent latency:** mean {_seconds(agent_latency.get('mean'))}, "
        f"p50 {_seconds(agent_latency.get('p50'))}, "
        f"p95 {_seconds(agent_latency.get('p95'))}",
        f"- **Agent tokens:** {_number(agent.get('mean_tokens_per_measured_trial'))} "
        "mean tokens per measured trial",
        f"- **Agent estimated cost:** {_usd(agent_cost.get('mean_per_measured_trial'))} "
        "mean per measured trial",
        f"- **Agent cost per successful trial:** "
        f"{_usd(agent_cost.get('per_successful_trial'))}",
        "",
    ]

    if source_label or source_url or commit_sha:
        source_parts: list[str] = []
        if source_label and source_url:
            source_parts.append(f"[{source_label}]({source_url})")
        elif source_label:
            source_parts.append(source_label)
        elif source_url:
            source_parts.append(source_url)

        if commit_sha:
            source_parts.append(f"commit `{commit_sha}`")

        lines.extend([
            "## Source",
            "",
            " · ".join(source_parts),
            "",
        ])

    lines.extend([
        "## Per-case reliability and agent performance",
        "",
        "| Case | Passed | Observed pass rate | Mean latency | p50 | p95 | Mean tokens | Mean estimated cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])

    for case in report.get("cases", []):
        case_metrics = case.get("metrics") or {}
        case_agent = case_metrics.get("agent") or {}
        case_latency = case_agent.get("latency_seconds") or {}
        case_cost = case_agent.get("estimated_cost_usd") or {}

        lines.append(
            "| "
            + " | ".join(
                [
                    str(case.get("case_id", "unknown")),
                    f"{case.get('passed_trials', 0)}/{case.get('total_trials', 0)}",
                    _pct(case.get("pass_rate")),
                    _seconds(case_latency.get("mean")),
                    _seconds(case_latency.get("p50")),
                    _seconds(case_latency.get("p95")),
                    _number(case_agent.get("mean_tokens_per_measured_trial")),
                    _usd(case_cost.get("mean_per_measured_trial")),
                ]
            )
            + " |"
        )

    lines.extend([
        "",
        "## Evaluation overhead",
        "",
        "The semantic judge is evaluation infrastructure, not part of the production-like "
        "agent serving cost. It is therefore reported separately.",
        "",
        f"- **Judge latency:** mean {_seconds(judge_latency.get('mean'))}, "
        f"p50 {_seconds(judge_latency.get('p50'))}, "
        f"p95 {_seconds(judge_latency.get('p95'))}",
        f"- **Judge tokens:** {_number(judge.get('mean_tokens_per_measured_trial'))} "
        "mean tokens per measured trial",
        f"- **Judge estimated cost:** {_usd(judge_cost.get('mean_per_measured_trial'))} "
        "mean per measured trial",
        f"- **Total agent cost:** {_usd(agent_cost.get('total'))}",
        f"- **Total judge cost:** {_usd(judge_cost.get('total'))}",
        f"- **Total benchmark estimated cost:** "
        f"{_usd(evaluation.get('estimated_total_cost_usd'))}",
        f"- **Combined measured agent + judge time:** "
        f"{_seconds(evaluation.get('combined_measured_latency_seconds'))}",
        "",
        "## Failed-trial analysis",
        "",
        *_render_failure_section(report),
        "",
        "## Methodology",
        "",
        "Each live trial is graded on exact trajectory properties such as required and "
        "forbidden tools, tool arguments, and tool ordering. A separate structured "
        "LLM-as-judge evaluates semantic outcome quality. Runtime, token usage, and "
        "estimated cost are captured for both the evaluated agent and the judge.",
        "",
        "The benchmark repeats the same fixed cases because model behavior is "
        "probabilistic. The observed pass rate describes this benchmark run; it is "
        "not a claim of perfect production reliability.",
        "",
        "Latency percentiles are most informative with larger samples. Overall p50/p95 "
        f"use {agent_latency.get('sample_count', 0)} agent observations here. "
        f"Per-case percentile estimates use only {trials_per_case} observations and "
        "should be treated as descriptive when that sample is small.",
        "",
        f"Estimated costs use the pricing table dated "
        f"`{evaluation.get('pricing_as_of', 'unknown')}` and are not billing records.",
        "",
    ])

    return "\n".join(lines)


def write_markdown_report(
    report: dict[str, Any],
    output_path: Path,
    *,
    source_label: str | None = None,
    source_url: str | None = None,
    commit_sha: str | None = None,
) -> None:
    """Write a benchmark report as UTF-8 Markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_benchmark_report(
            report,
            source_label=source_label,
            source_url=source_url,
            commit_sha=commit_sha,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Repeated-trial benchmark JSON artifact.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/evaluation-report.md"),
        help="Markdown output path.",
    )
    parser.add_argument("--source-label", default=None)
    parser.add_argument("--source-url", default=None)
    parser.add_argument("--commit-sha", default=None)
    args = parser.parse_args()

    report = json.loads(args.input.read_text(encoding="utf-8"))
    write_markdown_report(
        report,
        args.output,
        source_label=args.source_label,
        source_url=args.source_url,
        commit_sha=args.commit_sha,
    )


if __name__ == "__main__":
    main()
