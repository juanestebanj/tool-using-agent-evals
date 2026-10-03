from evals.render_report import render_benchmark_report


def _metrics(*, mean, p50, p95, tokens, mean_cost, total_cost, successful_cost=None):
    return {
        "latency_seconds": {
            "sample_count": 4,
            "mean": mean,
            "p50": p50,
            "p95": p95,
        },
        "mean_tokens_per_measured_trial": tokens,
        "estimated_cost_usd": {
            "total": total_cost,
            "mean_per_measured_trial": mean_cost,
            "per_successful_trial": successful_cost,
            "fully_priced": True,
        },
    }


def _benchmark_report():
    passing_trial = {
        "trial": 1,
        "passed": True,
        "evaluation": {
            "passed": True,
            "gating_checks": ["required_tools", "semantic_outcome"],
            "checks": {
                "required_tools": {"passed": True},
                "semantic_outcome": {"passed": True},
            },
        },
        "report": {
            "trajectory": [
                {"type": "tool_call", "name": "check_payment"}
            ]
        },
    }
    failing_trial = {
        "trial": 2,
        "passed": False,
        "evaluation": {
            "passed": False,
            "gating_checks": ["required_tools", "semantic_outcome"],
            "checks": {
                "required_tools": {"passed": False},
                "semantic_outcome": {"passed": True},
            },
        },
        "report": {
            "trajectory": [
                {"type": "tool_call", "name": "get_invoice"}
            ]
        },
    }

    return {
        "passed": False,
        "case_count": 1,
        "trials_per_case": 2,
        "passed_trials": 1,
        "failed_trials": 1,
        "total_trials": 2,
        "pass_rate": 0.5,
        "metrics": {
            "agent": _metrics(
                mean=2.5,
                p50=2.5,
                p95=2.95,
                tokens=1000,
                mean_cost=0.00012,
                total_cost=0.00024,
                successful_cost=0.00024,
            ),
            "judge": _metrics(
                mean=1.0,
                p50=1.0,
                p95=1.2,
                tokens=500,
                mean_cost=0.00008,
                total_cost=0.00016,
            ),
            "evaluation": {
                "combined_measured_latency_seconds": 7.0,
                "estimated_total_cost_usd": 0.0004,
                "pricing_as_of": "2026-10-01",
            },
        },
        "cases": [
            {
                "case_id": "duplicate-charge",
                "passed_trials": 1,
                "failed_trials": 1,
                "total_trials": 2,
                "pass_rate": 0.5,
                "metrics": {
                    "agent": _metrics(
                        mean=2.5,
                        p50=2.5,
                        p95=2.95,
                        tokens=1000,
                        mean_cost=0.00012,
                        total_cost=0.00024,
                        successful_cost=0.00024,
                    ),
                    "judge": _metrics(
                        mean=1.0,
                        p50=1.0,
                        p95=1.2,
                        tokens=500,
                        mean_cost=0.00008,
                        total_cost=0.00016,
                    ),
                    "evaluation": {
                        "combined_measured_latency_seconds": 7.0,
                        "estimated_total_cost_usd": 0.0004,
                        "pricing_as_of": "2026-10-01",
                    },
                },
                "trials": [passing_trial, failing_trial],
            }
        ],
    }


def test_render_benchmark_report_summarizes_quality_latency_and_cost():
    markdown = render_benchmark_report(
        _benchmark_report(),
        source_label="Benchmark #1",
        source_url="https://example.test/run/1",
        commit_sha="abc123",
    )

    assert "# Evaluation Report" in markdown
    assert "**Observed pass rate:** 50.0% (1/2 live trials)" in markdown
    assert "mean 2.500 s, p50 2.500 s, p95 2.950 s" in markdown
    assert "$0.00012000" in markdown
    assert "[Benchmark #1](https://example.test/run/1)" in markdown
    assert "commit `abc123`" in markdown
    assert "| duplicate-charge | 1/2 | 50.0% |" in markdown


def test_render_benchmark_report_surfaces_failed_checks_and_trajectory():
    markdown = render_benchmark_report(_benchmark_report())

    assert "**duplicate-charge, trial 2:**" in markdown
    assert "failed checks: required_tools" in markdown
    assert "tool trajectory: get_invoice" in markdown


def test_render_benchmark_report_explains_statistical_scope():
    markdown = render_benchmark_report(_benchmark_report())

    assert "not a claim of perfect production reliability" in markdown
    assert "Per-case percentile estimates use only 2 observations" in markdown


def test_render_benchmark_report_handles_all_passed_run():
    report = _benchmark_report()
    report["passed"] = True
    report["passed_trials"] = 2
    report["failed_trials"] = 0
    report["pass_rate"] = 1.0
    report["cases"][0]["passed_trials"] = 2
    report["cases"][0]["failed_trials"] = 0
    report["cases"][0]["pass_rate"] = 1.0
    for trial in report["cases"][0]["trials"]:
        trial["passed"] = True
        trial["evaluation"]["passed"] = True
        trial["evaluation"]["checks"]["required_tools"]["passed"] = True

    markdown = render_benchmark_report(report)

    assert "No failed trials were observed in this benchmark run." in markdown
