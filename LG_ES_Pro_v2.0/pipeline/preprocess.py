# -*- coding: utf-8 -*-
"""데이터 전처리: B2B/B2C RAW 필터링, 타입 정규화."""
import pandas as pd


def _normalize_columns(df, alias):
    rename = {}
    for std, db in alias.items():
        if db in df.columns and std != db:
            rename[db] = std
        else:
            for c in df.columns:
                if str(c).strip().lower() == str(db).strip().lower() and c not in rename:
                    rename[c] = std; break
    return df.rename(columns=rename) if rename else df


def _normalize_columns_flexible(df, possible):
    rename = {}
    for std, cands in possible.items():
        if std in df.columns: continue
        for c in df.columns:
            for cand in cands:
                if str(c).strip().lower() == str(cand).strip().lower():
                    rename[c] = std; break
            if c in rename: break
    return df.rename(columns=rename) if rename else df


def preprocess_b2b(df, alias):
    df = df.copy()
    try: from .config import B2B_POSSIBLE_COLUMN_NAMES
    except ImportError: from pipeline.config import B2B_POSSIBLE_COLUMN_NAMES
    df = _normalize_columns_flexible(df, B2B_POSSIBLE_COLUMN_NAMES)
    df = _normalize_columns(df, alias)
    scoring_col = "scoring_yn"
    if scoring_col not in df.columns:
        for c in df.columns:
            if "scoring" in str(c).lower():
                df = df.rename(columns={c: scoring_col}); break
    if scoring_col in df.columns:
        df = df[df[scoring_col].astype(str).str.upper().str.strip().isin(("Y", "YES", "1"))]
    for col in ["region", "country"]:
        if col in df.columns:
            df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
    for c in ["title_tag_score", "description_tag_score", "h1_tag_score", "canonical_link_score", "feature_alt_score"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["year", "month", "week"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def preprocess_b2c(df, alias):
    df = df.copy()
    try: from .config import B2C_POSSIBLE_COLUMN_NAMES
    except ImportError: from pipeline.config import B2C_POSSIBLE_COLUMN_NAMES
    df = _normalize_columns_flexible(df, B2C_POSSIBLE_COLUMN_NAMES)
    df = _normalize_columns(df, alias)
    mon_col = "monitoring"
    if mon_col not in df.columns:
        for c in df.columns:
            if "monitoring" in str(c).lower():
                df = df.rename(columns={c: mon_col}); break
    if mon_col in df.columns:
        df = df[df[mon_col].astype(str).str.upper().str.strip() == "Y"]
    for col in ["region", "country", "division"]:
        if col in df.columns:
            df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
    for c in ["ufn_score", "basic_assets_score", "spec_summary_score", "faq_score", "title_score", "description_score", "h1_score", "canonical_score", "alt_feature_score", "alt_front_score"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["year", "month", "week"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    return df
