# -*- coding: utf-8 -*-
"""데일리 모니터링 데이터 로드 및 LLM용 컨텍스트 생성."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARSED = ROOT / "data" / "parsed"


def load_parsed_data():
    """data/parsed/all_days.json 로드."""
    path = PARSED / "all_days.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_context_text(data: list) -> str:
    """자유 질의·심층 분석용 상세 컨텍스트 문자열."""
    if not data:
        return "(분석 기간 데이터가 없습니다. data/parsed/all_days.json 을 먼저 생성하세요.)"
    lines = [
        "# 2026.1H Galaxy Unpacked 데일리 모니터링 데이터 요약",
        "",
        "## 분석 기간",
        f"- 일자: {data[0].get('date')} ({data[0].get('d_day')}) ~ {data[-1].get('date')} ({data[-1].get('d_day')})",
        "",
        "## 일별 버즈 (전체 / Ultra, 전년대비)",
    ]
    for d in data:
        lines.append(
            f"- {d.get('date')} {d.get('d_day')}: 전체 {d.get('buzz_total')} (YoY {d.get('buzz_total_yoy')}), "
            f"Ultra {d.get('buzz_ultra')} (YoY {d.get('buzz_ultra_yoy')})"
        )
    lines.append("")
    lines.append("## 시계열 트렌드 (일별 Total 버즈)")
    last = data[-1]
    for p in (last.get("trend_total_points") or [])[-10:]:
        lines.append(f"- D{p['d']}: {p['value']:,}건")
    lines.append("")
    lines.append("## 채널/권역 요약")
    for d in [data[0], data[-1]]:
        ct = d.get("channel_text")
        if ct:
            lines.append(f"[{d.get('date')}] {ct[:500]}")
    lines.append("")
    lines.append("## 반응 드라이버 (기간 내)")
    seen = set()
    for d in data:
        for s in (d.get("driver_summaries") or [])[:4]:
            if s and s not in seen:
                seen.add(s)
                lines.append(f"- {s}")
    ev = last.get("event_2026")
    if ev:
        lines.append("")
        lines.append("## D-20 시점 Event 누적")
        lines.append(f"Total {ev[0]}, Family {ev[1]}, Ultra {ev[2]}, Baseline {ev[3]}, Buds {ev[4]}, AI Total {ev[5]}, Pure {ev[6]}")
    return "\n".join(lines)
