"""In-memory storage and filtering for tickets."""

from __future__ import annotations

from typing import Dict, List, Optional

from models import Ticket, now_iso

_tickets: Dict[str, Ticket] = {}
_classification_log: List[dict] = []


def add(ticket: Ticket) -> Ticket:
    _tickets[ticket.id] = ticket
    return ticket


def get(ticket_id: str) -> Optional[Ticket]:
    return _tickets.get(ticket_id)


def delete(ticket_id: str) -> bool:
    return _tickets.pop(ticket_id, None) is not None


def update(ticket_id: str, changes: dict) -> Optional[Ticket]:
    t = _tickets.get(ticket_id)
    if t is None:
        return None
    for k, v in changes.items():
        if v is not None and hasattr(t, k):
            setattr(t, k, v)
    # keep resolved_at consistent with status
    if changes.get("status") == "resolved" and t.resolved_at is None:
        t.resolved_at = now_iso()
    t.updated_at = now_iso()
    return t


def list_tickets(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
) -> List[Ticket]:
    results = list(_tickets.values())
    if category:
        results = [t for t in results if t.category == category]
    if priority:
        results = [t for t in results if t.priority == priority]
    if status:
        results = [t for t in results if t.status == status]
    if customer_id:
        results = [t for t in results if t.customer_id == customer_id]
    if assigned_to:
        results = [t for t in results if t.assigned_to == assigned_to]
    # newest first
    results.sort(key=lambda t: t.created_at, reverse=True)
    return results


def count() -> int:
    return len(_tickets)


def log_classification(entry: dict) -> None:
    _classification_log.append(entry)


def classification_log() -> List[dict]:
    return list(_classification_log)


def reset() -> None:
    _tickets.clear()
    _classification_log.clear()
