#!/usr/bin/env python3
"""
파이프라인 실행 진입점.
사용: MYSQL_PASSWORD=xxx python run_pipeline.py
     또는 .env 파일 설정 후 python run_pipeline.py
"""
import os
from pathlib import Path

# .env 파일이 있으면 로드 (python-dotenv 선택)
_env = Path(__file__).resolve().parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

# 환경 변수로 비밀번호 필수
if not os.environ.get("MYSQL_PASSWORD"):
    print("MYSQL_PASSWORD 환경 변수를 설정하거나 .env 파일에 MYSQL_PASSWORD=... 를 넣으세요.")
    exit(1)

from pipeline.run import run_pipeline

if __name__ == "__main__":
    run_pipeline()
