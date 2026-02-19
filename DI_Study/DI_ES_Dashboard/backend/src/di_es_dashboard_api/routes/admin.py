from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from di_es_dashboard_api.config import settings
from di_es_dashboard_api.db import get_db
from di_es_dashboard_api.models import ReportFile, ReportIngestLog
from di_es_dashboard_api.schemas import ReportFileOut
from di_es_dashboard_api.services.ingestion import create_report_file_record, ingest_excel_report, _log


router = APIRouter(prefix="/admin")


def _ensure_upload_dir() -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _process_upload(report_file_id: int) -> None:
    from di_es_dashboard_api.db import SessionLocal

    db = SessionLocal()
    try:
        report_file = db.get(ReportFile, report_file_id)
        if not report_file:
            return
        try:
            ingest_excel_report(db, report_file)
            db.commit()
        except Exception as e:
            report_file.status = "failed"
            report_file.error_message = str(e)
            db.add(report_file)
            _log(db, report_file.id, "ERROR", "Ingestion failed", {"error": str(e)})
            db.commit()
    finally:
        db.close()


@router.post("/uploads", response_model=ReportFileOut)
def upload_report(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ReportFileOut:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    upload_dir = _ensure_upload_dir()
    stored_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    stored_path = upload_dir / stored_name

    with stored_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        report_file = create_report_file_record(db, stored_path, file.filename)
        report_file.status = "processing"
        db.add(report_file)
        _log(db, report_file.id, "INFO", "Upload received", {"stored_path": str(stored_path)})
        db.commit()
    except Exception as e:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    background.add_task(_process_upload, report_file.id)
    db.refresh(report_file)

    return ReportFileOut.model_validate(report_file)


@router.get("/uploads", response_model=list[ReportFileOut])
def list_uploads(db: Session = Depends(get_db)) -> list[ReportFileOut]:
    rows = db.execute(select(ReportFile).order_by(ReportFile.created_at.desc()).limit(200)).scalars().all()
    return [ReportFileOut.model_validate(r) for r in rows]


@router.get("/uploads/{upload_id}")
def upload_detail(upload_id: int, db: Session = Depends(get_db)) -> dict:
    report = db.get(ReportFile, upload_id)
    if not report:
        raise HTTPException(status_code=404, detail="Upload not found")

    logs = db.execute(
        select(ReportIngestLog.level, ReportIngestLog.message, ReportIngestLog.context, ReportIngestLog.created_at)
        .where(ReportIngestLog.report_file_id == upload_id)
        .order_by(ReportIngestLog.created_at.asc())
    ).all()
    return {
        "report": ReportFileOut.model_validate(report),
        "logs": [
            {"level": level, "message": message, "context": context, "created_at": created_at}
            for (level, message, context, created_at) in logs
        ],
    }


@router.post("/uploads/{upload_id}/reprocess", response_model=ReportFileOut)
def reprocess_upload(upload_id: int, background: BackgroundTasks, db: Session = Depends(get_db)) -> ReportFileOut:
    report = db.get(ReportFile, upload_id)
    if not report:
        raise HTTPException(status_code=404, detail="Upload not found")

    report.status = "processing"
    report.error_message = None
    db.add(report)
    _log(db, report.id, "INFO", "Reprocess requested")
    db.commit()

    background.add_task(_process_upload, report.id)
    db.refresh(report)
    return ReportFileOut.model_validate(report)
