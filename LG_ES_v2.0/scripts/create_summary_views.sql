-- Summary 집계 VIEW 생성 (API 속도 개선용)
-- MySQL에서 실행 후 .env 에 SUMMARY_VIEW_B2B=v_summary_b2b, SUMMARY_VIEW_B2C=v_summary_b2c 설정
-- 테이블명이 다르면 아래 reportbusiness_es_old_v2 / report_es_old 를 실제 테이블명으로 수정하세요.

-- ---------------------------------------------------------------------------
-- B2B: region/country 별 집계 (만점 85 = Title20+Description20+H115+Canonical15+Feature15)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_summary_b2b AS
SELECT
    region,
    country,
    COUNT(*) AS sku_count,
    0 AS title_tag_score,
    0 AS description_tag_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(h1_tag_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0), 6) AS h1_tag_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(canonical_link_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0), 6) AS canonical_link_score,
    ROUND(COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(feature_cards,'')), ',', '.'), '') AS DECIMAL(10,2))), 0), 6) AS feature_alt_score,
    ROUND(
        (COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(h1_tag_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0)
         + COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(canonical_link_pf,'')), ',', '.'), '') AS DECIMAL(10,2))), 0)
         + COALESCE(AVG(CAST(NULLIF(REPLACE(TRIM(COALESCE(feature_cards,'')), ',', '.'), '') AS DECIMAL(10,2))), 0)) / 85.0 * 100.0,
        6
    ) AS total_score_pct
FROM reportbusiness_es_old_v2
WHERE (scoring = 'Y' OR UPPER(TRIM(COALESCE(scoring,'')))= 'Y')
  AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != ''
GROUP BY region, country
ORDER BY region, country;

-- ---------------------------------------------------------------------------
-- B2C: region/country/division 별 집계
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_summary_b2c AS
SELECT
    region,
    country,
    division,
    COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score), 6) AS ufn_score,
    ROUND(AVG(basic_asset_score), 6) AS basic_assets_score,
    ROUND(AVG(summary_spec_score), 6) AS spec_summary_score,
    ROUND(AVG(faqs_score), 6) AS faq_score,
    ROUND(AVG(title_tag_score), 6) AS title_score,
    ROUND(AVG(description_tag_score), 6) AS description_score,
    ROUND(AVG(h1_tag_score), 6) AS h1_score,
    ROUND(AVG(canonical_link_score), 6) AS canonical_score,
    ROUND(AVG(feature_alt_score), 6) AS alt_feature_score,
    ROUND(AVG(front_image_alt_score), 6) AS alt_front_score,
    ROUND(
        (COALESCE(AVG(ufn_score),0) + COALESCE(AVG(basic_asset_score),0) + COALESCE(AVG(summary_spec_score),0) + COALESCE(AVG(faqs_score),0)
         + COALESCE(AVG(title_tag_score),0) + COALESCE(AVG(description_tag_score),0) + COALESCE(AVG(h1_tag_score),0) + COALESCE(AVG(canonical_link_score),0)
         + COALESCE(AVG(feature_alt_score),0) + COALESCE(AVG(front_image_alt_score),0)),
        6
    ) AS total_score_pct
FROM report_es_old
WHERE (monitoring = 'Y' OR UPPER(TRIM(COALESCE(monitoring,'')))= 'Y')
  AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != '' AND TRIM(COALESCE(division,'')) != ''
GROUP BY region, country, division
ORDER BY region, country, division;
