from typing import Optional, List
from pydantic import BaseModel, Field

class AnalysisResult(BaseModel):
    summary: str = Field(..., description="One-line summary of the issue")
    category: str = Field(..., description="Issue category (e.g., Tagging Request, Bug Report)")
    urgency: str = Field(..., description="Urgency level: High, Medium, Low")
    root_cause_hypothesis: str = Field(..., description="Brief explanation of potential cause")
    required_action: str = Field(..., description="Suggested action: Code Fix, Configuration Change, etc.")
    suggested_assignee_team: str = Field(..., description="Suggested team to handle this issue")
    confidence_score: float = Field(..., description="Confidence score between 0.0 and 1.0")
    
    # New fields for advanced taxonomy
    country: Optional[str] = Field(None, description="Country code or name extracted from issue (e.g., KR, US, EU)")
    related_site: Optional[str] = Field(None, description="Related site or component (e.g., Shop, Dotcom, Webads)")
    translated_description: Optional[str] = Field(None, description="Korean translation of the original description")
