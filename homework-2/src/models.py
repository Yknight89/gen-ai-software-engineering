"""Domain model and enums for support tickets."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from pydantic import BaseModel

# --- Enum-like allowed value sets (kept as sets so validators can reuse them) ---
CATEGORIES = {
    "account_access", "technical_issue", "billing_question",
    "feature_request", "bug_report", "other",
}
PRIORITIES = {"urgent", "high", "medium", "low"}
STATUSES = {"new", "in_progress", "waiting_customer", "resolved", "closed"}
SOURCES = {"web_form", "email", "api", "chat", "phone"}
DEVICE_TYPES = {"desktop", "mobile", "tablet"}


def now_iso() -> str:
    """Current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Ticket:
    """A single support ticket held in memory."""

    customer_id: str
    customer_email: str
    customer_name: str
    subject: str
    description: str
    category: str = "other"
    priority: str = "medium"
    status: str = "new"
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    resolved_at: Optional[str] = None
    # Classification bookkeeping (populated in Phase 2)
    classification_confidence: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_email": self.customer_email,
            "customer_name": self.customer_name,
            "subject": self.subject,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "metadata": self.metadata,
            "classification_confidence": self.classification_confidence,
        }


# --- Pydantic request models (so /docs renders editable, pre-filled bodies) ---
class TicketMetadataIn(BaseModel):
    source: Optional[str] = None
    browser: Optional[str] = None
    device_type: Optional[str] = None


class TicketIn(BaseModel):
    customer_id: str
    customer_email: str
    customer_name: str
    subject: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[TicketMetadataIn] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_id": "CUST-1001",
                "customer_email": "jane@example.com",
                "customer_name": "Jane Doe",
                "subject": "Cannot log in to my account",
                "description": "I can't access my account after resetting my password. This is blocking my work.",
                "category": "account_access",
                "priority": "high",
                "status": "new",
                "tags": ["login"],
                "metadata": {"source": "web_form", "browser": "Chrome", "device_type": "desktop"},
            }
        }
    }


class TicketUpdateIn(BaseModel):
    """All fields optional — used for PUT (partial update allowed)."""
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[TicketMetadataIn] = None

    model_config = {
        "json_schema_extra": {
            "example": {"status": "in_progress", "assigned_to": "agent-7", "priority": "urgent"}
        }
    }
