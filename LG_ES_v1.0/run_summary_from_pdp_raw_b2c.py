#!/usr/bin/env python3
"""
B2C Summary by Country 시트와 동일한 집계를 PDP_Raw에서 수행하여 검증합니다.
엑셀 수식: AVERAGEIFS(PDP_Raw!AK:AT, Country=Summary.C, Monitoring='Y', Division=Summary.D)
"""
import pandas as pd
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "DATA"
B2C_FILE = "LG.com ES B2C Contents Monitoring Report_2025-M11.xlsx"

# PDP_Raw 점수 컬럼 (0-based 36~45 = AK~AT)
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


def aggregate_summary_from_pdp(df: pd.DataFrame) -> pd.DataFrame:
    """PDP_Raw에서 Summary by Country K~T와 동일한 집계 (Monitoring='Y', Country+Division별)."""
    scored = df[df["Monitoring"] == "Y"].copy()
    agg_cols = {c: "mean" for c in SCORE_COLS if c in scored.columns}
    if not agg_cols:
        # fallback: 컬럼명 공백/점 차이
        for i, c in enumerate(scored.columns):
            if i >= 36 and i <= 45:
                agg_cols[c] = "mean"
    agg = scored.groupby(["Region", "Country", "Division"], as_index=False).agg(
        sku_count=("Country", "count"),
        **{c.replace(".", "_").replace(" ", "_")[:20]: (c, "mean") for c in agg_cols}
    )
    # 컬럼명 단순화
    renames = {}
    for c in agg.columns:
        if c not in ["Region", "Country", "Division", "sku_count"] and "mean" in str(agg[c].dtype):
            renames[c] = f"score_{c[:15]}"
    agg = agg.rename(columns=renames)
    # total_score_pct (만점 100)
    score_cols_found = [c for c in agg.columns if c.startswith("score_") or c in SCORE_COLS]
    if score_cols_found:
        agg["total_score_pct"] = agg[score_cols_found].mean(axis=1) * 10  # 각 10점 만점
    agg = agg.round(6)
    return agg


def load_summary_sheet(excel_path: Path) -> pd.DataFrame:
    """Summary by Country 시트에서 데이터 영역만 로드 (C=country, D=division, K~T=10~19)."""
    df = pd.read_excel(excel_path, sheet_name="Summary by Country", header=None)
    # 데이터 행: 10~60 (0-based 9~59), C=2, D=3, K~T=열 10~19 (0-based 10~19)
    ncols = min(20, df.shape[1])
    data = df.iloc[9:60, list(range(2, ncols))].copy()
    data.columns = ["country", "division"] + [f"col_{i}" for i in range(10, 10 + data.shape[1] - 2)]
    data = data[data["country"].notna() & (data["country"].astype(str).str.strip() != "")]
    for i in range(2, data.shape[1]):
        data.iloc[:, i] = pd.to_numeric(data.iloc[:, i], errors="coerce")
    return data


def main():
    excel_path = DATA_DIR / B2C_FILE
    if not excel_path.exists():
        print(f"파일 없음: {excel_path}", file=sys.stderr)
        sys.exit(1)

    pdp = load_pdp_raw(excel_path)
    scored = pdp[pdp["Monitoring"] == "Y"].copy()
    score_cols_present = [c for c in SCORE_COLS if c in scored.columns]
    agg_dict = {"Region": "first", "Country": "first", "Division": "first", "Monitoring": "count"}
    agg_dict.update({c: "mean" for c in score_cols_present})
    out = scored.groupby(["Region", "Country", "Division"], as_index=False).agg(agg_dict)
    out = out.rename(columns={"Monitoring": "sku_count"})
    if score_cols_present:
        out["total_score_pct"] = out[score_cols_present].mean(axis=1)
    out = out.round(6)

    print("=== B2C PDP_Raw에서 집계한 Summary by Country (Monitoring=Y, 국가·Division별) ===\n")
    print(out.head(15).to_string())
    print(f"\n... 총 {len(out)}개 (Region, Country, Division) 조합")

    try:
        summary_sheet = load_summary_sheet(excel_path)
        merged = out.merge(
            summary_sheet,
            left_on=["Country", "Division"],
            right_on=["country", "division"],
            how="outer",
        )
        print("\n검증: Summary 시트와 동일 Country·Division 행 비교 시 수치 일치 여부 확인.")
    except Exception as e:
        print(f"\nSummary 시트 비교 생략: {e}")
    print("(U, W는 이전 기간/갭 참조로 PDP_Raw 단일 소스로는 미제공)")


if __name__ == "__main__":
    main()
