# -*- coding: utf-8 -*-
"""파이프라인 설정: DB 연결 및 테이블/컬럼 매핑."""
import os
from pathlib import Path

MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysql.cnxkr.com")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "10080"))
MYSQL_USER = os.environ.get("MYSQL_USER", "lg_ha")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "lg_ha")

TABLE_B2B = "reportbusiness_es_old"
TABLE_B2C = "report_es_old"

COLUMN_ALIAS_B2B = {
    "region": "region",
    "country": "country",
    "scoring_yn": "scoring_yn",
    "title_tag_score": "title_tag_score",
    "description_tag_score": "description_tag_score",
    "h1_tag_score": "h1_tag_score",
    "canonical_link_score": "canonical_link_score",
    "feature_alt_score": "feature_alt_score",
    "total_score": "total_score",
    "year": "year",
    "month": "month",
    "week": "week",
}

COLUMN_ALIAS_B2C = {
    "region": "region",
    "country": "country",
    "division": "division",
    "monitoring": "monitoring",
    "ufn_score": "ufn_score",
    "basic_assets_score": "basic_assets_score",
    "spec_summary_score": "spec_summary_score",
    "faq_score": "faq_score",
    "title_score": "title_score",
    "description_score": "description_score",
    "h1_score": "h1_score",
    "canonical_score": "canonical_score",
    "alt_feature_score": "alt_feature_score",
    "alt_front_score": "alt_front_score",
    "year": "year",
    "month": "month",
    "week": "week",
}

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "pipeline_output"

B2B_SCORE_COLUMNS = [
    "title_tag_score", "description_tag_score", "h1_tag_score",
    "canonical_link_score", "feature_alt_score",
]
B2C_SCORE_COLUMNS = [
    "ufn_score", "basic_assets_score", "spec_summary_score", "faq_score",
    "title_score", "description_score", "h1_score", "canonical_score",
    "alt_feature_score", "alt_front_score",
]
