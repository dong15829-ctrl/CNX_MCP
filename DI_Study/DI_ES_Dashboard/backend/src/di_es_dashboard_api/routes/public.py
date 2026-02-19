from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from di_es_dashboard_api.db import get_db
from di_es_dashboard_api.models import CountryMetric, CountrySummary, IssueAltText, IssueBottom30, ReportFile
from di_es_dashboard_api.schemas import (
    CountryDetailResponse,
    IssuesAltTextResponse,
    IssuesBottom30Response,
    OverviewKpis,
    OverviewMetric,
    OverviewResponse,
    OverviewTrendPoint,
    Period,
    RankingResponse,
    CountryRankingRow,
)


router = APIRouter()


def _get_active_report(db: Session, report_type: str, year: int, month: int) -> ReportFile | None:
    return db.execute(
        select(ReportFile).where(
            ReportFile.report_type == report_type,
            ReportFile.year == year,
            ReportFile.month == month,
            ReportFile.is_active.is_(True),
            ReportFile.status == "completed",
        )
    ).scalar_one_or_none()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/periods")
def list_periods(reportType: str = Query(...), db: Session = Depends(get_db)) -> list[Period]:
    rows = db.execute(
        select(ReportFile.year, ReportFile.month)
        .where(ReportFile.report_type == reportType, ReportFile.is_active.is_(True), ReportFile.status == "completed")
        .order_by(ReportFile.year.desc(), ReportFile.month.desc())
    ).all()
    return [Period(year=y, month=m) for (y, m) in rows]


@router.get("/overview", response_model=OverviewResponse)
def overview(
    reportType: str = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
) -> OverviewResponse:
    report = _get_active_report(db, reportType, year, month)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    avg_total = db.execute(
        select(func.avg(CountrySummary.total_score)).where(CountrySummary.report_file_id == report.id)
    ).scalar_one_or_none()
    countries_count = db.execute(
        select(func.count()).select_from(CountrySummary).where(CountrySummary.report_file_id == report.id)
    ).scalar_one()
    alt_count = db.execute(
        select(func.count()).select_from(IssueAltText).where(IssueAltText.report_file_id == report.id)
    ).scalar_one()
    bottom_count = db.execute(
        select(func.count()).select_from(IssueBottom30).where(IssueBottom30.report_file_id == report.id)
    ).scalar_one()

    metrics_rows = db.execute(
        select(CountryMetric.metric_key, CountryMetric.metric_label, func.avg(CountryMetric.value))
        .where(CountryMetric.report_file_id == report.id)
        .group_by(CountryMetric.metric_key, CountryMetric.metric_label)
        .order_by(CountryMetric.metric_key.asc())
    ).all()
    metrics = [OverviewMetric(metric_key=k, metric_label=l, avg_value=v) for (k, l, v) in metrics_rows]

    trend_rows = db.execute(
        select(ReportFile.year, ReportFile.month, func.avg(CountrySummary.total_score))
        .join(CountrySummary, CountrySummary.report_file_id == ReportFile.id)
        .where(ReportFile.report_type == reportType, ReportFile.is_active.is_(True), ReportFile.status == "completed")
        .group_by(ReportFile.year, ReportFile.month)
        .order_by(ReportFile.year.asc(), ReportFile.month.asc())
    ).all()
    trend = [OverviewTrendPoint(year=y, month=m, avg_total_score=v) for (y, m, v) in trend_rows]

    return OverviewResponse(
        report_type=reportType,
        period=Period(year=year, month=month),
        kpis=OverviewKpis(
            avg_total_score=avg_total,
            countries_count=int(countries_count),
            alt_text_errors_count=int(alt_count),
            bottom30_count=int(bottom_count),
        ),
        metrics=metrics,
        trend=trend,
    )


@router.get("/countries/ranking", response_model=RankingResponse)
def country_ranking(
    reportType: str = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    sortKey: str = Query("total_score"),
    sortOrder: str = Query("desc"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> RankingResponse:
    report = _get_active_report(db, reportType, year, month)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    base_query = select(CountrySummary).where(CountrySummary.report_file_id == report.id)
    total = db.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()

    order_desc = sortOrder.lower() != "asc"
    if sortKey == "total_score":
        order_col = CountrySummary.total_score
        query = base_query.order_by(order_col.desc() if order_desc else order_col.asc())
    else:
        metric_key = sortKey
        metric_sub = (
            select(CountryMetric.country, CountryMetric.value)
            .where(CountryMetric.report_file_id == report.id, CountryMetric.metric_key == metric_key)
            .subquery()
        )
        query = (
            select(CountrySummary)
            .join(metric_sub, metric_sub.c.country == CountrySummary.country, isouter=True)
            .where(CountrySummary.report_file_id == report.id)
            .order_by(metric_sub.c.value.desc() if order_desc else metric_sub.c.value.asc())
        )

    rows = db.execute(query.offset((page - 1) * pageSize).limit(pageSize)).scalars().all()
    countries = [r.country for r in rows]

    metrics_for_page = db.execute(
        select(CountryMetric.country, CountryMetric.metric_key, CountryMetric.value)
        .where(CountryMetric.report_file_id == report.id, CountryMetric.country.in_(countries))
    ).all()
    metric_map: dict[str, dict[str, float | None]] = {}
    for country, key, value in metrics_for_page:
        metric_map.setdefault(country, {})[key] = value

    items = [
        CountryRankingRow(
            region=r.region,
            country=r.country,
            total_score=r.total_score,
            rank_current=r.rank_current,
            rank_change=r.rank_change,
            metrics=metric_map.get(r.country, {}),
        )
        for r in rows
    ]

    return RankingResponse(
        report_type=reportType,
        period=Period(year=year, month=month),
        page=page,
        page_size=pageSize,
        total=int(total),
        items=items,
    )


@router.get("/countries/{country}", response_model=CountryDetailResponse)
def country_detail(
    country: str,
    reportType: str = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
) -> CountryDetailResponse:
    report = _get_active_report(db, reportType, year, month)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    summary = db.execute(
        select(CountrySummary).where(CountrySummary.report_file_id == report.id, CountrySummary.country == country)
    ).scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Country not found")

    metrics = db.execute(
        select(CountryMetric.metric_key, CountryMetric.metric_label, CountryMetric.value)
        .where(CountryMetric.report_file_id == report.id, CountryMetric.country == country)
        .order_by(CountryMetric.metric_key.asc())
    ).all()

    alt_count = db.execute(
        select(func.count()).select_from(IssueAltText).where(IssueAltText.report_file_id == report.id, IssueAltText.country == country)
    ).scalar_one()
    bottom_count = db.execute(
        select(func.count()).select_from(IssueBottom30).where(IssueBottom30.report_file_id == report.id, IssueBottom30.country == country)
    ).scalar_one()

    return CountryDetailResponse(
        report_type=reportType,
        period=Period(year=year, month=month),
        country=country,
        region=summary.region,
        total_score=summary.total_score,
        metrics=[{"metric_key": k, "metric_label": l, "value": v} for (k, l, v) in metrics],
        issues={"alt_text": int(alt_count), "bottom30": int(bottom_count)},
    )


@router.get("/issues/alt-text", response_model=IssuesAltTextResponse)
def issues_alt_text(
    reportType: str = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    country: str | None = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> IssuesAltTextResponse:
    report = _get_active_report(db, reportType, year, month)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    q = select(IssueAltText).where(IssueAltText.report_file_id == report.id)
    if country:
        q = q.where(IssueAltText.country == country)

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.offset((page - 1) * pageSize).limit(pageSize)).scalars().all()

    return IssuesAltTextResponse(
        report_type=reportType,
        period=Period(year=year, month=month),
        page=page,
        page_size=pageSize,
        total=int(total),
        items=[
            {
                "id": r.id,
                "country": r.country,
                "url": r.url,
                "card_index": r.card_index,
                "src": r.src,
                "alt_length": r.alt_length,
                "alt_comment": r.alt_comment,
            }
            for r in rows
        ],
    )


@router.get("/issues/bottom30", response_model=IssuesBottom30Response)
def issues_bottom30(
    reportType: str = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    country: str | None = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> IssuesBottom30Response:
    report = _get_active_report(db, reportType, year, month)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    q = select(IssueBottom30).where(IssueBottom30.report_file_id == report.id)
    if country:
        q = q.where(IssueBottom30.country == country)

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.order_by(IssueBottom30.total_score.asc()).offset((page - 1) * pageSize).limit(pageSize)).scalars().all()

    return IssuesBottom30Response(
        report_type=reportType,
        period=Period(year=year, month=month),
        page=page,
        page_size=pageSize,
        total=int(total),
        items=[
            {
                "id": r.id,
                "region": r.region,
                "country": r.country,
                "total_score": r.total_score,
                "rank_prev": r.rank_prev,
                "rank_current": r.rank_current,
                "rank_change": r.rank_change,
            }
            for r in rows
        ],
    )

