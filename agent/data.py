"""Deterministic synthetic billing records used by tests and later agent evals.

The dataset is intentionally small, explicit, and stable. It is not production data.
Amounts are stored as integer cents to avoid floating-point ambiguity in tests.
"""

from typing import Final, TypedDict


class CustomerRecord(TypedDict):
    customer_id: str
    name: str
    email: str
    status: str


class InvoiceRecord(TypedDict):
    invoice_id: str
    customer_id: str
    amount_cents: int
    currency: str
    status: str
    due_date: str


class PaymentRecord(TypedDict):
    payment_id: str
    invoice_id: str
    amount_cents: int
    currency: str
    status: str
    created_at: str


CUSTOMERS: Final[dict[str, CustomerRecord]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Alice Morgan",
        "email": "alice@example.com",
        "status": "active",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Diego Ruiz",
        "email": "diego@example.com",
        "status": "active",
    },
}

INVOICES: Final[dict[str, InvoiceRecord]] = {
    "INV-1042": {
        "invoice_id": "INV-1042",
        "customer_id": "CUST-001",
        "amount_cents": 12000,
        "currency": "USD",
        "status": "paid",
        "due_date": "2026-09-15",
    },
    "INV-1043": {
        "invoice_id": "INV-1043",
        "customer_id": "CUST-001",
        "amount_cents": 7500,
        "currency": "USD",
        "status": "open",
        "due_date": "2026-10-15",
    },
    "INV-2001": {
        "invoice_id": "INV-2001",
        "customer_id": "CUST-002",
        "amount_cents": 4999,
        "currency": "USD",
        "status": "paid",
        "due_date": "2026-09-20",
    },
}

PAYMENTS: Final[tuple[PaymentRecord, ...]] = (
    {
        "payment_id": "PAY-9001",
        "invoice_id": "INV-1042",
        "amount_cents": 12000,
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2026-09-10T14:02:00Z",
    },
    {
        "payment_id": "PAY-9002",
        "invoice_id": "INV-1042",
        "amount_cents": 12000,
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2026-09-10T14:03:00Z",
    },
    {
        "payment_id": "PAY-9003",
        "invoice_id": "INV-1043",
        "amount_cents": 7500,
        "currency": "USD",
        "status": "failed",
        "created_at": "2026-09-22T09:30:00Z",
    },
    {
        "payment_id": "PAY-9004",
        "invoice_id": "INV-2001",
        "amount_cents": 4999,
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2026-09-18T18:45:00Z",
    },
)
