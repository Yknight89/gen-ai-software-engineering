# 🏦 Homework 1: Banking Transactions API

> **Student Name**: Adewale (Wale) Adetiba
> **Date Submitted**: 2026-09-13
> **AI Tools Used**: Claude (Cowork)

---

## 📋 Project Overview

A minimal REST API for banking transactions, built with **Python + FastAPI** and
**in-memory storage** (no database). It implements all four required endpoints,
full request validation, transaction history filtering, and two bonus features
(a per-account summary and CSV export). FastAPI serves interactive Swagger docs
at `/docs`, which is the easiest way to explore and demo the API.

### ✅ Features implemented

**Core endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transactions` | Create a transaction (validated) |
| `GET`  | `/transactions` | List transactions, with filters |
| `GET`  | `/transactions/{id}` | Get one transaction by id |
| `GET`  | `/accounts/{accountId}/balance` | Net account balance |

**Validation** (Task 2)
- Amount must be a positive number with at most 2 decimal places.
- Accounts must match the format `ACC-XXXXX` (5 alphanumeric characters).
- Currency must be a valid ISO 4217 code (USD, EUR, GBP, JPY, …).
- Type must be one of `deposit | withdrawal | transfer`.
- Invalid requests return HTTP 400 with a structured `details` array.

**History filtering** (Task 3) on `GET /transactions`
- `?accountId=ACC-12345` — matches either side of the transaction
- `?type=transfer`
- `?from=2026-01-01&to=2026-01-31` — inclusive date range
- Any combination of the above.

**Bonus features** (Task 4)
- **Option A — Summary:** `GET /accounts/{accountId}/summary` returns total
  deposits, total withdrawals, transaction count, and most recent transaction date.
- **Option C — Export (extra):** `GET /transactions/export?format=csv` downloads
  all transactions as CSV.

### 🏗️ Architecture decisions

- **FastAPI + Uvicorn** — minimal boilerplate, automatic OpenAPI/Swagger docs at
  `/docs`, and native async request handling.
- **In-memory store** — a single module-level list in `src/storage.py`. Simple,
  matches the assignment, and resets on restart.
- **Manual validation** in `src/validators.py` rather than relying on Pydantic's
  auto-422, so the error response exactly matches the required
  `{ "error": "Validation failed", "details": [...] }` contract.
- **Separation of concerns:** `models.py` (data), `validators.py` (rules),
  `storage.py` (persistence + balance/summary logic), `app.py` (HTTP routing).
- **Balance rule:** only `completed` transactions affect a balance. A `deposit`
  credits `toAccount`, a `withdrawal` debits `fromAccount`, and a `transfer`
  debits `fromAccount` and credits `toAccount`. New transactions default to
  `completed` when a status is not supplied, so balances are demonstrable
  immediately.
- **Port 3000** to match the sample requests in the assignment.

### 📁 Structure

```
homework-1/
├── README.md
├── HOWTORUN.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── app.py            # FastAPI app + routes
│   ├── models.py         # Transaction model
│   ├── validators.py     # validation rules
│   ├── storage.py        # in-memory store, balance, summary
│   └── currencies.py     # ISO 4217 currency helper
├── demo/
│   ├── run.sh            # start the server
│   ├── sample-requests.sh
│   ├── sample-requests.http
│   └── sample-data.json
└── docs/
    └── screenshots/      # AI usage + API running screenshots
```

<div align="center">

*This project was completed as part of the AI-Assisted Development course.*

</div>
