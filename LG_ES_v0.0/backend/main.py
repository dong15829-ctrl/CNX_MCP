"""
FastAPI 백엔드: Excel Summary 기반 대시보드 API
"""
from pathlib import Path

import sqlite3
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "reports.db"

app = FastAPI(title="LG ES Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/reports")
def list_reports():
    """사용 가능한 리포트 목록 (report_type, month)"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, report_type, month, file_name FROM reports ORDER BY report_type, month"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/filters")
def get_filters(
    request: Request,
    report_type: str = Query(..., description="B2B or B2C"),
    month: str = Query(..., description="e.g. 2025-M11"),
):
    """선택한 리포트의 Region/Country 목록."""
    conn = get_conn()
    r = conn.execute(
        "SELECT id FROM reports WHERE report_type = ? AND month = ?",
        (report_type.upper(), month),
    ).fetchone()
    if not r:
        conn.close()
        return {"regions": [], "countries": []}
    report_id = r["id"]
    regions = [
        row[0] for row in conn.execute(
            "SELECT DISTINCT region FROM summary WHERE report_id = ? AND region IS NOT NULL AND region != '' ORDER BY region",
            (report_id,),
        ).fetchall()
    ]
    region_filter = request.query_params.getlist("region")
    if region_filter:
        placeholders = ",".join("?" * len(region_filter))
        countries = [
            row[0]
            for row in conn.execute(
                f"SELECT DISTINCT country FROM summary WHERE report_id = ? AND country IS NOT NULL AND country != '' AND region IN ({placeholders}) ORDER BY country",
                (report_id, *region_filter),
            ).fetchall()
        ]
    else:
        countries = [
            row[0] for row in conn.execute(
                "SELECT DISTINCT country FROM summary WHERE report_id = ? AND country IS NOT NULL AND country != '' ORDER BY country",
                (report_id,),
            ).fetchall()
        ]
    conn.close()
    return {"regions": regions, "countries": countries}


@app.get("/api/summary")
def get_summary(
    request: Request,
    report_type: str = Query(..., description="B2B or B2C"),
    month: str = Query(..., description="e.g. 2025-M11"),
):
    """Summary 행 목록 (region/country 다중 필터 지원)"""
    region = request.query_params.getlist("region")
    country = request.query_params.getlist("country")
    conn = get_conn()
    r = conn.execute(
        "SELECT id FROM reports WHERE report_type = ? AND month = ?",
        (report_type.upper(), month),
    ).fetchone()
    if not r:
        conn.close()
        return []
    report_id = r["id"]
    sql = """SELECT region, country, gp1_status, sku, sku_oct, gap_sku,
                  total_score, total_score_oct, gap_score,
                  title_score, description_score, h1_score, canonical_score,
                  alt_text_score, product_category_score, blog_score,
                  prev_rank, curr_rank, rank_change
           FROM summary WHERE report_id = ?"""
    params: list = [report_id]
    if region and len(region):
        sql += " AND region IN (" + ",".join("?" * len(region)) + ")"
        params.extend(region)
    if country and len(country):
        sql += " AND country IN (" + ",".join("?" * len(country)) + ")"
        params.extend(country)
    sql += " ORDER BY total_score DESC NULLS LAST"
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/checklist")
def get_checklist(month: str | None = Query(None, description="e.g. 2025-M10")):
    """Checklist & Criteria 시트 데이터. B2B 전용."""
    import json
    conn = get_conn()
    report_id = None
    if month:
        r = conn.execute(
            "SELECT id FROM reports WHERE report_type = ? AND month = ?",
            ("B2B", month),
        ).fetchone()
        if r:
            report_id = r["id"]
    if report_id is None:
        r = conn.execute(
            "SELECT id FROM reports WHERE report_type = ? ORDER BY month LIMIT 1",
            ("B2B",),
        ).fetchone()
        if r:
            report_id = r["id"]
    if report_id is None:
        conn.close()
        return []
    rows = conn.execute(
        "SELECT row_index, row_data FROM checklist WHERE report_id = ? ORDER BY row_index",
        (report_id,),
    ).fetchall()
    conn.close()
    return [json.loads(r["row_data"]) for r in rows]


def _is_empty_cell(v):
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    return False


def _is_empty_row(row):
    if not row:
        return True
    return all(_is_empty_cell(c) for c in row)


def _trim_sheet_rows(rows):
    """맨 아래/맨 위 빈 행 제거."""
    if not rows:
        return rows
    while rows and _is_empty_row(rows[-1]):
        rows.pop()
    while len(rows) > 1 and _is_empty_row(rows[0]):
        rows.pop(0)
    return rows


@app.get("/api/sheet")
def get_sheet(
    month: str = Query(..., description="e.g. 2025-M10"),
    sheet: str = Query(..., description="PLP_BUSINESS | Product Category | Blog | Feature Card Alt Text Error"),
):
    """B2B 시트 데이터 (PLP_BUSINESS, Product Category, Blog 등)."""
    import json
    try:
        conn = get_conn()
        month_val = (month or "").strip()
        r = conn.execute(
            "SELECT id FROM reports WHERE report_type = ? AND month = ?",
            ("B2B", month_val),
        ).fetchone()
        if not r:
            conn.close()
            return []
        report_id = r["id"]
        rows = conn.execute(
            "SELECT row_index, row_data FROM sheet_data WHERE report_id = ? AND sheet_name = ? ORDER BY row_index",
            (report_id, sheet),
        ).fetchall()
        conn.close()
        result = []
        for row in rows:
            try:
                result.append(json.loads(row["row_data"]))
            except (TypeError, ValueError):
                result.append([])
        return _trim_sheet_rows(result)
    except Exception:
        return []


@app.get("/api/stats")
def get_stats(
    request: Request,
    report_type: str = Query(..., description="B2B or B2C"),
    month: str = Query(..., description="e.g. 2025-M11"),
):
    """Region별 집계."""
    region = request.query_params.getlist("region")
    country = request.query_params.getlist("country")
    conn = get_conn()
    r = conn.execute(
        "SELECT id FROM reports WHERE report_type = ? AND month = ?",
        (report_type.upper(), month),
    ).fetchone()
    if not r:
        conn.close()
        return []
    report_id = r["id"]
    sql = """SELECT region,
                  COUNT(*) AS country_count,
                  AVG(total_score) AS avg_total_score,
                  AVG(gap_score) AS avg_gap_score
           FROM summary WHERE report_id = ? AND region IS NOT NULL AND region != ''"""
    params: list = [report_id]
    if region and len(region):
        sql += " AND region IN (" + ",".join("?" * len(region)) + ")"
        params.extend(region)
    if country and len(country):
        sql += " AND country IN (" + ",".join("?" * len(country)) + ")"
        params.extend(country)
    sql += " GROUP BY region ORDER BY avg_total_score DESC"
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")

    @app.get("/")
    def index():
        return FileResponse(
            FRONTEND / "index.html",
            headers={"Cache-Control": "private, max-age=300"},
        )
