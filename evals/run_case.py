"""Run one live agent case and capture its tool-use trajectory as JSON."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agents import Runner

from agent.agent import build_agent
from evals.metrics import serialize_usage


def _raw_field(item: Any, name: str) -> Any:
    """Read a field from an SDK item's raw payload without assuming one shape."""
    raw_item = getattr(item, "raw_item", None)
    if isinstance(raw_item, Mapping):
        return raw_item.get(name)
    return getattr(raw_item, name, None)


def _parse_arguments(arguments: Any) -> Any:
    """Parse JSON tool arguments when possible while preserving unexpected values."""
    if not isinstance(arguments, str):
        return arguments
    try:
        return json.loads(arguments)
    except json.JSONDecodeError:
        return arguments


def serialize_tool_trajectory(items: list[Any]) -> list[dict[str, Any]]:
    """Extract tool calls and outputs from Agents SDK run items.

    The SDK may expose raw items as typed objects or mappings, so this function uses
    a mapping-safe inspection pattern and stores only the fields needed for evals.
    """
    trajectory: list[dict[str, Any]] = []

    for item in items:
        item_type = getattr(item, "type", None)

        if item_type == "tool_call_item":
            trajectory.append(
                {
                    "type": "tool_call",
                    "name": _raw_field(item, "name"),
                    "arguments": _parse_arguments(_raw_field(item, "arguments")),
                    "call_id": _raw_field(item, "call_id") or _raw_field(item, "id"),
                }
            )
        elif item_type == "tool_call_output_item":
            call_id = getattr(item, "call_id", None)
            if callable(call_id):
                call_id = call_id()
            trajectory.append(
                {
                    "type": "tool_output",
                    "call_id": call_id
                    or _raw_field(item, "call_id")
                    or _raw_field(item, "id"),
                    "output": getattr(item, "output", None),
                }
            )

    return trajectory


def run_case(prompt: str) -> dict[str, Any]:
    """Execute one live agent case and return an evaluation-friendly report."""
    agent = build_agent()
    started = time.perf_counter()
    result = Runner.run_sync(agent, prompt)
    elapsed_seconds = time.perf_counter() - started

    return {
        "prompt": prompt,
        "final_output": result.final_output,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "usage_metrics": serialize_usage(
            result.context_wrapper.usage,
            model=str(agent.model),
        ),
        "trajectory": serialize_tool_trajectory(result.new_items),
    }


def write_report(report: dict[str, Any], output_path: Path) -> None:
    """Write a run report without mutating repository source files."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompt",
        default="I think invoice INV-1042 was charged twice.",
        help="User prompt to send to the billing agent.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/live-run.json"),
        help="Path for the captured JSON report.",
    )
    args = parser.parse_args()

    report = run_case(args.prompt)
    write_report(report, args.output)
    print(json.dumps(report, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
