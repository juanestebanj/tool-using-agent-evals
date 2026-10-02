from types import SimpleNamespace

from evals.metrics import (
    PRICING_AS_OF,
    aggregate_benchmark_metrics,
    aggregate_run_metrics,
    estimate_text_cost_usd,
    serialize_usage,
    summarize_distribution,
)


def _usage(
    *,
    requests=2,
    input_tokens=1000,
    output_tokens=200,
    cached_tokens=100,
    cache_write_tokens=50,
    reasoning_tokens=25,
):
    return SimpleNamespace(
        requests=requests,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        input_tokens_details=SimpleNamespace(
            cached_tokens=cached_tokens,
            cache_write_tokens=cache_write_tokens,
        ),
        output_tokens_details=SimpleNamespace(reasoning_tokens=reasoning_tokens),
    )


def test_serialize_usage_captures_token_breakdown_and_cost():
    result = serialize_usage(_usage(), model="gpt-6-luna")

    assert result["requests"] == 2
    assert result["input_tokens"] == 1000
    assert result["cached_input_tokens"] == 100
    assert result["cache_write_input_tokens"] == 50
    assert result["output_tokens"] == 200
    assert result["reasoning_tokens"] == 25
    assert result["total_tokens"] == 1200
    assert result["estimated_cost_usd"] is not None
    assert result["pricing_as_of"] == PRICING_AS_OF


def test_cost_estimate_prices_cached_and_uncached_input_separately():
    cost = estimate_text_cost_usd(
        model="gpt-6-luna",
        input_tokens=1_000_000,
        cached_input_tokens=200_000,
        cache_write_input_tokens=100_000,
        output_tokens=100_000,
    )

    # 700K regular input + 200K cached + 100K cache-write + 100K output.
    assert cost == 0.1345


def test_unknown_model_keeps_usage_but_leaves_cost_unpriced():
    result = serialize_usage(_usage(), model="unknown-model")

    assert result["total_tokens"] == 1200
    assert result["estimated_cost_usd"] is None


def test_aggregate_run_metrics_combines_agent_and_judge_metrics():
    reports = [
        {
            "elapsed_seconds": 1.5,
            "usage_metrics": {
                "requests": 2,
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "estimated_cost_usd": 0.001,
            },
            "semantic_judgment": {
                "elapsed_seconds": 0.5,
                "usage_metrics": {
                    "requests": 1,
                    "input_tokens": 50,
                    "output_tokens": 10,
                    "total_tokens": 60,
                    "estimated_cost_usd": 0.0005,
                },
            },
        },
        {
            "elapsed_seconds": 2.0,
            "usage_metrics": {
                "requests": 1,
                "input_tokens": 80,
                "output_tokens": 15,
                "total_tokens": 95,
                "estimated_cost_usd": 0.0008,
            },
            "semantic_judgment": {
                "elapsed_seconds": 0.75,
                "usage_metrics": {
                    "requests": 1,
                    "input_tokens": 40,
                    "output_tokens": 8,
                    "total_tokens": 48,
                    "estimated_cost_usd": 0.0004,
                },
            },
        },
    ]

    result = aggregate_run_metrics(reports)

    assert result["agent_elapsed_seconds"] == 3.5
    assert result["judge_elapsed_seconds"] == 1.25
    assert result["combined_elapsed_seconds"] == 4.75
    assert result["requests"] == 5
    assert result["input_tokens"] == 270
    assert result["output_tokens"] == 53
    assert result["total_tokens"] == 323
    assert result["estimated_cost_usd"] == 0.0027



def test_summarize_distribution_reports_mean_p50_and_p95():
    result = summarize_distribution([1.0, 2.0, 3.0, 4.0, 5.0])

    assert result == {
        "sample_count": 5,
        "mean": 3.0,
        "p50": 3.0,
        "p95": 4.8,
    }


def test_benchmark_metrics_separate_agent_and_judge_costs():
    trials = [
        {
            "passed": True,
            "report": {
                "elapsed_seconds": 2.0,
                "usage_metrics": {
                    "requests": 2,
                    "total_tokens": 100,
                    "estimated_cost_usd": 0.001,
                },
                "semantic_judgment": {
                    "elapsed_seconds": 0.5,
                    "usage_metrics": {
                        "requests": 1,
                        "total_tokens": 50,
                        "estimated_cost_usd": 0.0004,
                    },
                },
            },
        },
        {
            "passed": False,
            "report": {
                "elapsed_seconds": 4.0,
                "usage_metrics": {
                    "requests": 2,
                    "total_tokens": 140,
                    "estimated_cost_usd": 0.0014,
                },
                "semantic_judgment": {
                    "elapsed_seconds": 1.0,
                    "usage_metrics": {
                        "requests": 1,
                        "total_tokens": 70,
                        "estimated_cost_usd": 0.0006,
                    },
                },
            },
        },
    ]

    result = aggregate_benchmark_metrics(trials)

    assert result["agent"]["latency_seconds"]["mean"] == 3.0
    assert result["agent"]["latency_seconds"]["p50"] == 3.0
    assert result["agent"]["latency_seconds"]["p95"] == 3.9
    assert result["agent"]["total_tokens"] == 240
    assert result["agent"]["mean_tokens_per_measured_trial"] == 120.0
    assert result["agent"]["estimated_cost_usd"]["total"] == 0.0024
    assert result["agent"]["estimated_cost_usd"]["mean_per_measured_trial"] == 0.0012
    assert result["agent"]["estimated_cost_usd"]["per_successful_trial"] == 0.0024

    assert result["judge"]["latency_seconds"]["mean"] == 0.75
    assert result["judge"]["estimated_cost_usd"]["total"] == 0.001
    assert result["evaluation"]["estimated_total_cost_usd"] == 0.0034
