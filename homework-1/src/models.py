"""Domain model for a banking transaction."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

# Allowed enum-like values (kept as plain sets so validators can reuse them).
TRANSACTION_TYPES = {"deposit", "withdrawal", "transfer"}
TRANSACTION_STATUSES = {"pending", "completed", "failed"}


def _now_iso() -> str:
    """Current UTC time as an ISO 8601 string (e.g. 2026-09-13T10:00:00+00:00)."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Transaction:
    """A single banking transaction held in memory.

    Fields mirror the assignment's data model exactly:
    id, fromAccount, toAccount, amount, currency, type, timestamp, status.
    """

    fromAccount: str | None
    toAccount: str | None
    amount: float
    currency: str
    type: str
    status: str = "completed"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        """Serialise to a plain dict with the canonical field ordering."""
        return {
            "id": self.id,
            "fromAccount": self.fromAccount,
            "toAccount": self.toAccount,
            "amount": self.amount,
            "currency": self.currency,
            "type": self.type,
            "timestamp": self.timestamp,
            "status": self.status,
        }


# ---------------------------------------------------------------------------
# Request model used only for the POST body. Kept permissive (business rules
# live in validators.py) but typed enough that FastAPI/Swagger renders an
# editable, pre-filled request body at /docs.
# ---------------------------------------------------------------------------
from typing import Optional  # noqa: E402
from pydantic import BaseModel  # noqa: E402


class TransactionIn(BaseModel):
    fromAccount: Optional[str] = None
    toAccount: Optional[str] = None
    amount: float
    currency: str
    type: str
    status: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "fromAccount": "ACC-12345",
                "toAccount": "ACC-67890",
                "amount": 100.50,
                "currency": "USD",
                "type": "transfer",
            }
        }
    }
