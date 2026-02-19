#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse 2/1~2/6 daily monitoring HTML and extract structured data for report."""

import re
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "parsed"

FILE_PATTERN = re.compile(
    r"2월_([1-6])일자_데일리_모니터링_.*?\.html", re.IGNORECASE
)


def parse_report(html_path: Path) -> dict:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    out = {"file": html_path.name, "date": None, "d_day": None}

    # Title: "2026.1H Daily Monitoring Report - 2026-02-01 (D-25)"
    title_el = soup.find("span", class_="dm-report-title__text")
    if title_el:
        out["title_raw"] = title_el.get_text(strip=True)
        m = re.search(r"(\d{4}-\d{2}-\d{2})\s*\(D-(\d+)\)", title_el.get_text())
        if m:
            out["date"] = m.group(1)
            out["d_day"] = "D-" + m.group(2)

    # Buzz Summary (first analysis-answer)
    first_answer = soup.find("p", class_="analysis-answer")
    if first_answer:
        text = first_answer.get_text(separator=" ", strip=True)
        out["buzz_summary_text"] = text
        # Extract numbers: 전체 약 137K, x2.8, Ultra 약 24K, x1.7
        m_total = re.search(r"전체\s*버즈량은\s*약\s*([\d.]+K?|[\d.]+M)", text)
        m_total_yoy = re.search(r"전년대비\s*(\S+)", text) or re.search(r"\(전년\s*대비\s*(\S+)\)", text)
        m_ultra = re.search(r"Ultra\s*버즈량은\s*약\s*([\d.]+K?|[\d.]+M)", text)
        yoys = re.findall(r"[x×](\d+\.?\d*)", text)
        out["buzz_total"] = m_total.group(1) if m_total else None
        out["buzz_total_yoy"] = ("x" + yoys[0]) if yoys else (m_total_yoy.group(1) if m_total_yoy else None)
        out["buzz_ultra"] = m_ultra.group(1) if m_ultra else None
        out["buzz_ultra_yoy"] = ("x" + yoys[1]) if len(yoys) >= 2 else None

    # Event table: 2026.1H row
    table = soup.find("div", class_="dm-records-table--event")
    if table:
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            for row in rows:
                cells = row.find_all("td", class_="dm-cell-index") + row.find_all("td", class_="dm-cell-number")
                if not cells:
                    continue
                labels = [c.get_text(strip=True) for c in row.find_all("td")]
                if labels and "2026.1H" in labels[0]:
                    out["event_2026"] = labels[1:] if len(labels) > 1 else labels
                    break

    # Trend: data-value for Total series (last point = that day's total buzz volume)
    trend_total = []
    for circle in soup.find_all("circle", attrs={"data-series": "Total"}):
        x = circle.get("data-x")
        v = circle.get("data-value")
        if x is not None and v is not None:
            trend_total.append({"d": int(x), "value": int(v)})
    if trend_total:
        trend_total.sort(key=lambda t: t["d"])
        out["trend_total_points"] = trend_total

    # Channel paragraph (second analysis-answer often has 미디어·소비자·커뮤니티)
    all_answers = soup.find_all("p", class_="analysis-answer")
    for p in all_answers[1:3]:
        t = p.get_text(strip=True)
        if "미디어" in t or "소비자" in t or "커뮤니티" in t or "Channel" in t:
            out["channel_text"] = t
            break
    if "channel_text" not in out:
        out["channel_text"] = None

    # Driver insights: first 5 driver-summary
    drivers = []
    for span in soup.find_all("span", class_="driver-summary"):
        drivers.append(span.get_text(strip=True))
    out["driver_summaries"] = drivers[:8]

    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for f in sorted(DATA_DIR.iterdir()):
        if f.suffix.lower() != ".html":
            continue
        if FILE_PATTERN.search(f.name):
            try:
                data = parse_report(f)
                reports.append(data)
            except Exception as e:
                print(f"Skip {f.name}: {e}")

    # Sort by date
    reports.sort(key=lambda r: (r.get("date") or ""))

    # Save per-day and aggregated
    for r in reports:
        d = (r.get("date") or "unknown").replace("-", "")
        with open(OUT_DIR / f"daily_{d}.json", "w", encoding="utf-8") as fp:
            json.dump(r, fp, ensure_ascii=False, indent=2)

    with open(OUT_DIR / "all_days.json", "w", encoding="utf-8") as fp:
        json.dump(reports, fp, ensure_ascii=False, indent=2)

    print(f"Parsed {len(reports)} reports -> {OUT_DIR}")
    return reports


if __name__ == "__main__":
    main()
