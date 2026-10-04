from copy import deepcopy

from evals.judge_calibration import (
    build_calibration_report,
    render_calibration_markdown,
)
from evals.judge_calibration_cases import CALIBRATION_CASES
from evals.run_judge_calibration import run_calibration
from evals.semantic_grader import SEMANTIC_DIMENSIONS


def _judge_from_human(case):
    human = case["human_label"]
    return {
        **{dimension: human[dimension] for dimension in SEMANTIC_DIMENSIONS},
        "passed": human["passed"],
        "reason": "Matches the human label.",
        "elapsed_seconds": 0.1,
        "usage_metrics": {
            "model": "gpt-6-luna",
            "requests": 1,
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
            "estimated_cost_usd": 0.00002,
        },
    }


def test_calibration_set_is_balanced_and_human_labels_are_consistent():
    ids = [case["id"] for case in CALIBRATION_CASES]
    labels = [case["human_label"] for case in CALIBRATION_CASES]

    assert len(CALIBRATION_CASES) == 16
    assert len(ids) == len(set(ids))
    assert sum(label["passed"] for label in labels) == 8
    assert sum(not label["passed"] for label in labels) == 8

    for label in labels:
        assert label["passed"] is all(
            label[dimension] for dimension in SEMANTIC_DIMENSIONS
        )


def test_build_calibration_report_scores_perfect_agreement():
    judgments = {
        case["id"]: _judge_from_human(case)
        for case in CALIBRATION_CASES
    }

    report = build_calibration_report(CALIBRATION_CASES, judgments)

    assert report["execution_errors"] == 0
    assert report["overall_pass_label"]["accuracy"] == 1.0
    assert report["overall_pass_label"]["false_positive"] == 0
    assert report["overall_pass_label"]["false_negative"] == 0
    assert report["exact_rubric_match_rate"] == 1.0
    assert report["false_positive_cases"] == []
    assert report["false_negative_cases"] == []
    assert report["usage"]["measured_cases"] == 16
    assert report["usage"]["estimated_cost_usd"] == 0.00032


def test_build_calibration_report_surfaces_false_positive():
    judgments = {
        case["id"]: _judge_from_human(case)
        for case in CALIBRATION_CASES
    }
    target = next(
        case for case in CALIBRATION_CASES
        if case["id"] == "fail-invented-support-channel"
    )
    judgments[target["id"]] = {
        "answers_request": True,
        "grounded_in_evidence": True,
        "no_contradictions": True,
        "no_unsupported_claims": True,
        "passed": True,
        "reason": "Incorrectly accepted.",
        "elapsed_seconds": 0.1,
        "usage_metrics": {
            "model": "gpt-6-luna",
            "requests": 1,
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
            "estimated_cost_usd": 0.00002,
        },
    }

    report = build_calibration_report(CALIBRATION_CASES, judgments)

    assert report["overall_pass_label"]["false_positive"] == 1
    assert report["overall_pass_label"]["accuracy"] == 0.9375
    assert report["false_positive_cases"] == [
        "fail-invented-support-channel"
    ]
    assert (
        report["dimension_metrics"]["no_unsupported_claims"]["accuracy"]
        == 0.9375
    )


def test_build_calibration_report_distinguishes_rubric_from_overall_agreement():
    judgments = {
        case["id"]: _judge_from_human(case)
        for case in CALIBRATION_CASES
    }
    target = next(
        case for case in CALIBRATION_CASES
        if case["id"] == "fail-duplicate-contradiction"
    )
    altered = deepcopy(judgments[target["id"]])
    altered["grounded_in_evidence"] = True
    # Overall still fails because other dimensions remain false.
    altered["passed"] = False
    judgments[target["id"]] = altered

    report = build_calibration_report(CALIBRATION_CASES, judgments)

    assert report["overall_pass_label"]["accuracy"] == 1.0
    assert report["exact_rubric_match_rate"] == 0.9375
    assert report["rubric_disagreement_cases"] == [
        "fail-duplicate-contradiction"
    ]


def test_calibration_execution_error_is_not_counted_as_label_disagreement():
    judgments = {
        case["id"]: _judge_from_human(case)
        for case in CALIBRATION_CASES
    }
    judgments["pass-customer-status"] = {
        "error": {"type": "RuntimeError", "message": "model unavailable"}
    }

    report = build_calibration_report(CALIBRATION_CASES, judgments)

    assert report["execution_errors"] == 1
    assert report["comparable_cases"] == 15
    assert "pass-customer-status" not in report["false_negative_cases"]


def test_render_calibration_markdown_explains_false_positive_risk():
    judgments = {
        case["id"]: _judge_from_human(case)
        for case in CALIBRATION_CASES
    }
    report = build_calibration_report(CALIBRATION_CASES, judgments)

    markdown = render_calibration_markdown(report)

    assert "# Semantic Judge Calibration Report" in markdown
    assert "False-positive rate" in markdown
    assert "usually the more dangerous error" in markdown
    assert "does not define a universal pass threshold" in markdown


def test_run_calibration_uses_committed_human_labels_without_live_calls():
    cases = CALIBRATION_CASES[:2]
    by_prompt = {
        case["report"]["prompt"]: _judge_from_human(case)
        for case in cases
    }

    def fake_judge(report, *, model=None):
        assert model == "test-model"
        return deepcopy(by_prompt[report["prompt"]])

    result = run_calibration(
        calibration_cases=cases,
        judge_fn=fake_judge,
        model="test-model",
    )

    assert result["case_count"] == 2
    assert result["overall_pass_label"]["accuracy"] == 1.0
