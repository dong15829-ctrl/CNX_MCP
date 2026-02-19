# -*- coding: utf-8 -*-
"""
LG ES Pro v1.0 대시보드 API.
로그인 + MySQL 연동 SUMMARY/트렌드/RAW API.
"""
import csv
import io
import os
import secrets
import time
from pathlib import Path

# .env 로드 (MYSQL_* 등). dotenv 없어도 수동 파싱으로 로드
_env = Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        for line in _env.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'\"")
                if k and v:
                    os.environ.setdefault(k, v)

from fastapi import Depends, FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# 간단한 세션 저장 (메모리). 세션값: { "user_id": int, "email": str, "role": "admin"|"user", "login_at": float }. 운영 시 Redis 등 권장.
sessions: dict[str, dict] = {}
# 관리자용 사용 현황/로그 (메모리). 운영 시 DB 또는 Redis 권장.
activity_log: list[dict] = []  # {"ts": float, "user_id": int, "email": str, "action": str, "detail": str}
download_log: list[dict] = []   # {"ts": float, "user_id": int, "email": str, "download_type": str, "period_or_detail": str}
_MAX_LOG_ENTRIES = 500
# Summary API 응답 캐시 (동일 조건 재요청 시 DB 부하 감소). TTL 60초. .env SUMMARY_CACHE_TTL=0 이면 비활성화.
_summary_cache: dict[tuple, tuple[float, list]] = {}
SUMMARY_CACHE_TTL = float(os.environ.get("SUMMARY_CACHE_TTL", "60").strip() or "0")
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
# 최초 관리자 시드용 (테이블에 admin이 없을 때만 사용)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or os.environ.get("ADMIN_USERNAME", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

app = FastAPI(title="LG ES Pro v1.0 Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session_id(request: Request) -> str | None:
    return request.cookies.get("session_id")


def require_auth(request: Request):
    sid = get_session_id(request)
    if not sid or sid not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return sessions[sid]


def require_admin(request: Request):
    """관리자만 허용. require_auth 후 사용."""
    user = require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


@app.on_event("startup")
def on_startup():
    """users 테이블 생성 및 최초 관리자 시드."""
    from backend.db import is_db_configured, get_connection
    from backend import auth_user
    if not is_db_configured():
        return
    try:
        conn = get_connection()
        try:
            auth_user.ensure_users_table(conn)
            if auth_user.count_users(conn, role_filter="admin") == 0 and ADMIN_EMAIL and ADMIN_PASSWORD:
                auth_user.create_user(conn, ADMIN_EMAIL, ADMIN_PASSWORD, role="admin")
        finally:
            conn.close()
    except Exception:
        pass


# ----- 인증 -----
@app.post("/auth/login")
async def login(request: Request):
    from backend.db import is_db_configured, get_connection
    from backend import auth_user
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="DB 미연동. 관리자에게 문의하세요.")
    try:
        body = await request.json()
    except Exception:
        body = None
    if not body:
        raise HTTPException(status_code=400, detail="JSON body required")
    username = (body.get("username") or body.get("id") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    conn = get_connection()
    try:
        user = auth_user.get_user_by_email(conn, username)
        if not user or not auth_user.verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        # 승인 대기(is_active=0) 시 로그인 불가 - DB에서 is_active 직접 재확인
        if not auth_user.is_user_active(conn, user["id"]):
            raise HTTPException(status_code=403, detail="승인 대기 중입니다. 관리자 승인 후 로그인할 수 있습니다.")
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = {"user_id": user["id"], "email": user["email"], "role": user["role"], "login_at": time.time()}
        activity_log.append({"ts": time.time(), "user_id": user["id"], "email": user["email"], "action": "login", "detail": "Sign in"})
        if len(activity_log) > _MAX_LOG_ENTRIES:
            activity_log[:] = activity_log[-_MAX_LOG_ENTRIES:]
        response = JSONResponse(content={"ok": True, "username": user["email"], "role": user["role"]})
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
        return response
    finally:
        conn.close()


@app.post("/auth/logout")
def logout(request: Request):
    sid = get_session_id(request)
    if sid and sid in sessions:
        del sessions[sid]
    response = JSONResponse(content={"ok": True})
    response.delete_cookie("session_id")
    return response


@app.get("/auth/me")
def auth_me(request: Request):
    user = require_auth(request)
    return {"username": user.get("email", ""), "role": user.get("role", "user")}


@app.post("/auth/register")
async def register(request: Request):
    """회원가입. 기본 역할은 user, is_active=0(승인 대기). 관리자 승인 후 로그인 가능."""
    from backend.db import is_db_configured, get_connection
    from backend import auth_user
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="DB 미연동.")
    try:
        body = await request.json()
    except Exception:
        body = None
    if not body:
        raise HTTPException(status_code=400, detail="JSON body required")
    email = (body.get("email") or body.get("username") or "").strip()
    password = body.get("password") or ""
    try:
        conn = get_connection()
        try:
            u = auth_user.create_user(conn, email, password, role="user", is_active=False)
            return {"ok": True, "username": u["email"], "role": u["role"], "pending_approval": True, "message": "가입이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다."}
        finally:
            conn.close()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----- 관리자 전용 API -----
@app.get("/api/admin/users")
def admin_list_users(
    request: Request,
    role: str | None = Query(None, description="admin | user"),
    active_only: bool = Query(False),
    pending_only: bool = Query(False, description="승인 대기만"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    require_admin(request)
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        auth_user.ensure_users_table(conn)
        items = auth_user.list_users(conn, role_filter=role or None, active_only=active_only, pending_only=pending_only, limit=limit, offset=offset)
        total = auth_user.count_users(conn, role_filter=role or None, active_only=active_only, pending_only=pending_only)
        return {"items": items, "total": total}
    finally:
        conn.close()


@app.post("/api/admin/users")
async def admin_create_user(request: Request):
    """관리자 전용: 새 사용자(관리자/일반) 생성."""
    require_admin(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    role = (body.get("role") or "user").strip().lower()
    if role not in ("admin", "user"):
        role = "user"
    if not email:
        raise HTTPException(status_code=400, detail="이메일을 입력해 주세요.")
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        u = auth_user.create_user(conn, email, password, role=role)
        return {"ok": True, "user": {"id": u["id"], "email": u["email"], "role": u["role"], "is_active": u["is_active"]}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.patch("/api/admin/users/{user_id:int}")
async def admin_update_user(request: Request, user_id: int):
    require_admin(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    role = body.get("role")
    is_active = body.get("is_active")
    password = body.get("password")
    if role is None and is_active is None and (password is None or password == ""):
        raise HTTPException(status_code=400, detail="role, is_active, password 중 하나 이상 필요")
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        updated = auth_user.update_user(conn, user_id, role=role, is_active=is_active, password=password if password else None)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True, "user": {"id": updated["id"], "email": updated["email"], "role": updated["role"], "is_active": updated["is_active"]}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.delete("/api/admin/users/{user_id:int}")
def admin_delete_user(request: Request, user_id: int):
    """관리자 전용: 사용자 계정 삭제."""
    require_admin(request)
    from backend.db import get_connection
    from backend import auth_user
    conn = get_connection()
    try:
        deleted = auth_user.delete_user(conn, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        return {"ok": True, "deleted_id": user_id}
    finally:
        conn.close()


# ----- 관리자: 사용 현황 / 파이프라인 / 다운로드·활동 로그 -----
def _fmt_ts(ts: float) -> str:
    from datetime import datetime
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")


@app.get("/api/admin/usage")
def admin_usage(request: Request):
    """유저별 사용 현황: 마지막 로그인, 7일 세션 수, 7일 다운로드 수."""
    require_admin(request)
    from backend.db import get_connection
    from backend import auth_user
    now = time.time()
    seven_days_ago = now - 7 * 86400
    # 현재 세션에서 로그인 시각 수집
    login_by_user: dict[int, float] = {}
    for s in sessions.values():
        uid = s.get("user_id")
        t = s.get("login_at") or 0
        if uid and (not login_by_user.get(uid) or t > login_by_user[uid]):
            login_by_user[uid] = t
    downloads_7d: dict[int, int] = {}
    for e in download_log:
        if e["ts"] >= seven_days_ago:
            uid = e.get("user_id") or 0
            downloads_7d[uid] = downloads_7d.get(uid, 0) + 1
    conn = get_connection()
    try:
        auth_user.ensure_users_table(conn)
        users = auth_user.list_users(conn, limit=500, offset=0)
        items = []
        for u in users:
            uid = u["id"]
            items.append({
                "user_id": uid,
                "email": u["email"],
                "role": u["role"],
                "last_login": _fmt_ts(login_by_user[uid]) if login_by_user.get(uid) else None,
                "sessions_7d": 1 if login_by_user.get(uid) and login_by_user[uid] >= seven_days_ago else 0,
                "downloads_7d": downloads_7d.get(uid, 0),
            })
        return {"items": items, "total": len(items)}
    finally:
        conn.close()


@app.get("/api/admin/pipeline-status")
def admin_pipeline_status(request: Request):
    """데이터 파이프라인/인터페이스 현황. (현재 스텁; 실제 스케줄러 연동 시 교체)"""
    require_admin(request)
    # 스텁: 실제로는 pipeline 실행 이력 DB 또는 스케줄러 API 연동
    return {
        "items": [
            {"name": "B2B Summary", "type": "DB sync", "last_run": None, "status": "idle", "note": "On-demand from dashboard"},
            {"name": "B2C Summary", "type": "DB sync", "last_run": None, "status": "idle", "note": "On-demand from dashboard"},
        ],
        "total": 2,
    }


@app.get("/api/admin/download-log")
def admin_download_log(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """다운로드 이력 (최신순)."""
    require_admin(request)
    slice_log = list(reversed(download_log))[offset : offset + limit]
    return {
        "items": [{"ts": _fmt_ts(e["ts"]), "user_id": e.get("user_id"), "email": e.get("email", ""), "download_type": e.get("download_type", ""), "period_or_detail": e.get("period_or_detail", "")} for e in slice_log],
        "total": len(download_log),
    }


@app.get("/api/admin/activity-log")
def admin_activity_log(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """활동 로그 (최신순)."""
    require_admin(request)
    slice_log = list(reversed(activity_log))[offset : offset + limit]
    return {
        "items": [{"ts": _fmt_ts(e["ts"]), "user_id": e.get("user_id"), "email": e.get("email", ""), "action": e.get("action", ""), "detail": e.get("detail", "")} for e in slice_log],
        "total": len(activity_log),
    }


@app.post("/api/admin/log-download")
async def admin_log_download(request: Request):
    """다운로드 시 프론트에서 호출하여 이력 기록."""
    user = require_auth(request)
    try:
        body = await request.json() or {}
    except Exception:
        body = {}
    download_type = (body.get("download_type") or body.get("type") or "Excel").strip()
    period_or_detail = (body.get("period_or_detail") or body.get("period") or body.get("detail") or "").strip()
    entry = {
        "ts": time.time(),
        "user_id": user.get("user_id"),
        "email": user.get("email", ""),
        "download_type": download_type,
        "period_or_detail": period_or_detail,
    }
    download_log.append(entry)
    if len(download_log) > _MAX_LOG_ENTRIES:
        download_log[:] = download_log[-_MAX_LOG_ENTRIES:]
    return {"ok": True}


@app.get("/api/health")
def health(request: Request):
    """DB 설정 여부 확인. 인증 없이 호출 가능."""
    from backend.db import is_db_configured
    return {"db_configured": is_db_configured(), "message": "DB 연동됨" if is_db_configured() else "프로젝트 루트 .env 에 MYSQL_PASSWORD 설정 후 서버 재시작"}


@app.get("/api/version")
def api_version():
    """배포된 API 버전 확인 (422 해결 여부 확인용). 인증/DB 불필요."""
    return {"version": "2.0", "api": "Depends(require_db)", "message": "이 메시지가 보이면 서버가 최신 코드로 동작 중입니다."}


# ----- DB 연동 API -----
def require_db():
    """DB 미설정 시 503. Depends()로 사용하여 시그니처 변경 없음."""
    from backend.db import is_db_configured
    if not is_db_configured():
        raise HTTPException(
            status_code=503,
            detail="DB 미연동. 프로젝트 루트에 .env 파일을 만들고 MYSQL_PASSWORD 등 DB 정보를 설정한 뒤 서버를 재시작하세요.",
        )


def _to_503(e: Exception) -> HTTPException | None:
    """연결/인증 관련 예외면 503 메시지 반환."""
    s = str(e).lower()
    if "password" in s or "access denied" in s or "connect" in s:
        return HTTPException(
            status_code=503,
            detail="DB 연결 실패. .env의 MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE 를 확인하세요.",
        )
    return None


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException은 그대로 JSON으로 반환 (422 등 검증 오류 유지)."""
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
def handle_data_errors(request: Request, exc: Exception):
    """예외 시 항상 JSON 반환 (프론트 파싱 오류 방지). 연결/인증 예외는 503, 나머지는 500."""
    from fastapi.responses import JSONResponse
    err = _to_503(exc)
    if err:
        return JSONResponse(status_code=503, content={"detail": err.detail})
    return JSONResponse(status_code=500, content={"detail": str(exc) or "Internal Server Error"})


@app.get("/api/reports")
def list_reports(request: Request, _: None = Depends(require_db)):
    require_auth(request)
    from backend.data import get_available_months, get_summary_snapshot
    reports = get_available_months()
    latest_counts = {rt: len(get_summary_snapshot(rt)) for rt in ("B2B", "B2C")}
    for r in reports:
        if r.get("month") == "latest":
            r["count"] = latest_counts.get(r["report_type"], 0)
        else:
            r["count"] = None
    return reports


@app.get("/api/filters")
def get_filters(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query(..., description="B2B or B2C"),
    month: str = Query("latest"),
):
    require_auth(request)
    from backend.data import get_filters_from_snapshot
    month = (request.query_params.get("month") or "latest").strip()
    region_filter = request.query_params.getlist("region")
    regions = tuple(sorted(region_filter)) if region_filter else ()
    return get_filters_from_snapshot(report_type, region_filter=regions, month=month or None)


@app.get("/api/summary")
def get_summary(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query(..., description="B2B or B2C"),
    month: str = Query("latest"),
):
    require_auth(request)
    from backend.data import get_summary_snapshot
    month = (request.query_params.get("month") or "latest").strip()
    region_filter = request.query_params.getlist("region")
    country_filter = request.query_params.getlist("country")
    regions = tuple(sorted(region_filter)) if region_filter else ()
    countries = tuple(sorted(country_filter)) if country_filter else ()
    cache_key = (report_type.upper(), month, regions, countries)
    if SUMMARY_CACHE_TTL > 0 and cache_key in _summary_cache:
        ts, cached = _summary_cache[cache_key]
        if time.time() - ts < SUMMARY_CACHE_TTL:
            return cached
    rows = get_summary_snapshot(report_type, region_filter or None, country_filter or None, month=month or None)
    if SUMMARY_CACHE_TTL > 0:
        _summary_cache[cache_key] = (time.time(), rows)
    return rows


@app.get("/api/debug/summary-sample")
def debug_summary_sample(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query("B2B"),
):
    """B2B Summary 실제 반환 데이터 샘플 (첫 3행). 인증 필요."""
    require_auth(request)
    from backend.data import get_summary_snapshot
    rows = get_summary_snapshot(report_type, None, None)
    sample = (rows or [])[:3]
    return {"count_total": len(rows or []), "sample": sample, "keys_in_sample": list(sample[0].keys()) if sample else []}


@app.get("/api/stats")
def get_stats(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query(...),
    month: str = Query("latest"),
):
    require_auth(request)
    from backend.data import get_summary_snapshot
    region_filter = request.query_params.getlist("region")
    country_filter = request.query_params.getlist("country")
    rows = get_summary_snapshot(report_type, region_filter or None, country_filter or None)
    from collections import defaultdict
    agg = defaultdict(lambda: {"country_count": 0, "avg_total_score": 0.0, "total_score_sum": 0.0})
    for r in rows:
        reg = r.get("region") or ""
        agg[reg]["country_count"] += 1
        try:
            s = float(r.get("total_score_pct") or r.get("total_score") or 0)
        except (TypeError, ValueError):
            s = 0
        agg[reg]["total_score_sum"] += s
    result = []
    for reg, v in agg.items():
        v["region"] = reg
        v["avg_total_score"] = round(v["total_score_sum"] / v["country_count"], 6) if v["country_count"] else 0
        del v["total_score_sum"]
        result.append(v)
    result.sort(key=lambda x: -x["avg_total_score"])
    return result


@app.get("/api/summary/trend")
def get_summary_trend(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query(...),
    by: str = Query("month", description="month or week"),
):
    require_auth(request)
    from backend.data import get_summary_trend
    return get_summary_trend(report_type, by)


@app.get("/api/summary/download")
def download_summary(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query(...),
    format: str = Query("csv"),
):
    require_auth(request)
    from backend.data import get_summary_snapshot
    region_filter = request.query_params.getlist("region")
    country_filter = request.query_params.getlist("country")
    rows = get_summary_snapshot(report_type, region_filter or None, country_filter or None)
    if not rows:
        raise HTTPException(status_code=404, detail="No summary data")
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=summary_{report_type.lower()}_snapshot.csv"},
    )


@app.get("/api/raw")
def get_raw_json(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query(..., description="B2B or B2C"),
    region: str | None = Query(None),
    country: str | None = Query(None),
    limit: int = Query(500, ge=1, le=2000),
):
    """RAW 테이블 행 JSON. Summary 테이블 셀 클릭 시 해당 region/country의 상세(raw) 조회용."""
    require_auth(request)
    from backend.data import get_raw_rows
    region_filter = [region] if region else None
    country_filter = [country] if country else None
    rows = get_raw_rows(report_type, region_filter=region_filter, country_filter=country_filter, limit=limit)
    return {"items": rows, "total": len(rows)}


@app.get("/api/raw/download")
def download_raw(
    request: Request,
    _: None = Depends(require_db),
    report_type: str = Query(..., description="B2B or B2C"),
):
    """RAW 테이블(reportbusiness_es_old_v2 / report_es_old) 전처리 결과 CSV 다운로드."""
    require_auth(request)
    from backend.data import get_raw_df_for_download
    region_filter = request.query_params.getlist("region")
    country_filter = request.query_params.getlist("country")
    df = get_raw_df_for_download(report_type, region_filter or None, country_filter or None)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No raw data")
    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=raw_{report_type.lower()}.csv"},
    )


SAMPLE_BLOG_ROWS = [
    ["Region", "Country", "URL", "'25", "'26", "Latest Blog Date", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    ["LATAM", "Argentina", "https://www.lg.com/ar/business/soluciones-de-climatizacion/blog-list", 8, 1, "2026-01-02", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["ASIA", "Australia", "https://www.lg.com/au/business/air-solution/air-solutions-blog/", 4, 0, "2025-11-03", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["LATAM", "Brazil", "https://www.lg.com/br/business/ar-condicionado/blog-list/", 8, 0, "2025-10-31", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["NA", "Canada", "https://www.lg.com/ca_en/business/air-solution/blog-list/", 0, 0, "2024-05-27", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["LATAM", "Chile", "https://www.lg.com/cl/business/soluciones-de-climatizacion/blog-list", 7, 0, "2025-09-15", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["ASIA", "China", "https://www.lg.com/cn/business/air-solution/blog-list/", 12, 1, "2026-01-10", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["LATAM", "Colombia", "https://www.lg.com/co/business/soluciones-de-climatizacion/blog-list", 3, 0, "2025-08-20", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["EU", "Czech", "https://www.lg.com/cz/business/air-solution/blog-list/", 5, 0, "2025-07-12", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["MEA", "Egypt", "https://www.lg.com/eg/business/air-solution/blog-list/", 2, 0, "2025-06-01", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["EU", "France", "https://www.lg.com/fr/business/air-solution/blog-list/", 6, 0, "2025-11-28", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["EU", "Germany", "https://www.lg.com/de/business/air-solution/blog-list/", 9, 0, "2025-10-05", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["EU", "Greece", "https://www.lg.com/gr/business/air-solution/blog-list/", 4, 0, "2025-04-18", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["EU", "Hungary", "https://www.lg.com/hu/business/air-solution/blog-list/", 3, 0, "2025-03-22", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["INDIA", "India", "https://www.lg.com/in/business/air-solution/blog-list/", 10, 1, "2026-01-05", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["ASIA", "Indonesia", "https://www.lg.com/id/business/air-solution/blog-list/", 5, 0, "2025-09-30", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["MEA", "Israel", "https://www.lg.com/il/business/air-solution/blog-list/", 4, 0, "2025-08-14", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


@app.get("/api/sheet")
def get_sheet(
    request: Request,
    month: str = Query("latest"),
    sheet: str = Query(..., description="PLP_BUSINESS, Product Category, Blog 등"),
):
    """시트 RAW 데이터. 파이프라인에는 별도 시트 없음 — Blog는 샘플 데이터 반환."""
    require_auth(request)
    if sheet == "Blog":
        return SAMPLE_BLOG_ROWS
    return []


@app.get("/api/checklist")
def get_checklist(
    request: Request,
    month: str = Query("latest"),
):
    """체크리스트. 파이프라인에는 없음 — 빈 배열 반환."""
    require_auth(request)
    return []


# ----- 정적·페이지 -----
if FRONTEND_DIR.exists():
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    # Serve frontend files directly for demo access
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

    @app.get("/login")
    def login_page():
        return FileResponse(FRONTEND_DIR / "login.html")

    @app.get("/")
    def index(request: Request):
        if get_session_id(request) not in sessions:
            return RedirectResponse(url="/login", status_code=302)
        return FileResponse(FRONTEND_DIR / "index.html")
