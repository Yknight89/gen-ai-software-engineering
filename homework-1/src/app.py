"""Banking Transactions API — FastAPI application.

Endpoints (see homework-1/TASKS.md):
    POST /transactions                     create a transaction
    GET  /transactions                     list (filter by accountId, type, from, to)
    GET  /transactions/{id}                get one by id
    GET  /accounts/{accountId}/balance     account balance
    GET  /accounts/{accountId}/summary     bonus: per-account summary (Option A)
    GET  /transactions/export?format=csv   bonus extra: CSV export (Option C)

Storage is in-memory only. Interactive docs are served at /docs.
"""

from __future__ import annotations

from typing import Optional

import csv
import io

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse

import storage
from models import Transaction, TransactionIn
from validators import validate_transaction, is_valid_account_format

app = FastAPI(
    title="Banking Transactions API",
    description="Homework 1 — a minimal in-memory banking transactions REST API.",
    version="1.0.0",
)


def _validation_error(details: list[dict]) -> JSONResponse:
    """Build the exact error contract required by the assignment (HTTP 400)."""
    return JSONResponse(
        status_code=400,
        content={"error": "Validation failed", "details": details},
    )


def _not_found(message: str) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "Not found", "message": message})


@app.exception_handler(RequestValidationError)
async def _reformat_validation_error(request: Request, exc: RequestValidationError):
    """Map FastAPI/Pydantic body errors to the assignment's error contract."""
    details = []
    for e in exc.errors():
        loc = e.get("loc") or []
        field = next((str(x) for x in reversed(loc) if x != "body"), "body")
        details.append({"field": field, "message": e.get("msg", "Invalid value")})
    return JSONResponse(status_code=400, content={"error": "Validation failed", "details": details})


@app.get("/", tags=["meta"])
def root() -> dict:
    """Tiny landing payload so hitting the root is not a 404."""
    return {
        "service": "Banking Transactions API",
        "docs": "/docs",
        "endpoints": [
            "POST /transactions",
            "GET /transactions",
            "GET /transactions/{id}",
            "GET /accounts/{accountId}/balance",
            "GET /accounts/{accountId}/summary",
            "GET /transactions/export?format=csv",
        ],
    }


# ----------------------------------------------------------------------------
# Create
# ----------------------------------------------------------------------------
@app.post("/transactions", status_code=201, tags=["transactions"])
async def create_transaction(payload: TransactionIn):
    data = payload.model_dump()
    errors = validate_transaction(data)
    if errors:
        return _validation_error(errors)

    tx = Transaction(
        fromAccount=data.get("fromAccount"),
        toAccount=data.get("toAccount"),
        amount=float(data["amount"]),
        currency=str(data["currency"]).upper(),
        type=data["type"],
        status=data.get("status") or "completed",
    )
    storage.add(tx)
    return tx.to_dict()


# ----------------------------------------------------------------------------
# Export (must be declared BEFORE /transactions/{id} so "export" is not treated
# as an id path parameter).
# ----------------------------------------------------------------------------
@app.get("/transactions/export", tags=["transactions"])
def export_transactions(format: str = "csv"):
    if format.lower() != "csv":
        return _validation_error(
            [{"field": "format", "message": "Only 'csv' export format is supported"}]
        )

    buffer = io.StringIO()
    fieldnames = [
        "id", "fromAccount", "toAccount", "amount",
        "currency", "type", "timestamp", "status",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for t in storage.all_transactions():
        writer.writerow(t.to_dict())

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


# ----------------------------------------------------------------------------
# List with filters
# ----------------------------------------------------------------------------
@app.get("/transactions", tags=["transactions"])
def list_transactions(
    accountId: Optional[str] = None,
    type: Optional[str] = None,
    from_: Optional[str] = None,
    to: Optional[str] = None,
    request: Request = None,
):
    # FastAPI cannot bind a query param literally named "from" (reserved word),
    # so read it straight from the query string.
    date_from = request.query_params.get("from") if request else from_
    results = storage.list_transactions(
        account_id=accountId, tx_type=type, date_from=date_from, date_to=to
    )
    return {"count": len(results), "transactions": [t.to_dict() for t in results]}


# ----------------------------------------------------------------------------
# Get one by id
# ----------------------------------------------------------------------------
@app.get("/transactions/{tx_id}", tags=["transactions"])
def get_transaction(tx_id: str):
    tx = storage.get(tx_id)
    if tx is None:
        return _not_found(f"No transaction with id '{tx_id}'")
    return tx.to_dict()


# ----------------------------------------------------------------------------
# Balance
# ----------------------------------------------------------------------------
@app.get("/accounts/{account_id}/balance", tags=["accounts"])
def account_balance(account_id: str):
    if not is_valid_account_format(account_id):
        return _validation_error(
            [{"field": "accountId", "message": "accountId must match the format ACC-XXXXX"}]
        )
    return storage.balance(account_id)


# ----------------------------------------------------------------------------
# Summary (bonus — Option A)
# ----------------------------------------------------------------------------
@app.get("/accounts/{account_id}/summary", tags=["accounts"])
def account_summary(account_id: str):
    if not is_valid_account_format(account_id):
        return _validation_error(
            [{"field": "accountId", "message": "accountId must match the format ACC-XXXXX"}]
        )
    return storage.summary(account_id)
