from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("Health Check Passed!")

def test_analyze():
    payload = {
        "summary": "System crash",
        "description": "Server crashed due to memory leak."
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"\nAnalyze Result: {data['category']} - {data['root_cause_hypothesis']}")
    assert "summary" in data

def test_route():
    payload = {
        "summary": "GDPR compliance issue",
        "description": "Need to delete user data.",
        "custom_fields": {"Region": "EU"}
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"\nRoute Result: {data['recommended_team']} ({data['reason']})")
    assert data['recommended_team'] == "Legal-EU-Team"

def test_search():
    payload = {
        "query": "Login failure",
        "limit": 3
    }
    response = client.post("/search", json=payload)
    assert response.status_code == 200
    results = response.json()
    print(f"\nSearch Results: {len(results)} found")
    assert len(results) > 0

if __name__ == "__main__":
    test_health()
    test_analyze()
    test_route()
    test_search()
