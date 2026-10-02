"""Runtime, token-usage, and estimated-cost helpers for eval reports."""

from __future__ import annotations

from math import ceil, floor
from statistics import mean
from typing import Any


PRICING_AS_OF = "2026-10-01"

# Standard short-context text pricing in USD per 1M tokens.
# Keep pricing data isolated so it can be reviewed and updated independently.
MODEL_PRICING_PER_MILLION: dict[str, dict[str, float]] = {
    "gpt-6-luna": {
        "input": 0.10,
        "cached_input": 0.01,
        "cache_write_input": 0.125,
        "output": 0.50,
    },
}


def _detail_value(details: Any, name: str) -> int:
    if details is None:
        return 0
    if isinstance(details, dict):
        value = details.get(name, 0)
    else:
        value = getattr(details, name, 0)
    return int(value or 0)


def estimate_text_cost_usd(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    cache_write_input_tokens: int = 0,
) -> float | None:
    """Estimate Standard short-context text cost for a supported model."""
    pricing = MODEL_PRICING_PER_MILLION.get(model)
    if pricing is None:
        return None

    uncached_input_tokens = max(
        input_tokens - cached_input_tokens - cache_write_input_tokens,
        0,
    )
    cost = (
        uncached_input_tokens * pricing["input"]
        + cached_input_tokens * pricing["cached_input"]
        + cache_write_input_tokens * pricing["cache_write_input"]
        + output_tokens * pricing["output"]
    ) / 1_000_000

    return round(cost, 8)


def serialize_usage(usage: Any, *, model: str) -> dict[str, Any]:
    """Convert Agents SDK usage into stable JSON metrics plus estimated cost."""
    input_details = getattr(usage, "input_tokens_details", None)
    output_details = getattr(usage, "output_tokens_details", None)

    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    cached_input_tokens = _detail_value(input_details, "cached_tokens")
    cache_write_input_tokens = _detail_value(input_details, "cache_write_tokens")
    reasoning_tokens = _detail_value(output_details, "reasoning_tokens")

    return {
        "model": model,
        "requests": int(getattr(usage, "requests", 0) or 0),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "cache_write_input_tokens": cache_write_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
        "estimated_cost_usd": estimate_text_cost_usd(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens,
            cache_write_input_tokens=cache_write_input_tokens,
        ),
        "pricing_as_of": PRICING_AS_OF,
    }


def aggregate_run_metrics(case_reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate agent and judge runtime/usage metrics across suite cases."""
    agent_elapsed = 0.0
    judge_elapsed = 0.0
    requests = 0
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    estimated_cost = 0.0
    priced_components = 0

    for report in case_reports:
        agent_elapsed += float(report.get("elapsed_seconds", 0) or 0)

        agent_metrics = report.get("usage_metrics") or {}
        semantic = report.get("semantic_judgment") or {}
        judge_metrics = semantic.get("usage_metrics") or {}
        judge_elapsed += float(semantic.get("elapsed_seconds", 0) or 0)

        for metrics in (agent_metrics, judge_metrics):
            requests += int(metrics.get("requests", 0) or 0)
            input_tokens += int(metrics.get("input_tokens", 0) or 0)
            output_tokens += int(metrics.get("output_tokens", 0) or 0)
            total_tokens += int(metrics.get("total_tokens", 0) or 0)
            cost = metrics.get("estimated_cost_usd")
            if cost is not None:
                estimated_cost += float(cost)
                priced_components += 1

    return {
        "agent_elapsed_seconds": round(agent_elapsed, 3),
        "judge_elapsed_seconds": round(judge_elapsed, 3),
        "combined_elapsed_seconds": round(agent_elapsed + judge_elapsed, 3),
        "requests": requests,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(estimated_cost, 8)
        if priced_components
        else None,
        "pricing_as_of": PRICING_AS_OF,
    }



def summarize_distribution(values: list[float]) -> dict[str, float | int | None]:
    """Summarize one numeric distribution with mean, p50, and p95.

    Percentiles use linear interpolation between neighboring observations. Small
    sample sizes remain descriptive rather than statistically strong tail estimates.
    """
    if not values:
        return {
            "sample_count": 0,
            "mean": None,
            "p50": None,
            "p95": None,
        }

    ordered = sorted(float(value) for value in values)

    def percentile(percent: float) -> float:
        if len(ordered) == 1:
            return ordered[0]

        rank = (len(ordered) - 1) * percent
        lower = floor(rank)
        upper = ceil(rank)
        if lower == upper:
            return ordered[lower]

        weight = rank - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * weight

    return {
        "sample_count": len(ordered),
        "mean": round(mean(ordered), 6),
        "p50": round(percentile(0.50), 6),
        "p95": round(percentile(0.95), 6),
    }


def aggregate_benchmark_metrics(
    trial_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate repeated trials while separating agent and evaluator economics."""
    passed_count = sum(1 for trial in trial_results if trial.get("passed") is True)

    agent_latencies: list[float] = []
    judge_latencies: list[float] = []
    agent_costs: list[float] = []
    judge_costs: list[float] = []
    agent_requests = 0
    judge_requests = 0
    agent_total_tokens = 0
    judge_total_tokens = 0
    agent_usage_samples = 0
    judge_usage_samples = 0
    agent_unpriced_samples = 0
    judge_unpriced_samples = 0

    for trial in trial_results:
        report = trial.get("report")
        if not isinstance(report, dict):
            continue

        elapsed = report.get("elapsed_seconds")
        if isinstance(elapsed, (int, float)):
            agent_latencies.append(float(elapsed))

        agent_metrics = report.get("usage_metrics")
        if isinstance(agent_metrics, dict):
            agent_usage_samples += 1
            agent_requests += int(agent_metrics.get("requests", 0) or 0)
            agent_total_tokens += int(agent_metrics.get("total_tokens", 0) or 0)
            cost = agent_metrics.get("estimated_cost_usd")
            if isinstance(cost, (int, float)):
                agent_costs.append(float(cost))
            else:
                agent_unpriced_samples += 1

        semantic = report.get("semantic_judgment")
        if not isinstance(semantic, dict):
            continue

        judge_elapsed = semantic.get("elapsed_seconds")
        if isinstance(judge_elapsed, (int, float)):
            judge_latencies.append(float(judge_elapsed))

        judge_metrics = semantic.get("usage_metrics")
        if isinstance(judge_metrics, dict):
            judge_usage_samples += 1
            judge_requests += int(judge_metrics.get("requests", 0) or 0)
            judge_total_tokens += int(judge_metrics.get("total_tokens", 0) or 0)
            cost = judge_metrics.get("estimated_cost_usd")
            if isinstance(cost, (int, float)):
                judge_costs.append(float(cost))
            else:
                judge_unpriced_samples += 1

    agent_fully_priced = agent_usage_samples > 0 and agent_unpriced_samples == 0
    judge_fully_priced = judge_usage_samples > 0 and judge_unpriced_samples == 0

    agent_total_cost = round(sum(agent_costs), 8) if agent_fully_priced else None
    judge_total_cost = round(sum(judge_costs), 8) if judge_fully_priced else None

    total_eval_cost = (
        round(agent_total_cost + judge_total_cost, 8)
        if agent_total_cost is not None and judge_total_cost is not None
        else None
    )

    return {
        "agent": {
            "latency_seconds": summarize_distribution(agent_latencies),
            "requests": agent_requests,
            "usage_sample_count": agent_usage_samples,
            "total_tokens": agent_total_tokens,
            "mean_tokens_per_measured_trial": round(
                agent_total_tokens / agent_usage_samples, 3
            )
            if agent_usage_samples
            else None,
            "estimated_cost_usd": {
                "total": agent_total_cost,
                "mean_per_measured_trial": round(
                    agent_total_cost / agent_usage_samples, 8
                )
                if agent_total_cost is not None and agent_usage_samples
                else None,
                "per_successful_trial": round(
                    agent_total_cost / passed_count, 8
                )
                if agent_total_cost is not None and passed_count
                else None,
                "fully_priced": agent_fully_priced,
            },
        },
        "judge": {
            "latency_seconds": summarize_distribution(judge_latencies),
            "requests": judge_requests,
            "usage_sample_count": judge_usage_samples,
            "total_tokens": judge_total_tokens,
            "mean_tokens_per_measured_trial": round(
                judge_total_tokens / judge_usage_samples, 3
            )
            if judge_usage_samples
            else None,
            "estimated_cost_usd": {
                "total": judge_total_cost,
                "mean_per_measured_trial": round(
                    judge_total_cost / judge_usage_samples, 8
                )
                if judge_total_cost is not None and judge_usage_samples
                else None,
                "fully_priced": judge_fully_priced,
            },
        },
        "evaluation": {
            "combined_measured_latency_seconds": round(
                sum(agent_latencies) + sum(judge_latencies), 3
            ),
            "estimated_total_cost_usd": total_eval_cost,
            "pricing_as_of": PRICING_AS_OF,
        },
    }
