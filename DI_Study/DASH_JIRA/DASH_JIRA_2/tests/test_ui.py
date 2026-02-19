from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_ui_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "JIRA Agent Dashboard" in response.text
    print("UI Serving Test Passed!")

    response = client.get("/static/style.css")
    assert response.status_code == 200
    print("CSS Serving Test Passed!")

    response = client.get("/static/app.js")
    assert response.status_code == 200
    print("JS Serving Test Passed!")

if __name__ == "__main__":
    test_ui_serving()
