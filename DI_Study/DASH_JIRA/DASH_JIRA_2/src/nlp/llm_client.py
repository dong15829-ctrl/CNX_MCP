from openai import OpenAI
import json
from src.config import settings
from src.nlp.models import AnalysisResult

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini" # Cost-effective model

    def analyze_issue(self, summary: str, description: str) -> AnalysisResult:
        system_prompt = """
        You are an expert JIRA Issue Triage Agent.
        Analyze the given Jira issue (Summary and Description) and provide a structured analysis in JSON format.
        
        **IMPORTANT**: 
        1. All text fields (summary, root_cause_hypothesis, required_action) MUST be in **Korean**.
        2. Extract 'country' and 'related_site' if mentioned (e.g., [ES] -> Spain, [Webads] -> Webads).
        3. Provide a full Korean translation of the description in 'translated_description'.
        
        Output Schema:
        {
            "summary": "One line summary of the issue in Korean",
            "category": "One of [Bug Report, Feature Request, Inquiry, Access Request, Tagging Request]",
            "urgency": "One of [Low, Medium, High, Critical]",
            "root_cause_hypothesis": "Brief hypothesis of the root cause in Korean",
            "required_action": "Suggested action to resolve the issue in Korean",
            "suggested_assignee_team": "Recommended team name",
            "confidence_score": float (0.0 to 1.0),
            "country": "Extracted country (e.g., KR, US, EU) or null",
            "related_site": "Extracted site/component or null",
            "translated_description": "Full Korean translation of the description"
        }
        """

        user_prompt = f"""
        Analyze the following Jira issue:
        
        Summary: {summary}
        Description: {description}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            return AnalysisResult(**data)
            
        except Exception as e:
            print(f"LLM Analysis failed: {e}")
            # Return a fallback result
            return AnalysisResult(
                summary=summary[:100],
                category="미분류 (Unclassified)",
                urgency="중 (Medium)",
                root_cause_hypothesis="분석 실패 (LLM 연결 오류)",
                required_action="수동 검토 필요",
                suggested_assignee_team="Triage Team",
                confidence_score=0.0,
                country=None,
                related_site=None,
                translated_description="번역 실패"
            )

    def get_embedding(self, text: str) -> list[float]:
        try:
            text = text.replace("\n", " ")
            response = self.client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return []
