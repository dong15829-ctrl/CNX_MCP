"""
기존 src/data/words.json(legacy) → 확장 스키마 버전(src/data/words_v2.json)으로 변환.
필드:
    id, word, level, pos, meaning_ko, meanings_ko, pronunciation,
    example_en, example_ko, freq_rank, difficulty_score, tags, source
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).parent
LEGACY_PATH = ROOT / "src" / "data" / "words.json"
OUTPUT_PATH = ROOT / "src" / "data" / "words_v2.json"

# 레벨별 난이도 점수(0~1)
LEVEL_SCORE = {
    "beginner": 0.2,
    "intermediate": 0.5,
    "advanced": 0.8,
}


def load_legacy() -> List[Dict[str, Any]]:
    with LEGACY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def normalize_entry(entry: Dict[str, Any], index: int) -> Dict[str, Any]:
    level = entry.get("level") or "beginner"
    meaning = entry.get("meaning") or ""
    meanings = entry.get("meanings") or ([meaning] if meaning else [])

    return {
        "id": entry.get("id") or index + 1,
        "word": entry.get("word") or "",
        "level": level,
        "pos": entry.get("pos") or "unknown",
        "meaning_ko": meaning,
        "meanings_ko": meanings,
        "pronunciation": entry.get("pronunciation") or "",
        "example_en": entry.get("example") or "",
        "example_ko": entry.get("example_meaning") or "",
        "freq_rank": index + 1,  # 빈도 데이터가 없으므로 인덱스로 대체
        "difficulty_score": LEVEL_SCORE.get(level, 0.5),
        "tags": entry.get("tags") or [],
        "source": entry.get("source") or "legacy",
    }


def dedupe(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for e in entries:
        key = (e["word"].lower(), e["level"])
        if key in seen:
            continue
        seen.add(key)
        result.append(e)
    return result


def main() -> None:
    legacy = load_legacy()
    normalized = [normalize_entry(entry, i) for i, entry in enumerate(legacy)]
    deduped = dedupe(normalized)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    print(f"converted: {len(legacy)} -> {len(deduped)} entries")
    print(f"written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
