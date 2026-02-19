from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..config import (
    CLOSED_STATUS_MARKERS,
    DATA_FILE,
    DEFAULT_TIME_WINDOW_DAYS,
    HIGH_PRIORITY_MARKERS,
    TOP_LIMIT,
)
from .reference_data import reference_data


def _normalize_string(value: Any) -> Optional[str]:
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return None


def _coalesce(df: pd.DataFrame, columns: List[str]) -> pd.Series:
    valid_cols = [col for col in columns if col in df.columns]
    if not valid_cols:
        return pd.Series([None] * len(df), index=df.index)
    filled = df[valid_cols].replace(r"^\s*$", pd.NA, regex=True).bfill(axis=1)
    return filled.iloc[:, 0]


RAW_DATA_COLUMNS = [
    "Issue key",
    "Issue id",
    "Summary",
    "Issue Type",
    "Status",
    "Priority",
    "Resolution",
    "Assignee",
    "Reporter",
    "Creator",
    "Created",
    "Updated",
    "Resolved",
    "Description",
    "Custom field (Ads Region)",
    "Custom field (Project Region)",
    "Custom field (Region-ES2)",
    "Custom field (Country-ES1)",
    "Custom field (Country-ES2)",
    "Custom field (Country (AEME Only))",
    "Custom field (Category)",
    "Custom field (Category & Subcategory)",
    "Custom field (Request Type)",
    "Custom field (Cause)",
    "Custom field (Root cause)",
    "Custom field (Cause and Action)",
    "Custom field (Urgency)",
]

COLUMN_RENAMES = {
    "Issue key": "issue_key",
    "Issue id": "issue_id",
    "Summary": "summary",
    "Issue Type": "issue_type",
    "Status": "status",
    "Priority": "priority",
    "Resolution": "resolution",
    "Assignee": "assignee",
    "Reporter": "reporter",
    "Creator": "creator",
    "Created": "created_at",
    "Updated": "updated_at",
    "Resolved": "resolved_at",
    "Description": "description",
    "Custom field (Ads Region)": "ads_region",
    "Custom field (Project Region)": "project_region",
    "Custom field (Region-ES2)": "region_es2",
    "Custom field (Country-ES1)": "country_es1",
    "Custom field (Country-ES2)": "country_es2",
    "Custom field (Country (AEME Only))": "country_aeme",
    "Custom field (Category)": "category_raw",
    "Custom field (Category & Subcategory)": "category_sub",
    "Custom field (Request Type)": "request_type",
    "Custom field (Cause)": "cause",
    "Custom field (Root cause)": "root_cause",
    "Custom field (Cause and Action)": "cause_and_action",
    "Custom field (Urgency)": "urgency_raw",
}

PLACEHOLDER_VALUES = {"none", "none: null", "null", "-", "n/a", "tbd"}

REGION_TOKEN_MAP = {
    "NA": "NA",
    "NAM": "NA",
    "NAR": "NA",
    "NORAM": "NA",
    "NALA": "NA",
    "AMER": "NA",
    "AMERICAS": "NA",
    "US": "NA",
    "USA": "NA",
    "CA": "NA",
    "EU": "EU",
    "EMEA": "EMEA",
    "MEA": "MENA",
    "MENA": "MENA",
    "APAC": "APAC",
    "APJ": "APAC",
    "AP": "APAC",
    "SEA": "SEA",
    "AUNZ": "APAC",
    "ANZ": "APAC",
    "ASEAN": "SEA",
    "LAT": "LATAM",
    "LATAM": "LATAM",
    "SAM": "LATAM",
    "LAM": "LATAM",
    "GLOBAL": "Global",
    "WW": "Global",
    "ROW": "Global",
    "WL": "Global",
    "HQ": "Global",
    "OC": "APAC",
    "KOR": "KR",
    "KSA": "MENA",
    "AF": "Africa",
    "AFRICA": "Africa",
}

REGION_COUNTRY_GROUPS = {
    "NA": {"US", "CA"},
    "LATAM": {
        "AR",
        "BR",
        "CL",
        "CO",
        "CR",
        "DO",
        "EC",
        "GT",
        "HN",
        "MX",
        "NI",
        "PA",
        "PE",
        "PR",
        "PY",
        "SV",
        "UY",
        "VE",
    },
    "EU": {
        "AL",
        "AT",
        "BE",
        "BG",
        "CH",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GB",
        "GR",
        "HR",
        "HU",
        "IE",
        "IS",
        "IT",
        "LT",
        "LU",
        "LV",
        "MT",
        "NL",
        "NO",
        "PL",
        "PT",
        "RO",
        "RU",
        "SE",
        "SI",
        "SK",
        "UA",
        "UK",
    },
    "APAC": {
        "AU",
        "BD",
        "CN",
        "HK",
        "ID",
        "IN",
        "JP",
        "KR",
        "KZ",
        "MY",
        "NZ",
        "PH",
        "PK",
        "SG",
        "TH",
        "TW",
        "VN",
        "UZ",
        "SB",
    },
    "MENA": {
        "AE",
        "BH",
        "DZ",
        "EG",
        "IQ",
        "JO",
        "KW",
        "LB",
        "IL",
        "MA",
        "OM",
        "QA",
        "SA",
        "TN",
        "TR",
        "YE",
        "PS",
    },
    "AFRICA": {
        "GA",
        "KE",
        "NG",
        "ZA",
        "TZ",
        "UG",
        "CM",
        "GH",
        "SN",
        "ZW",
        "RW",
        "BW",
        "MW",
        "MZ",
    },
}

COUNTRY_TO_REGION = {
    country: region for region, countries in REGION_COUNTRY_GROUPS.items() for country in countries
}

COUNTRY_NAME_TO_CODE = {
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "USA": "US",
    "CANADA": "CA",
    "MEXICO": "MX",
    "ARGENTINA": "AR",
    "BRAZIL": "BR",
    "CHILE": "CL",
    "COLOMBIA": "CO",
    "PERU": "PE",
    "URUGUAY": "UY",
    "PARAGUAY": "PY",
    "SPAIN": "ES",
    "FRANCE": "FR",
    "GERMANY": "DE",
    "ITALY": "IT",
    "UNITED KINGDOM": "UK",
    "GREAT BRITAIN": "UK",
    "ENGLAND": "UK",
    "SCOTLAND": "UK",
    "WALES": "UK",
    "POLAND": "PL",
    "PORTUGAL": "PT",
    "NETHERLANDS": "NL",
    "BELGIUM": "BE",
    "SWEDEN": "SE",
    "NORWAY": "NO",
    "DENMARK": "DK",
    "FINLAND": "FI",
    "IRELAND": "IE",
    "ROMANIA": "RO",
    "BULGARIA": "BG",
    "HUNGARY": "HU",
    "GREECE": "GR",
    "CZECH REPUBLIC": "CZ",
    "SLOVAKIA": "SK",
    "SWITZERLAND": "CH",
    "AUSTRIA": "AT",
    "TURKEY": "TR",
    "RUSSIA": "RU",
    "UKRAINE": "UA",
    "ISRAEL": "IL",
    "SINGAPORE": "SG",
    "INDIA": "IN",
    "INDONESIA": "ID",
    "VIETNAM": "VN",
    "THAILAND": "TH",
    "MALAYSIA": "MY",
    "PHILIPPINES": "PH",
    "HONG KONG": "HK",
    "TAIWAN": "TW",
    "SOUTH KOREA": "KR",
    "KOREA": "KR",
    "JAPAN": "JP",
    "CHINA": "CN",
    "AUSTRALIA": "AU",
    "NEW ZEALAND": "NZ",
    "UAE": "AE",
    "UNITED ARAB EMIRATES": "AE",
    "SAUDI ARABIA": "SA",
    "KINGDOM OF SAUDI ARABIA": "SA",
    "QATAR": "QA",
    "EGYPT": "EG",
    "MOROCCO": "MA",
    "TUNISIA": "TN",
    "OMAN": "OM",
    "BAHRAIN": "BH",
    "LEBANON": "LB",
    "JORDAN": "JO",
    "KUWAIT": "KW",
    "PALESTINE": "PS",
    "SOUTH AFRICA": "ZA",
    "KENYA": "KE",
    "NIGERIA": "NG",
    "TANZANIA": "TZ",
    "UGANDA": "UG",
    "GHANA": "GH",
    "SENEGAL": "SN",
    "CAMEROON": "CM",
    "BOTSWANA": "BW",
    "RWANDA": "RW",
    "MALAWI": "MW",
    "MOZAMBIQUE": "MZ",
    "ZIMBABWE": "ZW",
    "GABON": "GA",
}

COUNTRY_TOKEN_MAP = {
    code: code for code in COUNTRY_TO_REGION.keys()
}
COUNTRY_TOKEN_MAP.update(
    {
        "US": "US",
        "USA": "US",
        "UK": "UK",
        "GB": "UK",
        "UAE": "AE",
        "KSA": "SA",
        "SAU": "SA",
        "KO": "KR",
        "KR": "KR",
        "KOR": "KR",
        "CN": "CN",
        "CHN": "CN",
        "KU": "KW",
        "KW": "KW",
    }
)

TOKEN_PATTERN = re.compile(r"[\[(]([A-Za-z0-9_\\-\\/]{2,20})[\])]")


def _normalize_placeholder(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in PLACEHOLDER_VALUES:
        return None
    return value


def _normalize_region_label(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    token = value.strip().upper()
    if not token:
        return None
    return REGION_TOKEN_MAP.get(token, token)


def _normalize_country_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = value.strip().upper()
    token = re.sub(r"[^A-Za-z]", "", raw)
    if not token:
        return None
    name_mapped = COUNTRY_NAME_TO_CODE.get(raw) or COUNTRY_NAME_TO_CODE.get(token)
    if name_mapped:
        token = name_mapped
    token = COUNTRY_TOKEN_MAP.get(token, token)
    if token in COUNTRY_TO_REGION:
        return token
    return None


def _finalize_country_code(value: Optional[str]) -> Optional[str]:
    normalized = _normalize_country_code(value)
    if normalized:
        return normalized
    if not value:
        return None
    token = re.sub(r"[^A-Za-z]", "", str(value)).upper()
    return token or None


def _extract_tokens(*texts: Optional[str]) -> List[str]:
    tokens: List[str] = []
    for text in texts:
        if not text:
            continue
        for raw in TOKEN_PATTERN.findall(text):
            parts = re.split(r"[^A-Za-z0-9]+", raw)
            tokens.extend(
                part.upper()
                for part in parts
                if part and 2 <= len(part) <= 5
            )
    return tokens


def _resolve_country_from_site(info) -> Optional[str]:
    if info is None:
        return None
    if getattr(info, "country_code", None):
        country_code = info.country_code.upper()
        normalized = _normalize_country_code(country_code)
        return normalized or country_code
    if getattr(info, "country", None):
        return _normalize_country_code(info.country)
    return None


def _resolve_region_from_site(info) -> Optional[str]:
    if info is None:
        return None
    if getattr(info, "region", None):
        normalized = _normalize_region_label(info.region)
        if normalized:
            return normalized
    country = _resolve_country_from_site(info)
    if country:
        return COUNTRY_TO_REGION.get(country)
    return None

CATEGORY_KEYWORDS = {
    "Tagging Request": [
        "tag",
        "pixel",
        "tracking",
        "gtm",
        "analytics",
        "lc request",
    ],
    "Data Discrepancy": [
        "discrep",
        "mismatch",
        "difference",
        "gap",
        "variance",
    ],
    "Access Request": [
        "access",
        "permission",
        "enable",
        "account",
        "credential",
        "token",
    ],
    "Bug Report": [
        "bug",
        "error",
        "fail",
        "incorrect",
        "not working",
        "issue",
    ],
    "Feature Request": [
        "feature",
        "enhancement",
        "improvement",
        "new report",
        "dashboard",
        "support request",
    ],
}

ACTION_BY_CATEGORY = {
    "Tagging Request": "Configuration Change",
    "Data Discrepancy": "Investigation",
    "Access Request": "Access Provisioning",
    "Bug Report": "Code Fix",
    "Feature Request": "Solution Design",
}

TEAM_BY_REGION = {
    "na": "Ops Team NA",
    "us": "Ops Team NA",
    "ca": "Ops Team NA",
    "eu": "Ops Team EU",
    "uk": "Ops Team EU",
    "fr": "Ops Team EU",
    "de": "Ops Team EU",
    "apac": "Ops Team APAC",
    "sea": "Ops Team APAC",
    "kr": "Ops Team KR",
    "mena": "Ops Team MENA",
}


@dataclass
class IssueSummary:
    issue_key: str
    summary: str
    status: str
    priority: Optional[str]
    issue_type: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    region: Optional[str]
    country: Optional[str]
    category: Optional[str]
    is_closed: bool
    is_high_priority: bool


class JiraDataRepository:
    """Loads the Jira CSV once and exposes handy analytics helpers."""

    def __init__(self, data_path: Path | str = DATA_FILE) -> None:
        self.data_path = Path(data_path)
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.data_path}")
        self._df = self._load_dataframe()
        self._analysis_engine = None

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    def attach_analysis_engine(self, engine) -> None:
        self._analysis_engine = engine

    def get_issue_analysis(self, issue_key: str, refresh: bool = False) -> Dict[str, Any]:
        if not self._analysis_engine:
            raise KeyError("analysis engine not ready")
        return self._analysis_engine.get_issue_analysis(issue_key, refresh=refresh)

    # ------------------------------------------------------------------
    # Data loading helpers
    # ------------------------------------------------------------------
    def _load_dataframe(self) -> pd.DataFrame:
        return self._load_and_prepare(self.data_path)

    @classmethod
    def load_dataset(cls, path: Path) -> pd.DataFrame:
        return cls._load_and_prepare(path).copy()

    @classmethod
    def _load_and_prepare(cls, path: Path) -> pd.DataFrame:
        available_columns = pd.read_csv(path, nrows=0).columns.tolist()
        usecols = [col for col in RAW_DATA_COLUMNS if col in available_columns]
        df = pd.read_csv(path, usecols=usecols)
        rename_map = {k: v for k, v in COLUMN_RENAMES.items() if k in df.columns}
        df = df.rename(columns=rename_map)

        df = df.dropna(subset=["issue_key"])
        df = df.replace({pd.NA: None})

        if "issue_id" not in df.columns:
            df["issue_id"] = None

        for date_col in ["created_at", "updated_at", "resolved_at"]:
            if date_col in df.columns:
                df[date_col] = cls._parse_datetime(df[date_col])

        df["created_date"] = df["created_at"].dt.date
        df["updated_date"] = df["updated_at"].dt.date

        df["region"] = (
            _coalesce(df, ["ads_region", "project_region", "region_es2"])
            .apply(_normalize_string)
            .apply(_normalize_placeholder)
            .apply(_normalize_region_label)
        )
        df["country"] = (
            _coalesce(df, ["country_es1", "country_es2", "country_aeme"])
            .apply(_normalize_string)
            .apply(_normalize_placeholder)
            .apply(_normalize_country_code)
        )
        df["category"] = _coalesce(
            df, ["category_raw", "category_sub", "request_type"]
        ).apply(_normalize_string)
        df["root_cause"] = _coalesce(df, ["root_cause", "cause"]).apply(
            _normalize_string
        )

        df["country"] = df.apply(
            lambda row: cls._resolve_country_value(
                row.get("country"), row.get("summary"), row.get("description")
            ),
            axis=1,
        )
        df["region"] = df.apply(
            lambda row: cls._resolve_region_value(
                row.get("region"),
                row.get("country"),
                row.get("summary"),
                row.get("description"),
            ),
            axis=1,
        )

        df["status"] = df["status"].fillna("Unknown")
        df["priority"] = df["priority"].fillna("Unspecified")

        df["is_closed"] = df["status"].str.lower().apply(cls._is_closed_status)
        df["is_high_priority"] = df["priority"].str.lower().apply(cls._is_high_priority)

        if "created_at" in df.columns:
            now = pd.Timestamp.utcnow().tz_localize(None)
            df["age_days"] = (now - df["created_at"]).dt.days

        if "resolved_at" in df.columns:
            df["resolution_hours"] = (
                (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600
            )

        df["status_bucket"] = df["is_closed"].map({True: "Closed", False: "Open"})

        return df

    @staticmethod
    def _is_closed_status(status: str) -> bool:
        status = status or ""
        lowered = status.lower()
        return any(marker in lowered for marker in CLOSED_STATUS_MARKERS)

    @staticmethod
    def _is_high_priority(priority: str) -> bool:
        priority = priority or ""
        lowered = priority.lower()
        return any(marker in lowered for marker in HIGH_PRIORITY_MARKERS)

    @staticmethod
    def _parse_datetime(series: pd.Series) -> pd.Series:
        primary = pd.to_datetime(series, format="%d/%b/%y %I:%M %p", errors="coerce")
        fallback_mask = primary.isna() & series.notna()
        if fallback_mask.any():
            primary.loc[fallback_mask] = pd.to_datetime(
                series.loc[fallback_mask], errors="coerce"
            )
        return primary.dt.tz_localize(None)

    @staticmethod
    def _coerce_datetime_value(value: Any) -> Optional[pd.Timestamp]:
        if value is None or value == "":
            return None
        if isinstance(value, pd.Timestamp):
            ts = value
        elif isinstance(value, datetime):
            ts = pd.Timestamp(value)
        else:
            ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return None
        if ts.tzinfo is not None:
            try:
                ts = ts.tz_convert(None)
            except TypeError:
                ts = ts.tz_localize(None)
        return ts

    def _prepare_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = record.copy()
        normalized["issue_key"] = record.get("issue_key")
        if not normalized["issue_key"]:
            raise ValueError("issue_key is required for ingestion")

        normalized["status"] = record.get("status") or "Unknown"
        normalized["priority"] = record.get("priority") or "Unspecified"
        normalized["region"] = _normalize_region_label(
            _normalize_placeholder(_normalize_string(record.get("region")))
        )
        normalized["country"] = _finalize_country_code(
            _normalize_placeholder(_normalize_string(record.get("country")))
        )
        normalized["category"] = _normalize_string(
            record.get("category")
            or record.get("category_sub")
            or record.get("request_type")
        )
        normalized["root_cause"] = _normalize_string(
            record.get("root_cause") or record.get("cause")
        )
        normalized["cause"] = _normalize_string(record.get("cause"))
        normalized["urgency_raw"] = _normalize_string(
            record.get("urgency_raw") or record.get("urgency")
        )

        summary = record.get("summary")
        description = record.get("description")

        normalized["country"] = self._resolve_country_value(
            normalized.get("country"), summary, description
        )

        normalized["region"] = self._resolve_region_value(
            normalized.get("region"),
            normalized.get("country"),
            summary,
            description,
        )

        for date_col in ["created_at", "updated_at", "resolved_at"]:
            ts = self._coerce_datetime_value(record.get(date_col))
            if ts is not None:
                ts = pd.Timestamp(ts).tz_localize(None)
            normalized[date_col] = ts

        normalized["created_date"] = (
            normalized["created_at"].date() if normalized.get("created_at") else None
        )
        normalized["updated_date"] = (
            normalized["updated_at"].date() if normalized.get("updated_at") else None
        )

        normalized["is_closed"] = self._is_closed_status(normalized["status"])
        normalized["is_high_priority"] = self._is_high_priority(normalized["priority"])
        normalized["status_bucket"] = (
            "Closed" if normalized["is_closed"] else "Open"
        )

        now = pd.Timestamp.utcnow().tz_localize(None)
        created_at = normalized.get("created_at")
        resolved_at = normalized.get("resolved_at")

        if created_at is not None:
            normalized["age_days"] = int((now - created_at).days)
        else:
            normalized["age_days"] = None

        if created_at is not None and resolved_at is not None:
            delta = resolved_at - created_at
            normalized["resolution_hours"] = delta.total_seconds() / 3600
        else:
            normalized["resolution_hours"] = None

        return normalized

    # ------------------------------------------------------------------
    # Mutation helpers (webhook ingestion)
    # ------------------------------------------------------------------
    def upsert_issue(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._prepare_record(record)
        # Ensure dataframe has all required columns
        for column in normalized.keys():
            if column not in self._df.columns:
                self._df[column] = None

        new_row = pd.DataFrame([normalized])
        self._df = (
            pd.concat([self._df, new_row], ignore_index=True)
            .drop_duplicates(subset=["issue_key"], keep="last")
            .reset_index(drop=True)
        )
        return normalized

    # ------------------------------------------------------------------
    # Analytics surfaced to the API layer
    # ------------------------------------------------------------------
    def get_summary(self) -> Dict[str, Any]:
        df = self._df
        total = len(df)
        open_issues = int((~df["is_closed"]).sum())
        closed_issues = int(df["is_closed"].sum())
        high_priority_open = int((~df["is_closed"] & df["is_high_priority"]).sum())
        avg_resolution = (
            float(df["resolution_hours"].dropna().mean())
            if "resolution_hours" in df
            else 0.0
        )
        latest_update = (
            df["updated_at"].max().isoformat() if "updated_at" in df else None
        )

        return {
            "total_issues": total,
            "open_issues": open_issues,
            "closed_issues": closed_issues,
            "high_priority_open": high_priority_open,
            "avg_resolution_hours": round(avg_resolution, 2) if avg_resolution else None,
            "last_updated": latest_update,
        }

    def get_status_distribution(self, top_n: int = TOP_LIMIT) -> List[Dict[str, Any]]:
        counts = self._df["status"].value_counts().head(top_n)
        return [
            {"status": status, "count": int(count)}
            for status, count in counts.items()
        ]

    def get_priority_distribution(self) -> List[Dict[str, Any]]:
        counts = self._df["priority"].value_counts()
        return [
            {"priority": priority, "count": int(count)}
            for priority, count in counts.items()
        ]

    def get_region_distribution(self, top_n: int = TOP_LIMIT) -> List[Dict[str, Any]]:
        series = self._df["region"].fillna("Unspecified")
        counts = series.value_counts().head(top_n)
        return [
            {"region": region, "count": int(count)} for region, count in counts.items()
        ]

    def get_category_distribution(self, top_n: int = TOP_LIMIT) -> List[Dict[str, Any]]:
        if "category" not in self._df:
            return []
        series = self._df["category"].fillna("Unspecified")
        counts = series.value_counts().head(top_n)
        return [
            {"category": category, "count": int(count)}
            for category, count in counts.items()
        ]

    def get_time_series(self, days: int = DEFAULT_TIME_WINDOW_DAYS, granularity: str = "day") -> List[Dict[str, Any]]:
        df = self._df.dropna(subset=["created_at"]).copy()
        if df.empty:
            return []
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        cutoff = pd.Timestamp.utcnow().tz_localize(None) - timedelta(days=days - 1)
        window_df = df[df["created_at"] >= cutoff]
        if window_df.empty:
            window_df = df.tail(days)

        granularity = (granularity or "day").lower()
        if granularity not in {"day", "week", "month", "year"}:
            granularity = "day"

        window_df["bucket_start"] = self._compute_bucket_start(window_df["created_at"], granularity)

        series = (
            window_df.groupby("bucket_start")
            .agg(
                total=("issue_key", "count"),
                closed=("is_closed", "sum"),
                high_priority=("is_high_priority", "sum"),
            )
            .reset_index()
        )

        series = series.rename(columns={"bucket_start": "date"})
        series = series.sort_values(by="date")
        series["date"] = series["date"].apply(lambda d: d.isoformat())
        series["label"] = series["date"].apply(
            lambda value: self._format_bucket_label(value, granularity)
        )
        series["open"] = series["total"] - series["closed"]
        series["granularity"] = granularity

        return series.to_dict(orient="records")

    @staticmethod
    def _compute_bucket_start(series: pd.Series, granularity: str) -> pd.Series:
        if granularity == "day":
            return series.dt.floor("D").dt.date
        if granularity == "week":
            return series.dt.to_period("W").dt.start_time.dt.date
        if granularity == "month":
            return series.dt.to_period("M").dt.start_time.dt.date
        if granularity == "year":
            return series.dt.to_period("Y").dt.start_time.dt.date
        return series.dt.floor("D").dt.date

    @staticmethod
    def _format_bucket_label(value: str, granularity: str) -> str:
        try:
            base = pd.Timestamp(value)
        except Exception:
            return value
        if granularity == "day":
            return base.strftime("%m/%d")
        if granularity == "week":
            end = base + timedelta(days=6)
            return f"{base.strftime('%Y-%m-%d')} ~ {end.strftime('%m-%d')}"
        if granularity == "month":
            return base.strftime("%Y-%m")
        if granularity == "year":
            return base.strftime("%Y")
        return base.strftime("%m/%d")

    # ------------------------------------------------------------------
    # Issue level helpers
    # ------------------------------------------------------------------
    def search_issues(
        self,
        status: Optional[List[str]] = None,
        priority: Optional[List[str]] = None,
        region: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        text: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        df = self._df
        filtered = df

        if status:
            lowered = [s.lower() for s in status]
            filtered = filtered[filtered["status"].str.lower().isin(lowered)]
        if priority:
            lowered = [p.lower() for p in priority]
            filtered = filtered[filtered["priority"].str.lower().isin(lowered)]
        if region:
            lowered = [r.lower() for r in region]
            filtered = filtered[filtered["region"].fillna("").str.lower().isin(lowered)]
        if category:
            lowered = [c.lower() for c in category]
            filtered = filtered[
                filtered["category"].fillna("").str.lower().isin(lowered)
            ]
        if text:
            filtered = filtered[
                filtered["summary"]
                .fillna("")
                .str.contains(text, case=False, regex=False)
                | filtered["description"]
                .fillna("")
                .str.contains(text, case=False, regex=False)
            ]

        total = len(filtered)
        sort_by = sort_by if sort_by in filtered.columns else "created_at"
        ascending = sort_order == "asc"
        filtered = filtered.sort_values(by=sort_by, ascending=ascending)

        start = (page - 1) * page_size
        end = start + page_size
        page_df = filtered.iloc[start:end]

        items = [
            {
                "issue_key": row.issue_key,
                "summary": row.summary,
                "status": row.status,
                "priority": row.priority,
                "issue_type": row.issue_type,
                "created_at": row.created_at.isoformat()
                if pd.notna(row.created_at)
                else None,
                "updated_at": row.updated_at.isoformat()
                if pd.notna(row.updated_at)
                else None,
                "region": row.region,
                "country": row.country,
                "category": row.category,
                "is_closed": bool(row.is_closed),
                "is_high_priority": bool(row.is_high_priority),
            }
            for row in page_df.itertuples()
        ]

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def get_issue_detail(self, issue_key: str) -> Dict[str, Any]:
        record = self._get_issue_row(issue_key)
        return {
            "issue_key": record["issue_key"],
            "summary": record.get("summary"),
            "status": record.get("status"),
            "priority": record.get("priority"),
            "issue_type": record.get("issue_type"),
            "assignee": record.get("assignee"),
            "reporter": record.get("reporter"),
            "creator": record.get("creator"),
            "created_at": record["created_at"].isoformat()
            if pd.notna(record["created_at"])
            else None,
            "updated_at": record["updated_at"].isoformat()
            if pd.notna(record["updated_at"])
            else None,
            "resolved_at": (
                record["resolved_at"].isoformat()
                if pd.notna(record["resolved_at"])
                else None
            ),
            "region": record.get("region"),
            "country": record.get("country"),
            "category": record.get("category"),
            "root_cause": record.get("root_cause"),
            "description": record.get("description"),
            "resolution": record.get("resolution"),
            "is_closed": bool(record.get("is_closed")),
            "is_high_priority": bool(record.get("is_high_priority")),
            "age_days": int(record["age_days"]) if pd.notna(record["age_days"]) else None,
            "resolution_hours": (
                float(record["resolution_hours"])
                if pd.notna(record["resolution_hours"])
                else None
            ),
            "reference_context": self._build_reference_context(
                record.get("summary"), record.get("description")
            ),
        }

    def get_taxonomy(self, issue_key: str) -> Dict[str, Any]:
        record = self._get_issue_row(issue_key)
        summary = (record.get("summary") or "").strip()
        description = (record.get("description") or "").strip()
        category, confidence = self._classify_category(
            summary, description, record.get("category"), record.get("issue_type")
        )
        urgency = self._classify_urgency(
            record.get("priority"), record.get("urgency_raw")
        )
        root_cause = (
            record.get("root_cause") or record.get("cause") or "Pending analysis"
        )
        required_action = ACTION_BY_CATEGORY.get(category, "Investigation")
        suggested_team = self._suggest_team(record.get("region"), category)
        timeline = self._build_timeline(record, required_action)
        processing_state = "Resolved" if record.get("is_closed") else record.get("status")

        return {
            "issue_key": issue_key,
            "summary": summary,
            "category": category,
            "confidence": round(confidence, 2),
            "urgency": urgency,
            "root_cause": root_cause,
            "required_action": required_action,
            "suggested_team": suggested_team,
            "processing_state": processing_state,
            "tags": [
                tag for tag in [category, record.get("region"), record.get("priority")] if tag
            ],
            "timeline": timeline,
        }

    def _get_issue_row(self, issue_key: str) -> pd.Series:
        df = self._df
        row = df[df["issue_key"] == issue_key].head(1)
        if row.empty:
            raise KeyError(f"Issue {issue_key} not found")
        return row.iloc[0]

    @staticmethod
    def _classify_category(
        summary: str,
        description: str,
        existing_category: Optional[str],
        issue_type: Optional[str],
    ) -> tuple[str, float]:
        text = f"{summary} {description}".lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category, 0.9
        if existing_category:
            return existing_category, 0.7
        if issue_type:
            return issue_type, 0.6
        return "Operations", 0.4

    @staticmethod
    def _classify_urgency(priority: Optional[str], raw: Optional[str]) -> str:
        if raw:
            return raw
        priority_value = (priority or "").lower()
        if any(marker in priority_value for marker in ["highest", "high", "critical", "p1"]):
            return "High"
        if "medium" in priority_value or "normal" in priority_value:
            return "Medium"
        if priority_value:
            return priority
        return "Low"

    @staticmethod
    def _suggest_team(region: Optional[str], category: str) -> str:
        region_key = (region or "").lower()
        for key, team in TEAM_BY_REGION.items():
            if key in region_key:
                return team
        if category == "Access Request":
            return "Identity/Ops Control Tower"
        if category == "Feature Request":
            return "Product Ops"
        return "Global Ops"

    def _build_timeline(
        self, record: pd.Series, required_action: str
    ) -> List[Dict[str, Any]]:
        timeline: List[Dict[str, Any]] = []
        created_at = record.get("created_at")
        updated_at = record.get("updated_at")
        resolved_at = record.get("resolved_at")
        status = record.get("status")
        resolution = record.get("resolution")

        if pd.notna(created_at):
            timeline.append(
                {
                    "stage": "Created",
                    "status": "Received",
                    "timestamp": created_at.isoformat(),
                    "detail": "티켓이 생성되었습니다.",
                }
            )
        if (
            pd.notna(updated_at)
            and pd.notna(created_at)
            and updated_at > created_at
        ):
            timeline.append(
                {
                    "stage": "Last Update",
                    "status": status,
                    "timestamp": updated_at.isoformat(),
                    "detail": "상태가 업데이트되었습니다.",
                }
            )
        if record.get("is_closed") and pd.notna(resolved_at):
            timeline.append(
                {
                    "stage": "Resolved",
                    "status": resolution or "Resolved",
                    "timestamp": resolved_at.isoformat(),
                    "detail": "티켓이 종결되었습니다.",
                }
            )
        else:
            timeline.append(
                {
                    "stage": "Next Action",
                    "status": "Planned",
                    "timestamp": None,
                    "detail": required_action,
                }
            )
        return timeline

    def _build_reference_context(
        self, summary: Optional[str], description: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        tokens = list(dict.fromkeys(_extract_tokens(summary, description)))
        if not tokens:
            return None

        site_refs: List[Dict[str, Any]] = []
        abbreviation_refs: List[Dict[str, Any]] = []

        for token in tokens:
            site_info = reference_data.resolve_site_code(token)
            if site_info:
                country_code = _resolve_country_from_site(site_info)
                site_refs.append(
                    {
                        "token": token,
                        "subsidiary": site_info.subsidiary,
                        "region": _resolve_region_from_site(site_info),
                        "country": site_info.country,
                        "country_code": country_code,
                        "base_url": site_info.base_url,
                        "time_zone": site_info.time_zone,
                        "currency": site_info.currency,
                    }
                )

            abbreviation = reference_data.describe_abbreviation(token)
            if abbreviation and any(abbreviation.values()):
                abbreviation_refs.append(
                    {
                        "token": token,
                        "definition": abbreviation.get("definition"),
                        "scope": abbreviation.get("scope"),
                        "example": abbreviation.get("example"),
                    }
                )

        if not site_refs and not abbreviation_refs:
            return None

        return {
            "site_codes": site_refs or None,
            "abbreviations": abbreviation_refs or None,
        }

    @classmethod
    def _resolve_region_value(
        cls,
        current_region: Optional[str],
        country: Optional[str],
        summary: Optional[str],
        description: Optional[str],
    ) -> Optional[str]:
        normalized_current = _normalize_region_label(current_region)
        inferred = cls._infer_region_from_text(summary, description) or cls._infer_region_from_country(country)
        if not normalized_current:
            return inferred

        placeholder_values = {"", "UNSPECIFIED", "UNKNOWN", "NONE", "N/A"}
        upper_current = normalized_current.upper()
        if upper_current in placeholder_values:
            return inferred or normalized_current
        if upper_current == "NA" and country not in {"US", "CA"}:
            return inferred or normalized_current
        return normalized_current

    @classmethod
    def _resolve_country_value(
        cls,
        current_country: Optional[str],
        summary: Optional[str],
        description: Optional[str],
    ) -> Optional[str]:
        normalized_current = _finalize_country_code(current_country)
        inferred = _finalize_country_code(
            cls._infer_country_from_text(summary, description)
        )
        if normalized_current and len(normalized_current) == 2:
            return normalized_current
        return inferred or normalized_current

    @staticmethod
    def _infer_region_from_text(summary: Optional[str], description: Optional[str]) -> Optional[str]:
        tokens = _extract_tokens(summary, description)
        for token in tokens:
            mapped = REGION_TOKEN_MAP.get(token)
            if mapped:
                return mapped
        for token in tokens:
            site_info = reference_data.resolve_site_code(token)
            region = _resolve_region_from_site(site_info)
            if region:
                return region
        for token in tokens:
            canonical = COUNTRY_TOKEN_MAP.get(token, token)
            region = COUNTRY_TO_REGION.get(canonical)
            if region:
                return region
        return None

    @staticmethod
    def _infer_country_from_text(summary: Optional[str], description: Optional[str]) -> Optional[str]:
        tokens = _extract_tokens(summary, description)
        for token in tokens:
            mapped = COUNTRY_TOKEN_MAP.get(token)
            if mapped:
                return mapped
        for token in tokens:
            site_info = reference_data.resolve_site_code(token)
            country = _resolve_country_from_site(site_info)
            if country:
                return country
        return None

    @staticmethod
    def _infer_region_from_country(country: Optional[str]) -> Optional[str]:
        if not country:
            return None
        normalized = _normalize_country_code(country)
        if not normalized:
            return None
        return COUNTRY_TO_REGION.get(normalized)


repository = JiraDataRepository()

try:
    from .analysis_pipeline import AnalysisPipeline

    analysis_pipeline = AnalysisPipeline(repository)
    repository.attach_analysis_engine(analysis_pipeline)
except Exception as exc:  # pragma: no cover - graceful degradation
    analysis_pipeline = None
    logger = logging.getLogger(__name__)
    logger.error("분석 파이프라인 초기화 실패: %s", exc)
