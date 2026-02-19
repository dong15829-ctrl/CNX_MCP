from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class IssueModel(BaseModel):
    issue_key: str
    issue_id: Optional[int] = None
    summary: str
    description: Optional[str] = None
    status: Optional[str] = None
    issue_type: Optional[str] = None
    priority: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assignee_id: Optional[str] = None
    reporter_id: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    analysis_result: Dict[str, Any] = Field(default_factory=dict)

class CommentModel(BaseModel):
    issue_key: str
    author_id: Optional[str] = None
    body: str
    created_at: Optional[datetime] = None
    is_internal: bool = False
