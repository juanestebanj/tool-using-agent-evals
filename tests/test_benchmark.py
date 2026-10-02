from copy import deepcopy

from evals.benchmark import build_benchmark_report, evaluate_trial
from evals.cases import DUPLICATE_CHARGE_CASE, MISSING_INVOICE_ID_CASE
from evals.run_benchmark import run_live_benchmark


def _usage_metrics(*, tokens=100, cost=0.001, requests=1):
    return {
        "model": "gpt-6-luna",
        "requests": requests,
        "input_tokens": tokens - 20,
        "output_tokens": 20,
        "total_tokens": tokens,
        "estimated_cost_usd": cost,
    }


def _passing_duplicate_report():
    return {
        "prompt": DUPLICATE_CHARGE_CASE.prompt,
        "final_output": (
            "Invoice INV-1042 was charged twice. "
            "Two successful payments were recorded."
        ),
        "elapsed_seconds": 2.0,
        "usage_metrics": _usage_metrics(tokens=120, cost=0.0012, requests=2),
        "trajectory": [
            {
                "type": "tool_call",
                "name": "check_payment",
                "arguments": {"invoice_id": "INV-1042"},
                "call_id": "call-1",
            }
        ],
        "semantic_judgment": {
            "passed": True,
            "answers_request": True,
            "grounded_in_evidence": True,
            "no_contradictions": True,
            "no_unsupported_claims": True,
            "reason": "Grounded.",
            "elapsed_seconds": 0.5,
            "usage_metrics": _usage_metrics(tokens=60, cost=0.0004),
        },
    }


def _passing_missing_id_report():
    return {
        "prompt": MISSING_INVOICE_ID_CASE.prompt,
        "final_output": "Please provide the invoice ID.",
        "elapsed_seconds": 1.0,
        "usage_metrics": _usage_metrics(tokens=80, cost=0.0008),
        "trajectory": [],
        "semantic_judgment": {
            "passed": True,
            "answers_request": True,
            "grounded_in_evidence": True,
            "no_contradictions": True,
            "no_unsupported_claims": True,
            "reason": "Correctly asks for the missing identifier.",
            "elapsed_seconds": 0.4,
            "usage_metrics": _usage_metrics(tokens=50, cost=0.0003),
        },
    }


def test_evaluate_trial_grades_one_report():
    result = evaluate_trial(
        case=DUPLICATE_CHARGE_CASE,
        trial_number=2,
        report=_passing_duplicate_report(),
    )

    assert result["trial"] == 2
    assert result["passed"] is True
    assert result["evaluation"]["passed"] is True


def test_build_benchmark_report_aggregates_repeated_trials():
    cases = {
        DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE,
        MISSING_INVOICE_ID_CASE.id: MISSING_INVOICE_ID_CASE,
    }
    trial_results = {
        "duplicate-charge": [
            evaluate_trial(
                case=DUPLICATE_CHARGE_CASE,
                trial_number=1,
                report=_passing_duplicate_report(),
            ),
            evaluate_trial(
                case=DUPLICATE_CHARGE_CASE,
                trial_number=2,
                report=_passing_duplicate_report(),
            ),
        ],
        "missing-invoice-id": [
            evaluate_trial(
                case=MISSING_INVOICE_ID_CASE,
                trial_number=1,
                report=_passing_missing_id_report(),
            ),
            evaluate_trial(
                case=MISSING_INVOICE_ID_CASE,
                trial_number=2,
                report=_passing_missing_id_report(),
            ),
        ],
    }

    result = build_benchmark_report(
        trial_results,
        cases,
        trials_per_case=2,
    )

    assert result["passed"] is True
    assert result["total_trials"] == 4
    assert result["passed_trials"] == 4
    assert result["pass_rate"] == 1.0
    assert result["cases"][0]["total_trials"] == 2
    assert result["metrics"]["agent"]["latency_seconds"]["sample_count"] == 4


def test_run_live_benchmark_repeats_each_case_without_live_api_calls():
    cases = {DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE}
    calls = []

    def fake_run_case(prompt):
        calls.append(prompt)
        return _passing_duplicate_report()

    def fake_judge(report):
        return deepcopy(report["semantic_judgment"])

    result = run_live_benchmark(
        trials_per_case=3,
        cases=cases,
        run_case_fn=fake_run_case,
        judge_report_fn=fake_judge,
    )

    assert calls == [DUPLICATE_CHARGE_CASE.prompt] * 3
    assert result["total_trials"] == 3
    assert result["passed_trials"] == 3
    assert result["pass_rate"] == 1.0


def test_execution_failure_counts_as_failed_trial():
    cases = {DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE}
    trial_results = {
        "duplicate-charge": [
            {
                "trial": 1,
                "passed": False,
                "error": {"type": "RuntimeError", "message": "model unavailable"},
                "report": {
                    "prompt": DUPLICATE_CHARGE_CASE.prompt,
                    "trajectory": [],
                    "error": {
                        "type": "RuntimeError",
                        "message": "model unavailable",
                    },
                },
            }
        ]
    }

    result = build_benchmark_report(
        trial_results,
        cases,
        trials_per_case=1,
    )

    assert result["passed"] is False
    assert result["failed_trials"] == 1
    assert result["pass_rate"] == 0.0
