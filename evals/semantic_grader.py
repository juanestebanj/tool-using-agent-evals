"""LLM-as-judge grading for semantic answer correctness."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from typing import Any

from typing_extensions import TypedDict

from agents import Agent, Runner

from evals.metrics import serialize_usage


JUDGE_NAME = "Semantic Outcome Judge"
DEFAULT_JUDGE_MODEL = "gpt-6-luna"
SEMANTIC_DIMENSIONS = (
    "answers_request",
    "grounded_in_evidence",
    "no_contradictions",
    "no_unsupported_claims",
)

EVALUATED_AGENT_CAPABILITIES = {
    "billing_tools_are_read_only": True,
    "can_change_billing_state": False,
    "can_issue_refunds": False,
}

JUDGE_INSTRUCTIONS = """
You evaluate the semantic correctness of a billing-support agent's final answer.

Judge only the final answer's meaning relative to:
- the user's request
- the captured tool calls and tool outputs
- the declared capabilities of the evaluated agent

Do not grade tool selection, tool ordering, or exact arguments. Deterministic graders
handle those separately.

Apply these criteria:
1. The answer addresses the user's request, or appropriately asks for missing
   information when the request cannot be answered.
2. Billing facts are grounded in the captured tool evidence. Capability claims may
   instead be grounded in the declared agent capabilities.
3. The answer does not contradict tool outputs or declared agent capabilities.
4. The answer does not invent unsupported customer, invoice, payment, refund,
   state-change, support-channel, or escalation facts.

Do not penalize harmless wording differences, formatting, verbosity, or synonyms.
Treat tool outputs as the source of truth for billing facts.

Return a concise reason and one boolean for each criterion.
""".strip()


class SemanticJudgeOutput(TypedDict):
    """Structured dimensions returned by the semantic judge model."""

    answers_request: bool
    grounded_in_evidence: bool
    no_contradictions: bool
    no_unsupported_claims: bool
    reason: str


def build_semantic_judge(model: str | None = None) -> Agent:
    """Create a judge agent with structured output and no tools."""
    judge_model = model or os.getenv("EVAL_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
    return Agent(
        name=JUDGE_NAME,
        instructions=JUDGE_INSTRUCTIONS,
        model=judge_model,
        output_type=SemanticJudgeOutput,
    )


def build_judge_input(report: dict[str, Any]) -> str:
    """Render one captured agent report as judge input."""
    payload = {
        "user_prompt": report.get("prompt", ""),
        "agent_capabilities": EVALUATED_AGENT_CAPABILITIES,
        "tool_trajectory": report.get("trajectory", []),
        "agent_final_answer": report.get("final_output", ""),
    }
    return (
        "Evaluate this captured agent run against the semantic rubric.\n\n"
        + json.dumps(payload, indent=2, sort_keys=True, default=str)
    )


def judge_report(
    report: dict[str, Any],
    *,
    run_sync: Callable[..., Any] = Runner.run_sync,
    model: str | None = None,
) -> dict[str, Any]:
    """Run the semantic judge and deterministically aggregate its rubric dimensions."""
    judge = build_semantic_judge(model=model)
    started = time.perf_counter()
    result = run_sync(judge, build_judge_input(report))
    elapsed_seconds = time.perf_counter() - started
    judgment = result.final_output

    if not isinstance(judgment, dict):
        raise TypeError(
            "Semantic judge returned an unexpected output type: "
            f"{type(judgment).__name__}"
        )

    for field in SEMANTIC_DIMENSIONS:
        if not isinstance(judgment.get(field), bool):
            raise TypeError(f"Semantic judge field {field!r} must be a boolean.")

    if not isinstance(judgment.get("reason"), str):
        raise TypeError("Semantic judge field 'reason' must be a string.")

    return {
        **judgment,
        "passed": all(judgment[field] for field in SEMANTIC_DIMENSIONS),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "usage_metrics": serialize_usage(
            result.context_wrapper.usage,
            model=str(judge.model),
        ),
    }
