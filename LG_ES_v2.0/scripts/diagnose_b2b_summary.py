#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B2B Summary 0.00 원인 진단: reportbusiness_es_old_v2 테이블 컬럼·샘플·집계 결과 확인.
사용: 프로젝트 루트에서  python scripts/diagnose_b2b_summary.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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
    if not os.environ.get("MYSQL_PASSWORD"):
        print("MYSQL_PASSWORD가 없습니다. .env 를 설정하세요.")
        return 1

    from backend.db import get_connection, TABLE_B2B

    conn = get_connection()
    cur = conn.cursor()

    print("=== 1. B2B 테이블 컬럼 (실제 DB) ===")
    print(f"   테이블: {TABLE_B2B}")
    try:
        cur.execute(f"DESCRIBE `{TABLE_B2B}`")
        desc = cur.fetchall()
        cols = [d[0] for d in desc] if desc else []
        print(f"   컬럼 수: {len(cols)}")
        print(f"   컬럼명: {cols}")
    except Exception as e:
        print(f"   [오류] {e}")
        conn.close()
        return 1

    # 백엔드 SQL이 기대하는 컬럼 (legacy)
    legacy_score = ["h1_tag_pf", "canonical_link_pf", "feature_cards", "scoring"]
    # v2 등에서 쓸 수 있는 표준명
    standard_score = ["h1_tag_score", "canonical_link_score", "feature_alt_score", "title_tag_score", "description_tag_score"]

    has_legacy = [c for c in legacy_score if c in cols]
    has_standard = [c for c in standard_score if c in cols]
    print(f"   legacy (h1_tag_pf 등): {has_legacy}")
    print(f"   standard (_score):      {has_standard}")

    if not has_legacy and not has_standard:
        print("   → 점수용 컬럼이 없거나 이름이 다릅니다. 위 '컬럼명' 전체를 확인해 backend/data.py SQL 또는 .env B2B_SCORE_SCHEMA 를 맞추세요.")

    print("\n=== 2. scoring='Y' 행 수 및 샘플 ===")
    scoring_col = "scoring" if "scoring" in cols else None
    if not scoring_col:
        for c in cols:
            if "scoring" in str(c).lower():
                scoring_col = c
                break
    if scoring_col:
        cur.execute(f"""
            SELECT COUNT(*) FROM `{TABLE_B2B}`
            WHERE (UPPER(TRIM(COALESCE(`{scoring_col}`,'')))= 'Y' OR TRIM(COALESCE(`{scoring_col}`,''))= '1')
              AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != ''
        """)
        n = cur.fetchone()[0]
        print(f"   조건 충족 행 수: {n}")

        # 샘플: 있는 점수 컬럼만 선택
        sample_cols = ["region", "country", scoring_col]
        for c in legacy_score + standard_score:
            if c in cols and c not in sample_cols:
                sample_cols.append(c)
        sel = ", ".join(f"`{c}`" for c in sample_cols if c in cols)
        if sel:
            cur.execute(f"""
                SELECT {sel} FROM `{TABLE_B2B}`
                WHERE (UPPER(TRIM(COALESCE(`{scoring_col}`,'')))= 'Y' OR TRIM(COALESCE(`{scoring_col}`,''))= '1')
                  AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != ''
                LIMIT 3
            """)
            rows = cur.fetchall()
            names = [d[0] for d in cur.description]
            for i, row in enumerate(rows):
                print(f"   샘플 {i+1}: {dict(zip(names, row))}")
    else:
        print("   scoring 컬럼을 찾을 수 없습니다. 컬럼 목록:", cols[:20])

    print("\n=== 3. API와 동일한 SUMMARY 집계 결과 (첫 2행) ===")
    try:
        from backend.data import get_summary_b2b_snapshot_sql
        rows = get_summary_b2b_snapshot_sql()
        print(f"   SUMMARY 행 수: {len(rows)}")
        for i, r in enumerate(rows[:2]):
            print(f"   행 {i+1}: {r}")
        if rows and len(rows) > 0:
            first = rows[0]
            scores = [k for k in first if "score" in k.lower() or k == "total_score_pct"]
            non_zero = [k for k in scores if first.get(k) not in (None, "", 0, 0.0)]
            if not non_zero and scores:
                print("   → 모든 점수 컬럼이 0 또는 비어 있음. 위 1·2에서 DB 컬럼명/값을 확인하세요.")
    except Exception as e:
        print(f"   [오류] {e}")
        import traceback
        traceback.print_exc()

    print("\n=== 4. 권장 사항 ===")
    if has_standard and not has_legacy:
        print("   테이블에 _score 컬럼만 있습니다. .env 에 다음 추가 후 서버 재시작:")
        print("   B2B_SCORE_SCHEMA=v2")
    elif has_legacy and not has_standard:
        print("   테이블에 h1_tag_pf 등 legacy 컬럼이 있습니다. 샘플 값이 비어 있으면 파이프라인/적재 데이터를 확인하세요.")
    else:
        print("   - SUMMARY가 전부 0이면: 위 샘플에서 점수 컬럼에 실제 값이 들어오는지 확인.")
        print("   - 컬럼명이 legacy(h1_tag_pf 등)면 B2B_SCORE_SCHEMA 설정 없음. _score면 .env 에 B2B_SCORE_SCHEMA=v2 추가.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
