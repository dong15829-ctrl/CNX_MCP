# -*- coding: utf-8 -*-
"""
DB 기반 데이터 로드 및 집계.
reportbusiness_es_old(B2B), report_es_old(B2C)에서 조회 후 파이프라인 전처리·집계 로직 적용.
환경변수 SUMMARY_VIEW_B2B / SUMMARY_VIEW_B2C 가 있으면 해당 VIEW(또는 테이블)에서 미리 집계된 데이터를 읽음.
"""
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd

from backend.db import get_connection, TABLE_B2B, TABLE_B2C

# 미리 집계된 VIEW/테이블 사용 시 (선택). .env 에 SUMMARY_VIEW_B2B=v_summary_b2b 등 설정
SUMMARY_VIEW_B2B = os.environ.get("SUMMARY_VIEW_B2B", "").strip() or None
SUMMARY_VIEW_B2C = os.environ.get("SUMMARY_VIEW_B2C", "").strip() or None
# B2B 테이블이 _score 컬럼(h1_tag_score 등)을 쓰면 v2. legacy= h1_tag_pf, canonical_link_pf, feature_cards
# 테이블명에 v2가 있으면 기본 v2, 아니면 legacy (db import 후 설정)
def _b2b_score_schema():
    v = os.environ.get("B2B_SCORE_SCHEMA", "").strip().lower()
    if v in ("v2", "legacy"):
        return v
    return "v2" if (TABLE_B2B and "v2" in TABLE_B2B) else "legacy"
B2B_SCORE_SCHEMA = _b2b_score_schema()
from pipeline.config import (
    COLUMN_ALIAS_B2B,
    COLUMN_ALIAS_B2C,
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


def _load_table(conn, table: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM `{table}`", conn)


def _df_to_rows(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    df = df.copy()
    for c in df.columns:
        if hasattr(df[c].dtype, "kind") and df[c].dtype.kind == "f":
            df[c] = df[c].fillna(0.0).apply(lambda x: round(float(x), 6))
    return df.to_dict(orient="records")


def _cursor_to_rows(cursor) -> list[dict]:
    """cursor.execute() 후 fetchall() 결과를 list[dict]로 변환."""
    if cursor.description is None:
        return []
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, row)) for row in rows]


def _normalize_numeric_rows(rows: list[dict]) -> list[dict]:
    """Decimal 등 DB 숫자 타입을 float로 바꿔 JSON/프론트에서 안정적으로 표시되도록 함."""
    from decimal import Decimal
    out = []
    for r in rows:
        row = {}
        for k, v in r.items():
            if v is None or v == "":
                row[k] = v
            elif isinstance(v, Decimal):
                row[k] = round(float(v), 6)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                row[k] = round(float(v), 6) if isinstance(v, float) else v
            else:
                row[k] = v
        out.append(row)
    return out


# B2B 스코어 컬럼: DB/SQL이 NULL 반환 시 0으로 채워 프론트 "—" 방지
B2B_SCORE_KEYS = ("title_tag_score", "description_tag_score", "h1_tag_score", "canonical_link_score", "feature_alt_score", "total_score_pct")


def _b2b_fill_scores(rows: list[dict]) -> list[dict]:
    """B2B 행 목록에서 스코어 키를 반드시 포함 (없거나 None이면 0.0). 프론트 '—' 방지."""
    out = []
    for r in rows:
        row = dict(r)
        for k in B2B_SCORE_KEYS:
            v = row.get(k)
            row[k] = 0.0 if (v is None or v == "") else (float(v) if not isinstance(v, (int, float)) else v)
        out.append(row)
    return out


# ----- DB에서 바로 집계 (실제 테이블 컬럼명 기준, 타임아웃 방지) -----
# B2B 엑셀 수식: (Title+Description+H1+Canonical+Feature)/85*100 (만점 20+20+15+15+15=85)
# reportbusiness_es_old_v2: scoring, h1_tag_pf, canonical_link_pf, feature_cards; title/description은 텍스트→0
# REPLACE(col, ',', '.') 로 소수점 콤마 처리 후 CAST
SQL_B2B_SNAPSHOT = """
SELECT
    region,
    country,
    COUNT(*) AS sku_count,
    0 AS title_tag_score,
    0 AS description_tag_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(h1_tag_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0), 6) AS h1_tag_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(canonical_link_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0), 6) AS canonical_link_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(feature_cards,'')), ',', '.'), '') AS DECIMAL(10,2))), 0), 6) AS feature_alt_score,
    ROUND(
        (COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(h1_tag_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0)
         + COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(canonical_link_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0)
         + COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(feature_cards,'')), ',', '.'), '') AS DECIMAL(10,2))), 0)) / 85.0 * 100.0,
        6
    ) AS total_score_pct
FROM `{table}`
WHERE (scoring = 'Y' OR UPPER(TRIM(COALESCE(scoring,'')))= 'Y')
  AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != ''
GROUP BY region, country
ORDER BY region, country
"""

# B2B v2: 테이블에 _score 컬럼(title_tag_score, description_tag_score, h1_tag_score 등)이 있을 때
# .env B2B_SCORE_SCHEMA=v2 로 사용. 만점 85 = Title20+Description20+H115+Canonical15+Feature15
SQL_B2B_SNAPSHOT_V2 = """
SELECT
    region,
    country,
    COUNT(*) AS sku_count,
    ROUND(COALESCE(AVG(title_tag_score), 0), 6) AS title_tag_score,
    ROUND(COALESCE(AVG(description_tag_score), 0), 6) AS description_tag_score,
    ROUND(COALESCE(AVG(h1_tag_score), 0), 6) AS h1_tag_score,
    ROUND(COALESCE(AVG(canonical_link_score), 0), 6) AS canonical_link_score,
    ROUND(COALESCE(AVG(feature_alt_score), 0), 6) AS feature_alt_score,
    ROUND(
        (COALESCE(AVG(title_tag_score), 0) + COALESCE(AVG(description_tag_score), 0)
         + COALESCE(AVG(h1_tag_score), 0) + COALESCE(AVG(canonical_link_score), 0) + COALESCE(AVG(feature_alt_score), 0)) / 85.0 * 100.0,
        6
    ) AS total_score_pct
FROM `{table}`
WHERE (scoring = 'Y' OR UPPER(TRIM(COALESCE(scoring,'')))= 'Y')
  AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != ''
GROUP BY region, country
ORDER BY region, country
"""

# B2C report_es_old: ufn_score, basic_asset_score(단수), summary_spec_score, faqs_score, title_tag_score, description_tag_score, h1_tag_score, canonical_link_score, feature_alt_score, front_image_alt_score
SQL_B2C_SNAPSHOT = """
SELECT
    region,
    country,
    division,
    COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score), 6) AS ufn_score,
    ROUND(AVG(basic_asset_score), 6) AS basic_assets_score,
    ROUND(AVG(summary_spec_score), 6) AS spec_summary_score,
    ROUND(AVG(faqs_score), 6) AS faq_score,
    ROUND(AVG(title_tag_score), 6) AS title_score,
    ROUND(AVG(description_tag_score), 6) AS description_score,
    ROUND(AVG(h1_tag_score), 6) AS h1_score,
    ROUND(AVG(canonical_link_score), 6) AS canonical_score,
    ROUND(AVG(feature_alt_score), 6) AS alt_feature_score,
    ROUND(AVG(front_image_alt_score), 6) AS alt_front_score,
    ROUND(
        (COALESCE(AVG(ufn_score),0) + COALESCE(AVG(basic_asset_score),0) + COALESCE(AVG(summary_spec_score),0) + COALESCE(AVG(faqs_score),0)
         + COALESCE(AVG(title_tag_score),0) + COALESCE(AVG(description_tag_score),0) + COALESCE(AVG(h1_tag_score),0) + COALESCE(AVG(canonical_link_score),0)
         + COALESCE(AVG(feature_alt_score),0) + COALESCE(AVG(front_image_alt_score),0)),
        6
    ) AS total_score_pct
FROM `{table}`
WHERE (monitoring = 'Y' OR UPPER(TRIM(COALESCE(monitoring,'')))= 'Y')
  AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != '' AND TRIM(COALESCE(division,'')) != ''
GROUP BY region, country, division
ORDER BY region, country, division
"""


def _parse_month(month_str):
    """'YYYY-MM' -> (year_int, month_int), 'latest' or empty -> None."""
    if not month_str or str(month_str).strip().lower() == "latest":
        return None
    s = str(month_str).strip()
    parts = s.split("-")
    if len(parts) != 2:
        return None
    try:
        y, m = int(parts[0]), int(parts[1])
        if 1 <= m <= 12:
            return (y, m)
    except (ValueError, TypeError):
        pass
    return None


def _get_latest_year_month(conn, table):
    """테이블에서 가장 최근 (year, month) 반환."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT year, month FROM `{table}` WHERE year IS NOT NULL AND month IS NOT NULL ORDER BY year DESC, month DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row and len(row) >= 2:
            y, m = row[0], row[1]
            if y is not None and m is not None:
                return (int(float(y)), int(float(m)))
    except Exception:
        pass
    return None


def get_summary_b2b_snapshot_sql(region_filter=None, country_filter=None, month=None) -> list[dict]:
    """B2B SUMMARY. month 지정 시 해당 월만 조회. SUMMARY_VIEW_B2B는 month 미지원이면 RAW 테이블 사용."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        month_param = _parse_month(month) if month else None
        use_view = bool(SUMMARY_VIEW_B2B and (month_param is None))
        if not use_view and month_param is None:
            month_param = _get_latest_year_month(conn, TABLE_B2B)
        if use_view:
            cursor.execute(f"SELECT * FROM `{SUMMARY_VIEW_B2B}`")
            rows = _cursor_to_rows(cursor)
        else:
            if B2B_SCORE_SCHEMA == "v2":
                sql = SQL_B2B_SNAPSHOT_V2.format(table=TABLE_B2B)
            else:
                sql = SQL_B2B_SNAPSHOT.format(table=TABLE_B2B)
            if month_param:
                y, m = month_param
                sql = sql.replace("GROUP BY", " AND year = %s AND CAST(month AS UNSIGNED) = %s\nGROUP BY")
                cursor.execute(sql, (y, m))
            else:
                cursor.execute(sql)
            rows = _cursor_to_rows(cursor)
        if region_filter:
            rows = [r for r in rows if r.get("region") in region_filter]
        if country_filter:
            rows = [r for r in rows if r.get("country") in country_filter]
        return _normalize_numeric_rows(rows)
    finally:
        conn.close()


def get_summary_b2c_snapshot_sql(region_filter=None, country_filter=None, month=None) -> list[dict]:
    """B2C SUMMARY. month 지정 시 해당 월만 조회."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        month_param = _parse_month(month) if month else None
        use_view = bool(SUMMARY_VIEW_B2C and (month_param is None))
        if not use_view and month_param is None:
            month_param = _get_latest_year_month(conn, TABLE_B2C)
        if use_view:
            cursor.execute(f"SELECT * FROM `{SUMMARY_VIEW_B2C}`")
            rows = _cursor_to_rows(cursor)
        else:
            sql = SQL_B2C_SNAPSHOT.format(table=TABLE_B2C)
            if month_param:
                y, m = month_param
                sql = sql.replace("GROUP BY", " AND year = %s AND CAST(month AS UNSIGNED) = %s\nGROUP BY")
                cursor.execute(sql, (y, m))
            else:
                cursor.execute(sql)
            rows = _cursor_to_rows(cursor)
        if region_filter:
            rows = [r for r in rows if r.get("region") in region_filter]
        if country_filter:
            rows = [r for r in rows if r.get("country") in country_filter]
        return _normalize_numeric_rows(rows)
    finally:
        conn.close()


def get_b2b_raw_df(conn=None):
    """B2B RAW DataFrame (전처리 적용). conn 없으면 새 연결 후 닫음."""
    own = conn is None
    if own:
        conn = get_connection()
    try:
        df = _load_table(conn, TABLE_B2B)
        df = preprocess_b2b(df, COLUMN_ALIAS_B2B)
        return df
    finally:
        if own and conn:
            conn.close()


def get_b2c_raw_df(conn=None):
    """B2C RAW DataFrame (전처리 적용)."""
    own = conn is None
    if own:
        conn = get_connection()
    try:
        df = _load_table(conn, TABLE_B2C)
        df = preprocess_b2c(df, COLUMN_ALIAS_B2C)
        return df
    finally:
        if own and conn:
            conn.close()


def _b2b_sql_all_zeros(rows: list[dict]) -> bool:
    """B2B SQL 결과가 전부 0인지 (점수 컬럼 기준). 전부 0이면 pandas 폴백으로 재집계."""
    if not rows:
        return True
    for r in rows:
        for k in ("h1_tag_score", "canonical_link_score", "feature_alt_score", "total_score_pct"):
            v = r.get(k)
            if v is not None and v != "" and float(v) != 0:
                return False
    return True


def get_summary_b2b_snapshot(region_filter=None, country_filter=None, month=None) -> list[dict]:
    """B2B SUMMARY. 집계 VIEW/테이블(SUMMARY_VIEW_B2B) 또는 SQL 집계 우선(빠름). 실패 시에만 pandas 폴백. 스코어 null→0 보정."""
    # 1) 미리 만들어 둔 집계 VIEW/테이블이 있으면 그대로 읽기 (가장 빠름)
    if SUMMARY_VIEW_B2B:
        try:
            rows = get_summary_b2b_snapshot_sql(region_filter, country_filter, month=month)
            return _b2b_fill_scores(rows)
        except Exception:
            pass
    # 2) VIEW 없으면 RAW 테이블에 대해 SQL로 집계 (pandas보다 빠름)
    try:
        rows = get_summary_b2b_snapshot_sql(region_filter, country_filter, month=month)
        if rows and not _b2b_sql_all_zeros(rows):
            return _b2b_fill_scores(rows)
    except Exception:
        pass
    # 3) 폴백: pandas로 RAW 로드 후 집계
    df = get_b2b_raw_df()
    if not df.empty:
        snap = aggregate_b2b_snapshot(df)
        if not snap.empty:
            rows = _df_to_rows(snap)
            if region_filter:
                rows = [r for r in rows if r.get("region") in region_filter]
            if country_filter:
                rows = [r for r in rows if r.get("country") in country_filter]
            if rows:
                return _b2b_fill_scores(rows)
    try:
        rows = get_summary_b2b_snapshot_sql(region_filter, country_filter, month=month)
        return _b2b_fill_scores(rows)
    except Exception:
        return []


def get_summary_b2c_snapshot(region_filter=None, country_filter=None, month=None) -> list[dict]:
    """B2C SUMMARY. month 지정 시 해당 월만 조회."""
    try:
        return get_summary_b2c_snapshot_sql(region_filter, country_filter, month=month)
    except Exception:
        df = get_b2c_raw_df()
        if df.empty:
            return []
        snap = aggregate_b2c_snapshot(df)
        rows = _df_to_rows(snap)
        if region_filter:
            rows = [r for r in rows if r.get("region") in region_filter]
        if country_filter:
            rows = [r for r in rows if r.get("country") in country_filter]
        return rows


def get_available_months() -> list[dict]:
    """DB에서 report_type별 사용 가능한 year/month 목록. month 포맷: YYYY-MM. 'latest' 포함."""
    result: list[dict] = []
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for report_type, table in (("B2B", TABLE_B2B), ("B2C", TABLE_B2C)):
            try:
                cursor.execute(
                    f"SELECT DISTINCT year, month FROM `{table}` WHERE year IS NOT NULL AND month IS NOT NULL ORDER BY year DESC, month DESC LIMIT 24"
                )
                rows = cursor.fetchall()
            except Exception:
                rows = []
            months = []
            for row in rows:
                y, m = row[0], row[1]
                if y is not None and m is not None:
                    try:
                        sy = str(int(float(y)))
                        sm = str(int(float(m)))
                        if sy and sm:
                            months.append(f"{sy}-{sm.zfill(2)}")
                    except (TypeError, ValueError):
                        pass
            result.append({"report_type": report_type, "month": "latest"})
            for mon in months:
                result.append({"report_type": report_type, "month": mon})
    finally:
        conn.close()
    return result


def get_summary_snapshot(report_type: str, region_filter=None, country_filter=None, month=None) -> list[dict]:
    if report_type.upper() == "B2B":
        return get_summary_b2b_snapshot(region_filter, country_filter, month=month)
    if report_type.upper() == "B2C":
        return get_summary_b2c_snapshot(region_filter, country_filter, month=month)
    return []


def get_summary_trend(report_type: str, by: str) -> list[dict]:
    if report_type.upper() == "B2B":
        df = get_b2b_raw_df()
        if df.empty:
            return []
        if by == "month":
            t = aggregate_b2b_trend_month(df)
        else:
            t = aggregate_b2b_trend_week(df)
        return _df_to_rows(t)
    if report_type.upper() == "B2C":
        df = get_b2c_raw_df()
        if df.empty:
            return []
        if by == "month":
            t = aggregate_b2c_trend_month(df)
        else:
            t = aggregate_b2c_trend_week(df)
        return _df_to_rows(t)
    return []


def get_filters_from_snapshot(report_type: str, region_filter: tuple = (), month=None) -> dict:
    rows = get_summary_snapshot(report_type, month=month)
    regions = sorted({r.get("region") for r in rows if r.get("region")} - {None, ""})
    if region_filter:
        region_set = set(region_filter)
        rows = [r for r in rows if r.get("region") in region_set]
    countries = sorted({r.get("country") for r in rows if r.get("country")} - {None, ""})
    return {"regions": regions, "countries": countries}


def get_raw_rows(report_type: str, region_filter=None, country_filter=None, limit: int = 0) -> list[dict]:
    """RAW 테이블 행 목록. limit=0 이면 전부."""
    if report_type.upper() == "B2B":
        df = get_b2b_raw_df()
    elif report_type.upper() == "B2C":
        df = get_b2c_raw_df()
    else:
        return []
    if df.empty:
        return []
    if region_filter:
        if "region" in df.columns:
            df = df[df["region"].astype(str).isin(region_filter)]
    if country_filter:
        if "country" in df.columns:
            df = df[df["country"].astype(str).isin(country_filter)]
    if limit > 0:
        df = df.head(limit)
    return _df_to_rows(df)


def get_raw_df_for_download(report_type: str, region_filter=None, country_filter=None) -> pd.DataFrame:
    """RAW 다운로드용 DataFrame."""
    if report_type.upper() == "B2B":
        df = get_b2b_raw_df()
    elif report_type.upper() == "B2C":
        df = get_b2c_raw_df()
    else:
        return pd.DataFrame()
    if df.empty:
        return df
    if region_filter and "region" in df.columns:
        df = df[df["region"].astype(str).isin(region_filter)]
    if country_filter and "country" in df.columns:
        df = df[df["country"].astype(str).isin(country_filter)]
    return df
