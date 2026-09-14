"""In-memory storage for transactions and the derived balance/summary logic.

No database is used — data lives in a module-level list for the life of the
process, exactly as the assignment requests.
"""

from __future__ import annotations

from datetime import datetime, date

from models import Transaction

# The one and only "table".
_transactions: list[Transaction] = []


def add(tx: Transaction) -> Transaction:
    _transactions.append(tx)
    return tx


def get(tx_id: str) -> Transaction | None:
    return next((t for t in _transactions if t.id == tx_id), None)


def _parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def list_transactions(
    account_id: str | None = None,
    tx_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[Transaction]:
    """Return transactions, optionally narrowed by any combination of filters."""
    results = list(_transactions)

    if account_id:
        results = [
            t for t in results
            if t.fromAccount == account_id or t.toAccount == account_id
        ]

    if tx_type:
        results = [t for t in results if t.type == tx_type]

    # Date range filtering compares calendar dates (inclusive on both ends).
    if date_from:
        try:
            start = date.fromisoformat(date_from)
            results = [
                t for t in results
                if (dt := _parse_ts(t.timestamp)) and dt.date() >= start
            ]
        except ValueError:
            pass
    if date_to:
        try:
            end = date.fromisoformat(date_to)
            results = [
                t for t in results
                if (dt := _parse_ts(t.timestamp)) and dt.date() <= end
            ]
        except ValueError:
            pass

    return results


def balance(account_id: str) -> dict:
    """Compute the net balance for an account from completed transactions.

    Rules:
      - deposit    -> credits toAccount
      - withdrawal -> debits fromAccount
      - transfer   -> debits fromAccount and credits toAccount
    Only transactions with status == "completed" affect the balance.
    """
    total = 0.0
    for t in _transactions:
        if t.status != "completed":
            continue
        if t.type == "deposit" and t.toAccount == account_id:
            total += t.amount
        elif t.type == "withdrawal" and t.fromAccount == account_id:
            total -= t.amount
        elif t.type == "transfer":
            if t.toAccount == account_id:
                total += t.amount
            if t.fromAccount == account_id:
                total -= t.amount
    return {"accountId": account_id, "balance": round(total, 2)}


def summary(account_id: str) -> dict:
    """Bonus feature (Option A): per-account transaction summary."""
    related = [
        t for t in _transactions
        if t.fromAccount == account_id or t.toAccount == account_id
    ]
    total_deposits = round(
        sum(t.amount for t in related if t.type == "deposit" and t.toAccount == account_id),
        2,
    )
    total_withdrawals = round(
        sum(t.amount for t in related if t.type == "withdrawal" and t.fromAccount == account_id),
        2,
    )
    most_recent = None
    dated = [(_parse_ts(t.timestamp), t) for t in related]
    dated = [(d, t) for d, t in dated if d is not None]
    if dated:
        most_recent = max(dated, key=lambda pair: pair[0])[1].timestamp

    return {
        "accountId": account_id,
        "totalDeposits": total_deposits,
        "totalWithdrawals": total_withdrawals,
        "transactionCount": len(related),
        "mostRecentTransactionDate": most_recent,
    }


def all_transactions() -> list[Transaction]:
    return list(_transactions)


def reset() -> None:
    """Clear all data (used by tests / seeding)."""
    _transactions.clear()
