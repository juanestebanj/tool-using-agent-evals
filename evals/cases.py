"""Named evaluation cases for tool-using agent behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvalCase:
    """Expected deterministic trajectory properties for one agent task."""

    id: str
    prompt: str
    required_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    expected_arguments: dict[str, dict[str, Any]]
    ordered_tools: tuple[str, ...]


DUPLICATE_CHARGE_CASE = EvalCase(
    id="duplicate-charge",
    prompt="I think invoice INV-1042 was charged twice.",
    required_tools=("get_invoice", "check_payment"),
    forbidden_tools=("get_customer",),
    expected_arguments={
        "get_invoice": {"invoice_id": "INV-1042"},
        "check_payment": {"invoice_id": "INV-1042"},
    },
    ordered_tools=("get_invoice", "check_payment"),
)

CASES: dict[str, EvalCase] = {
    DUPLICATE_CHARGE_CASE.id: DUPLICATE_CHARGE_CASE,
}
