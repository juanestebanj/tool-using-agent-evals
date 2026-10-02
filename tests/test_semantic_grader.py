from types import SimpleNamespace

import pytest

from evals.semantic_grader import (
    EVALUATED_AGENT_CAPABILITIES,
    JUDGE_INSTRUCTIONS,
    build_judge_input,
    build_semantic_judge,
    judge_report,
)


def _usage():
    return SimpleNamespace(
        requests=1,
        input_tokens=100,
        output_tokens=20,
        total_tokens=120,
        input_tokens_details=SimpleNamespace(
            cached_tokens=0,
            cache_write_tokens=0,
        ),
        output_tokens_details=SimpleNamespace(reasoning_tokens=5),
    )


def _result(final_output):
    return SimpleNamespace(
        final_output=final_output,
        context_wrapper=SimpleNamespace(usage=_usage()),
    )


def _report():
    return {
        "prompt": "Was invoice INV-2001 charged more than once?",
        "trajectory": [
            {
                "type": "tool_call",
                "name": "check_payment",
                "arguments": {"invoice_id": "INV-2001"},
                "call_id": "call-1",
            },
            {
                "type": "tool_output",
                "call_id": "call-1",
                "output": {
                    "invoice_id": "INV-2001",
                    "matching_successful_payments": 1,
                    "duplicate": False,
                },
            },
        ],
        "final_output": "No. INV-2001 has one successful payment.",
    }


def test_semantic_judge_has_no_tools_and_uses_structured_output():
    judge = build_semantic_judge(model="gpt-6-luna")

    assert judge.tools == []
    assert judge.output_type is not str
    assert "Do not grade tool selection" in JUDGE_INSTRUCTIONS
    assert "declared capabilities" in JUDGE_INSTRUCTIONS


def test_build_judge_input_contains_prompt_trajectory_and_answer():
    text = build_judge_input(_report())

    assert "INV-2001" in text
    assert "check_payment" in text
    assert "one successful payment" in text
    assert '"can_issue_refunds": false' in text
    assert '"billing_tools_are_read_only": true' in text
    assert EVALUATED_AGENT_CAPABILITIES["can_change_billing_state"] is False


def test_judge_report_passes_when_all_rubric_dimensions_pass():
    def fake_run_sync(agent, prompt):
        return _result({
                "answers_request": True,
                "grounded_in_evidence": True,
                "no_contradictions": True,
                "no_unsupported_claims": True,
                "reason": "The answer matches the payment evidence.",
            })

    result = judge_report(_report(), run_sync=fake_run_sync, model="gpt-6-luna")

    assert result["passed"] is True
    assert result["reason"] == "The answer matches the payment evidence."


def test_judge_report_fails_when_any_semantic_dimension_fails():
    def fake_run_sync(agent, prompt):
        return _result({
                "answers_request": True,
                "grounded_in_evidence": True,
                "no_contradictions": False,
                "no_unsupported_claims": True,
                "reason": "The answer contradicts the tool output.",
            })

    result = judge_report(_report(), run_sync=fake_run_sync)

    assert result["passed"] is False
    assert result["no_contradictions"] is False


def test_judge_report_rejects_malformed_boolean_field():
    def fake_run_sync(agent, prompt):
        return _result({
                "answers_request": "yes",
                "grounded_in_evidence": True,
                "no_contradictions": True,
                "no_unsupported_claims": True,
                "reason": "Malformed.",
            })

    with pytest.raises(TypeError, match="answers_request"):
        judge_report(_report(), run_sync=fake_run_sync)
