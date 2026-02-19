# -*- coding: utf-8 -*-
"""
파이프라인 실행: DB 로드 -> 전처리 -> 집계 -> CSV 저장.
"""
import sys
from pathlib import Path

# 상위 경로에서 pipeline 패키지 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from pipeline.config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
    TABLE_B2B,
    TABLE_B2C,
    COLUMN_ALIAS_B2B,
    COLUMN_ALIAS_B2C,
    OUTPUT_DIR,
)
from pipeline.preprocess import preprocess_b2b, preprocess_b2c
from pipeline.aggregate import (
    aggregate_b2b_snapshot,
    aggregate_b2b_trend_month,
    aggregate_b2b_trend_week,
    aggregate_b2c_snapshot,
    aggregate_b2c_trend_month,
    aggregate_b2c_trend_week,
)


def get_connection():
    """MySQL 연결. pymysql 또는 mysql.connector 사용."""
    try:
        import pymysql
        return pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
        )
    except ImportError:
        try:
            import mysql.connector
            return mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
            )
        except ImportError:
            raise RuntimeError("pymysql 또는 mysql-connector-python 설치 필요: pip install pymysql")


def load_table(conn, table: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM `{table}`", conn)


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MYSQL_PASSWORD:
        print("MYSQL_PASSWORD 환경 변수를 설정하세요.")
        sys.exit(1)

    print("DB 연결 중...")
    conn = get_connection()

    try:
        # ----- B2B -----
        print(f"B2B 로드: {TABLE_B2B}")
        df_b2b = load_table(conn, TABLE_B2B)
        print(f"  행 수: {len(df_b2b)}, 컬럼: {list(df_b2b.columns)[:10]}...")

        print("B2B 전처리...")
        df_b2b = preprocess_b2b(df_b2b, COLUMN_ALIAS_B2B)
        print(f"  전처리 후 행 수: {len(df_b2b)}")

        snap_b2b = aggregate_b2b_snapshot(df_b2b)
        trend_m_b2b = aggregate_b2b_trend_month(df_b2b)
        trend_w_b2b = aggregate_b2b_trend_week(df_b2b)

        snap_b2b.to_csv(OUTPUT_DIR / "summary_b2b_snapshot.csv", index=False, encoding="utf-8-sig")
        if not trend_m_b2b.empty:
            trend_m_b2b.to_csv(OUTPUT_DIR / "summary_b2b_trend_month.csv", index=False, encoding="utf-8-sig")
        if not trend_w_b2b.empty:
            trend_w_b2b.to_csv(OUTPUT_DIR / "summary_b2b_trend_week.csv", index=False, encoding="utf-8-sig")
        print(f"  저장: summary_b2b_snapshot.csv ({len(snap_b2b)}행)")
        if not trend_m_b2b.empty:
            print(f"  저장: summary_b2b_trend_month.csv ({len(trend_m_b2b)}행)")
        if not trend_w_b2b.empty:
            print(f"  저장: summary_b2b_trend_week.csv ({len(trend_w_b2b)}행)")

        # ----- B2C -----
        print(f"B2C 로드: {TABLE_B2C}")
        df_b2c = load_table(conn, TABLE_B2C)
        print(f"  행 수: {len(df_b2c)}, 컬럼: {list(df_b2c.columns)[:10]}...")

        print("B2C 전처리...")
        df_b2c = preprocess_b2c(df_b2c, COLUMN_ALIAS_B2C)
        print(f"  전처리 후 행 수: {len(df_b2c)}")

        snap_b2c = aggregate_b2c_snapshot(df_b2c)
        trend_m_b2c = aggregate_b2c_trend_month(df_b2c)
        trend_w_b2c = aggregate_b2c_trend_week(df_b2c)

        snap_b2c.to_csv(OUTPUT_DIR / "summary_b2c_snapshot.csv", index=False, encoding="utf-8-sig")
        if not trend_m_b2c.empty:
            trend_m_b2c.to_csv(OUTPUT_DIR / "summary_b2c_trend_month.csv", index=False, encoding="utf-8-sig")
        if not trend_w_b2c.empty:
            trend_w_b2c.to_csv(OUTPUT_DIR / "summary_b2c_trend_week.csv", index=False, encoding="utf-8-sig")
        print(f"  저장: summary_b2c_snapshot.csv ({len(snap_b2c)}행)")
        if not trend_m_b2c.empty:
            print(f"  저장: summary_b2c_trend_month.csv ({len(trend_m_b2c)}행)")
        if not trend_w_b2c.empty:
            print(f"  저장: summary_b2c_trend_week.csv ({len(trend_w_b2c)}행)")

    finally:
        conn.close()

    print(f"완료. 출력 디렉터리: {OUTPUT_DIR}")


if __name__ == "__main__":
    run_pipeline()
