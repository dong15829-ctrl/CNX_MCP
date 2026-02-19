# -*- coding: utf-8 -*-
"""
데이터 전처리: B2B / B2C RAW 필터링, 타입 정규화, 결측 처리.
"""
import pandas as pd


def _normalize_columns(df: pd.DataFrame, alias: dict) -> pd.DataFrame:
    """DB 컬럼명을 표준명으로 매핑. alias: standard_name -> db_column_name."""
    rename = {}
    for std_name, db_name in alias.items():
        if db_name in df.columns and std_name != db_name:
            rename[db_name] = std_name
        else:
            for c in df.columns:
                if str(c).strip().lower() == str(db_name).strip().lower() and c not in rename:
                    rename[c] = std_name
                    break
    return df.rename(columns=rename) if rename else df


def preprocess_b2b(df: pd.DataFrame, alias: dict) -> pd.DataFrame:
    """
    B2B RAW 전처리.
    - 컬럼명 표준화
    - scoring_yn == 'Y' 필터
    - 필수 키/점수 컬럼 결측 제거 또는 보정
    - year, month, week 숫자화
    """
    df = df.copy()
    df = _normalize_columns(df, alias)
    # 조건: Scoring Y/N = 'Y'
    scoring_col = "scoring_yn"
    if scoring_col not in df.columns:
        for c in df.columns:
            if "scoring" in str(c).lower() or "y/n" in str(c).lower():
                df = df.rename(columns={c: scoring_col})
                break
    if scoring_col in df.columns:
        df = df[df[scoring_col].astype(str).str.upper().str.strip() == "Y"]
    # 필수 키
    for col in ["region", "country"]:
        if col in df.columns:
            df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
    # 점수 컬럼 숫자화
    score_cols = [
        "title_tag_score", "description_tag_score", "h1_tag_score",
        "canonical_link_score", "feature_alt_score"
    ]
    for c in score_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # 시계열
    for c in ["year", "month", "week"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def preprocess_b2c(df: pd.DataFrame, alias: dict) -> pd.DataFrame:
    """
    B2C RAW 전처리.
    - 컬럼명 표준화
    - monitoring == 'Y' 필터
    - 필수 키/점수 컬럼 결측 보정
    - year, month, week 숫자화
    """
    df = df.copy()
    df = _normalize_columns(df, alias)
    # 조건: Monitoring = 'Y'
    mon_col = "monitoring"
    if mon_col not in df.columns:
        for c in df.columns:
            if "monitoring" in str(c).lower():
                df = df.rename(columns={c: mon_col})
                break
    if mon_col in df.columns:
        df = df[df[mon_col].astype(str).str.upper().str.strip() == "Y"]
    # 필수 키
    for col in ["region", "country", "division"]:
        if col in df.columns:
            df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
    # 점수 컬럼 숫자화
    score_cols = [
        "ufn_score", "basic_assets_score", "spec_summary_score", "faq_score",
        "title_score", "description_score", "h1_score", "canonical_score",
        "alt_feature_score", "alt_front_score"
    ]
    for c in score_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # 시계열
    for c in ["year", "month", "week"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df
