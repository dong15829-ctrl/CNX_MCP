#!/bin/bash
# LG ES v2.0 통합 - 백엔드+프론트엔드 한 번에 실행
cd "$(dirname "$0")"
echo "프로젝트 디렉토리: $(pwd)"
echo "서버 시작 중... (종료: Ctrl+C)"
echo "접속 주소: http://127.0.0.1:8000 또는 http://localhost:8000"
echo "로그인: http://127.0.0.1:8000/login"
echo ""
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
