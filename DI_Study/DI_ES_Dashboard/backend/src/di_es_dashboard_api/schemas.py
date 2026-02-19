from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Period(ORMModel):
    year: int
    month: int


class ReportFileOut(ORMModel):
    id: int
    report_type: str
    year: int
    month: int
    revision: int
    file_name: str
    is_active: bool
    status: str
    warnings_count: int
    error_message: str | None
    created_at: datetime
    ingested_at: datetime | None


class OverviewKpis(ORMModel):
    avg_total_score: float | None
    countries_count: int
    alt_text_errors_count: int
    bottom30_count: int


class OverviewMetric(ORMModel):
    metric_key: str
    metric_label: str
    avg_value: float | None


class OverviewTrendPoint(ORMModel):
    year: int
    month: int
    avg_total_score: float | None


class OverviewResponse(ORMModel):
    report_type: str
    period: Period
    compare: Literal["off", "mom", "yoy"] = "off"
    kpis: OverviewKpis
    metrics: list[OverviewMetric]
    trend: list[OverviewTrendPoint]


class CountryRankingRow(ORMModel):
    region: str | None
    country: str
    total_score: float | None
    rank_current: int | None = None
    rank_change: int | None = None
    metrics: dict[str, float | None] = Field(default_factory=dict)


class RankingResponse(ORMModel):
    report_type: str
    period: Period
    page: int
    page_size: int
    total: int
    items: list[CountryRankingRow]


class CountryDetailResponse(ORMModel):
    report_type: str
    period: Period
    country: str
    region: str | None
    total_score: float | None
    total_score_prev: float | None = None
    total_delta: float | None = None
    metrics: list[dict[str, Any]]
    issues: dict[str, int] = Field(default_factory=dict)


class IssueAltTextRow(ORMModel):
    id: int
    country: str
    url: str
    card_index: int | None
    src: str | None
    alt_length: int | None
    alt_comment: str | None


class IssuesAltTextResponse(ORMModel):
    report_type: str
    period: Period
    page: int
    page_size: int
    total: int
    items: list[IssueAltTextRow]


class IssueBottom30Row(ORMModel):
    id: int
    region: str | None
    country: str
    total_score: float | None
    rank_prev: int | None
    rank_current: int | None
    rank_change: int | None


class IssuesBottom30Response(ORMModel):
    report_type: str
    period: Period
    page: int
    page_size: int
    total: int
    items: list[IssueBottom30Row]
