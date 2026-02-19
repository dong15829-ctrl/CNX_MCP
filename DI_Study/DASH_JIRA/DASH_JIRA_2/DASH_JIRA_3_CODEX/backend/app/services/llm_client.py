from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around OpenAI Chat Completions."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        self._client = None
        if self.api_key and OpenAI:
            try:
                self._client = OpenAI(api_key=self.api_key)
            except Exception as exc:  # pragma: no cover - initialization failure
                logger.error("OpenAI 초기화 실패: %s", exc)
                self._client = None

    def available(self) -> bool:
        return self._client is not None

    def _chat(self, messages: list[dict[str, str]], **kwargs) -> Optional[str]:
        if not self.available():
            return None
        try:
            response = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 512),
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("OpenAI 요청 실패: %s", exc)
            return None

    def translate(self, text: str, target_language: str) -> Optional[str]:
        if not text or not self.available():
            return None
        prompt = (
            f"Translate the following text into {target_language}. "
            "Return only the translated text without additional commentary.\n\n"
            f"{text}"
        )
        messages = [
            {"role": "system", "content": "You are a professional translator."},
            {"role": "user", "content": prompt},
        ]
        return self._chat(messages, max_tokens=min(800, len(text) * 2))

    def summarize(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.available():
            return None
        instructions = (
            "Summarize the Jira ticket and provide structured Korean output. "
            "Respond ONLY in valid JSON (no 코드블록/markdown) with keys: overview, "
            "requirements, risks, sla, recommended_org. Include concise Korean sentences."
        )
        messages = [
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ]
        raw = self._chat(messages, max_tokens=600)
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            logger.warning("LLM 요약 JSON 파싱 실패: %s", raw)
        return None


llm_client = LLMClient()
