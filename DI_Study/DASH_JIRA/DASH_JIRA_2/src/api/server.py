from fastapi import FastAPI, HTTPException
from typing import List
from src.api.schemas import IssueRequest, AnalysisResponse, SearchRequest, SearchResult, RoutingResponse
from src.nlp.processor import NLPProcessor
from src.routing.rules import RuleEngine
from src.search.vector_store import VectorStore
from src.ingestion.models import IssueModel

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="JIRA Agent API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Initialize services
nlp_processor = NLPProcessor()
rule_engine = RuleEngine()
vector_store = VectorStore()

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_issue(request: IssueRequest):
    try:
        result = nlp_processor.process_issue(request.summary, request.description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route", response_model=RoutingResponse)
async def route_issue(request: IssueRequest):
    try:
        # 1. Analyze first
        analysis = nlp_processor.process_issue(request.summary, request.description)
        
        # 2. Create a temporary IssueModel for rule engine
        issue = IssueModel(
            issue_key="TEMP",
            summary=request.summary,
            description=request.description,
            custom_fields=request.custom_fields
        )
        
        # 3. Apply Rules
        team = rule_engine.apply_rules(issue, analysis)
        
        if team:
            return RoutingResponse(recommended_team=team, reason="Rule Match")
        
        # 4. Fallback to LLM suggestion
        return RoutingResponse(
            recommended_team=analysis.suggested_assignee_team, 
            reason="LLM Suggestion"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[SearchResult])
async def search_issues(request: SearchRequest):
    try:
        results = vector_store.search_similar_cases(request.query, request.limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from fastapi.responses import FileResponse

@app.get("/")
async def read_root():
    return FileResponse('src/static/index.html')

# --- Knowledge Base Endpoints ---
# --- Knowledge Base Endpoints ---
@app.get("/issues/stats")
async def get_issue_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Total count
        cur.execute("SELECT COUNT(*) FROM issues")
        total = cur.fetchone()[0]
        
        # By Type
        cur.execute("SELECT issue_type, COUNT(*) FROM issues GROUP BY issue_type ORDER BY COUNT(*) DESC LIMIT 5")
        by_type = {row[0]: row[1] for row in cur.fetchall()}
        
        # By Priority
        cur.execute("SELECT priority, COUNT(*) FROM issues GROUP BY priority ORDER BY COUNT(*) DESC LIMIT 5")
        by_priority = {row[0]: row[1] for row in cur.fetchall()}
        
        return {
            "total": total,
            "by_type": by_type,
            "by_priority": by_priority
        }
    finally:
        cur.close()
        conn.close()

@app.get("/issues")
async def get_issues(limit: int = 20, offset: int = 0, search: str = None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = "SELECT issue_key, summary, issue_type, status, created, priority, description, project_name FROM issues"
        params = []
        
        if search:
            query += " WHERE summary ILIKE %s OR issue_key ILIKE %s"
            params.extend([f"%{search}%", f"%{search}%"])
            
        query += " ORDER BY created DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        
        issues = []
        for row in rows:
            issues.append({
                "issue_key": row[0],
                "summary": row[1],
                "issue_type": row[2],
                "status": row[3],
                "created": row[4],
                "priority": row[5],
                "description": row[6],
                "project_name": row[7]
            })
        return issues
    finally:
        cur.close()
        conn.close()

# --- Simulation Endpoints ---
import pandas as pd
import random

TEST_DATA_PATH = '/home/ubuntu/DI/DASH_JIRA_2/processed/dataset_test.csv'

@app.get("/simulation/test-data")
async def get_test_data():
    try:
        # Read only a subset or cache this in production
        df = pd.read_csv(TEST_DATA_PATH)
        # Pick a random row
        row = df.sample(n=1).iloc[0]
        
        return {
            "summary": row.get('Summary', ''),
            "description": row.get('Description', ''),
            "issue_type": row.get('Issue Type', ''),
            "project": row.get('Project name', '') or row.get('Project key', ''),
            "priority": row.get('Priority', '')
        }
    except Exception as e:
        return {"error": str(e)}
