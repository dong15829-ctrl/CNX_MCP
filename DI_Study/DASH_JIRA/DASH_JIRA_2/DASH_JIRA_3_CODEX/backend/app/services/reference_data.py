from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from ..config import META_DIR


def _simplify_region_label(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return None
    upper = value.upper()
    if "APAC" in upper:
        return "APAC"
    if "EUROPE" in upper or "EU " in upper or "EU\n" in upper or upper.strip() == "EU":
        return "EU"
    if "LA" in upper or "LAT" in upper:
        return "LATAM"
    if "CIS" in upper:
        return "CIS"
    if "AFRICA" in upper:
        return "Africa"
    if "MENA" in upper or "MEA" in upper or "MIDDLE EAST" in upper:
        return "MENA"
    if "CHINA" in upper or "CN" in upper:
        return "China"
    if "GLOBAL" in upper:
        return "Global"
    if "NA" in upper or "NORTH AMERICA" in upper or "AMERIC" in upper:
        return "NA"
    if "SEA" in upper:
        return "SEA"
    return value.strip()


@dataclass
class SiteCodeInfo:
    token: str
    subsidiary: Optional[str]
    country: Optional[str]
    country_code: Optional[str]
    region: Optional[str]
    base_url: Optional[str]
    time_zone: Optional[str]
    currency: Optional[str]


class ReferenceData:
    def __init__(self, meta_dir: Path) -> None:
        self.meta_dir = meta_dir
        self._site_code_map = self._load_site_code_map()
        self._abbreviation_map = self._load_abbreviation_map()

    def _read_csv(self, filename: str) -> Optional[pd.DataFrame]:
        path = self.meta_dir / filename
        if not path.exists():
            return None
        try:
            return pd.read_csv(path)
        except Exception:
            return None

    def _load_site_code_map(self) -> Dict[str, SiteCodeInfo]:
        df = self._read_csv("report_suite_info.csv")
        if df is None:
            return {}

        mapping: Dict[str, SiteCodeInfo] = {}
        records = df.to_dict("records")
        for record in records:
            subsidiary = str(record.get("Subsidiary") or "").strip()
            if not subsidiary:
                continue
            token_key = subsidiary.upper()
            country_code = str(record.get("Country Code (Site Code)") or "").strip()
            country_name = str(record.get("Country") or "").strip()
            region_label = _simplify_region_label(record.get("Region"))
            base_url = str(record.get("Base URL") or "").strip() or None
            time_zone = str(record.get("Time Zone") or "").strip() or None
            currency = str(record.get("Currency Code") or "").strip() or None

            info = SiteCodeInfo(
                token=token_key,
                subsidiary=subsidiary,
                country=country_name or None,
                country_code=country_code.upper() if country_code else None,
                region=region_label,
                base_url=base_url,
                time_zone=time_zone,
                currency=currency,
            )
            mapping[token_key] = info

            # Also map country/site codes so tokens like "NL" can be resolved
            if country_code:
                mapping[country_code.upper()] = info

        return mapping

    def _load_abbreviation_map(self) -> Dict[str, Dict[str, Optional[str]]]:
        df = self._read_csv("abbreviation_dictionary.csv")
        if df is None:
            return {}
        mapping: Dict[str, Dict[str, Optional[str]]] = {}
        for record in df.to_dict("records"):
            token = str(record.get("약어") or "").strip()
            if not token:
                continue
            mapping[token.upper()] = {
                "definition": str(record.get("풀이") or "").strip() or None,
                "scope": str(record.get("삼성닷컴/CNX") or "").strip() or None,
                "example": str(record.get("예시") or "").strip() or None,
            }
        return mapping

    def resolve_site_code(self, token: Optional[str]) -> Optional[SiteCodeInfo]:
        if not token:
            return None
        return self._site_code_map.get(token.strip().upper())

    def describe_abbreviation(self, token: Optional[str]) -> Optional[Dict[str, Optional[str]]]:
        if not token:
            return None
        return self._abbreviation_map.get(token.strip().upper())


reference_data = ReferenceData(META_DIR)
