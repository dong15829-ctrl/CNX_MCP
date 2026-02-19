# -*- coding: utf-8 -*-
"""파이프라인 설정: DB 테이블/컬럼 매핑."""
import os
from pathlib import Path

TABLE_B2B = "reportbusiness_es_old_v2"
TABLE_B2C = "report_es_old"

COLUMN_ALIAS_B2B = {
    "region": "region", "country": "country", "scoring_yn": "scoring_yn",
    "title_tag_score": "title_tag_score", "description_tag_score": "description_tag_score",
    "h1_tag_score": "h1_tag_score", "canonical_link_score": "canonical_link_score",
    "feature_alt_score": "feature_alt_score", "total_score": "total_score",
    "year": "year", "month": "month", "week": "week",
}
B2B_POSSIBLE_COLUMN_NAMES = {
    "region": ["region", "Region", "REGION"],
    "country": ["country", "Country", "COUNTRY"],
    "scoring_yn": ["scoring_yn", "scoring", "Scoring Y/N"],
    "title_tag_score": ["title_tag_score", "Title Tag Score"],
    "description_tag_score": ["description_tag_score", "Description Tag Score"],
    "h1_tag_score": ["h1_tag_score", "H1 Tag Score", "h1_tag_pf"],
    "canonical_link_score": ["canonical_link_score", "Canonical Link Score", "canonical_link_pf"],
    "feature_alt_score": ["feature_alt_score", "Feature Alt Score", "feature_cards"],
    "total_score": ["total_score", "Total Score"],
    "year": ["year", "Year"], "month": ["month", "Month"], "week": ["week", "Week"],
}

COLUMN_ALIAS_B2C = {
    "region": "region", "country": "country", "division": "division", "monitoring": "monitoring",
    "ufn_score": "ufn_score", "basic_assets_score": "basic_assets_score",
    "spec_summary_score": "spec_summary_score", "faq_score": "faq_score",
    "title_score": "title_score", "description_score": "description_score",
    "h1_score": "h1_score", "canonical_score": "canonical_score",
    "alt_feature_score": "alt_feature_score", "alt_front_score": "alt_front_score",
    "year": "year", "month": "month", "week": "week",
}
B2C_POSSIBLE_COLUMN_NAMES = {
    "region": ["region", "Region"], "country": ["country", "Country"],
    "division": ["division", "Division"], "monitoring": ["monitoring", "Monitoring"],
    "ufn_score": ["ufn_score", "1. UFN"], "basic_assets_score": ["basic_assets_score", "basic_asset_score"],
    "spec_summary_score": ["spec_summary_score", "summary_spec_score"],
    "faq_score": ["faq_score", "faqs_score"],
    "title_score": ["title_score", "title_tag_score"],
    "description_score": ["description_score", "description_tag_score"],
    "h1_score": ["h1_score", "h1_tag_score"],
    "canonical_score": ["canonical_score", "canonical_link_score"],
    "alt_feature_score": ["alt_feature_score", "feature_alt_score"],
    "alt_front_score": ["alt_front_score", "front_image_alt_score"],
    "year": ["year", "Year"], "month": ["month", "Month"], "week": ["week", "Week"],
}

BASE_DIR = Path(__file__).resolve().parent.parent
B2B_SCORE_COLUMNS = ["title_tag_score", "description_tag_score", "h1_tag_score", "canonical_link_score", "feature_alt_score"]
B2C_SCORE_COLUMNS = ["ufn_score", "basic_assets_score", "spec_summary_score", "faq_score", "title_score", "description_score", "h1_score", "canonical_score", "alt_feature_score", "alt_front_score"]
