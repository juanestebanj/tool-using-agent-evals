from types import SimpleNamespace

from evals.run_case import serialize_tool_trajectory


def test_serialize_tool_trajectory_captures_calls_and_outputs():
    items = [
        SimpleNamespace(
            type="tool_call_item",
            raw_item={
                "type": "function_call",
                "name": "check_payment",
                "arguments": '{"invoice_id":"INV-1042"}',
                "call_id": "call-1",
            },
        ),
        SimpleNamespace(
            type="tool_call_output_item",
            raw_item={"type": "function_call_output", "call_id": "call-1"},
            call_id="call-1",
            output={"ok": True, "duplicate_charge_detected": True},
        ),
    ]

    assert serialize_tool_trajectory(items) == [
        {
            "type": "tool_call",
            "name": "check_payment",
            "arguments": {"invoice_id": "INV-1042"},
            "call_id": "call-1",
        },
        {
            "type": "tool_output",
            "call_id": "call-1",
            "output": {"ok": True, "duplicate_charge_detected": True},
        },
    ]


def test_serialize_tool_trajectory_ignores_non_tool_items():
    items = [SimpleNamespace(type="message_output_item", raw_item={"type": "message"})]

    assert serialize_tool_trajectory(items) == []


def test_serialize_tool_trajectory_preserves_non_json_arguments():
    items = [
        SimpleNamespace(
            type="tool_call_item",
            raw_item={
                "name": "get_invoice",
                "arguments": "not-json",
                "call_id": "call-2",
            },
        )
    ]

    result = serialize_tool_trajectory(items)

    assert result[0]["arguments"] == "not-json"
