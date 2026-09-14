# ▶️ How to Run the application

A Python 3.10+ REST API built with FastAPI. No database is required — data is
kept in memory and resets each time the server restarts.

## 1. Prerequisites

- Python 3.10 or newer (`python3 --version`)
- `pip` and `venv`

## 2. Set up and install

From the `homework-1/` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Run the server

**Option A — the demo script:**

```bash
./demo/run.sh
```

**Option B — manually:**

```bash
cd src
uvicorn app:app --host 0.0.0.0 --port 3000 --reload
```

The API is now available at **http://localhost:3000**.

## 4. Explore it

- Interactive Swagger docs: **http://localhost:3000/docs**
- Health/index: **http://localhost:3000/**

## 5. Try some requests

Run the bundled sample calls (server must be running):

```bash
./demo/sample-requests.sh
```

…or use the sample cURL commands below:

```bash
# Create a transaction
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":100.50,"currency":"USD","type":"transfer"}'

# List all transactions
curl http://localhost:3000/transactions

# Filter by account
curl "http://localhost:3000/transactions?accountId=ACC-12345"

# Get account balance
curl http://localhost:3000/accounts/ACC-12345/balance

# Bonus: account summary
curl http://localhost:3000/accounts/ACC-12345/summary

# Bonus: CSV export
curl "http://localhost:3000/transactions/export?format=csv"
```

## 6. Stop the server

Press `Ctrl+C` in the terminal running Uvicorn.
