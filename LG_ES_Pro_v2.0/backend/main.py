# -*- coding: utf-8 -*-
"""LG ES Pro v2.0 대시보드 API."""
import csv, io, os, secrets, time
from pathlib import Path

_env = Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv; load_dotenv(_env)
    except ImportError:
        for line in _env.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("="); k, v = k.strip(), v.strip().strip("'\"")
                if k and v: os.environ.setdefault(k, v)

from fastapi import Depends, FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

sessions: dict[str, dict] = {}
activity_log: list[dict] = []
download_log: list[dict] = []
_MAX_LOG_ENTRIES = 500
_summary_cache: dict[tuple, tuple[float, list]] = {}
SUMMARY_CACHE_TTL = float(os.environ.get("SUMMARY_CACHE_TTL", "60").strip() or "0")
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or os.environ.get("ADMIN_USERNAME", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

app = FastAPI(title="LG ES Pro v2.0 Dashboard API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_session_id(request: Request) -> str | None:
    return request.cookies.get("session_id")

def require_auth(request: Request):
    sid = get_session_id(request)
    if not sid or sid not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return sessions[sid]

def require_admin(request: Request):
    user = require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


@app.on_event("startup")
def on_startup():
    from backend.db import is_db_configured, get_connection
    from backend import auth_user
    if not is_db_configured(): return
    try:
        conn = get_connection()
        try:
            auth_user.ensure_users_table(conn)
            if auth_user.count_users(conn, role_filter="admin") == 0 and ADMIN_EMAIL and ADMIN_PASSWORD:
                auth_user.create_user(conn, ADMIN_EMAIL, ADMIN_PASSWORD, role="admin")
        finally: conn.close()
    except Exception: pass


# ===== 인증 =====
@app.post("/auth/login")
async def login(request: Request):
    from backend.db import is_db_configured, get_connection
    from backend import auth_user
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="DB 미연동")
    try: body = await request.json()
    except Exception: body = None
    if not body: raise HTTPException(status_code=400, detail="JSON body required")
    username = (body.get("username") or body.get("id") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    conn = get_connection()
    try:
        user = auth_user.get_user_by_email(conn, username)
        if not user or not auth_user.verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not auth_user.is_user_active(conn, user["id"]):
            raise HTTPException(status_code=403, detail="승인 대기 중입니다.")
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = {"user_id": user["id"], "email": user["email"], "role": user["role"], "login_at": time.time()}
        activity_log.append({"ts": time.time(), "user_id": user["id"], "email": user["email"], "action": "login", "detail": "Sign in"})
        if len(activity_log) > _MAX_LOG_ENTRIES: activity_log[:] = activity_log[-_MAX_LOG_ENTRIES:]
        response = JSONResponse(content={"ok": True, "username": user["email"], "role": user["role"]})
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
        return response
    finally: conn.close()

@app.post("/auth/logout")
def logout(request: Request):
    sid = get_session_id(request)
    if sid and sid in sessions: del sessions[sid]
    response = JSONResponse(content={"ok": True})
    response.delete_cookie("session_id")
    return response

@app.get("/auth/me")
def auth_me(request: Request):
    user = require_auth(request)
    return {"username": user.get("email", ""), "role": user.get("role", "user")}

@app.post("/auth/register")
async def register(request: Request):
    from backend.db import is_db_configured, get_connection
    from backend import auth_user
    if not is_db_configured(): raise HTTPException(status_code=503, detail="DB 미연동")
    try: body = await request.json()
    except Exception: body = None
    if not body: raise HTTPException(status_code=400, detail="JSON body required")
    email = (body.get("email") or body.get("username") or "").strip()
    password = body.get("password") or ""
    try:
        conn = get_connection()
        try:
            u = auth_user.create_user(conn, email, password, role="user", is_active=False)
            return {"ok": True, "username": u["email"], "role": u["role"], "pending_approval": True}
        finally: conn.close()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== 관리자 API =====
@app.get("/api/admin/users")
def admin_list_users(request: Request, role: str | None = Query(None), active_only: bool = Query(False), pending_only: bool = Query(False), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    require_admin(request)
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        auth_user.ensure_users_table(conn)
        items = auth_user.list_users(conn, role_filter=role, active_only=active_only, pending_only=pending_only, limit=limit, offset=offset)
        total = auth_user.count_users(conn, role_filter=role, active_only=active_only, pending_only=pending_only)
        return {"items": items, "total": total}
    finally: conn.close()

@app.post("/api/admin/users")
async def admin_create_user(request: Request):
    require_admin(request)
    try: body = await request.json()
    except Exception: body = {}
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    role = (body.get("role") or "user").strip().lower()
    if role not in ("admin", "user"): role = "user"
    if not email: raise HTTPException(status_code=400, detail="이메일을 입력해 주세요.")
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        u = auth_user.create_user(conn, email, password, role=role)
        return {"ok": True, "user": {"id": u["id"], "email": u["email"], "role": u["role"], "is_active": u["is_active"]}}
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))
    finally: conn.close()

@app.patch("/api/admin/users/{user_id:int}")
async def admin_update_user(request: Request, user_id: int):
    require_admin(request)
    try: body = await request.json()
    except Exception: body = {}
    role, is_active, password = body.get("role"), body.get("is_active"), body.get("password")
    if role is None and is_active is None and not password:
        raise HTTPException(status_code=400, detail="role, is_active, password 중 하나 이상 필요")
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        updated = auth_user.update_user(conn, user_id, role=role, is_active=is_active, password=password if password else None)
        if not updated: raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True, "user": {"id": updated["id"], "email": updated["email"], "role": updated["role"], "is_active": updated["is_active"]}}
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))
    finally: conn.close()

@app.delete("/api/admin/users/{user_id:int}")
def admin_delete_user(request: Request, user_id: int):
    require_admin(request)
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        if not auth_user.delete_user(conn, user_id): raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True, "deleted_id": user_id}
    finally: conn.close()

def _fmt_ts(ts: float) -> str:
    from datetime import datetime
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")

@app.get("/api/admin/usage")
def admin_usage(request: Request):
    require_admin(request)
    from backend.db import get_connection
    from backend import auth_user
    now = time.time(); seven = now - 7 * 86400
    login_by_user = {}
    for s in sessions.values():
        uid, t = s.get("user_id"), s.get("login_at", 0)
        if uid and (not login_by_user.get(uid) or t > login_by_user[uid]): login_by_user[uid] = t
    dl7 = {}
    for e in download_log:
        if e["ts"] >= seven: uid = e.get("user_id", 0); dl7[uid] = dl7.get(uid, 0) + 1
    conn = get_connection()
    try:
        auth_user.ensure_users_table(conn)
        users = auth_user.list_users(conn, limit=500, offset=0)
        items = [{"user_id": u["id"], "email": u["email"], "role": u["role"],
                  "last_login": _fmt_ts(login_by_user[u["id"]]) if login_by_user.get(u["id"]) else None,
                  "sessions_7d": 1 if login_by_user.get(u["id"]) and login_by_user[u["id"]] >= seven else 0,
                  "downloads_7d": dl7.get(u["id"], 0)} for u in users]
        return {"items": items, "total": len(items)}
    finally: conn.close()

@app.get("/api/admin/pipeline-status")
def admin_pipeline_status(request: Request):
    require_admin(request)
    return {"items": [{"name": "B2B Summary", "type": "DB sync", "last_run": None, "status": "idle", "note": "On-demand"}, {"name": "B2C Summary", "type": "DB sync", "last_run": None, "status": "idle", "note": "On-demand"}], "total": 2}

@app.get("/api/admin/download-log")
def admin_download_log(request: Request, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    require_admin(request)
    sl = list(reversed(download_log))[offset:offset+limit]
    return {"items": [{"ts": _fmt_ts(e["ts"]), "user_id": e.get("user_id"), "email": e.get("email",""), "download_type": e.get("download_type",""), "period_or_detail": e.get("period_or_detail","")} for e in sl], "total": len(download_log)}

@app.get("/api/admin/activity-log")
def admin_activity_log(request: Request, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    require_admin(request)
    sl = list(reversed(activity_log))[offset:offset+limit]
    return {"items": [{"ts": _fmt_ts(e["ts"]), "user_id": e.get("user_id"), "email": e.get("email",""), "action": e.get("action",""), "detail": e.get("detail","")} for e in sl], "total": len(activity_log)}

@app.post("/api/admin/log-download")
async def admin_log_download(request: Request):
    user = require_auth(request)
    try: body = await request.json() or {}
    except Exception: body = {}
    entry = {"ts": time.time(), "user_id": user.get("user_id"), "email": user.get("email",""), "download_type": (body.get("download_type") or "Excel").strip(), "period_or_detail": (body.get("period_or_detail") or "").strip()}
    download_log.append(entry)
    if len(download_log) > _MAX_LOG_ENTRIES: download_log[:] = download_log[-_MAX_LOG_ENTRIES:]
    return {"ok": True}


# ===== 시스템 =====
@app.get("/api/health")
def health():
    from backend.db import is_db_configured
    return {"db_configured": is_db_configured()}

@app.get("/api/version")
def api_version():
    return {"version": "2.0-pro", "message": "LG ES Pro v2.0 서버 동작 중"}


# ===== DB 연동 API =====
def require_db():
    from backend.db import is_db_configured
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="DB 미연동. .env에 MYSQL_PASSWORD 설정 후 재시작.")

def _to_503(e):
    s = str(e).lower()
    if "password" in s or "access denied" in s or "connect" in s:
        return HTTPException(status_code=503, detail="DB 연결 실패. .env 확인.")
    return None

@app.exception_handler(HTTPException)
def http_exc_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
def generic_exc_handler(request, exc):
    err = _to_503(exc)
    if err: return JSONResponse(status_code=503, content={"detail": err.detail})
    return JSONResponse(status_code=500, content={"detail": str(exc) or "Internal Server Error"})

@app.get("/api/reports")
def list_reports(request: Request, _: None = Depends(require_db)):
    require_auth(request)
    from backend.data import get_available_months, get_summary_snapshot
    reports = get_available_months()
    latest_counts = {rt: len(get_summary_snapshot(rt)) for rt in ("B2B", "B2C")}
    for r in reports:
        r["count"] = latest_counts.get(r["report_type"], 0) if r.get("month") == "latest" else None
    return reports

@app.get("/api/filters")
def get_filters(request: Request, _: None = Depends(require_db), report_type: str = Query(...), month: str = Query("latest")):
    require_auth(request)
    from backend.data import get_filters_from_snapshot
    month = (request.query_params.get("month") or "latest").strip()
    region_filter = request.query_params.getlist("region")
    return get_filters_from_snapshot(report_type, region_filter=tuple(sorted(region_filter)) if region_filter else (), month=month or None)

@app.get("/api/summary")
def get_summary(request: Request, _: None = Depends(require_db), report_type: str = Query(...), month: str = Query("latest")):
    require_auth(request)
    from backend.data import get_summary_snapshot
    month = (request.query_params.get("month") or "latest").strip()
    regions = tuple(sorted(request.query_params.getlist("region")))
    countries = tuple(sorted(request.query_params.getlist("country")))
    cache_key = (report_type.upper(), month, regions, countries)
    if SUMMARY_CACHE_TTL > 0 and cache_key in _summary_cache:
        ts, cached = _summary_cache[cache_key]
        if time.time() - ts < SUMMARY_CACHE_TTL: return cached
    rows = get_summary_snapshot(report_type, regions or None, countries or None, month=month or None)
    if SUMMARY_CACHE_TTL > 0: _summary_cache[cache_key] = (time.time(), rows)
    return rows

@app.get("/api/stats")
def get_stats(request: Request, _: None = Depends(require_db), report_type: str = Query(...), month: str = Query("latest")):
    require_auth(request)
    from backend.data import get_summary_snapshot
    from collections import defaultdict
    rows = get_summary_snapshot(report_type, request.query_params.getlist("region") or None, request.query_params.getlist("country") or None)
    agg = defaultdict(lambda: {"country_count": 0, "total_score_sum": 0.0})
    for r in rows:
        reg = r.get("region", "")
        agg[reg]["country_count"] += 1
        try: agg[reg]["total_score_sum"] += float(r.get("total_score_pct") or 0)
        except: pass
    result = []
    for reg, v in agg.items():
        result.append({"region": reg, "country_count": v["country_count"], "avg_total_score": round(v["total_score_sum"]/v["country_count"], 6) if v["country_count"] else 0})
    result.sort(key=lambda x: -x["avg_total_score"])
    return result

@app.get("/api/summary/trend")
def get_summary_trend(request: Request, _: None = Depends(require_db), report_type: str = Query(...), by: str = Query("month")):
    require_auth(request)
    from backend.data import get_summary_trend
    return get_summary_trend(report_type, by)

@app.get("/api/summary/download")
def download_summary(request: Request, _: None = Depends(require_db), report_type: str = Query(...)):
    require_auth(request)
    from backend.data import get_summary_snapshot
    rows = get_summary_snapshot(report_type, request.query_params.getlist("region") or None, request.query_params.getlist("country") or None)
    if not rows: raise HTTPException(status_code=404, detail="No summary data")
    buf = io.StringIO()
    csv.DictWriter(buf, fieldnames=list(rows[0].keys()), extrasaction="ignore").writeheader()
    csv.DictWriter(buf, fieldnames=list(rows[0].keys()), extrasaction="ignore").writerows(rows)
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue().encode("utf-8-sig")]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=summary_{report_type.lower()}.csv"})

@app.get("/api/raw")
def get_raw_json(request: Request, _: None = Depends(require_db), report_type: str = Query(...), region: str | None = Query(None), country: str | None = Query(None), limit: int = Query(500, ge=1, le=2000)):
    require_auth(request)
    from backend.data import get_raw_rows
    rows = get_raw_rows(report_type, [region] if region else None, [country] if country else None, limit=limit)
    return {"items": rows, "total": len(rows)}

@app.get("/api/raw/download")
def download_raw(request: Request, _: None = Depends(require_db), report_type: str = Query(...)):
    require_auth(request)
    from backend.data import get_raw_df_for_download
    df = get_raw_df_for_download(report_type, request.query_params.getlist("region") or None, request.query_params.getlist("country") or None)
    if df is None or df.empty: raise HTTPException(status_code=404, detail="No raw data")
    buf = io.StringIO(); df.to_csv(buf, index=False, encoding="utf-8-sig"); buf.seek(0)
    return StreamingResponse(iter([buf.getvalue().encode("utf-8-sig")]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=raw_{report_type.lower()}.csv"})

SAMPLE_BLOG_ROWS = [
    ["Region","Country","URL","'25","'26","Latest Blog Date","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
    ["LATAM","Argentina","https://www.lg.com/ar/business/soluciones-de-climatizacion/blog-list",8,1,"2026-01-02",1,0,0,0,0,0,0,0,0,0,0,0],
    ["ASIA","Australia","https://www.lg.com/au/business/air-solution/air-solutions-blog/",4,0,"2025-11-03",0,0,0,0,0,0,0,0,0,0,0,0],
    ["LATAM","Brazil","https://www.lg.com/br/business/ar-condicionado/blog-list/",8,0,"2025-10-31",0,0,0,0,0,0,0,0,0,0,0,0],
    ["NA","Canada","https://www.lg.com/ca_en/business/air-solution/blog-list/",0,0,"2024-05-27",0,0,0,0,0,0,0,0,0,0,0,0],
    ["LATAM","Chile","https://www.lg.com/cl/business/soluciones-de-climatizacion/blog-list",7,0,"2025-09-15",0,0,0,0,0,0,0,0,0,0,0,0],
    ["ASIA","China","https://www.lg.com/cn/business/air-solution/blog-list/",12,1,"2026-01-10",1,0,0,0,0,0,0,0,0,0,0,0],
    ["EU","France","https://www.lg.com/fr/business/air-solution/blog-list/",6,0,"2025-11-28",0,0,0,0,0,0,0,0,0,0,0,0],
    ["EU","Germany","https://www.lg.com/de/business/air-solution/blog-list/",9,0,"2025-10-05",0,0,0,0,0,0,0,0,0,0,0,0],
    ["INDIA","India","https://www.lg.com/in/business/air-solution/blog-list/",10,1,"2026-01-05",1,0,0,0,0,0,0,0,0,0,0,0],
    ["MEA","Israel","https://www.lg.com/il/business/air-solution/blog-list/",4,0,"2025-08-14",0,0,0,0,0,0,0,0,0,0,0,0],
]

@app.get("/api/sheet")
def get_sheet(request: Request, month: str = Query("latest"), sheet: str = Query(...)):
    require_auth(request)
    if sheet == "Blog": return SAMPLE_BLOG_ROWS
    return []

@app.get("/api/checklist")
def get_checklist(request: Request, month: str = Query("latest")):
    require_auth(request)
    return []


# ===== 정적 파일 =====
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")

    @app.get("/login")
    def login_page():
        return FileResponse(FRONTEND_DIR / "login.html")

    @app.get("/")
    def index(request: Request):
        if get_session_id(request) not in sessions:
            return RedirectResponse(url="/login", status_code=302)
        return FileResponse(FRONTEND_DIR / "index.html")
