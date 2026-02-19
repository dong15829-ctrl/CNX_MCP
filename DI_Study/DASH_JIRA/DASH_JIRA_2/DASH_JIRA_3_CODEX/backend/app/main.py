from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import DEFAULT_TIME_WINDOW_DAYS
from .logging_config import configure_logging
from .middleware import RequestLoggingMiddleware
from .schemas import IngestionResponse, JiraWebhookPayload
from .services.data_loader import repository
from .services.ingestion import ingestion_service
from .services.simulation import simulator

configure_logging()
logger = logging.getLogger("jira_monitor")

app = FastAPI(title="Jira Monitoring API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/")
def root() -> dict:
    return {
        "message": "Jira monitoring backend is alive",
        "records": len(repository.dataframe),
    }


@app.get("/api/summary")
def get_summary() -> dict:
    return repository.get_summary()


@app.get("/api/metrics/time-series")
def get_time_series(
    days: int = Query(DEFAULT_TIME_WINDOW_DAYS, ge=7, le=1825),
    granularity: str = Query("day", pattern="^(day|week|month|year)$"),
) -> list:
    return repository.get_time_series(days=days, granularity=granularity)


@app.get("/api/metrics/status")
def get_status_distribution() -> list:
    return repository.get_status_distribution()


@app.get("/api/metrics/priority")
def get_priority_distribution() -> list:
    return repository.get_priority_distribution()


@app.get("/api/metrics/region")
def get_region_distribution() -> list:
    return repository.get_region_distribution()


@app.get("/api/metrics/category")
def get_category_distribution() -> list:
    return repository.get_category_distribution()


@app.get("/api/issues")
def list_issues(
    status: Optional[List[str]] = Query(default=None),
    priority: Optional[List[str]] = Query(default=None),
    region: Optional[List[str]] = Query(default=None),
    category: Optional[List[str]] = Query(default=None),
    text: Optional[str] = Query(default=None, min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
) -> dict:
    return repository.search_issues(
        status=status,
        priority=priority,
        region=region,
        category=category,
        text=text,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.get("/api/issues/{issue_key}")
def get_issue(issue_key: str) -> dict:
    try:
        return repository.get_issue_detail(issue_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/filters")
def get_filters() -> dict:
    df = repository.dataframe
    return {
        "statuses": sorted(df["status"].dropna().unique().tolist()),
        "priorities": sorted(df["priority"].dropna().unique().tolist()),
        "regions": sorted(df["region"].dropna().unique().tolist()),
        "categories": sorted(df["category"].dropna().unique().tolist()),
    }


@app.post("/api/ingest/jira-webhook", response_model=IngestionResponse)
def ingest_jira_webhook(payload: JiraWebhookPayload) -> IngestionResponse:
    record = ingestion_service.ingest_webhook(payload)
    return IngestionResponse(issue_key=record["issue_key"], ingested=True)


@app.get("/api/issues/{issue_key}/taxonomy")
def get_issue_taxonomy(issue_key: str) -> dict:
    try:
        return repository.get_taxonomy(issue_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/issues/{issue_key}/analysis")
def get_issue_analysis(issue_key: str, refresh: bool = Query(False)) -> dict:
    try:
        return repository.get_issue_analysis(issue_key, refresh=refresh)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/simulation/state")
def get_simulation_state() -> dict:
    return simulator.get_state()


@app.post("/api/simulation/reset")
def reset_simulation() -> dict:
    simulator.reset()
    return simulator.get_state()


@app.post("/api/simulation/next")
def run_simulation(batch: int = Query(1, ge=1, le=50)) -> dict:
    ingested = simulator.ingest_next(batch=batch)
    summary = simulator.get_state()
    summary["last_ingested"] = ingested
    return summary


@app.get("/health")
def health_check() -> dict:
    summary = repository.get_summary()
    return {
        "status": "ok",
        "records": summary["total_issues"],
        "last_updated": summary["last_updated"],
        "open_issues": summary["open_issues"],
        "high_priority_open": summary["high_priority_open"],
    }
