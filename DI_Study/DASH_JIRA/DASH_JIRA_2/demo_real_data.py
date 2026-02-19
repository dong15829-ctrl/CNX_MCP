import psycopg2
from fastapi.testclient import TestClient
from src.api.server import app
from src.config import settings
import json

client = TestClient(app)

def get_real_issue():
    conn = psycopg2.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    cur = conn.cursor()
    # Fetch a random issue that has a description
    cur.execute("SELECT issue_key, summary, description, custom_fields FROM issues WHERE description IS NOT NULL ORDER BY RANDOM() LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    
    if row:
        return {
            "issue_key": row[0],
            "summary": row[1],
            "description": row[2],
            "custom_fields": row[3]
        }
    return None

def run_demo():
    print("=== JIRA Agent Real Data Demo ===\n")
    
    # 1. Fetch Real Data
    issue = get_real_issue()
    if not issue:
        print("No issues found in DB.")
        return

    print(f"🔹 Selected Real Issue: {issue['issue_key']}")
    print(f"   Summary: {issue['summary']}")
    print(f"   Description: {issue['description'][:100]}...") # Truncate for display
    print("-" * 50)

    # 2. Analyze
    print("\n🔹 1. AI Analysis (LLM)")
    payload = {
        "summary": issue['summary'],
        "description": issue['description'],
        "custom_fields": issue['custom_fields']
    }
    try:
        response = client.post("/analyze", json=payload)
        data = response.json()
        print(f"   Category: {data.get('category')}")
        print(f"   Urgency: {data.get('urgency')}")
        print(f"   Root Cause: {data.get('root_cause_hypothesis')}")
        print(f"   Action: {data.get('required_action')}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Route
    print("\n🔹 2. Routing Recommendation")
    try:
        response = client.post("/route", json=payload)
        data = response.json()
        print(f"   Team: {data.get('recommended_team')}")
        print(f"   Reason: {data.get('reason')}")
    except Exception as e:
        print(f"   Error: {e}")

    # 4. Search
    print("\n🔹 3. Similar Case Search (Vector DB)")
    search_payload = {
        "query": issue['summary'],
        "limit": 3
    }
    try:
        response = client.post("/search", json=search_payload)
        results = response.json()
        for res in results:
            print(f"   - [{res['issue_key']}] {res['summary']} (Sim: {res['similarity']:.4f})")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    run_demo()
