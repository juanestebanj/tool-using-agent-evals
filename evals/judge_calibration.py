"""Deterministic analysis for semantic-judge calibration against human labels."""

from __future__ import annotations

from typing import Any

from evals.semantic_grader import SEMANTIC_DIMENSIONS


CALIBRATION_SET_VERSION = "2026-10-04-v1"


def _safe_divide(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _binary_metrics(
    human_values: list[bool],
    judge_values: list[bool],
) -> dict[str, Any]:
    if len(human_values) != len(judge_values):
        raise ValueError("Human and judge label counts must match.")

    tp = sum(
        1
        for human, judge in zip(human_values, judge_values)
        if human and judge
    )
    tn = sum(
        1
        for human, judge in zip(human_values, judge_values)
        if not human and not judge
    )
    fp = sum(
        1
        for human, judge in zip(human_values, judge_values)
        if not human and judge
    )
    fn = sum(
        1
        for human, judge in zip(human_values, judge_values)
        if human and not judge
    )
    total = len(human_values)

    return {
        "sample_count": total,
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": _safe_divide(tp + tn, total),
        "precision": _safe_divide(tp, tp + fp),
        "recall": _safe_divide(tp, tp + fn),
        "specificity": _safe_divide(tn, tn + fp),
        "false_positive_rate": _safe_divide(fp, fp + tn),
        "false_negative_rate": _safe_divide(fn, fn + tp),
    }


def _usage_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    elapsed = 0.0
    requests = 0
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    estimated_cost = 0.0
    priced = 0
    measured = 0
    models: set[str] = set()

    for result in case_results:
        judgment = result.get("judge_label")
        if not isinstance(judgment, dict):
            continue
        if judgment.get("error"):
            continue

        measured += 1
        elapsed += float(judgment.get("elapsed_seconds", 0) or 0)
        usage = judgment.get("usage_metrics")
        if not isinstance(usage, dict):
            continue

        model = usage.get("model")
        if model:
            models.add(str(model))
        requests += int(usage.get("requests", 0) or 0)
        input_tokens += int(usage.get("input_tokens", 0) or 0)
        output_tokens += int(usage.get("output_tokens", 0) or 0)
        total_tokens += int(usage.get("total_tokens", 0) or 0)
        cost = usage.get("estimated_cost_usd")
        if isinstance(cost, (int, float)):
            estimated_cost += float(cost)
            priced += 1

    return {
        "measured_cases": measured,
        "models": sorted(models),
        "elapsed_seconds": round(elapsed, 3),
        "requests": requests,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": (
            round(estimated_cost, 8)
            if measured > 0 and priced == measured
            else None
        ),
    }


def build_calibration_report(
    calibration_cases: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    judgments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compare live judge labels with independent human labels."""
    case_results: list[dict[str, Any]] = []
    execution_errors = 0

    human_pass_values: list[bool] = []
    judge_pass_values: list[bool] = []
    per_dimension_human = {name: [] for name in SEMANTIC_DIMENSIONS}
    per_dimension_judge = {name: [] for name in SEMANTIC_DIMENSIONS}

    for case in calibration_cases:
        case_id = str(case["id"])
        human = case["human_label"]
        judgment = judgments.get(case_id)

        if not isinstance(judgment, dict) or judgment.get("error"):
            execution_errors += 1
            case_results.append(
                {
                    "case_id": case_id,
                    "human_label": human,
                    "judge_label": judgment,
                    "overall_agreement": False,
                    "exact_rubric_match": False,
                    "dimension_agreement": {},
                    "human_rationale": case.get("human_rationale", ""),
                }
            )
            continue

        human_pass = bool(human["passed"])
        judge_pass = bool(judgment["passed"])
        human_pass_values.append(human_pass)
        judge_pass_values.append(judge_pass)

        dimension_agreement: dict[str, bool] = {}
        for dimension in SEMANTIC_DIMENSIONS:
            human_value = bool(human[dimension])
            judge_value = bool(judgment[dimension])
            per_dimension_human[dimension].append(human_value)
            per_dimension_judge[dimension].append(judge_value)
            dimension_agreement[dimension] = human_value == judge_value

        case_results.append(
            {
                "case_id": case_id,
                "human_label": human,
                "judge_label": judgment,
                "overall_agreement": human_pass == judge_pass,
                "exact_rubric_match": all(dimension_agreement.values()),
                "dimension_agreement": dimension_agreement,
                "human_rationale": case.get("human_rationale", ""),
            }
        )

    comparable_cases = len(human_pass_values)
    overall_metrics = _binary_metrics(human_pass_values, judge_pass_values)

    dimension_metrics = {
        dimension: _binary_metrics(
            per_dimension_human[dimension],
            per_dimension_judge[dimension],
        )
        for dimension in SEMANTIC_DIMENSIONS
    }

    exact_matches = sum(
        1 for result in case_results if result.get("exact_rubric_match") is True
    )
    overall_agreements = sum(
        1 for result in case_results if result.get("overall_agreement") is True
    )

    false_positive_cases = [
        result["case_id"]
        for result in case_results
        if isinstance(result.get("judge_label"), dict)
        and not result["judge_label"].get("error")
        and result["human_label"]["passed"] is False
        and result["judge_label"].get("passed") is True
    ]
    false_negative_cases = [
        result["case_id"]
        for result in case_results
        if isinstance(result.get("judge_label"), dict)
        and not result["judge_label"].get("error")
        and result["human_label"]["passed"] is True
        and result["judge_label"].get("passed") is False
    ]
    rubric_disagreement_cases = [
        result["case_id"]
        for result in case_results
        if result.get("exact_rubric_match") is False
        and isinstance(result.get("judge_label"), dict)
        and not result["judge_label"].get("error")
    ]

    return {
        "calibration_set_version": CALIBRATION_SET_VERSION,
        "case_count": len(calibration_cases),
        "comparable_cases": comparable_cases,
        "execution_errors": execution_errors,
        "overall_pass_label": overall_metrics,
        "overall_agreement_rate": _safe_divide(
            overall_agreements,
            comparable_cases,
        ),
        "exact_rubric_match_rate": _safe_divide(
            exact_matches,
            comparable_cases,
        ),
        "dimension_metrics": dimension_metrics,
        "false_positive_cases": false_positive_cases,
        "false_negative_cases": false_negative_cases,
        "rubric_disagreement_cases": rubric_disagreement_cases,
        "usage": _usage_summary(case_results),
        "cases": case_results,
    }


def _pct(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def render_calibration_markdown(report: dict[str, Any]) -> str:
    """Render calibration diagnostics without imposing an acceptance threshold."""
    overall = report["overall_pass_label"]
    usage = report["usage"]

    lines = [
        "# Semantic Judge Calibration Report",
        "",
        f"- **Calibration set:** {report['calibration_set_version']}",
        f"- **Human-labeled cases:** {report['case_count']}",
        f"- **Comparable cases:** {report['comparable_cases']}",
        f"- **Execution errors:** {report['execution_errors']}",
        f"- **Overall pass/fail accuracy:** {_pct(overall['accuracy'])}",
        f"- **False-positive rate:** {_pct(overall['false_positive_rate'])}",
        f"- **False-negative rate:** {_pct(overall['false_negative_rate'])}",
        f"- **Exact four-dimension rubric match:** "
        f"{_pct(report['exact_rubric_match_rate'])}",
        "",
        "A false positive means the judge passed an answer that the human label marked "
        "as failing. For a gating evaluator, that is usually the more dangerous error.",
        "",
        "## Confusion matrix",
        "",
        "| | Judge pass | Judge fail |",
        "| --- | ---: | ---: |",
        f"| Human pass | {overall['true_positive']} | {overall['false_negative']} |",
        f"| Human fail | {overall['false_positive']} | {overall['true_negative']} |",
        "",
        "## Rubric-dimension agreement",
        "",
        "| Dimension | Accuracy | False-positive rate | False-negative rate |",
        "| --- | ---: | ---: | ---: |",
    ]

    for dimension in SEMANTIC_DIMENSIONS:
        metrics = report["dimension_metrics"][dimension]
        lines.append(
            f"| {dimension} | {_pct(metrics['accuracy'])} | "
            f"{_pct(metrics['false_positive_rate'])} | "
            f"{_pct(metrics['false_negative_rate'])} |"
        )

    lines.extend([
        "",
        "## Disagreements",
        "",
        "**False-positive cases:** "
        + (
            ", ".join(report["false_positive_cases"])
            if report["false_positive_cases"]
            else "none"
        ),
        "",
        "**False-negative cases:** "
        + (
            ", ".join(report["false_negative_cases"])
            if report["false_negative_cases"]
            else "none"
        ),
        "",
        "**Any rubric-dimension disagreement:** "
        + (
            ", ".join(report["rubric_disagreement_cases"])
            if report["rubric_disagreement_cases"]
            else "none"
        ),
        "",
        "## Judge execution cost",
        "",
        f"- **Models:** {', '.join(usage['models']) if usage['models'] else 'n/a'}",
        f"- **Elapsed judge time:** {usage['elapsed_seconds']:.3f} s",
        f"- **Input tokens:** {usage['input_tokens']}",
        f"- **Output tokens:** {usage['output_tokens']}",
        f"- **Total tokens:** {usage['total_tokens']}",
        "- **Estimated cost:** "
        + (
            "$" + f"{usage['estimated_cost_usd']:.8f}"
            if usage["estimated_cost_usd"] is not None
            else "n/a"
        ),
        "",
        "## Interpretation",
        "",
        "Calibration measures agreement with an independent human-labeled set; it does "
        "not prove that either the judge or the human labels are infallible. Disagreements "
        "should be reviewed case by case before changing the judge prompt or acceptance "
        "policy. This report intentionally does not define a universal pass threshold.",
        "",
    ])

    return "\n".join(lines)
