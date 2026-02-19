from src.ingestion.models import IssueModel
from src.nlp.models import AnalysisResult
from src.routing.rules import RuleEngine
from src.search.vector_store import VectorStore

def test_rule_engine():
    engine = RuleEngine()
    
    # Case 1: EU GDPR -> Legal-EU-Team
    issue1 = IssueModel(
        issue_key="TEST-1", 
        summary="GDPR compliance issue", 
        custom_fields={"Region": "EU"}
    )
    analysis1 = AnalysisResult(
        summary="GDPR issue", category="Legal", urgency="High", 
        root_cause_hypothesis="N/A", required_action="N/A", 
        suggested_assignee_team="N/A", confidence_score=0.0
    )
    
    team1 = engine.apply_rules(issue1, analysis1)
    print(f"Case 1 (EU GDPR): {team1}")
    assert team1 == "Legal-EU-Team"

    # Case 2: Critical Priority -> On-Call-Manager
    issue2 = IssueModel(
        issue_key="TEST-2", 
        summary="System Down", 
        priority="Critical"
    )
    team2 = engine.apply_rules(issue2, analysis1)
    print(f"Case 2 (Critical): {team2}")
    assert team2 == "On-Call-Manager"
    
    print("Rule Engine Test Passed!")

def test_vector_store():
    store = VectorStore()
    results = store.search_similar_cases("Login failure")
    
    print(f"\nVector Search Results: {len(results)}")
    for res in results:
        print(f"- {res['issue_key']}: {res['summary']} ({res['status']})")
        
    assert len(results) <= 3
    print("Vector Store Test Passed!")

if __name__ == "__main__":
    test_rule_engine()
    test_vector_store()
