#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${HOME}/.venvs/slcc_ai"

if [[ ! -d "${VENV_PATH}" ]]; then
  cat <<'MSG' >&2
[ERROR] ~/.venvs/slcc_ai 가 없습니다. 아래 순서로 먼저 생성해 주세요.
  python3 -m venv ~/.venvs/slcc_ai
  source ~/.venvs/slcc_ai/bin/activate && pip install -r requirements.txt
MSG
  exit 1
fi

source "${VENV_PATH}/bin/activate"

export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy}"

echo "[INFO] PYTHONPATH=${PYTHONPATH}"
echo "[INFO] OPENAI_API_KEY=${OPENAI_API_KEY:+(set)}"
echo "[INFO] Uvicorn starting..."

exec uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
