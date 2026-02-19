from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class IssueRequest(BaseModel):
    summary: str
    description: str
    custom_fields: Optional[Dict[str, Any]] = {}

class AnalysisResponse(BaseModel):
    summary: str
    category: str
    urgency: str
    root_cause_hypothesis: str
    required_action: str
    suggested_assignee_team: str
    confidence_score: float
    country: Optional[str] = None
    related_site: Optional[str] = None
    translated_description: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

class SearchResult(BaseModel):
    issue_key: str
    summary: str
    description: str
    status: str
    similarity: float

class RoutingResponse(BaseModel):
    recommended_team: str
    reason: str
