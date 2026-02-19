#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
관리자 계정 생성/역할 변경 스크립트.
사용: .venv 활성화 후 프로젝트 루트에서
  python scripts/create_admin.py 이메일 비밀번호
  python scripts/create_admin.py  (→ .env의 ADMIN_EMAIL, ADMIN_PASSWORD 사용)
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)
    except ImportError:
        for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

sys.path.insert(0, str(ROOT))

from backend.db import is_db_configured, get_connection
from backend import auth_user


def main():
    if not is_db_configured():
        print("오류: DB가 설정되지 않았습니다. .env에 MYSQL_PASSWORD 등을 설정하세요.")
        sys.exit(1)

    if len(sys.argv) >= 3:
        email = sys.argv[1].strip()
        password = sys.argv[2]
    else:
        email = os.environ.get("ADMIN_EMAIL") or os.environ.get("ADMIN_USERNAME", "admin@example.com")
        password = os.environ.get("ADMIN_PASSWORD", "admin")
        if not email or not password:
            print("사용법: python scripts/create_admin.py 이메일 비밀번호")
            print("   또는 .env에 ADMIN_EMAIL, ADMIN_PASSWORD를 넣고 인자 없이 실행")
            sys.exit(1)

    conn = get_connection()
    try:
        auth_user.ensure_users_table(conn)
        existing = auth_user.get_user_by_email(conn, email)
        if existing:
            auth_user.update_user(conn, existing["id"], role="admin")
            print(f"기존 계정을 관리자로 변경했습니다: {email}")
        else:
            auth_user.create_user(conn, email, password, role="admin")
            print(f"관리자 계정을 생성했습니다: {email}")
    except ValueError as e:
        print(f"오류: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
