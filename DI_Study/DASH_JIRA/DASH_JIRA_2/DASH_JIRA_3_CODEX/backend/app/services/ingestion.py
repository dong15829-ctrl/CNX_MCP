from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from ..schemas import JiraIssueFields, JiraWebhookPayload
from .data_loader import JiraDataRepository, repository

REGION_FIELD_CANDIDATES = ("customfield_10013", "region", "customfield_region")
COUNTRY_FIELD_CANDIDATES = ("customfield_10014", "country", "customfield_country")
CATEGORY_FIELD_CANDIDATES = ("customfield_category", "category")
ROOT_CAUSE_FIELD_CANDIDATES = ("customfield_root_cause", "root_cause", "cause")


class IngestionService:
    """Maps Jira webhook payloads into repository records."""

    def __init__(self, data_repository: JiraDataRepository) -> None:
        self._repository = data_repository

    def ingest_webhook(self, payload: JiraWebhookPayload) -> Dict[str, Any]:
        record = self._transform_payload(payload)
        self._repository.upsert_issue(record)
        return record

    def _transform_payload(self, payload: JiraWebhookPayload) -> Dict[str, Any]:
        issue = payload.issue
        fields = issue.fields

        record: Dict[str, Any] = {
            "issue_key": issue.key,
            "issue_id": issue.id,
            "summary": fields.summary,
            "description": fields.description,
            "issue_type": self._named_value(fields.issuetype),
            "status": self._named_value(fields.status),
            "priority": self._named_value(fields.priority),
            "assignee": self._user_identifier(fields.assignee),
            "reporter": self._user_identifier(fields.reporter),
            "creator": self._user_identifier(fields.creator),
            "created_at": fields.created,
            "updated_at": fields.updated or fields.created,
            "resolved_at": fields.resolutiondate,
            "region": self._extract_custom_field(fields, REGION_FIELD_CANDIDATES),
            "country": self._extract_custom_field(fields, COUNTRY_FIELD_CANDIDATES),
            "category": self._extract_custom_field(fields, CATEGORY_FIELD_CANDIDATES),
            "root_cause": self._extract_custom_field(
                fields, ROOT_CAUSE_FIELD_CANDIDATES
            ),
            "webhook_event": payload.webhookEvent or payload.issue_event_type_name,
            "source": "webhook",
        }

        return record

    @staticmethod
    def _named_value(entity: Optional[Any]) -> Optional[str]:
        if not entity:
            return None
        return getattr(entity, "name", None) or getattr(entity, "value", None)

    @staticmethod
    def _user_identifier(user: Optional[Any]) -> Optional[str]:
        if not user:
            return None
        return (
            getattr(user, "emailAddress", None)
            or getattr(user, "displayName", None)
            or getattr(user, "accountId", None)
        )

    @staticmethod
    def _extract_custom_field(
        fields: JiraIssueFields, candidates: Iterable[str]
    ) -> Optional[str]:
        for key in candidates:
            value = getattr(fields, key, None)
            if value:
                return value
            if hasattr(fields, "model_extra"):
                extra_value = fields.model_extra.get(key)  # type: ignore[attr-defined]
                if extra_value:
                    return extra_value
        return None


ingestion_service = IngestionService(repository)
