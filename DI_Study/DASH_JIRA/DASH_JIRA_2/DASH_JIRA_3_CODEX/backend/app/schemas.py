from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class JiraNamedEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    key: Optional[str] = None
    name: Optional[str] = None


class JiraUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: Optional[str] = None
    displayName: Optional[str] = None
    emailAddress: Optional[str] = None


class JiraIssueFields(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: Optional[str] = None
    description: Optional[str] = None
    issuetype: Optional[JiraNamedEntity] = None
    status: Optional[JiraNamedEntity] = None
    priority: Optional[JiraNamedEntity] = None
    assignee: Optional[JiraUser] = None
    reporter: Optional[JiraUser] = None
    creator: Optional[JiraUser] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    resolutiondate: Optional[str] = None
    customfield_10013: Optional[str] = None  # Region
    customfield_10014: Optional[str] = None  # Country
    customfield_category: Optional[str] = None
    customfield_root_cause: Optional[str] = None


class JiraIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    key: str
    fields: JiraIssueFields


class JiraWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    webhookEvent: Optional[str] = None
    issue_event_type_name: Optional[str] = None
    issue: JiraIssue


class IngestionResponse(BaseModel):
    issue_key: str
    ingested: bool = True
