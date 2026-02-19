from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_advanced_taxonomy():
    payload = {
        "summary": "[LC Request] [ES] - [Webads] - [NEW TAGS]",
        "description": "Please add new tags for the Spanish site Webads component."
    }
    
    print("Sending request...")
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    print("\n--- Advanced Taxonomy Result ---")
    print(f"Summary: {data['summary']}")
    print(f"Country: {data.get('country')}")
    print(f"Site: {data.get('related_site')}")
    print(f"Translated Desc: {data.get('translated_description')}")
    
    # Check if fields are present (even if None due to mock/fallback)
    assert "country" in data
    assert "related_site" in data
    assert "translated_description" in data
    print("\nTest Passed!")

if __name__ == "__main__":
    test_advanced_taxonomy()
