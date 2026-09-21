"""Intelligent Customer Support System — FastAPI application (Phase 1).

Endpoints:
    POST   /tickets                 create a ticket
    POST   /tickets/import          bulk import from CSV / JSON / XML
    GET    /tickets                 list tickets (filter by category/priority/status/...)
    GET    /tickets/{id}            get one ticket
    PUT    /tickets/{id}            update a ticket
    DELETE /tickets/{id}            delete a ticket

In-memory storage only. Interactive docs at /docs.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import storage
import importers
import classifier
from models import now_iso
from models import Ticket, TicketIn, TicketUpdateIn
from validators import validate_ticket

app = FastAPI(
    title="Intelligent Customer Support System",
    description="Homework 2 — support ticket management with multi-format import.",
    version="1.0.0",
)

# Allow the local front-end (opened from file:// or a static server) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validation_error(details) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "Validation failed", "details": details})


def _not_found(msg) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "Not found", "message": msg})


@app.exception_handler(RequestValidationError)
async def _reformat_validation_error(request: Request, exc: RequestValidationError):
    details = []
    for e in exc.errors():
        loc = e.get("loc") or []
        field = next((str(x) for x in reversed(loc) if x not in ("body",)), "body")
        details.append({"field": field, "message": e.get("msg", "Invalid value")})
    return JSONResponse(status_code=400, content={"error": "Validation failed", "details": details})


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "Intelligent Customer Support System",
        "docs": "/docs",
        "tickets": storage.count(),
    }


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #
@app.post("/tickets", status_code=201, tags=["tickets"])
def create_ticket(payload: TicketIn, auto_classify: bool = False):
    data = payload.model_dump(exclude_none=True)
    errors = validate_ticket(data)
    if errors:
        return _validation_error(errors)

    classification = None
    if auto_classify:
        classification = classifier.classify(data.get("subject", ""), data.get("description", ""))
        # manual values win: only fill category/priority the caller did not set
        if "category" not in data:
            data["category"] = classification["category"]
        if "priority" not in data:
            data["priority"] = classification["priority"]

    md = data.get("metadata") or {}
    ticket = Ticket(
        customer_id=data["customer_id"],
        customer_email=data["customer_email"],
        customer_name=data["customer_name"],
        subject=data["subject"],
        description=data["description"],
        category=data.get("category", "other"),
        priority=data.get("priority", "medium"),
        status=data.get("status", "new"),
        assigned_to=data.get("assigned_to"),
        tags=data.get("tags", []),
        metadata=md,
    )
    if classification is not None:
        ticket.classification_confidence = classification["confidence"]
        storage.log_classification({
            "ticket_id": ticket.id, "at": now_iso(), "trigger": "on_create",
            "result": classification, "applied": True,
        })
    storage.add(ticket)
    return ticket.to_dict()


# --------------------------------------------------------------------------- #
# Bulk import (declared before /tickets/{id} routes)
# --------------------------------------------------------------------------- #
@app.post("/tickets/import", tags=["tickets"])
async def import_tickets(file: UploadFile = File(...), format: Optional[str] = Form(default=None)):
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return _validation_error([{"field": "file", "message": "File must be UTF-8 encoded text"}])

    # Determine format: use an explicit csv/json/xml value, otherwise infer from
    # the filename extension. (Swagger pre-fills the optional field with the
    # placeholder "string", so anything not a known format is treated as absent.)
    fmt = (format or "").lower().strip()
    if fmt not in ("csv", "json", "xml") and file.filename and "." in file.filename:
        fmt = file.filename.rsplit(".", 1)[-1].lower()

    try:
        records = importers.parse_by_format(text, fmt)
    except Exception as exc:  # malformed file / unsupported format
        return _validation_error([{"field": "file", "message": f"Could not parse file: {exc}"}])

    summary = importers.import_records(records)
    return JSONResponse(status_code=201, content=summary)


# --------------------------------------------------------------------------- #
# List
# --------------------------------------------------------------------------- #
@app.get("/tickets", tags=["tickets"])
def list_tickets(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
):
    results = storage.list_tickets(
        category=category, priority=priority, status=status,
        customer_id=customer_id, assigned_to=assigned_to,
    )
    return {"count": len(results), "tickets": [t.to_dict() for t in results]}


# --------------------------------------------------------------------------- #
# Read one
# --------------------------------------------------------------------------- #
@app.get("/tickets/{ticket_id}", tags=["tickets"])
def get_ticket(ticket_id: str):
    t = storage.get(ticket_id)
    if t is None:
        return _not_found(f"No ticket with id '{ticket_id}'")
    return t.to_dict()


# --------------------------------------------------------------------------- #
# Update
# --------------------------------------------------------------------------- #
@app.put("/tickets/{ticket_id}", tags=["tickets"])
def update_ticket(ticket_id: str, payload: TicketUpdateIn):
    if storage.get(ticket_id) is None:
        return _not_found(f"No ticket with id '{ticket_id}'")
    data = payload.model_dump(exclude_none=True)
    if not data:
        return _validation_error([{"field": "body", "message": "No fields provided to update"}])
    errors = validate_ticket(data, partial=True)
    if errors:
        return _validation_error(errors)
    if "metadata" in data and data["metadata"] is not None:
        # merge metadata rather than replace wholesale
        existing = storage.get(ticket_id).metadata or {}
        merged = dict(existing)
        merged.update(data["metadata"])
        data["metadata"] = merged
    updated = storage.update(ticket_id, data)
    return updated.to_dict()


# --------------------------------------------------------------------------- #
# Delete
# --------------------------------------------------------------------------- #
@app.delete("/tickets/{ticket_id}", tags=["tickets"])
def delete_ticket(ticket_id: str):
    if not storage.delete(ticket_id):
        return _not_found(f"No ticket with id '{ticket_id}'")
    return JSONResponse(status_code=200, content={"deleted": ticket_id})


# --------------------------------------------------------------------------- #
# Auto-classification (Task 2)
# --------------------------------------------------------------------------- #
@app.post("/tickets/{ticket_id}/auto-classify", tags=["classification"])
def auto_classify(ticket_id: str, apply: bool = True):
    """Classify a ticket's category + priority. apply=false previews without saving."""
    t = storage.get(ticket_id)
    if t is None:
        return _not_found(f"No ticket with id '{ticket_id}'")

    result = classifier.classify(t.subject, t.description)
    if apply:
        storage.update(ticket_id, {
            "category": result["category"],
            "priority": result["priority"],
            "classification_confidence": result["confidence"],
        })
    storage.log_classification({
        "ticket_id": ticket_id, "at": now_iso(), "trigger": "manual_endpoint",
        "result": result, "applied": apply,
    })
    return {"ticket_id": ticket_id, "applied": apply, **result}


@app.get("/classification-log", tags=["classification"])
def get_classification_log():
    """Return the log of all classification decisions."""
    log = storage.classification_log()
    return {"count": len(log), "entries": log}
