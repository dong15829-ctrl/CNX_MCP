from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ReportFile(Base):
    __tablename__ = "report_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_type: Mapped[str] = mapped_column(String(16), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int] = mapped_column(Integer, index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)

    file_name: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(String(1024))
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    ingested_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class ReportIngestLog(Base):
    __tablename__ = "report_ingest_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_file_id: Mapped[int] = mapped_column(ForeignKey("report_files.id"), index=True)
    level: Mapped[str] = mapped_column(String(16), default="INFO", index=True)
    message: Mapped[str] = mapped_column(Text)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class CountrySummary(Base):
    __tablename__ = "country_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_file_id: Mapped[int] = mapped_column(ForeignKey("report_files.id"), index=True)

    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str] = mapped_column(String(128), index=True)
    gp1_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    sku: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sku_prev: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sku_gap: Mapped[int | None] = mapped_column(Integer, nullable=True)

    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_score_prev: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_gap: Mapped[float | None] = mapped_column(Float, nullable=True)

    rank_prev: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_current: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_change: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_country_summary_report_country", "report_file_id", "country"),
    )


class CountryMetric(Base):
    __tablename__ = "country_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_file_id: Mapped[int] = mapped_column(ForeignKey("report_files.id"), index=True)
    country: Mapped[str] = mapped_column(String(128), index=True)
    metric_key: Mapped[str] = mapped_column(String(64), index=True)
    metric_label: Mapped[str] = mapped_column(String(128))
    group_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_country_metrics_report_country_metric", "report_file_id", "country", "metric_key"),
    )


class IssueAltText(Base):
    __tablename__ = "issues_alt_text"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_file_id: Mapped[int] = mapped_column(ForeignKey("report_files.id"), index=True)

    country: Mapped[str] = mapped_column(String(128), index=True)
    url: Mapped[str] = mapped_column(Text)
    card_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    src: Mapped[str | None] = mapped_column(Text, nullable=True)
    srcset: Mapped[str | None] = mapped_column(Text, nullable=True)
    alt: Mapped[str | None] = mapped_column(Text, nullable=True)
    alt_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alt_comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class IssueBottom30(Base):
    __tablename__ = "issues_bottom30"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_file_id: Mapped[int] = mapped_column(ForeignKey("report_files.id"), index=True)

    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str] = mapped_column(String(128), index=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_prev: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_current: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_change: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

