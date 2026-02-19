#!/usr/bin/env python3
"""
B2C 엑셀 PDP_Raw 시트를 읽어 Summary by Country와 동일한 집계로 SUMMARY 테이블을 생성합니다.
(엑셀 데이터 기반 쿼리와 동일한 로직 → CSV/엑셀 출력)

수식: AVERAGEIFS(PDP_Raw!AK:AT, Country=Summary.C, Monitoring='Y', Division=Summary.D)
"""
import pandas as pd
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "DATA"
OUT_DIR = Path(__file__).resolve().parent

# B2C 엑셀 파일 (기본: 최신 M11)
B2C_FILES = [
    "LG.com ES B2C Contents Monitoring Report_2025-M11.xlsx",
    "LG.com ES B2C Contents Monitoring Report_2025-M10.xlsx",
    "LG.com ES B2C Contents Monitoring Report_2025-M8.xlsx",
]

# PDP_Raw 점수 컬럼 (엑셀 AK~AT = 1. UFN ~ 10. Tag <Alt text>_(Front Image))
SCORE_COLS = [
    "1. UFN",
    "2. Basic Assets",
    "3. Spec Summary",
    "4. FAQ",
    "5. Tag <Title>",
    "6. Tag <Description>",
    "7. Tag <H1>",
    "8. Tag <Canonical Link>",
    "9. Tag <Alt text>_(Feature Cards) ",
    "10. Tag <Alt text>_(Front Image)",
]


def load_pdp_raw(excel_path: Path) -> pd.DataFrame:
    df = pd.read_excel(excel_path, sheet_name="PDP_Raw", header=1)
    return df


def build_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """PDP_Raw에서 Summary by Country와 동일한 집계 (Monitoring='Y', Region/Country/Division별)."""
    scored = df[df["Monitoring"] == "Y"].copy()
    score_cols_present = [c for c in SCORE_COLS if c in scored.columns]
    agg_dict = {"Monitoring": "count"}
    agg_dict.update({c: "mean" for c in score_cols_present})
    out = scored.groupby(["Region", "Country", "Division"], as_index=False).agg(agg_dict)
    out = out.rename(columns={"Monitoring": "sku_count"})
    # Summary K~T 컬럼명 정리 (B2B SUMMARY 테이블과 유사한 네이밍)
    renames = {
        "1. UFN": "ufn_avg",
        "2. Basic Assets": "basic_assets_avg",
        "3. Spec Summary": "spec_summary_avg",
        "4. FAQ": "faq_avg",
        "5. Tag <Title>": "title_avg",
        "6. Tag <Description>": "description_avg",
        "7. Tag <H1>": "h1_avg",
        "8. Tag <Canonical Link>": "canonical_avg",
        "9. Tag <Alt text>_(Feature Cards) ": "alt_feature_avg",
        "10. Tag <Alt text>_(Front Image)": "alt_front_avg",
    }
    out = out.rename(columns={k: v for k, v in renames.items() if k in out.columns})
    avg_cols = [c for c in renames.values() if c in out.columns]
    if avg_cols:
        out["total_score_pct"] = out[avg_cols].mean(axis=1)
    out = out.round(6)
    return out


def main():
    for filename in B2C_FILES:
        excel_path = DATA_DIR / filename
        if not excel_path.exists():
            continue
        print(f"처리 중: {filename}")
        pdp = load_pdp_raw(excel_path)
        summary = build_summary_table(pdp)
        base = filename.replace(".xlsx", "").replace(".xls", "")
        csv_path = OUT_DIR / f"SUMMARY_B2C_{base}.csv"
        summary.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"  → 저장: {csv_path} ({len(summary)}행)")
    if not any((DATA_DIR / f).exists() for f in B2C_FILES):
        print(f"B2C 엑셀 파일이 없습니다. {DATA_DIR} 확인.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
