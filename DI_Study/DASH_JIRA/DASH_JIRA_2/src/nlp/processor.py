import re
from src.nlp.llm_client import LLMClient
from src.nlp.models import AnalysisResult

class NLPProcessor:
    def __init__(self):
        self.llm_client = LLMClient()
        
    def mask_pii(self, text: str) -> str:
        if not text:
            return ""
            
        # Email masking
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '<EMAIL>', text)
        
        # Phone masking (simple pattern)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '<PHONE>', text)
        
        # IP Address masking (IPv4)
        text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', text)
        
        return text

    def process_issue(self, summary: str, description: str) -> AnalysisResult:
        # 1. Mask PII
        safe_summary = self.mask_pii(summary)
        safe_description = self.mask_pii(description)
        
        # 2. Analyze with LLM
        result = self.llm_client.analyze_issue(safe_summary, safe_description)
        
        return result
