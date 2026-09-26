from agent.data import CUSTOMERS
from agent.tools import check_payment, get_customer, get_invoice


def test_get_customer_returns_known_customer():
    result = get_customer("CUST-001")

    assert result["ok"] is True
    assert result["customer"]["customer_id"] == "CUST-001"
    assert result["customer"]["name"] == "Alice Morgan"


def test_get_customer_returns_copy_not_shared_state():
    result = get_customer("CUST-001")
    result["customer"]["name"] = "Changed"

    assert CUSTOMERS["CUST-001"]["name"] == "Alice Morgan"


def test_get_customer_returns_stable_not_found_result():
    assert get_customer("CUST-999") == {
        "ok": False,
        "error": "customer_not_found",
        "customer_id": "CUST-999",
    }


def test_get_invoice_returns_known_invoice():
    result = get_invoice("INV-1042")

    assert result["ok"] is True
    assert result["invoice"]["customer_id"] == "CUST-001"
    assert result["invoice"]["amount_cents"] == 12000
    assert result["invoice"]["currency"] == "USD"


def test_get_invoice_returns_stable_not_found_result():
    assert get_invoice("INV-9999") == {
        "ok": False,
        "error": "invoice_not_found",
        "invoice_id": "INV-9999",
    }


def test_check_payment_detects_duplicate_successful_charge():
    result = check_payment("INV-1042")

    assert result["ok"] is True
    assert result["successful_matching_payments"] == 2
    assert result["total_successful_cents"] == 24000
    assert result["duplicate_charge_detected"] is True


def test_check_payment_does_not_count_failed_payment_as_duplicate():
    result = check_payment("INV-1043")

    assert result["ok"] is True
    assert len(result["payments"]) == 1
    assert result["successful_matching_payments"] == 0
    assert result["total_successful_cents"] == 0
    assert result["duplicate_charge_detected"] is False


def test_check_payment_single_success_is_not_duplicate():
    result = check_payment("INV-2001")

    assert result["ok"] is True
    assert result["successful_matching_payments"] == 1
    assert result["duplicate_charge_detected"] is False


def test_check_payment_returns_not_found_for_unknown_invoice():
    assert check_payment("INV-9999") == {
        "ok": False,
        "error": "invoice_not_found",
        "invoice_id": "INV-9999",
    }
