# -*- coding: utf-8 -*-
"""집계: B2B/B2C 전처리 결과 -> SUMMARY (스냅 / 월별·주차별 트렌드)."""
import pandas as pd

try:
    from .config import B2B_SCORE_COLUMNS, B2C_SCORE_COLUMNS
except ImportError:
    from pipeline.config import B2B_SCORE_COLUMNS, B2C_SCORE_COLUMNS

B2B_MAX = 85.0
B2C_MAX = 100.0


def _agg_b2b(df, group_cols):
    cols = [c for c in B2B_SCORE_COLUMNS if c in df.columns]
    if not cols:
        return pd.DataFrame()
    agg = df.groupby(group_cols, as_index=False).agg(
        sku_count=("country", "count"),
        **{c: (c, "mean") for c in cols}
    )
    agg["total_score_pct"] = agg[cols].sum(axis=1) / B2B_MAX * 100.0
    return agg.round(6)


def aggregate_b2b_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    return _agg_b2b(df, ["region", "country"])


def aggregate_b2b_trend_month(df: pd.DataFrame) -> pd.DataFrame:
    if "year" not in df.columns or "month" not in df.columns:
        return pd.DataFrame()
    return _agg_b2b(df, ["region", "country", "year", "month"])


def aggregate_b2b_trend_week(df: pd.DataFrame) -> pd.DataFrame:
    if "year" not in df.columns or "week" not in df.columns:
        return pd.DataFrame()
    return _agg_b2b(df, ["region", "country", "year", "week"])


def _agg_b2c(df, group_cols):
    cols = [c for c in B2C_SCORE_COLUMNS if c in df.columns]
    if not cols:
        return pd.DataFrame()
    agg = df.groupby(group_cols, as_index=False).agg(
        sku_count=("country", "count"),
        **{c: (c, "mean") for c in cols}
    )
    agg["total_score_pct"] = agg[cols].mean(axis=1) * 10
    return agg.round(6)


def aggregate_b2c_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    return _agg_b2c(df, ["region", "country", "division"])


def aggregate_b2c_trend_month(df: pd.DataFrame) -> pd.DataFrame:
    if "year" not in df.columns or "month" not in df.columns:
        return pd.DataFrame()
    return _agg_b2c(df, ["region", "country", "division", "year", "month"])


def aggregate_b2c_trend_week(df: pd.DataFrame) -> pd.DataFrame:
    if "year" not in df.columns or "week" not in df.columns:
        return pd.DataFrame()
    return _agg_b2c(df, ["region", "country", "division", "year", "week"])
