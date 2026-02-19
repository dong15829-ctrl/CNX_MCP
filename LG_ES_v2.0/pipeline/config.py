# -*- coding: utf-8 -*-
"""파이프라인 설정: DB 연결 및 테이블/컬럼 매핑."""
import os
from pathlib import Path

MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysql.cnxkr.com")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "10080"))
MYSQL_USER = os.environ.get("MYSQL_USER", "lg_ha")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "lg_ha")

TABLE_B2B = "reportbusiness_es_old_v2"
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

# DB/엑셀에서 올 수 있는 여러 컬럼명 → 표준명 매핑 (SUMMARY 정확히 맞추기 위함)
# reportbusiness_es_old_v2 실제: scoring, h1_tag_pf, canonical_link_pf, feature_cards
B2B_POSSIBLE_COLUMN_NAMES = {
    "region": ["region", "Region", "REGION"],
    "country": ["country", "Country", "COUNTRY"],
    "scoring_yn": ["scoring_yn", "scoring", "Scoring Y/N", "Scoring_Y_N", "scoring y/n"],
    "title_tag_score": ["title_tag_score", "Title Tag Score", "title tag score", "TitleTagScore"],
    "description_tag_score": ["description_tag_score", "Description Tag Score", "description tag score"],
    "h1_tag_score": ["h1_tag_score", "H1 Tag Score", "h1 tag score", "H1TagScore", "h1_tag_pf"],
    "canonical_link_score": ["canonical_link_score", "Canonical Link Score", "canonical link score", "canonical_link_pf"],
    "feature_alt_score": ["feature_alt_score", "Feature Alt Score", "feature alt score", "FeatureAltScore", "feature_cards"],
    "total_score": ["total_score", "Total Score", "total score"],
    "year": ["year", "Year", "YEAR"],
    "month": ["month", "Month", "MONTH"],
    "week": ["week", "Week", "WEEK"],
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

# report_es_old 실제: basic_asset_score(단수), summary_spec_score, faqs_score, front_image_alt_score
B2C_POSSIBLE_COLUMN_NAMES = {
    "region": ["region", "Region", "REGION"],
    "country": ["country", "Country", "COUNTRY"],
    "division": ["division", "Division", "DIVISION"],
    "monitoring": ["monitoring", "Monitoring", "MONITORING"],
    "ufn_score": ["ufn_score", "1. UFN", "UFN", "ufn"],
    "basic_assets_score": ["basic_assets_score", "basic_asset_score", "2. Basic Assets", "Basic Assets"],
    "spec_summary_score": ["spec_summary_score", "summary_spec_score", "3. Spec Summary", "Spec Summary"],
    "faq_score": ["faq_score", "faqs_score", "4. FAQ", "FAQ"],
    "title_score": ["title_score", "title_tag_score", "5. Tag <Title>", "Tag <Title>"],
    "description_score": ["description_score", "description_tag_score", "6. Tag <Description>", "Tag <Description>"],
    "h1_score": ["h1_score", "h1_tag_score", "7. Tag <H1>", "Tag <H1>"],
    "canonical_score": ["canonical_score", "canonical_link_score", "8. Tag <Canonical Link>", "Tag <Canonical Link>"],
    "alt_feature_score": ["alt_feature_score", "feature_alt_score", "9. Tag <Alt text>_(Feature Cards)", "Alt Feature"],
    "alt_front_score": ["alt_front_score", "front_image_alt_score", "10. Tag <Alt text>_(Front Image)", "Alt Front"],
    "year": ["year", "Year", "YEAR"],
    "month": ["month", "Month", "MONTH"],
    "week": ["week", "Week", "WEEK"],
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
