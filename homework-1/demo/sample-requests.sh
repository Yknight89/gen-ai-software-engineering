#!/usr/bin/env bash
# Exercise every endpoint. Start the server first (./demo/run.sh), then run this.
set -uo pipefail
BASE="${BASE:-http://localhost:3000}"
hr(){ echo; echo "==== $1 ===="; }

hr "Create a transfer"
curl -s -X POST "$BASE/transactions" -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":100.50,"currency":"USD","type":"transfer"}'; echo

hr "Create a deposit"
curl -s -X POST "$BASE/transactions" -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":500,"currency":"EUR","type":"deposit"}'; echo

hr "Create a withdrawal"
curl -s -X POST "$BASE/transactions" -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","amount":40.25,"currency":"USD","type":"withdrawal"}'; echo

hr "Validation error example (expect HTTP 400)"
curl -s -X POST "$BASE/transactions" -H "Content-Type: application/json" \
  -d '{"fromAccount":"XX-1","toAccount":"ACC-67890","amount":-5,"currency":"XYZ","type":"transfer"}'; echo

hr "List all transactions"
curl -s "$BASE/transactions"; echo

hr "Filter by account"
curl -s "$BASE/transactions?accountId=ACC-12345"; echo

hr "Filter by type"
curl -s "$BASE/transactions?type=deposit"; echo

hr "Filter by date range"
curl -s "$BASE/transactions?from=2026-01-01&to=2026-12-31"; echo

hr "Account balance"
curl -s "$BASE/accounts/ACC-12345/balance"; echo

hr "Account summary (bonus)"
curl -s "$BASE/accounts/ACC-12345/summary"; echo

hr "CSV export (bonus)"
curl -s "$BASE/transactions/export?format=csv"; echo
