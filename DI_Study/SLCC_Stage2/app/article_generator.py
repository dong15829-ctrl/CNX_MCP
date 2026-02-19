# -*- coding: utf-8 -*-
"""기획 기사 생성 (제목·리드·섹션 구조, gpt-4o)."""

import json
import os
import re
from pathlib import Path

from .context_loader import load_parsed_data, build_context_text

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv():
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

# JSON 추출·수정 (llm_report_writer와 동일 로직)
def _repair_json(raw: str) -> str:
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)
    in_string = False
    escape = False
    out = []
    for i, c in enumerate(raw):
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
    return "".join(out)


def _extract_json(text: str) -> dict:
    raw = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if m:
        raw = m.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]
    for _ in range(2):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raw = _repair_json(raw)
    return json.loads(raw)


def generate_planning_article() -> dict:
    """데이터 기반 기획 기사 JSON 생성. 제미나이 스타일: 제목·서브헤드·리드·[Trend/Feature/Real Voice/Strategy/Insight]·마무리·출처."""
    data = load_parsed_data()
    context = build_context_text(data)
    if not data:
        return {
            "title": "분석 데이터 없음",
            "subheads": [],
            "lead": "data/parsed/all_days.json을 먼저 생성해 주세요.",
            "sections": [],
        }

    system = """당신은 마케팅 인텔리전스·소셜 리스닝 기획기사를 쓰는 **시사·트렌드 기사 작가**입니다.
- 톤: 숫자로 말하고, '충격' '폭발' 'J커브' '신드롬' 같은 강한 한 단어로 요약하며, 독자가 멈칫하게 만드는 헤드라인과 리드를 씁니다.
- 구조: [Trend] [Feature] [Real Voice] [Strategy] [Insight]처럼 섹션에 꼬리표를 달고, 본문에는 구체적 수치·비교표·인용문(소비자 목소리)을 넣습니다.
- 데이터만 근거로 쓰고, 없는 수치는 만들지 마세요. 드라이버·채널 요약을 'Real Voice'처럼 인용문 형태로 재구성해도 됩니다."""

    user = f"""아래는 2026.1H Galaxy Unpacked(26.1H Miracle UNPK) 데일리 모니터링 **실제 데이터 요약**입니다.
이 데이터만 사용해서 **제미나이/마케팅 인텔리전스팀 수준의 기획기사**를 작성하세요.

[필수 구조와 톤]
1. **title**: 한 줄. 임팩트 있는 훅 포함 (예: "아이폰 유저도 멈칫했다"… 갤럭시 'OO'가 던진 N만 버즈의 충격).
2. **subheads**: 서브헤드 3개. 각 한 줄, 불릿 형식. (예: "1월의 정적 깬 2월의 폭발… 단 6일 만에 2.8배 성장")
3. **attribution**: "(2026.02.07 = 마케팅 인텔리전스팀)" 형태 한 줄.
4. **lead**: 2~4문장. "지난 일주일, ~가 ~로 급변했다" 식으로 시작하고, **388K·전년대비 3.7배** 같은 수치를 반드시 넣은 뒤, "무엇이 대중을 이토록 움직였을까?" 같은 전환문으로 끝내기.
5. **sections**: 아래 6개 섹션을 **순서대로** 작성. 각 heading은 [Trend] [Weekly Contrast] [Feature] [Real Voice] [Strategy] [Insight] 형식의 꼬리표를 붙이고, body에는 수치·비교·인용(가능하면 "~" 형태)을 포함.
   - [Trend]: 일별 버즈 추이, J커브/분수령 일자, "초기/확산/폭발" 구간과 수치. 마지막에 "> Insight: ..." 한 줄.
   - [Weekly Contrast]: 지난주 vs 이번주 비교. 표처럼 항목(핵심 동인, 대화 주제, 경쟁사 반응, 주도 채널)과 변화의 핵심(Key Shift)을 문단으로 서술.
   - [Feature]: 이번 상승세의 일등 공신 기능(예: Privacy Display). 전체 비중·관심도·사용 맥락(예: SNS/금융/업무)을 수치로.
   - [Real Voice]: 소비자/커뮤니티 반응. 드라이버 요약을 인용문 형태로 2~3개 ("~" 로 감싸기). 트위터/커뮤니티/경쟁사 유저 반응처럼 구체적 맥락을 붙여도 됨.
   - [Strategy]: 로컬·채널 전략. 수원(공식)·로컬, 영국/한국 등 지역·채널별 버즈와 캠페인(#ExploreGalaxy, ENHYPEN 등)을 수치와 함께.
   - [Insight]: 남은 과제·리스크(감성 급락, 우려 등). "전문가들은 ~라고 지적했다" 식 마무리.
6. **closing**: 마지막 단락 1~2문장. "이제 주사위는 던져졌다" 식으로 언팩·판매량 기대감으로 끝내기.
7. **data_source**: [Data Source] 제목 아래 Period, Source, Metrics 세 줄.

출력: **유효한 JSON만** 출력. 문자열 안 줄바꿈은 \\n, 마지막 요소 뒤 쉼표 금지.

{{
  "title": "제목 한 줄 (훅 포함)",
  "subheads": ["서브1", "서브2", "서브3"],
  "attribution": "(2026.02.07 = 마케팅 인텔리전스팀)",
  "lead": "리드 문단. \\n으로 줄바꿈.",
  "sections": [
    {{ "heading": "[Trend] ...", "body": "본문. 수치·> Insight: 포함. \\n 줄바꿈." }},
    {{ "heading": "[Weekly Contrast] ...", "body": "..." }},
    {{ "heading": "[Feature] ...", "body": "..." }},
    {{ "heading": "[Real Voice] ...", "body": "인용문 포함..." }},
    {{ "heading": "[Strategy] ...", "body": "..." }},
    {{ "heading": "[Insight] ...", "body": "..." }}
  ],
  "closing": "마무리 1~2문장.",
  "data_source": "Period: ...\\nSource: ...\\nMetrics: ..."
}}

데이터 요약:
---
{context}
---
위 데이터만 사용해 JSON만 출력하세요."""

    _load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        return {"title": "오류", "lead": "OPENAI_API_KEY가 없습니다.", "sections": []}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.5,
            max_tokens=8000,
        )
        text = (resp.choices[0].message.content or "").strip()
        out = _extract_json(text)
    except Exception as e:
        return {"title": "오류", "lead": str(e), "sections": []}

    out.setdefault("title", "기획 기사")
    out.setdefault("subheads", [])
    out.setdefault("attribution", "")
    out.setdefault("lead", "")
    out.setdefault("sections", [])
    out.setdefault("closing", "")
    out.setdefault("data_source", "")
    if not isinstance(out["sections"], list):
        out["sections"] = []
    for s in out["sections"]:
        if isinstance(s, dict):
            s["heading"] = s.get("heading") or ""
            s["body"] = (s.get("body") or "").replace("\\n", "\n")
    if isinstance(out.get("lead"), str):
        out["lead"] = out["lead"].replace("\\n", "\n")
    if isinstance(out.get("closing"), str):
        out["closing"] = out["closing"].replace("\\n", "\n")
    if isinstance(out.get("data_source"), str):
        out["data_source"] = out["data_source"].replace("\\n", "\n")
    return out
