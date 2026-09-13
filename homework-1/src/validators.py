"""Validation logic for incoming transaction payloads.

Every validator appends {"field": ..., "message": ...} entries to a list so the
API can return the exact error contract required by the assignment:

    {
      "error": "Validation failed",
      "details": [ {"field": "amount", "message": "..."} ]
    }
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from currencies import is_valid_currency
from models import TRANSACTION_TYPES, TRANSACTION_STATUSES

# Account numbers follow the pattern ACC-XXXXX where X is alphanumeric (5 chars).
ACCOUNT_PATTERN = re.compile(r"^ACC-[A-Za-z0-9]{5}$")


def _is_valid_account(value) -> bool:
    return isinstance(value, str) and bool(ACCOUNT_PATTERN.match(value))


def _amount_errors(amount) -> list[dict]:
    errors: list[dict] = []
    # Reject booleans (bool is a subclass of int) and non-numeric input.
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        errors.append({"field": "amount", "message": "Amount must be a positive number"})
        return errors
    if amount <= 0:
        errors.append({"field": "amount", "message": "Amount must be a positive number"})
    # Enforce a maximum of two decimal places.
    try:
        exponent = Decimal(str(amount)).normalize().as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            errors.append({"field": "amount", "message": "Amount must have at most 2 decimal places"})
    except (InvalidOperation, ValueError):
        errors.append({"field": "amount", "message": "Amount must be a positive number"})
    return errors


def validate_transaction(payload) -> list[dict]:
    """Return a list of validation errors (empty list means the payload is valid)."""
    errors: list[dict] = []

    if not isinstance(payload, dict):
        return [{"field": "body", "message": "Request body must be a JSON object"}]

    tx_type = payload.get("type")
    from_account = payload.get("fromAccount")
    to_account = payload.get("toAccount")

    # --- type ---
    if tx_type not in TRANSACTION_TYPES:
        errors.append({
            "field": "type",
            "message": "Type must be one of: deposit, withdrawal, transfer",
        })

    # --- amount ---
    errors.extend(_amount_errors(payload.get("amount")))

    # --- currency ---
    currency = payload.get("currency")
    if not is_valid_currency(currency):
        errors.append({"field": "currency", "message": "Invalid currency code"})

    # --- accounts (which ones are required depends on the type) ---
    needs_from = tx_type in {"withdrawal", "transfer"}
    needs_to = tx_type in {"deposit", "transfer"}

    if needs_from or from_account is not None:
        if not _is_valid_account(from_account):
            errors.append({
                "field": "fromAccount",
                "message": "fromAccount must match the format ACC-XXXXX (5 alphanumeric characters)",
            })
    if needs_to or to_account is not None:
        if not _is_valid_account(to_account):
            errors.append({
                "field": "toAccount",
                "message": "toAccount must match the format ACC-XXXXX (5 alphanumeric characters)",
            })

    # --- status (optional; defaults to completed if omitted) ---
    status = payload.get("status")
    if status is not None and status not in TRANSACTION_STATUSES:
        errors.append({
            "field": "status",
            "message": "Status must be one of: pending, completed, failed",
        })

    return errors


def is_valid_account_format(value) -> bool:
    """Public helper so routes can validate accountId path params."""
    return _is_valid_account(value)
