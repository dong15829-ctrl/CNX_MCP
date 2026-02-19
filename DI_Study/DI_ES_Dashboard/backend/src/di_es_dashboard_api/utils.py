from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_report_filename(filename: str) -> tuple[str, int, int]:
    report_type = "UNKNOWN"
    if "B2B" in filename.upper():
        report_type = "B2B"
    elif "B2C" in filename.upper():
        report_type = "B2C"

    match = re.search(r"(\\d{4})-M(\\d{1,2})", filename)
    if not match:
        raise ValueError(f"Cannot parse year/month from filename: {filename}")

    year = int(match.group(1))
    month = int(match.group(2))
    return report_type, year, month


def clean_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        if v in {"", "-", "#N/A", "예외"}:
            return None
        return v
    return value


def to_int(value: Any) -> int | None:
    value = clean_cell(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int,)):
        return int(value)
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def to_float(value: Any) -> float | None:
    value = clean_cell(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"\\s+", "", text)
    return text


def slugify_metric(label: str) -> str:
    text = label.strip()
    text = re.sub(r"^\\d+\\.?\\s*", "", text)
    text = text.replace("↩", " ").replace("\\n", " ")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "metric"

