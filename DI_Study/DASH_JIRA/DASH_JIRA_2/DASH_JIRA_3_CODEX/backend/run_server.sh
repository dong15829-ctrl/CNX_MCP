#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR"
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

exec uvicorn app.main:app --host "$HOST" --port "$PORT"
