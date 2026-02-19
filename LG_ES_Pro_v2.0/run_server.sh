#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo ".venv 없음. python -m venv .venv && .venv/bin/pip install -r requirements.txt 먼저 실행하세요."
  exit 1
fi
echo "LG ES Pro v2.0 서버 시작. 종료: Ctrl+C"
exec .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload
