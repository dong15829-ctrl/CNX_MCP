#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM으로 기획기사형 주간 리포트 본문을 생성합니다.
SLCC_Stage2/.env 의 OPENAI_API_KEY 사용. 무조건 최고 성능 모델(gpt-4o) 연동.
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARSED = ROOT / "data" / "parsed"

# 최고 성능 모델 (고정)
OPENAI_MODEL_BEST = "gpt-4o"


def _load_dotenv():
    """프로젝트 루트의 .env를 읽어 os.environ에 넣음 (이미 있으면 덮어쓰지 않음)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and os.environ.get(key) is None:
                    os.environ[key] = value


def load_data():
    with open(PARSED / "all_days.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_data_summary(data: list) -> str:
    """LLM에 넘길 데이터 요약 텍스트 생성."""
    lines = [
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
    lines.append("## 시계열 트렌드 (일별 Total 버즈 수치, D-29 ~ 해당일)")
    last = data[-1]
    for p in (last.get("trend_total_points") or [])[-10:]:
        lines.append(f"- D{p['d']}: {p['value']:,}건")
    lines.append("")
    lines.append("## 채널/권역 요약 (기간 중 대표 일자)")
    for d in [data[0], data[-1]]:
        ct = d.get("channel_text")
        if ct:
            lines.append(f"[{d.get('date')}] {ct[:400]}...")
    lines.append("")
    lines.append("## 반응을 이끈 드라이버 (기간 내 반복·대표)")
    seen = set()
    for d in data:
        for s in (d.get("driver_summaries") or [])[:3]:
            if s and s not in seen:
                seen.add(s)
                lines.append(f"- {s}")
    lines.append("")
    ev = last.get("event_2026")
    if ev:
        lines.append("## D-20 시점 Event 누적 (2026.1H)")
        lines.append(f"- Total {ev[0]}, Product: Family {ev[1]}, Ultra {ev[2]}, Baseline {ev[3]}, Buds {ev[4]}, AI Total {ev[5]}, Pure {ev[6]}")
    return "\n".join(lines)


def build_prompt(data_summary: str) -> tuple[str, str]:
    system = """당신은 소셜 리스닝·마케팅 인사이트를 다루는 기획기사 전문 작가입니다.
주어진 데이터만을 바탕으로, 추론이나 과장 없이 수치와 사실에 기반한 기획기사형 주간 리포트를 한국어로 작성합니다.
문체: 간결하고 읽기 쉬운 문장, 불필요한 수식어 최소화, 인사이트를 한두 문장으로 요약하는 스타일."""

    user = f"""아래는 2026.1H Galaxy Unpacked 데일리 모니터링의 2월 1일~6일( D-25 ~ D-20 ) 통합 데이터 요약입니다.
이 데이터만 사용해서 **기획기사 형태의 주간 분석 리포트** 본문을 작성해 주세요.

요구사항:
1. **제목**: 한 줄, 핵심 인사이트가 드러나게 (예: 버즈 급증, 턴닝포인트 등).
2. **리드**: 2~4문장. 기간·전체 버즈 변화·전년대비·가장 눈에 띄는 일자/이벤트를 요약.
3. **본문 섹션**: 아래 4개 섹션을 반드시 포함. 각 섹션은 소제목 + 본문 2~5문장.
   - 일별 버즈 요약과 턴닝포인트
   - 채널·드라이버 인사이트 (수원/로컬, 미디어·소비자·커뮤니티, 반응 이끈 콘텐츠/이슈)
   - 제품·라인별 관심 (Family/Ultra/Baseline/Buds, AI)
   - 요약 및 전망 (한 주간 정리 + 이후 모니터링 포인트)

출력 형식: 반드시 아래 구조의 **유효한 JSON만** 출력하세요. 다른 설명·마크다운·코드블록 라벨 없이 순수 JSON만 출력.
- 문자열 안의 줄바꿈은 반드시 백슬래시+n(\\\\n) 두 글자로 표기.
- 마지막 배열/객체 요소 뒤에는 쉼표 금지(JSON 문법).
- 따옴표·백슬래시는 이스케이프(\\\\, \\") 처리.

{{
  "title": "제목 한 줄",
  "lead": "리드 문단. 문장 구분은 \\n으로.",
  "sections": [
    {{ "heading": "소제목", "body": "본문. 줄바꿈은 \\n으로." }},
    {{ "heading": "소제목2", "body": "본문2" }},
    {{ "heading": "소제목3", "body": "본문3" }},
    {{ "heading": "소제목4", "body": "본문4" }}
  ]
}}

데이터 요약:
---
{data_summary}
---
위 데이터를 바탕으로 JSON만 출력하세요."""

    return system, user


def call_llm(system: str, user: str) -> str:
    """OpenAI 호환 API로 채팅 완료 호출. .env 로드 후 무조건 최고 성능 모델 사용."""
    _load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")  # optional, for local/other endpoints
    model = OPENAI_MODEL_BEST  # 무조건 최고 성능

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY가 없습니다. SLCC_Stage2/.env 에 OPENAI_API_KEY=... 를 넣거나 "
            "환경변수로 설정한 뒤 다시 실행하세요."
        )

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai 패키지가 필요합니다. pip install openai")

    client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.5,
        max_tokens=4000,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text


def _repair_json(raw: str) -> str:
    """JSON 파싱 실패 시 흔한 오류 수정."""
    # 마지막 요소 뒤 쉼표 제거 (}, ] 앞의 , 제거)
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)
    # 문자열 값 안의 실제 줄바꿈을 \\n 두 글자로 치환 (JSON 허용)
    in_string = False
    escape = False
    i = 0
    out = []
    while i < len(raw):
        c = raw[i]
        if escape:
            out.append(c)
            escape = False
        elif c == "\\" and in_string:
            out.append(c)
            escape = True
        elif c == '"':
            in_string = not in_string
            out.append(c)
        elif c in "\n\r" and in_string:
            out.append("\\n")
        else:
            out.append(c)
        i += 1
    return "".join(out)


def extract_json(text: str) -> dict:
    """응답 텍스트에서 JSON 블록 추출. 파싱 실패 시 수정 후 재시도."""
    raw = text.strip()
    # ```json ... ``` 또는 ``` ... ``` 제거
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if m:
        raw = m.group(1).strip()
    # 첫 { 부터 마지막 } 까지 추출
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]
    for attempt in range(2):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            if attempt == 0:
                raw = _repair_json(raw)
            else:
                raise e
    return json.loads(raw)


def _normalize_report(structured: dict) -> dict:
    """필수 필드 보정."""
    if "title" not in structured or not isinstance(structured.get("title"), str):
        structured["title"] = "2026.1H 데일리 모니터링 주간 분석"
    if "lead" not in structured or not isinstance(structured.get("lead"), str):
        structured["lead"] = ""
    if "sections" not in structured or not isinstance(structured["sections"], list):
        structured["sections"] = []
    for i, sec in enumerate(structured["sections"]):
        if not isinstance(sec, dict):
            structured["sections"][i] = {"heading": "", "body": ""}
        else:
            sec["heading"] = sec.get("heading") or ""
            sec["body"] = sec.get("body") or ""
    return structured


def generate_report(data: list) -> dict:
    """데이터를 넣어 LLM 기획기사 구조 생성. 파싱 실패 시 수정 요청으로 1회 재시도."""
    summary = build_data_summary(data)
    system, user = build_prompt(summary)
    response_text = call_llm(system, user)
    try:
        structured = extract_json(response_text)
    except (json.JSONDecodeError, TypeError) as e:
        # 1회 재시도: LLM에게 JSON만 고쳐서 출력하라고 요청
        try:
            fix_user = f"""아래 텍스트는 JSON 형식이지만 문법 오류가 있어 파싱이 안 됩니다. 오류를 수정한 뒤 **수정된 JSON만** 출력하세요. 설명 없이 JSON만 출력.

오류: {e}

원문:
---
{response_text[:3500]}
---"""
            fix_text = call_llm(
                "You are a JSON repair assistant. Output only valid JSON, no markdown or explanation.",
                fix_user,
            )
            structured = extract_json(fix_text)
        except Exception:
            raise e
    return _normalize_report(structured)


def main():
    data = load_data()
    if not data:
        print("data/parsed/all_days.json 이 비어 있거나 없습니다.")
        return
    report = generate_report(data)
    out = ROOT / "data" / "parsed" / "llm_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"LLM 리포트 구조 저장: {out}")
    print("제목:", report.get("title", "")[:60])


if __name__ == "__main__":
    main()
