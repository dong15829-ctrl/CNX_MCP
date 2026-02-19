#!/usr/bin/env python3
"""
PLP_BUSINESS 시트에서 Summary와 동일한 집계를 수행하여 검증합니다.
엑셀 수식: AVERAGEIFS(PLP_BUSINESS!X:AB, Country=Summary.C, Scoring Y/N='Y')
"""
import pandas as pd
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "DATA"
B2B_FILE = "LG.com ES B2B Contents Monitoring Report_2025-M11.xlsx"


def load_plp_business(excel_path: Path) -> pd.DataFrame:
    df = pd.read_excel(excel_path, sheet_name="PLP_BUSINESS", header=1)
    return df


def aggregate_summary_from_plp(df: pd.DataFrame) -> pd.DataFrame:
    """PLP_BUSINESS에서 Summary K~O와 동일한 집계 (Scoring Y/N = 'Y'만)."""
    scored = df[df["Scoring Y/N"] == "Y"].copy()
    agg = scored.groupby(["Region", "Country"], as_index=False).agg(
        sku_count=("Country", "count"),
        title_avg=("Title Tag Score", "mean"),
        description_avg=("Description Tag Score", "mean"),
        h1_avg=("H1 Tag Score", "mean"),
        canonical_avg=("Canonical Link Score", "mean"),
        feature_alt_avg=("Feature Alt Score", "mean"),
        total_score_avg=("Total Score", "mean"),
    ).round(6)
    # Summary와 동일한 Total Score % (만점 85 가정)
    agg["total_score_pct"] = (
        agg["title_avg"] + agg["description_avg"] + agg["h1_avg"]
        + agg["canonical_avg"] + agg["feature_alt_avg"]
    ) / 85.0 * 100.0
    agg["total_score_pct"] = agg["total_score_pct"].round(6)
    return agg


def load_summary_sheet(excel_path: Path) -> pd.DataFrame:
    """Summary 시트에서 데이터 영역만 로드 (헤더 행 7~, Country=C열, K~O=11~15열)."""
    df = pd.read_excel(excel_path, sheet_name="Summary", header=None)
    # 데이터 행: 8~58 (0-based 7~57), C=2, K~O=10~14
    data = df.iloc[7:58, [2, 10, 11, 12, 13, 14]].copy()
    data.columns = ["country", "title_avg", "description_avg", "h1_avg", "canonical_avg", "feature_alt_avg"]
    data = data[data["country"].notna() & (data["country"].astype(str).str.strip() != "")]
    for c in ["title_avg", "description_avg", "h1_avg", "canonical_avg", "feature_alt_avg"]:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    return data


def main():
    excel_path = DATA_DIR / B2B_FILE
    if not excel_path.exists():
        print(f"파일 없음: {excel_path}", file=sys.stderr)
        sys.exit(1)

    plp = load_plp_business(excel_path)
    summary_agg = aggregate_summary_from_plp(plp)
    print("=== PLP_BUSINESS에서 집계한 Summary (Scoring Y/N = Y, 국가별) ===\n")
    print(summary_agg.head(20).to_string())
    print(f"\n... 총 {len(summary_agg)}개 국가")

    # Summary 시트와 비교 (같은 Country 기준)
    summary_sheet = load_summary_sheet(excel_path)
    merged = summary_agg.merge(
        summary_sheet,
        left_on="Country",
        right_on="country",
        how="outer",
        suffixes=("_plp", "_sheet"),
    )
    for col in ["title_avg", "description_avg", "h1_avg", "canonical_avg", "feature_alt_avg"]:
        plp_col, sheet_col = f"{col}_plp", f"{col}_sheet"
        if plp_col in merged.columns and sheet_col in merged.columns:
            diff = (merged[plp_col] - merged[sheet_col]).abs()
            max_diff = diff.max()
            print(f"\n{col}: PLP vs Sheet 최대 차이 = {max_diff:.6f}")
    print("\n검증 완료. (Product Category / Blog 컬럼은 다른 시트 참조로 제외)")


if __name__ == "__main__":
    main()
