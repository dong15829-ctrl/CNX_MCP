#!/usr/bin/env python3
"""
Create modeling/test splits from the Jira CSV exports.

Default behaviour:
  - Treat DATA/jira_data_gta/JIRA 2025ыЕД_4Q.csv as test data.
  - Treat every other CSV within that folder as modeling (train/dev) data.
  - Deduplicate records on Issue key, keeping the most recently updated snapshot.
  - Persist the two datasets as Parquet files under DATA/processed/.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Jira modeling/test datasets.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("DATA") / "jira_data_gta",
        help="Directory containing the raw Jira CSV exports.",
    )
    parser.add_argument(
        "--test-file",
        default="JIRA 2025ыЕД_4Q.csv",
        help="CSV file name (within data-dir) to treat as test data.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("DATA") / "processed",
        help="Directory where the processed Parquet files will be written.",
    )
    parser.add_argument(
        "--suffix",
        default="dataset",
        help="Base suffix for the output files (produces <suffix>_modeling/test).",
    )
    parser.add_argument(
        "--format",
        choices=("parquet", "csv"),
        default="csv",
        help="Output file format.",
    )
    parser.add_argument(
        "--dedupe",
        action="store_true",
        help="Drop duplicate Issue keys, keeping the most recently updated row.",
    )
    return parser.parse_args()


def load_frames(paths: Iterable[Path]) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    for path in paths:
        df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
        df["source_file"] = path.name
        frames.append(df)
    return frames


def dedupe_issue_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    if "Issue key" not in df.columns:
        return df
    sort_cols = ["Issue key"]
    if "Updated" in df.columns:
        sort_cols.append("Updated")
    df = df.sort_values(sort_cols, kind="mergesort")
    return df.drop_duplicates("Issue key", keep="last")


def combine(paths: Iterable[Path], dedupe: bool) -> pd.DataFrame:
    frames = load_frames(paths)
    if not frames:
        raise ValueError("No CSV files found for the requested split.")
    df = pd.concat(frames, ignore_index=True)
    return dedupe_issue_snapshot(df) if dedupe else df


def write_output(df: pd.DataFrame, out_dir: Path, base: str, fmt: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{base}.{fmt}"
    if fmt == "parquet":
        df.to_parquet(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    args = parse_args()
    data_dir: Path = args.data_dir
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    test_path = data_dir / args.test_file
    if not test_path.exists():
        raise FileNotFoundError(f"Test CSV not found: {test_path}")

    all_csvs = sorted(data_dir.glob("*.csv"))
    modeling_paths = [path for path in all_csvs if path != test_path]

    modeling_df = combine(modeling_paths, dedupe=args.dedupe)
    test_df = combine([test_path], dedupe=args.dedupe)

    modeling_path = write_output(
        modeling_df, args.out_dir, f"{args.suffix}_modeling", args.format
    )
    test_path_out = write_output(
        test_df, args.out_dir, f"{args.suffix}_test", args.format
    )

    print(f"Modeling dataset rows: {len(modeling_df):,}")
    print(f"Test dataset rows: {len(test_df):,}")
    print(f"Wrote {modeling_path}")
    print(f"Wrote {test_path_out}")


if __name__ == "__main__":
    main()
