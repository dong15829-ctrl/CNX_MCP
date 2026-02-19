-- =============================================================================
-- B2C SUMMARY: report_es_old 기반 (DB 파이프라인)
-- 연도·월·주차 컬럼으로 트렌드 분석 가능
-- =============================================================================
-- 테이블: report_es_old (B2C)
-- 조건: monitoring = 'Y'
-- 시계열 컬럼: year, month, week (실제 컬럼명 확인 후 수정)

-- (1) 현재 스냅 SUMMARY (기간 없음)
SELECT
    region,
    country,
    division,
    COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score), 6)              AS ufn_avg,
    ROUND(AVG(basic_assets_score), 6)     AS basic_assets_avg,
    ROUND(AVG(spec_summary_score), 6)     AS spec_summary_avg,
    ROUND(AVG(faq_score), 6)              AS faq_avg,
    ROUND(AVG(title_score), 6)            AS title_avg,
    ROUND(AVG(description_score), 6)      AS description_avg,
    ROUND(AVG(h1_score), 6)               AS h1_avg,
    ROUND(AVG(canonical_score), 6)        AS canonical_avg,
    ROUND(AVG(alt_feature_score), 6)      AS alt_feature_avg,
    ROUND(AVG(alt_front_score), 6)        AS alt_front_avg,
    ROUND((AVG(ufn_score)+AVG(basic_assets_score)+AVG(spec_summary_score)+AVG(faq_score)
         +AVG(title_score)+AVG(description_score)+AVG(h1_score)+AVG(canonical_score)
         +AVG(alt_feature_score)+AVG(alt_front_score))/100.0*100.0, 6) AS total_score_pct
FROM report_es_old
WHERE monitoring = 'Y'
GROUP BY region, country, division
ORDER BY region, country, division;


-- (2) 월별 트렌드 (year, month 기준)
SELECT
    region,
    country,
    division,
    year,
    month,
    COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score), 6)              AS ufn_avg,
    ROUND(AVG(basic_assets_score), 6)     AS basic_assets_avg,
    ROUND(AVG(spec_summary_score), 6)     AS spec_summary_avg,
    ROUND(AVG(faq_score), 6)              AS faq_avg,
    ROUND(AVG(title_score), 6)            AS title_avg,
    ROUND(AVG(description_score), 6)      AS description_avg,
    ROUND(AVG(h1_score), 6)               AS h1_avg,
    ROUND(AVG(canonical_score), 6)        AS canonical_avg,
    ROUND(AVG(alt_feature_score), 6)      AS alt_feature_avg,
    ROUND(AVG(alt_front_score), 6)        AS alt_front_avg,
    ROUND((AVG(ufn_score)+AVG(basic_assets_score)+AVG(spec_summary_score)+AVG(faq_score)
         +AVG(title_score)+AVG(description_score)+AVG(h1_score)+AVG(canonical_score)
         +AVG(alt_feature_score)+AVG(alt_front_score))/100.0*100.0, 6) AS total_score_pct
FROM report_es_old
WHERE monitoring = 'Y'
GROUP BY region, country, division, year, month
ORDER BY year, month, region, country, division;


-- (3) 주차별 트렌드 (year, week 기준)
SELECT
    region,
    country,
    division,
    year,
    week,
    COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score), 6)              AS ufn_avg,
    ROUND(AVG(basic_assets_score), 6)     AS basic_assets_avg,
    ROUND(AVG(spec_summary_score), 6)     AS spec_summary_avg,
    ROUND(AVG(faq_score), 6)              AS faq_avg,
    ROUND(AVG(title_score), 6)            AS title_avg,
    ROUND(AVG(description_score), 6)      AS description_avg,
    ROUND(AVG(h1_score), 6)               AS h1_avg,
    ROUND(AVG(canonical_score), 6)        AS canonical_avg,
    ROUND(AVG(alt_feature_score), 6)      AS alt_feature_avg,
    ROUND(AVG(alt_front_score), 6)        AS alt_front_avg,
    ROUND((AVG(ufn_score)+AVG(basic_assets_score)+AVG(spec_summary_score)+AVG(faq_score)
         +AVG(title_score)+AVG(description_score)+AVG(h1_score)+AVG(canonical_score)
         +AVG(alt_feature_score)+AVG(alt_front_score))/100.0*100.0, 6) AS total_score_pct
FROM report_es_old
WHERE monitoring = 'Y'
GROUP BY region, country, division, year, week
ORDER BY year, week, region, country, division;
