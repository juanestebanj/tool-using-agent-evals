"""LLM-as-judge grading for semantic answer correctness."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any, TypedDict

from agents import Agent, Runner


JUDGE_NAME = "Semantic Outcome Judge"
DEFAULT_JUDGE_MODEL = "gpt-6-luna"

JUDGE_INSTRUCTIONS = """
You evaluate the semantic correctness of a billing-support agent's final answer.

Judge only the final answer's meaning relative to:
- the user's request
- the captured tool calls and tool outputs

Do not grade tool selection, tool ordering, or exact arguments. Deterministic graders
handle those separately.

Apply these criteria:
1. The answer addresses the user's request, or appropriately asks for missing
   information when the request cannot be answered.
2. Billing claims are grounded in the captured evidence.
3. The answer does not contradict tool outputs.
4. The answer does not invent unsupported customer, invoice, payment, refund, or
   state-change facts.

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
    result = run_sync(build_semantic_judge(model=model), build_judge_input(report))
    judgment = result.final_output

    if not isinstance(judgment, dict):
        raise TypeError(
            "Semantic judge returned an unexpected output type: "
            f"{type(judgment).__name__}"
        )

    dimensions = (
        "answers_request",
        "grounded_in_evidence",
        "no_contradictions",
        "no_unsupported_claims",
    )

    for field in dimensions:
        if not isinstance(judgment.get(field), bool):
            raise TypeError(f"Semantic judge field {field!r} must be a boolean.")

    if not isinstance(judgment.get("reason"), str):
        raise TypeError("Semantic judge field 'reason' must be a string.")

    return {
        **judgment,
        "passed": all(judgment[field] for field in dimensions),
    }
