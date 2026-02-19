#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB 연결 및 SUMMARY 데이터 진단.
사용: 프로젝트 루트에서  python scripts/check_db.py
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# .env 수동 로드
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'\"")
            if k and v:
                os.environ.setdefault(k, v)

def main():
    print("=== 1. 환경 변수 ===")
    pw = os.environ.get("MYSQL_PASSWORD", "")
    print(f"  MYSQL_HOST: {os.environ.get('MYSQL_HOST')}")
    print(f"  MYSQL_PORT: {os.environ.get('MYSQL_PORT')}")
    print(f"  MYSQL_USER: {os.environ.get('MYSQL_USER')}")
    print(f"  MYSQL_PASSWORD: {'(설정됨)' if pw else '(비어있음)'}")
    print(f"  MYSQL_DATABASE: {os.environ.get('MYSQL_DATABASE')}")

    if not pw:
        print("\n  [오류] MYSQL_PASSWORD가 비어 있습니다. .env 파일을 확인하세요.")
        return 1

    print("\n=== 2. DB 연결 테스트 ===")
    try:
        from backend.db import get_connection, TABLE_B2B, TABLE_B2C
        conn = get_connection()
        print("  연결 성공.")
    except Exception as e:
        print(f"  [오류] 연결 실패: {e}")
        return 1

    try:
        cursor = conn.cursor()

        # B2B 테이블 (DESCRIBE로 컬럼만 확인, 빠름)
        print(f"\n=== 3. B2B 테이블: {TABLE_B2B} ===")
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_B2B}`")
            n = cursor.fetchone()[0]
            print(f"  전체 행 수: {n}")
        except Exception as e:
            print(f"  [오류] {e}")
            conn.close()
            return 1

        cursor.execute(f"DESCRIBE `{TABLE_B2B}`")
        desc = cursor.fetchall()
        cols_b2b = [d[0] for d in desc] if desc else []
        print(f"  컬럼 수: {len(cols_b2b)}")
        print(f"  컬럼명(전체): {cols_b2b}")

        # B2C 테이블
        print(f"\n=== 4. B2C 테이블: {TABLE_B2C} ===")
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_B2C}`")
            n = cursor.fetchone()[0]
            print(f"  전체 행 수: {n}")
        except Exception as e:
            print(f"  [오류] {e}")
            conn.close()
            return 1

        cursor.execute(f"DESCRIBE `{TABLE_B2C}`")
        desc = cursor.fetchall()
        cols_b2c = [d[0] for d in desc] if desc else []
        print(f"  컬럼 수: {len(cols_b2c)}")
        print(f"  컬럼명(전체): {cols_b2c}")

        conn.close()
    except Exception as e:
        print(f"  [오류] {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n=== 5. SUMMARY 집계(SQL) 테스트 ===")
    try:
        from backend.data import get_summary_b2b_snapshot_sql, get_summary_b2c_snapshot_sql
        b2b = get_summary_b2b_snapshot_sql()
        b2c = get_summary_b2c_snapshot_sql()
        print(f"  B2B SUMMARY 행 수: {len(b2b)}")
        print(f"  B2C SUMMARY 행 수: {len(b2c)}")
        if b2b:
            print(f"  B2B 샘플 키: {list(b2b[0].keys())[:8]}")
        if b2c:
            print(f"  B2C 샘플 키: {list(b2c[0].keys())[:8]}")
    except Exception as e:
        print(f"  [오류] SQL 집계 실패(DB 컬럼명이 다를 수 있음): {e}")
        print("  → 대시보드는 pandas 집계로 폴백하지만, 테이블이 크면 느릴 수 있습니다.")
        import traceback
        traceback.print_exc()
        return 1

    print("\n=== 6. API 연동 확인 ===")
    print("  백엔드 서버를 재시작한 뒤 다음을 확인하세요.")
    print("  - http://localhost:8010/api/version  → {\"version\":\"2.0\", ...} 이면 최신 코드 동작 중.")
    print("  - 여전히 'Field required' 422가 나오면: 서버 프로세스를 완전히 종료 후 다시 실행하세요.")

    print("\n=== 진단 완료 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
