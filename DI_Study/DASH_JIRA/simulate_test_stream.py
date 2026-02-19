"""
테스트용 JIRA 이벤트 스트림 시뮬레이터.

`DATA/jira_data_gta/JIRA 2025ыЕД_4Q.csv`를 기본 입력으로 사용하여
각 행을 jira.issue.created 이벤트 형태의 JSON으로 출력하거나,
옵션에 따라 HTTP 엔드포인트로 POST 전송한다.
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd


DEFAULT_FIELDS = [
    ("Issue key", "key"),
    ("Summary", "summary"),
    ("Issue Type", "issueType"),
    ("Status", "status"),
    ("Priority", "priority"),
    ("Assignee", "assignee"),
    ("Reporter", "reporter"),
    ("Created", "created"),
    ("Updated", "updated"),
    ("Resolved", "resolved"),
    ("Description", "description"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate incoming Jira tickets.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("DATA") / "jira_data_gta" / "JIRA 2025ыЕД_4Q.csv",
        help="테스트 이벤트로 사용할 CSV 경로",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.5,
        help="각 이벤트 사이 기본 간격(초)",
    )
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.5,
        help="간격에 추가되는 랜덤 지터 최대값(초)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="내보낼 최대 이벤트 수(기본 50, 0은 전체)",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="CSV 내 시작 행 인덱스",
    )
    parser.add_argument(
        "--post-url",
        type=str,
        help="이벤트를 POST할 엔드포인트(URL). 미지정 시 stdout으로 출력.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="POST 전송 시 타임아웃(초)",
    )
    return parser.parse_args()


def load_rows(path: Path, start: int = 0) -> Iterable[pd.Series]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if start:
        df = df.iloc[start:]
    for _, row in df.iterrows():
        yield row


def serialize_issue(row: pd.Series) -> Dict[str, Any]:
    data = row.to_dict()
    issue: Dict[str, Any] = {}
    for col, alias in DEFAULT_FIELDS:
        if col not in data:
            continue
        value = data[col]
        if pd.isna(value):
            continue
        issue[alias] = value
    return issue


def emit_event(
    issue: Dict[str, Any], row_idx: int, source: str, post_url: str | None, timeout: float
) -> None:
    payload = {
        "event": "jira.issue.created",
        "issue": issue,
        "meta": {
            "source_file": source,
            "row_index": row_idx,
            "simulated": True,
        },
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if post_url:
        request = urllib.request.Request(
            post_url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                resp.read()
        except urllib.error.URLError as exc:
            print(f"[WARN] POST 실패: {exc}")
    else:
        print(body.decode("utf-8"))


def main() -> None:
    args = parse_args()
    rows = load_rows(args.csv, args.start_index)
    count = 0
    for idx, row in enumerate(rows, start=args.start_index):
        if args.limit and count >= args.limit:
            break
        issue = serialize_issue(row)
        emit_event(issue, idx, args.csv.name, args.post_url, args.timeout)
        count += 1
        sleep_time = args.interval + random.uniform(0, max(0.0, args.jitter))
        time.sleep(sleep_time)
    print(f"총 {count}건 이벤트 전송 완료.")


if __name__ == "__main__":
    main()
