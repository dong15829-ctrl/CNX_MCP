#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B2B 점수 컬럼 실제 값 확인.
reportbusiness_es_old_v2 의 h1_tag_pf, canonical_link_pf, feature_cards, scoring 샘플 출력.
사용: 프로젝트 루트에서 .env 로드 후  .venv/bin/python scripts/check_b2b_scores.py
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
    # RAW 샘플 (scoring='Y' 인 행)
    cur.execute(f"""
        SELECT region, country, scoring, h1_tag_pf, canonical_link_pf, feature_cards
        FROM `{TABLE_B2B}`
        WHERE (scoring = 'Y' OR UPPER(TRIM(COALESCE(scoring,'')))= 'Y')
        LIMIT 15
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print("=== B2B RAW 샘플 (scoring='Y' 행) ===")
    print("컬럼:", cols)
    for i, row in enumerate(rows):
        print(f"  {i+1}: {dict(zip(cols, row))}")
    # 비어있지 않은 점수 컬럼 개수
    cur.execute(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN TRIM(COALESCE(h1_tag_pf,'')) != '' THEN 1 ELSE 0 END) AS h1_tag_pf_filled,
            SUM(CASE WHEN TRIM(COALESCE(canonical_link_pf,'')) != '' THEN 1 ELSE 0 END) AS canonical_link_pf_filled,
            SUM(CASE WHEN TRIM(COALESCE(feature_cards,'')) != '' THEN 1 ELSE 0 END) AS feature_cards_filled
        FROM `{TABLE_B2B}`
        WHERE (scoring = 'Y' OR UPPER(TRIM(COALESCE(scoring,'')))= 'Y')
    """)
    row = cur.fetchone()
    print("\n=== scoring='Y' 행 중 점수 컬럼 비어있지 않은 행 수 ===")
    print("  total:", row[0], "| h1_tag_pf 채워짐:", row[1], "| canonical_link_pf:", row[2], "| feature_cards:", row[3])

    # pandas 경로 1행 샘플 (백엔드와 동일한 집계)
    print("\n=== pandas 집계 결과 샘플 (첫 1행) ===")
    try:
        from backend.data import get_b2b_raw_df
        from pipeline.aggregate import aggregate_b2b_snapshot
        df = get_b2b_raw_df()
        print("  전처리 후 행 수:", len(df))
        if not df.empty:
            score_cols = [c for c in ["title_tag_score", "description_tag_score", "h1_tag_score", "canonical_link_score", "feature_alt_score"] if c in df.columns]
            print("  점수 컬럼:", score_cols)
            if score_cols:
                print("  샘플 값 (첫 행):", df[score_cols].iloc[0].to_dict())
            snap = aggregate_b2b_snapshot(df)
            if not snap.empty:
                print("  집계 후 첫 행:", snap.iloc[0].to_dict())
    except Exception as e:
        print("  오류:", e)
        import traceback
        traceback.print_exc()

    conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
