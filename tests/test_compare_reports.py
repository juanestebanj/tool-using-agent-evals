from copy import deepcopy

from evals.compare_reports import compare_benchmarks, render_comparison_markdown


def _trial(*, input_tokens=100, output_tokens=20, total_tokens=120):
    return {
        "passed": True,
        "report": {
            "usage_metrics": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }
        },
    }


def _benchmark(
    *,
    pass_rate=1.0,
    latency_mean=3.0,
    latency_p50=2.5,
    latency_p95=5.0,
    cost=0.001,
    eval_cost=0.002,
):
    passed_trials = round(pass_rate * 2)
    return {
        "passed": pass_rate == 1.0,
        "passed_trials": passed_trials,
        "failed_trials": 2 - passed_trials,
        "total_trials": 2,
        "pass_rate": pass_rate,
        "metrics": {
            "agent": {
                "latency_seconds": {
                    "mean": latency_mean,
                    "p50": latency_p50,
                    "p95": latency_p95,
                },
                "estimated_cost_usd": {
                    "mean_per_measured_trial": cost,
                    "per_successful_trial": cost,
                    "total": cost * 2,
                },
            },
            "judge": {
                "estimated_cost_usd": {
                    "mean_per_measured_trial": 0.0005,
                    "total": 0.001,
                }
            },
            "evaluation": {
                "estimated_total_cost_usd": eval_cost,
            },
        },
        "cases": [
            {
                "case_id": "duplicate-charge",
                "passed_trials": passed_trials,
                "failed_trials": 2 - passed_trials,
                "total_trials": 2,
                "pass_rate": pass_rate,
                "trials": [_trial(), _trial()],
            }
        ],
    }


def test_compare_benchmarks_reports_quality_latency_tokens_and_cost():
    baseline = _benchmark()
    candidate = _benchmark(
        latency_mean=2.4,
        latency_p50=2.0,
        latency_p95=4.0,
        cost=0.0009,
        eval_cost=0.0018,
    )
    for trial in candidate["cases"][0]["trials"]:
        trial["report"]["usage_metrics"] = {
            "input_tokens": 90,
            "output_tokens": 15,
            "total_tokens": 105,
        }

    result = compare_benchmarks(baseline, candidate)

    assert result["comparison"]["pass_rate_delta_percentage_points"] == 0.0
    assert (
        result["comparison"]["agent_latency_seconds"]["mean"]["percent_change"]
        == -20.0
    )
    assert (
        result["comparison"]["agent_tokens"]["mean_total_tokens"][
            "percent_change"
        ]
        == -12.5
    )
    assert (
        result["comparison"]["agent_cost_usd"]["mean_per_measured_trial"][
            "percent_change"
        ]
        == -10.0
    )
    assert result["regressions"] == []


def test_compare_benchmarks_flags_per_case_reliability_regression():
    baseline = _benchmark(pass_rate=1.0)
    candidate = _benchmark(pass_rate=0.5)

    result = compare_benchmarks(baseline, candidate)

    assert result["comparison"]["pass_rate_delta_percentage_points"] == -50.0
    assert result["regressions"] == ["duplicate-charge"]
    assert result["cases"][0]["status"] == "regression"


def test_compare_benchmarks_flags_improvement():
    baseline = _benchmark(pass_rate=0.5)
    candidate = _benchmark(pass_rate=1.0)

    result = compare_benchmarks(baseline, candidate)

    assert result["improvements"] == ["duplicate-charge"]
    assert result["cases"][0]["status"] == "improvement"


def test_compare_benchmarks_surfaces_case_set_mismatch():
    baseline = _benchmark()
    candidate = deepcopy(_benchmark())
    candidate["cases"].append(
        {
            "case_id": "new-case",
            "passed_trials": 2,
            "failed_trials": 0,
            "total_trials": 2,
            "pass_rate": 1.0,
            "trials": [_trial(), _trial()],
        }
    )

    result = compare_benchmarks(baseline, candidate)

    assert result["candidate_only_cases"] == ["new-case"]
    assert result["baseline_only_cases"] == []


def test_markdown_comparison_does_not_auto_declare_winner():
    result = compare_benchmarks(_benchmark(), _benchmark())

    markdown = render_comparison_markdown(
        result,
        baseline_label="Baseline #1",
        candidate_label="Candidate B",
    )

    assert "# Baseline vs Candidate Evaluation" in markdown
    assert "| Metric | Baseline #1 | Candidate B | Change |" in markdown
    assert "does not automatically declare a winner" in markdown
    assert "**Regressions:** none observed" in markdown
