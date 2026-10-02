"""Runtime, token-usage, and estimated-cost helpers for eval reports."""

from __future__ import annotations

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
