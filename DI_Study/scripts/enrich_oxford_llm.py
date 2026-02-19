"""
Oxford 3000(or fallback current list) -> LLM 보강 스크립트.

입력:
    - words_v2.json (혹은 지정 파일)에서 word/hint/level/pos 추출
    - .env 의 OPENAI_API_KEY 사용
출력:
    - src/data/words_v3.json (LLM 보강 결과)

설계:
    - 20개 단위로 배치하여 chat.completions로 JSON 배열 요청
    - 실패 시 재시도(최대 3회), 파싱 실패 시 단건 모드로 재시도
    - 결과는 항상 id 순으로 덮어쓴다
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "src" / "data" / "words_v2.json"
OUTPUT_PATH = ROOT / "src" / "data" / "words_v3.json"
ENV_PATH = ROOT / ".env"

# level -> 임시 CEFR 매핑(근사치)
LEVEL_TO_CEFR = {
    "beginner": "A1",
    "intermediate": "B1",
    "advanced": "C1",
}


@dataclass
class Item:
    id: int
    word: str
    pos: str
    cefr: str
    hint: str


def load_items(path: Path) -> List[Item]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items: List[Item] = []
    for entry in data:
        word = entry.get("word") or ""
        if not word:
            continue
        hint = entry.get("meaning_ko") or entry.get("meaning") or ""
        pos = (entry.get("pos") or "unknown").lower()
        cefr = LEVEL_TO_CEFR.get(entry.get("level"), "B1")
        items.append(
            Item(
                id=entry.get("id") or len(items) + 1,
                word=word,
                pos=pos,
                cefr=cefr,
                hint=hint,
            )
        )
    # 중복 제거(단어 기준)
    seen = set()
    unique: List[Item] = []
    for item in items:
        key = item.word.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def build_prompt(batch: Sequence[Item]) -> str:
    rows = [
        f"{it.word} | {it.hint} | {it.pos} | {it.cefr}"
        for it in batch
    ]
    lines = "\n".join(rows)
    return f"""
You are an English->Korean lexicographer.
For EACH line, return a JSON object with field "items":[...], each item has:
word, pos(one of n/v/adj/adv/other), cefr(A1-C2),
meaning_ko(main), meanings_ko(2-4 strings), example_en(<=18 words),
example_ko, difficulty_score(0-1), tags(array of strings from [everyday, academic, business, slang]),
pronunciation_ipa (IPA like /ˈæpəl/; keep concise, no brackets duplication)
Keep definitions concise/common. Use given hint only as a clue, not necessarily final.
Input lines:
{lines}
Return ONLY JSON with "items":[...].
"""


JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "word": {"type": "string"},
                    "pos": {"type": "string"},
                    "cefr": {"type": "string"},
                    "meaning_ko": {"type": "string"},
                    "meanings_ko": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "pronunciation_ipa": {"type": "string"},
                    "example_en": {"type": "string"},
                    "example_ko": {"type": "string"},
                    "difficulty_score": {"type": "number"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "additionalProperties": False,
                "required": [
                    "word",
                    "pos",
                    "cefr",
                    "meaning_ko",
                    "meanings_ko",
                    "pronunciation_ipa",
                    "example_en",
                    "example_ko",
                    "difficulty_score",
                    "tags",
                ],
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


def call_batch(client: OpenAI, batch: Sequence[Item]) -> List[Dict]:
    prompt = build_prompt(batch)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "lexicon_items",
                "schema": JSON_SCHEMA,
                "strict": True,
            },
        },
        temperature=0.3,
        max_tokens=1500,
    )
    content = resp.choices[0].message.content or "{}"
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        dump_path = ROOT / "tmp_llm_response.txt"
        dump_path.write_text(content, encoding="utf-8")
        raise
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("Unexpected response shape")
    return items


def call_single(client: OpenAI, item: Item) -> Dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": build_prompt([item]),
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "lexicon_items",
                "schema": JSON_SCHEMA,
                "strict": True,
            },
        },
        temperature=0.3,
        max_tokens=400,
    )
    payload = json.loads(resp.choices[0].message.content)
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not items:
        raise ValueError("Unexpected single response shape")
    return items[0]


def enrich(items: List[Item], existing: Dict[str, Dict]) -> List[Dict]:
    # .env 로드(간단 파서)
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    client = OpenAI()
    results: List[Dict] = list(existing.values())
    done_keys = {k.lower() for k in existing.keys()}
    batch_size = 25
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        batch = [b for b in batch if b.word.lower() not in done_keys]
        if not batch:
            continue
        for attempt in range(3):
            try:
                enriched = call_batch(client, batch)
            except Exception as e:
                if attempt == 2:
                    # 단건 처리로 폴백
                    enriched = []
                    for src in batch:
                        single = call_single(client, src)
                        enriched.append(single)
                else:
                    time.sleep(1.5)
                    continue
            # align by order
            for src, new in zip(batch, enriched):
                new["id"] = src.id
                new["word"] = src.word
                new.setdefault("pos", src.pos)
                new.setdefault("cefr", src.cefr)
                new["source"] = "oxford3000+llm"
            results.extend(enriched[: len(batch)])
            # 체크포인트 저장
            tmp_map = {r["word"].lower(): r for r in results}
            OUTPUT_PATH.write_text(json.dumps(list(tmp_map.values()), ensure_ascii=False, indent=2), encoding="utf-8")
            break
        time.sleep(0.05)  # rate-limit 완화
    return results


def main() -> None:
    src_path = Path(os.environ.get("WORDS_INPUT") or DEFAULT_INPUT)
    items = load_items(src_path)
    print(f"loaded {len(items)} unique words from {src_path}")
    existing_map: Dict[str, Dict] = {}
    if OUTPUT_PATH.exists():
        try:
            existing_data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
            existing_map = {e["word"].lower(): e for e in existing_data if "word" in e}
            # 발음기호가 비어 있으면 재생성 대상
            missing_pron = sum(1 for e in existing_map.values() if not e.get("pronunciation_ipa"))
            if missing_pron == len(existing_map) or os.environ.get("REFRESH_ALL"):
                print("existing data lacks pronunciation_ipa, will re-enrich all")
                existing_map = {}
            else:
                print(f"resume from existing {len(existing_map)} items in {OUTPUT_PATH}")
        except Exception:
            pass
    enriched = enrich(items, existing_map)
    # id 기준 정렬
    enriched.sort(key=lambda x: x.get("id", 0))
    OUTPUT_PATH.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written {len(enriched)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
