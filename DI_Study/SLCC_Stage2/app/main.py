# -*- coding: utf-8 -*-
"""자유 질의 기반 심층 분석 API (FastAPI)."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .context_loader import load_parsed_data, build_context_text
from .llm_analyzer import analyze
from .article_generator import generate_planning_article

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(title="SLCC 심층 분석 API", version="1.0")


class AnalyzeRequest(BaseModel):
    query: str
    style: str = "free"  # free | issues | insight | report


class AnalyzeResponse(BaseModel):
    answer: str
    style: str
    has_context: bool


@app.get("/")
def index():
    """프론트 페이지."""
    path = FRONTEND_DIR / "index.html"
    if not path.exists():
        raise HTTPException(404, "frontend/index.html not found")
    return FileResponse(path, media_type="text/html")


@app.post("/api/analyze", response_model=AnalyzeResponse)
def api_analyze(req: AnalyzeRequest):
    """자유 질의 → 심층 분석 결과 반환."""
    query = (req.query or "").strip()
    if not query:
        raise HTTPException(400, "query는 필수입니다.")
    style = req.style if req.style in ("free", "issues", "insight", "report") else "free"

    data = load_parsed_data()
    context = build_context_text(data)
    has_context = bool(data)

    answer = analyze(query=query, context=context, style=style)
    return AnalyzeResponse(answer=answer, style=style, has_context=has_context)


@app.post("/api/generate-article")
def api_generate_article():
    """데이터 기반 기획 기사 생성. 제목·리드·섹션 JSON 반환."""
    return generate_planning_article()


@app.get("/api/health")
def health():
    return {"status": "ok", "model": "gpt-4o"}
