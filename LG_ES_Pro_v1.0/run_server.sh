#!/bin/bash
# API 서버 실행. 422 해결을 위해 반드시 이 스크립트로 새로 띄우세요.
# 사용: ./run_server.sh   또는  bash run_server.sh
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo ".venv 없음. python -m venv .venv && .venv/bin/pip install -r requirements.txt 먼저 실행하세요."
  exit 1
fi
echo "서버 시작 (최신 코드 로드). 종료: Ctrl+C"
exec .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8010
