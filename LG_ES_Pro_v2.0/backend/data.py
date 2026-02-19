# -*- coding: utf-8 -*-
"""DB 기반 데이터 로드 및 집계."""
import os, sys
from pathlib import Path
from decimal import Decimal

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd
from backend.db import get_connection, TABLE_B2B, TABLE_B2C

SUMMARY_VIEW_B2B = os.environ.get("SUMMARY_VIEW_B2B", "").strip() or None
SUMMARY_VIEW_B2C = os.environ.get("SUMMARY_VIEW_B2C", "").strip() or None

def _b2b_score_schema():
    v = os.environ.get("B2B_SCORE_SCHEMA", "").strip().lower()
    if v in ("v2", "legacy"): return v
    return "v2" if (TABLE_B2B and "v2" in TABLE_B2B) else "legacy"
B2B_SCORE_SCHEMA = _b2b_score_schema()

from pipeline.config import COLUMN_ALIAS_B2B, COLUMN_ALIAS_B2C
from pipeline.preprocess import preprocess_b2b, preprocess_b2c
from pipeline.aggregate import (
    aggregate_b2b_snapshot, aggregate_b2b_trend_month, aggregate_b2b_trend_week,
    aggregate_b2c_snapshot, aggregate_b2c_trend_month, aggregate_b2c_trend_week,
)

def _load_table(conn, table): return pd.read_sql(f"SELECT * FROM `{table}`", conn)

def _df_to_rows(df):
    if df is None or df.empty: return []
    df = df.copy()
    for c in df.columns:
        if hasattr(df[c].dtype, "kind") and df[c].dtype.kind == "f":
            df[c] = df[c].fillna(0.0).apply(lambda x: round(float(x), 6))
    return df.to_dict(orient="records")

def _cursor_to_rows(cursor):
    if cursor.description is None: return []
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def _normalize_numeric_rows(rows):
    out = []
    for r in rows:
        row = {}
        for k, v in r.items():
            if v is None or v == "": row[k] = v
            elif isinstance(v, Decimal): row[k] = round(float(v), 6)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                row[k] = round(float(v), 6) if isinstance(v, float) else v
            else: row[k] = v
        out.append(row)
    return out

B2B_SCORE_KEYS = ("title_tag_score", "description_tag_score", "h1_tag_score", "canonical_link_score", "feature_alt_score", "total_score_pct")

def _b2b_fill_scores(rows):
    out = []
    for r in rows:
        row = dict(r)
        for k in B2B_SCORE_KEYS:
            v = row.get(k)
            row[k] = 0.0 if (v is None or v == "") else (float(v) if not isinstance(v, (int, float)) else v)
        out.append(row)
    return out

SQL_B2B_SNAPSHOT_V2 = """
SELECT region, country, COUNT(*) AS sku_count,
    ROUND(COALESCE(AVG(title_tag_score),0),6) AS title_tag_score,
    ROUND(COALESCE(AVG(description_tag_score),0),6) AS description_tag_score,
    ROUND(COALESCE(AVG(h1_tag_score),0),6) AS h1_tag_score,
    ROUND(COALESCE(AVG(canonical_link_score),0),6) AS canonical_link_score,
    ROUND(COALESCE(AVG(feature_alt_score),0),6) AS feature_alt_score,
    ROUND((COALESCE(AVG(title_tag_score),0)+COALESCE(AVG(description_tag_score),0)
        +COALESCE(AVG(h1_tag_score),0)+COALESCE(AVG(canonical_link_score),0)+COALESCE(AVG(feature_alt_score),0))/85.0*100.0,6) AS total_score_pct
FROM `{table}`
WHERE (scoring='Y' OR UPPER(TRIM(COALESCE(scoring,'')))='Y')
  AND TRIM(COALESCE(region,''))!='' AND TRIM(COALESCE(country,''))!=''
GROUP BY region, country ORDER BY region, country
"""

SQL_B2B_SNAPSHOT = """
SELECT region, country, COUNT(*) AS sku_count,
    0 AS title_tag_score, 0 AS description_tag_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(h1_tag_pf,'')),',','.'),''   ) AS DECIMAL(10,2))),0),6) AS h1_tag_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(canonical_link_pf,'')),',','.'),'') AS DECIMAL(10,2))),0),6) AS canonical_link_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(feature_cards,'')),',','.'),'') AS DECIMAL(10,2))),0),6) AS feature_alt_score,
    ROUND((COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(h1_tag_pf,'')),',','.'),''  ) AS DECIMAL(10,2))),0)
        +COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(canonical_link_pf,'')),',','.'),'') AS DECIMAL(10,2))),0)
        +COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(feature_cards,'')),',','.'),'') AS DECIMAL(10,2))),0))/85.0*100.0,6) AS total_score_pct
FROM `{table}`
WHERE (scoring='Y' OR UPPER(TRIM(COALESCE(scoring,'')))='Y')
  AND TRIM(COALESCE(region,''))!='' AND TRIM(COALESCE(country,''))!=''
GROUP BY region, country ORDER BY region, country
"""

SQL_B2C_SNAPSHOT = """
SELECT region, country, division, COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score),6) AS ufn_score,
    ROUND(AVG(basic_asset_score),6) AS basic_assets_score,
    ROUND(AVG(summary_spec_score),6) AS spec_summary_score,
    ROUND(AVG(faqs_score),6) AS faq_score,
    ROUND(AVG(title_tag_score),6) AS title_score,
    ROUND(AVG(description_tag_score),6) AS description_score,
    ROUND(AVG(h1_tag_score),6) AS h1_score,
    ROUND(AVG(canonical_link_score),6) AS canonical_score,
    ROUND(AVG(feature_alt_score),6) AS alt_feature_score,
    ROUND(AVG(front_image_alt_score),6) AS alt_front_score,
    ROUND((COALESCE(AVG(ufn_score),0)+COALESCE(AVG(basic_asset_score),0)+COALESCE(AVG(summary_spec_score),0)+COALESCE(AVG(faqs_score),0)
        +COALESCE(AVG(title_tag_score),0)+COALESCE(AVG(description_tag_score),0)+COALESCE(AVG(h1_tag_score),0)+COALESCE(AVG(canonical_link_score),0)
        +COALESCE(AVG(feature_alt_score),0)+COALESCE(AVG(front_image_alt_score),0)),6) AS total_score_pct
FROM `{table}`
WHERE (monitoring='Y' OR UPPER(TRIM(COALESCE(monitoring,'')))='Y')
  AND TRIM(COALESCE(region,''))!='' AND TRIM(COALESCE(country,''))!='' AND TRIM(COALESCE(division,''))!=''
GROUP BY region, country, division ORDER BY region, country, division
"""

def _parse_month(month_str):
    if not month_str or str(month_str).strip().lower() == "latest": return None
    parts = str(month_str).strip().split("-")
    if len(parts) != 2: return None
    try:
        y, m = int(parts[0]), int(parts[1])
        if 1 <= m <= 12: return (y, m)
    except (ValueError, TypeError): pass
    return None

def _get_latest_year_month(conn, table):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT year, month FROM `{table}` WHERE year IS NOT NULL AND month IS NOT NULL ORDER BY year DESC, month DESC LIMIT 1")
        row = cursor.fetchone()
        if row and len(row) >= 2 and row[0] is not None and row[1] is not None:
            return (int(float(row[0])), int(float(row[1])))
    except Exception: pass
    return None

def get_summary_b2b_snapshot_sql(region_filter=None, country_filter=None, month=None):
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
            sql = (SQL_B2B_SNAPSHOT_V2 if B2B_SCORE_SCHEMA == "v2" else SQL_B2B_SNAPSHOT).format(table=TABLE_B2B)
            if month_param:
                sql = sql.replace("GROUP BY", " AND year = %s AND CAST(month AS UNSIGNED) = %s\nGROUP BY")
                cursor.execute(sql, month_param)
            else:
                cursor.execute(sql)
            rows = _cursor_to_rows(cursor)
        if region_filter: rows = [r for r in rows if r.get("region") in region_filter]
        if country_filter: rows = [r for r in rows if r.get("country") in country_filter]
        return _normalize_numeric_rows(rows)
    finally: conn.close()

def get_summary_b2c_snapshot_sql(region_filter=None, country_filter=None, month=None):
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
                sql = sql.replace("GROUP BY", " AND year = %s AND CAST(month AS UNSIGNED) = %s\nGROUP BY")
                cursor.execute(sql, month_param)
            else:
                cursor.execute(sql)
            rows = _cursor_to_rows(cursor)
        if region_filter: rows = [r for r in rows if r.get("region") in region_filter]
        if country_filter: rows = [r for r in rows if r.get("country") in country_filter]
        return _normalize_numeric_rows(rows)
    finally: conn.close()

def get_b2b_raw_df(conn=None):
    own = conn is None
    if own: conn = get_connection()
    try:
        df = _load_table(conn, TABLE_B2B)
        return preprocess_b2b(df, COLUMN_ALIAS_B2B)
    finally:
        if own and conn: conn.close()

def get_b2c_raw_df(conn=None):
    own = conn is None
    if own: conn = get_connection()
    try:
        df = _load_table(conn, TABLE_B2C)
        return preprocess_b2c(df, COLUMN_ALIAS_B2C)
    finally:
        if own and conn: conn.close()

def _b2b_sql_all_zeros(rows):
    if not rows: return True
    for r in rows:
        for k in ("h1_tag_score", "canonical_link_score", "feature_alt_score", "total_score_pct"):
            v = r.get(k)
            if v is not None and v != "" and float(v) != 0: return False
    return True

def get_summary_b2b_snapshot(region_filter=None, country_filter=None, month=None):
    if SUMMARY_VIEW_B2B:
        try: return _b2b_fill_scores(get_summary_b2b_snapshot_sql(region_filter, country_filter, month=month))
        except Exception: pass
    try:
        rows = get_summary_b2b_snapshot_sql(region_filter, country_filter, month=month)
        if rows and not _b2b_sql_all_zeros(rows): return _b2b_fill_scores(rows)
    except Exception: pass
    df = get_b2b_raw_df()
    if not df.empty:
        snap = aggregate_b2b_snapshot(df)
        if not snap.empty:
            rows = _df_to_rows(snap)
            if region_filter: rows = [r for r in rows if r.get("region") in region_filter]
            if country_filter: rows = [r for r in rows if r.get("country") in country_filter]
            if rows: return _b2b_fill_scores(rows)
    try: return _b2b_fill_scores(get_summary_b2b_snapshot_sql(region_filter, country_filter, month=month))
    except Exception: return []

def get_summary_b2c_snapshot(region_filter=None, country_filter=None, month=None):
    try: return get_summary_b2c_snapshot_sql(region_filter, country_filter, month=month)
    except Exception:
        df = get_b2c_raw_df()
        if df.empty: return []
        snap = aggregate_b2c_snapshot(df)
        rows = _df_to_rows(snap)
        if region_filter: rows = [r for r in rows if r.get("region") in region_filter]
        if country_filter: rows = [r for r in rows if r.get("country") in country_filter]
        return rows

def get_available_months():
    result = []
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for rt, table in (("B2B", TABLE_B2B), ("B2C", TABLE_B2C)):
            try:
                cursor.execute(f"SELECT DISTINCT year, month FROM `{table}` WHERE year IS NOT NULL AND month IS NOT NULL ORDER BY year DESC, month DESC LIMIT 24")
                rows = cursor.fetchall()
            except Exception: rows = []
            months = []
            for row in rows:
                y, m = row[0], row[1]
                if y is not None and m is not None:
                    try: months.append(f"{int(float(y))}-{str(int(float(m))).zfill(2)}")
                    except (TypeError, ValueError): pass
            result.append({"report_type": rt, "month": "latest"})
            for mon in months: result.append({"report_type": rt, "month": mon})
    finally: conn.close()
    return result

def get_summary_snapshot(report_type, region_filter=None, country_filter=None, month=None):
    if report_type.upper() == "B2B": return get_summary_b2b_snapshot(region_filter, country_filter, month=month)
    if report_type.upper() == "B2C": return get_summary_b2c_snapshot(region_filter, country_filter, month=month)
    return []

def get_summary_trend(report_type, by):
    if report_type.upper() == "B2B":
        df = get_b2b_raw_df()
        if df.empty: return []
        return _df_to_rows(aggregate_b2b_trend_month(df) if by == "month" else aggregate_b2b_trend_week(df))
    if report_type.upper() == "B2C":
        df = get_b2c_raw_df()
        if df.empty: return []
        return _df_to_rows(aggregate_b2c_trend_month(df) if by == "month" else aggregate_b2c_trend_week(df))
    return []

def get_filters_from_snapshot(report_type, region_filter=(), month=None):
    rows = get_summary_snapshot(report_type, month=month)
    regions = sorted({r.get("region") for r in rows if r.get("region")} - {None, ""})
    if region_filter:
        rows = [r for r in rows if r.get("region") in set(region_filter)]
    countries = sorted({r.get("country") for r in rows if r.get("country")} - {None, ""})
    return {"regions": regions, "countries": countries}

def get_raw_rows(report_type, region_filter=None, country_filter=None, limit=0):
    if report_type.upper() == "B2B": df = get_b2b_raw_df()
    elif report_type.upper() == "B2C": df = get_b2c_raw_df()
    else: return []
    if df.empty: return []
    if region_filter and "region" in df.columns: df = df[df["region"].astype(str).isin(region_filter)]
    if country_filter and "country" in df.columns: df = df[df["country"].astype(str).isin(country_filter)]
    if limit > 0: df = df.head(limit)
    return _df_to_rows(df)

def get_raw_df_for_download(report_type, region_filter=None, country_filter=None):
    if report_type.upper() == "B2B": df = get_b2b_raw_df()
    elif report_type.upper() == "B2C": df = get_b2c_raw_df()
    else: return pd.DataFrame()
    if df.empty: return df
    if region_filter and "region" in df.columns: df = df[df["region"].astype(str).isin(region_filter)]
    if country_filter and "country" in df.columns: df = df[df["country"].astype(str).isin(country_filter)]
    return df
