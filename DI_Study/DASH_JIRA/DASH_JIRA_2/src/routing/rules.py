from typing import Optional, List, Dict
from src.ingestion.models import IssueModel
from src.nlp.models import AnalysisResult

class RuleEngine:
    def apply_rules(self, issue: IssueModel, analysis: AnalysisResult) -> Optional[str]:
        """
        Applies hard-coded rules to determine the assignee team.
        Returns the team name if a rule matches, otherwise None.
        """
        
        # Rule 1: EU GDPR issues -> Legal-EU-Team
        # Check custom fields for Region (assuming mapped) or infer from summary
        region = issue.custom_fields.get('Region', '')
        if region == 'EU' and 'GDPR' in issue.summary.upper():
            return "Legal-EU-Team"
            
        # Rule 2: Critical Priority -> On-Call-Manager
        if issue.priority and 'Critical' in issue.priority:
            return "On-Call-Manager"
            
        # Rule 3: Tagging Requests -> Global Tagging Team
        if analysis.category == "Tagging Request":
            return "Global Tagging Team"
            
        return None
