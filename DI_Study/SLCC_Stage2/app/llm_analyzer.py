# -*- coding: utf-8 -*-
"""자유 질의·심층 분석용 LLM 호출 (gpt-4o, .env)."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "gpt-4o"


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


def analyze(query: str, context: str, style: str = "free") -> str:
    """
    질의 + 컨텍스트로 심층 분석 응답 생성.
    style: free | issues | insight | report
    """
    _load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        return "[오류] OPENAI_API_KEY가 없습니다. .env 파일을 확인하세요."

    system = """당신은 소셜 리스닝·마케팅 데이터를 분석하는 **심층 분석 전문가**입니다.
- 주어진 데이터(컨텍스트)만을 근거로 답하되, 수치와 사실을 정확히 인용하세요.
- 추론이 필요할 때는 논리 단계를 밝히고, 핵심 이슈·리스크·기회를 구체적으로 짚어주세요.
- 답변은 한국어로, 정확하고 심층적인 사고가 담긴 형태로 작성하세요.
- 요청이 '기사형'·'리포트형'이면 제목·소제목·단락 구분이 있는 읽기 쉬운 문서 형태로 작성하세요."""

    style_guide = {
        "free": "사용자 질의에 맞춰 자유 형식으로 정확하고 심층적인 분석을 제공하세요.",
        "issues": "핵심 이슈·리스크·주의할 점을 우선순위 있게 정리하고, 각 항목별로 근거(데이터 인용)를 제시하세요.",
        "insight": "데이터에서 읽을 수 있는 인사이트를 3~5개로 요약하고, 각각 의미와 시사점을 설명하세요.",
        "report": "기사/리포트 형식(제목, 리드, 소제목 있는 본문, 요약)으로 심층 분석 보고서를 작성하세요.",
    }
    style_instruction = style_guide.get(style, style_guide["free"])

    user = f"""아래는 2026.1H Galaxy Unpacked 데일리 모니터링의 **실제 데이터 요약**입니다.
이 컨텍스트를 바탕으로 사용자 질의에 답하세요. 데이터에 없는 내용은 추측하지 말고, 있는 수치·사실을 인용하세요.

{style_instruction}

---
[데이터 컨텍스트]
{context}
---

[사용자 질의]
{query}
---

위 질의에 대해 정확하고 심층적인 답변을 작성하세요."""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=4000,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"[LLM 오류] {type(e).__name__}: {e}"
