"""Validation logic for ticket payloads.

Every validator appends {"field": ..., "message": ...} entries so the API can
return a structured error contract:

    { "error": "Validation failed", "details": [ {"field": ..., "message": ...} ] }
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from models import CATEGORIES, PRIORITIES, STATUSES, SOURCES, DEVICE_TYPES

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SUBJECT_MIN, SUBJECT_MAX = 1, 200
DESC_MIN, DESC_MAX = 10, 2000

REQUIRED_FIELDS = ["customer_id", "customer_email", "customer_name", "subject", "description"]


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def validate_ticket(payload: Dict[str, Any], partial: bool = False) -> List[Dict[str, str]]:
    """Return a list of validation errors (empty means valid).

    partial=True (for PUT) only validates fields that are present.
    """
    errors: List[Dict[str, str]] = []

    if not isinstance(payload, dict):
        return [{"field": "body", "message": "Request body must be a JSON object"}]

    def present(name):
        return name in payload and payload[name] is not None

    # Required fields (skipped for partial updates)
    if not partial:
        for f in REQUIRED_FIELDS:
            if not present(f) or not _is_nonempty_str(payload.get(f)):
                errors.append({"field": f, "message": f"{f} is required"})

    # Email
    if present("customer_email"):
        if not (isinstance(payload["customer_email"], str) and EMAIL_RE.match(payload["customer_email"])):
            errors.append({"field": "customer_email", "message": "Invalid email format"})

    # Subject length
    if present("subject") and isinstance(payload["subject"], str):
        n = len(payload["subject"])
        if n < SUBJECT_MIN or n > SUBJECT_MAX:
            errors.append({"field": "subject", "message": f"Subject must be {SUBJECT_MIN}-{SUBJECT_MAX} characters"})

    # Description length
    if present("description") and isinstance(payload["description"], str):
        n = len(payload["description"])
        if n < DESC_MIN or n > DESC_MAX:
            errors.append({"field": "description", "message": f"Description must be {DESC_MIN}-{DESC_MAX} characters"})

    # Enums
    if present("category") and payload["category"] not in CATEGORIES:
        errors.append({"field": "category", "message": "Invalid category"})
    if present("priority") and payload["priority"] not in PRIORITIES:
        errors.append({"field": "priority", "message": "Invalid priority"})
    if present("status") and payload["status"] not in STATUSES:
        errors.append({"field": "status", "message": "Invalid status"})

    # tags must be a list of strings if provided
    if present("tags"):
        tags = payload["tags"]
        if not (isinstance(tags, list) and all(isinstance(t, str) for t in tags)):
            errors.append({"field": "tags", "message": "tags must be a list of strings"})

    # metadata sub-enums if provided
    if present("metadata"):
        md = payload["metadata"]
        if not isinstance(md, dict):
            errors.append({"field": "metadata", "message": "metadata must be an object"})
        else:
            if md.get("source") not in (None, "") and md.get("source") not in SOURCES:
                errors.append({"field": "metadata.source", "message": "Invalid metadata.source"})
            if md.get("device_type") not in (None, "") and md.get("device_type") not in DEVICE_TYPES:
                errors.append({"field": "metadata.device_type", "message": "Invalid metadata.device_type"})

    return errors
