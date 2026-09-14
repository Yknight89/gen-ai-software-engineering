#!/usr/bin/env bash
# Start the Banking Transactions API on port 3000.
set -euo pipefail

# Resolve the homework-1 root (parent of this demo/ folder).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Create + activate a virtual environment on first run.
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies..."
pip install --quiet -r requirements.txt

echo "Starting API on http://localhost:3000  (docs at /docs)"
cd src
exec uvicorn app:app --host 0.0.0.0 --port 3000 --reload
