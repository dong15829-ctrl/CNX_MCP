from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.message import EmailMessage
import json
import logging
import os
import smtplib
from typing import Dict, List, Optional, Sequence, Tuple

from langdetect import detect, LangDetectException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .llm_client import llm_client

logger = logging.getLogger(__name__)


def _safe_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return str(value).strip()


class TranslationService:
    """Translation orchestrator supporting OpenAI and googletrans fallback."""

    def __init__(self) -> None:
        self.llm = llm_client
        self.enable_online = os.getenv("ENABLE_ONLINE_TRANSLATION", "0") == "1"
        self.target_language = os.getenv("TRANSLATION_TARGET_LANG", "ko")
        self._client = None
        if self.enable_online:
            try:
                from googletrans import Translator  # type: ignore

                self._client = Translator()
            except Exception as exc:  # pragma: no cover - optional dependency
                logger.warning("Google Translator 초기화 실패: %s", exc)
                self._client = None

    def _detect_language(self, text: str) -> str:
        if not text:
            return "unknown"
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

    def _translate(self, text: str, lang: str) -> str:
        if not text:
            return ""
        if lang == self.target_language or lang == "unknown":
            return text
        if self.llm.available():
            translated = self.llm.translate(text, self.target_language)
            if translated:
                return translated
        if self.enable_online and self._client:
            try:
                result = self._client.translate(text, src=lang, dest=self.target_language)
                return result.text
            except Exception as exc:  # pragma: no cover - optional dependency
                logger.warning("온라인 번역 실패 (%s): %s", lang, exc)
        return f"[{self.target_language} 번역][{lang}] {text}"

    def translate_fields(self, summary: str, description: str) -> Dict[str, Optional[str]]:
        summary_lang = self._detect_language(summary)
        description_lang = self._detect_language(description)
        translated_summary = self._translate(summary, summary_lang)
        translated_desc = self._translate(description, description_lang)
        return {
            "summary_original": summary or None,
            "summary_translated": translated_summary or None,
            "description_original": description or None,
            "description_translated": translated_desc or None,
            "summary_language": summary_lang,
            "description_language": description_lang,
        }


class RuleBasedSummarizer:
    """Fallback rule-based summarizer."""

    def summarize(self, summary_text: str, description_text: str, region: Optional[str], category: Optional[str]) -> Dict[str, Optional[str]]:
        combined = f"{summary_text} {description_text}".strip()
        overview = summary_text[:280] if summary_text else combined[:280]
        requirements = self._extract_section(description_text, ["request", "need", "please", "요청"])
        risks = self._extract_section(description_text, ["risk", "issue", "problem", "위험"])
        sla_hint = self._detect_sla(description_text)
        recommended_org = self._recommend_org(region, category)

        return {
            "overview": overview or "요약 정보가 부족합니다.",
            "requirements": requirements or "요청 사항이 명시되지 않았습니다.",
            "risks": risks or "위험 요소가 명확하지 않습니다.",
            "sla": sla_hint or "표준 SLA(48h) 적용",
            "recommended_org": recommended_org,
            "slots": {
                "category": category,
                "region": region,
                "requires_review": bool(risks),
            },
        }

    def _extract_section(self, text: str, keywords: Sequence[str]) -> Optional[str]:
        lowered = text.lower()
        for keyword in keywords:
            if keyword in lowered:
                start = lowered.index(keyword)
                snippet = text[start:start + 240]
                return snippet.strip()
        return None

    def _detect_sla(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if "urgent" in lowered or "p1" in lowered:
            return "긴급 대응 (24h)"
        if "hold" in lowered:
            return "일시 보류 상태 - SLA 모니터링 필요"
        return None

    def _recommend_org(self, region: Optional[str], category: Optional[str]) -> str:
        if category and "access" in category.lower():
            return "Identity/Ops Control Tower"
        if region:
            if region.upper() in {"EU", "EMEA"}:
                return "EU Program Ops"
            if region.upper() in {"APAC", "SEA"}:
                return "APAC Tagging Ops"
        return "Global Ops Center"


class SummarizationService:
    """LLM summarizer with rule-based fallback."""

    def __init__(self) -> None:
        self.llm = llm_client
        self.fallback = RuleBasedSummarizer()

    def summarize(self, summary_text: str, description_text: str, region: Optional[str], category: Optional[str]) -> Dict[str, Optional[str]]:
        payload = {
            "summary": summary_text,
            "description": description_text,
            "region": region,
            "category": category,
        }
        if self.llm.available():
            structured = self.llm.summarize(payload)
            if isinstance(structured, dict):
                outline = self._build_outline(summary_text, description_text, structured)
                return {
                    "overview": structured.get("overview") or summary_text or "요약 정보가 부족합니다.",
                    "requirements": structured.get("requirements") or "요청 사항이 명시되지 않았습니다.",
                    "risks": structured.get("risks") or "위험 요소가 명확하지 않습니다.",
                    "sla": structured.get("sla") or "표준 SLA(48h) 적용",
                    "recommended_org": structured.get("recommended_org") or "Global Ops Center",
                    "description_summary": outline,
                    "slots": {
                        "category": category,
                        "region": region,
                        "requires_review": bool(structured.get("risks")),
                    },
                }
        fallback = self.fallback.summarize(summary_text, description_text, region, category)
        fallback["description_summary"] = self._build_outline(summary_text, description_text, fallback)
        return fallback

    @staticmethod
    def _build_outline(summary_text: str, description_text: str, structured: Dict[str, any]) -> Dict[str, Optional[str]]:
        slots = structured.get("slots", {}) if isinstance(structured, dict) else {}
        target = slots.get("region") or structured.get("recommended_org")
        work = summary_text[:180] if summary_text else None
        details = description_text[:220] if description_text else None
        misc = structured.get("requirements") or structured.get("risks")
        return {
            "target": target or "대상 정보 없음",
            "work": work or "작업 내용이 명확하지 않습니다.",
            "details": details or "설명 정보가 부족합니다.",
            "etc": misc or "추가 메모 없음",
        }


@dataclass
class CaseRecommendation:
    issue_key: str
    summary: str
    similarity: float
    action: str
    status: str
    team: Optional[str] = None
    details: Optional[str] = None


class CaseMatcher:
    """TF-IDF 기반 간단한 유사 케이스 검색기."""

    def __init__(self, dataframe) -> None:
        texts = (
            dataframe["summary"].fillna("")
            + " "
            + dataframe["description"].fillna("")
        ).tolist()
        self.issue_keys = dataframe["issue_key"].tolist()
        self.issue_lookup = {key: idx for idx, key in enumerate(self.issue_keys)}
        self.vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(texts) if texts else None
        self._summaries = dataframe["summary"].fillna("").tolist()
        self._descriptions = dataframe["description"].fillna("").tolist()
        self._status = dataframe["status"].fillna("").tolist()
        self._regions = dataframe["region"].fillna("Global").tolist()

    def recommend(self, issue_key: str, text: str, top_k: int = 3) -> List[CaseRecommendation]:
        if self.matrix is None or not text.strip():
            return []
        query_vec = self.vectorizer.transform([text])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        current_idx = self.issue_lookup.get(issue_key)
        if current_idx is not None:
            scores[current_idx] = 0.0
        top_indices = scores.argsort()[::-1][: top_k * 2]
        results: List[CaseRecommendation] = []
        for idx in top_indices:
            if len(results) >= top_k:
                break
            score = float(scores[idx])
            if score <= 0.01:
                continue
            rec = CaseRecommendation(
                issue_key=self.issue_keys[idx],
                summary=self._summaries[idx][:160],
                similarity=round(score, 3),
                action="과거 해결 방법 참고",
                status=self._status[idx],
                team=self._regions[idx],
                details=self._descriptions[idx][:320] or None,
            )
            results.append(rec)
        return results


@dataclass
class AssignmentCandidate:
    name: str
    email: str
    reason: str
    confidence: float
    workload: Optional[str] = None


class AssignmentService:
    REGION_OWNERS = {
        "NA": ("NA Ops Lead", "na.ops@samsung.com"),
        "EU": ("EU Ops Lead", "eu.ops@samsung.com"),
        "APAC": ("APAC Ops Lead", "apac.ops@samsung.com"),
        "MENA": ("MENA Ops Lead", "mena.ops@samsung.com"),
        "LATAM": ("LATAM Ops Lead", "latam.ops@samsung.com"),
    }

    CATEGORY_SPECIALISTS = {
        "tagging": ("Tagging SME", "tagging.sme@samsung.com"),
        "access": ("Access Control Desk", "access.ops@samsung.com"),
        "bug": ("Engineering Escalation", "eng.escalation@samsung.com"),
    }

    def assign(self, record: Dict[str, any], summary: Dict[str, any]) -> Dict[str, any]:
        region = (record.get("region") or "").upper()
        category = (record.get("category") or "").lower()

        primary = self._build_primary(region, category)
        backups = self._build_backups(region)
        return {
            "primary": primary,
            "backups": backups,
            "reason": f"{summary.get('recommended_org')} 요청 기반 자동 추천",
        }

    def _build_primary(self, region: str, category: str) -> AssignmentCandidate:
        if category:
            for keyword, (name, email) in self.CATEGORY_SPECIALISTS.items():
                if keyword in category:
                    return AssignmentCandidate(
                        name=name,
                        email=email,
                        reason=f"카테고리 매칭 ({keyword})",
                        confidence=0.9,
                        workload="정상",
                    )
        if region in self.REGION_OWNERS:
            name, email = self.REGION_OWNERS[region]
            return AssignmentCandidate(
                name=name,
                email=email,
                reason=f"{region} 지역 담당자",
                confidence=0.8,
                workload="정상",
            )
        return AssignmentCandidate(
            name="Global Ops Queue",
            email="global.ops@samsung.com",
            reason="기본 담당 큐",
            confidence=0.5,
            workload="높음",
        )

    def _build_backups(self, region: str) -> List[AssignmentCandidate]:
        backups: List[AssignmentCandidate] = []
        for reg, (name, email) in self.REGION_OWNERS.items():
            if reg == region:
                continue
            backups.append(
                AssignmentCandidate(
                    name=name,
                    email=email,
                    reason=f"백업 지역 ({reg})",
                    confidence=0.6,
                    workload="정상",
                )
            )
        return backups[:2]


@dataclass
class NotificationRecord:
    channel: str
    recipient: str
    subject: str
    status: str
    timestamp: str
    detail: Optional[str] = None


class EmailClient:
    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.sender = os.getenv("SMTP_SENDER", self.username or "noreply@example.com")
        self.use_tls = os.getenv("SMTP_USE_TLS", "1") == "1"

    def available(self) -> bool:
        return bool(self.host and self.sender)

    def send(self, recipient: str, subject: str, body: str) -> bool:
        if not self.available():
            return False
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = recipient
        message.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message)
            return True
        except Exception as exc:  # pragma: no cover - external dependency
            logger.error("메일 전송 실패: %s", exc)
            return False


class NotificationService:
    def __init__(self) -> None:
        self.email_client = EmailClient()

    def send_assignment_mail(self, issue_key: str, assignment: Dict[str, any], summary: Dict[str, any]) -> List[NotificationRecord]:
        timestamp = datetime.utcnow().isoformat()
        primary = assignment.get("primary")
        if not isinstance(primary, AssignmentCandidate):
            return []
        subject = f"[Jira][{issue_key}] 자동 요약 & 담당자 추천"
        body = self._build_body(summary)
        status = "queued"
        if self.email_client.available():
            sent = self.email_client.send(f"{primary.name} <{primary.email}>", subject, body)
            status = "sent" if sent else "failed"
        else:
            status = "queued"
        record = NotificationRecord(
            channel="email",
            recipient=f"{primary.name} <{primary.email}>",
            subject=subject,
            status=status,
            timestamp=timestamp,
            detail=body[:240],
        )
        return [record]

    @staticmethod
    def _build_body(summary: Dict[str, any]) -> str:
        lines = [
            f"요약: {summary.get('overview')}",
            f"요청 사항: {summary.get('requirements')}",
            f"위험 요소: {summary.get('risks')}",
            f"SLA: {summary.get('sla')}",
            f"추천 조직: {summary.get('recommended_org')}",
        ]
        return "\n".join(filter(None, lines))


@dataclass
class ActionLog:
    stage: str
    status: str
    detail: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ActionLogger:
    def __init__(self) -> None:
        self._logs: Dict[str, List[ActionLog]] = {}

    def log(self, issue_key: str, stage: str, status: str, detail: str) -> None:
        self._logs.setdefault(issue_key, []).append(
            ActionLog(stage=stage, status=status, detail=detail)
        )

    def get(self, issue_key: str) -> List[Dict[str, str]]:
        return [log.__dict__ for log in self._logs.get(issue_key, [])]


class SLAService:
    def evaluate(self, record: Dict[str, any]) -> Dict[str, any]:
        created_at = record.get("created_at")
        status = record.get("status")
        priority = (record.get("priority") or "").lower()
        now = datetime.utcnow()
        if isinstance(created_at, datetime):
            created_ts = created_at
        else:
            created_ts = datetime.utcnow()
        elapsed = now - created_ts
        if "high" in priority or "p1" in priority:
            target = timedelta(hours=24)
        else:
            target = timedelta(hours=72)
        deadline = created_ts + target
        status_flag = "resolved" if record.get("is_closed") else ("at_risk" if now > deadline else "on_track")
        return {
            "status": status_flag,
            "deadline": deadline.isoformat(),
            "elapsed_hours": round(elapsed.total_seconds() / 3600, 1),
            "target_hours": target.total_seconds() / 3600,
            "current_status": status,
        }


class AnalysisPipeline:
    """End-to-end lightweight pipeline that covers PLAN 항목 (2~6번)."""

    def __init__(self, repository) -> None:
        self.repository = repository
        self.translation_service = TranslationService()
        self.summarizer = SummarizationService()
        self.case_matcher = CaseMatcher(repository.dataframe)
        self.assignment_service = AssignmentService()
        self.notification_service = NotificationService()
        self.logger = ActionLogger()
        self.sla_service = SLAService()
        self.cache: Dict[str, Dict[str, any]] = {}

    def _ensure_cached(self, issue_key: str) -> None:
        if issue_key in self.cache:
            if self._should_refresh_cache(issue_key):
                self._invalidate_cache(issue_key)
            return
        row = self.repository._get_issue_row(issue_key)
        summary_text = _safe_text(row.get("summary"))
        description_text = _safe_text(row.get("description"))
        combined_text = f"{summary_text}\n{description_text}".strip()

        translation = self.translation_service.translate_fields(summary_text, description_text)
        self.logger.log(issue_key, "translation", "success", f"언어 감지: {translation['summary_language']}/{translation['description_language']}")

        structured_summary = self.summarizer.summarize(summary_text, description_text, row.get("region"), row.get("category"))
        self.logger.log(issue_key, "summarization", "success", structured_summary["overview"][:80])

        case_recommendations = [
            rec.__dict__ for rec in self.case_matcher.recommend(issue_key, combined_text, top_k=3)
        ]
        case_recommendations = self._translate_case_recommendations(case_recommendations)
        self.logger.log(issue_key, "case_matching", "success", f"{len(case_recommendations)}건 추천")

        record_dict = row.to_dict()
        assignment = self.assignment_service.assign(record_dict, structured_summary)
        primary = assignment.get("primary")
        primary_reason = primary.reason if isinstance(primary, AssignmentCandidate) else "담당자 미지정"
        self.logger.log(issue_key, "assignment", "success", primary_reason)

        notifications = self.notification_service.send_assignment_mail(issue_key, assignment, structured_summary)
        for notif in notifications:
            self.logger.log(issue_key, "notification", notif.status, notif.subject)

        sla_state = self.sla_service.evaluate(record_dict)
        self.logger.log(issue_key, "sla", sla_state["status"], f"마감 {sla_state['deadline']}")

        self.cache[issue_key] = {
            "translation": translation,
            "summary": structured_summary,
            "case_recommendations": case_recommendations,
            "assignment": self._serialize_assignment(assignment),
            "notifications": [notif.__dict__ for notif in notifications],
            "logs": self.logger.get(issue_key),
            "sla": sla_state,
        }

    def _should_refresh_cache(self, issue_key: str) -> bool:
        if not self.translation_service.llm.available():
            return False
        cached = self.cache.get(issue_key)
        if not cached:
            return False
        translation = cached.get("translation") or {}
        target = (self.translation_service.target_language or "").lower()

        def needs_refresh(field: str) -> bool:
            original = (translation.get(f"{field}_original") or "").strip()
            translated = (translation.get(f"{field}_translated") or "").strip()
            language = (translation.get(f"{field}_language") or "").lower()
            if not original:
                return False
            if not translated:
                return True
            if translated == original and language != target:
                return True
            return False

        return needs_refresh("summary") or needs_refresh("description")

    def _invalidate_cache(self, issue_key: str) -> None:
        self.cache.pop(issue_key, None)
        self.logger._logs.pop(issue_key, None)

    def _translate_case_recommendations(self, cases: List[Dict[str, any]]) -> List[Dict[str, any]]:
        translated: List[Dict[str, any]] = []
        for item in cases:
            summary = item.get("summary") or ""
            details = item.get("details") or ""
            lang_summary = self.translation_service._detect_language(summary)
            lang_details = self.translation_service._detect_language(details)
            item["summary_translated"] = self.translation_service._translate(summary, lang_summary)
            if details:
                item["details_translated"] = self.translation_service._translate(details, lang_details)
            translated.append(item)
        return translated

    def _serialize_assignment(self, assignment: Dict[str, any]) -> Dict[str, any]:
        def serialize_candidate(candidate: Optional[AssignmentCandidate]) -> Optional[Dict[str, any]]:
            if not isinstance(candidate, AssignmentCandidate):
                return None
            return candidate.__dict__

        return {
            "primary": serialize_candidate(assignment.get("primary")),
            "backups": [serialize_candidate(cand) for cand in assignment.get("backups", []) if isinstance(cand, AssignmentCandidate)],
            "reason": assignment.get("reason"),
        }

    def get_issue_analysis(self, issue_key: str, refresh: bool = False) -> Dict[str, any]:
        if refresh:
            self._invalidate_cache(issue_key)
        self._ensure_cached(issue_key)
        return self.cache[issue_key]
