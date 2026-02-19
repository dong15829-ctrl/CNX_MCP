-- =============================================================================
-- B2B SUMMARY: reportbusiness_es_old 기반 (DB 파이프라인)
-- 연도·월·주차 컬럼으로 트렌드 분석 가능
-- =============================================================================
-- 테이블: reportbusiness_es_old (B2B)
-- 조건: scoring_yn = 'Y' (또는 실제 컬럼명에 맞게)
-- 시계열 컬럼: year, month, week (실제 컬럼명 확인 후 수정)

-- (1) 현재 스냅 SUMMARY (기간 없음, 최신 데이터 또는 전체 집계)
SELECT
    region,
    country,
    COUNT(*) AS sku_count,
    ROUND(AVG(title_tag_score), 6)       AS title_avg,
    ROUND(AVG(description_tag_score), 6) AS description_avg,
    ROUND(AVG(h1_tag_score), 6)          AS h1_avg,
    ROUND(AVG(canonical_link_score), 6)   AS canonical_avg,
    ROUND(AVG(feature_alt_score), 6)     AS feature_alt_avg,
    ROUND((AVG(title_tag_score)+AVG(description_tag_score)+AVG(h1_tag_score)
         +AVG(canonical_link_score)+AVG(feature_alt_score))/85.0*100.0, 6) AS total_score_pct
FROM reportbusiness_es_old
WHERE scoring_yn = 'Y'
GROUP BY region, country
ORDER BY region, country;


-- (2) 월별 트렌드 (year, month 기준)
SELECT
    region,
    country,
    year,
    month,
    COUNT(*) AS sku_count,
    ROUND(AVG(title_tag_score), 6)       AS title_avg,
    ROUND(AVG(description_tag_score), 6) AS description_avg,
    ROUND(AVG(h1_tag_score), 6)          AS h1_avg,
    ROUND(AVG(canonical_link_score), 6)   AS canonical_avg,
    ROUND(AVG(feature_alt_score), 6)     AS feature_alt_avg,
    ROUND((AVG(title_tag_score)+AVG(description_tag_score)+AVG(h1_tag_score)
         +AVG(canonical_link_score)+AVG(feature_alt_score))/85.0*100.0, 6) AS total_score_pct
FROM reportbusiness_es_old
WHERE scoring_yn = 'Y'
GROUP BY region, country, year, month
ORDER BY year, month, region, country;


-- (3) 주차별 트렌드 (year, week 기준)
SELECT
    region,
    country,
    year,
    week,
    COUNT(*) AS sku_count,
    ROUND(AVG(title_tag_score), 6)       AS title_avg,
    ROUND(AVG(description_tag_score), 6) AS description_avg,
    ROUND(AVG(h1_tag_score), 6)          AS h1_avg,
    ROUND(AVG(canonical_link_score), 6)   AS canonical_avg,
    ROUND(AVG(feature_alt_score), 6)     AS feature_alt_avg,
    ROUND((AVG(title_tag_score)+AVG(description_tag_score)+AVG(h1_tag_score)
         +AVG(canonical_link_score)+AVG(feature_alt_score))/85.0*100.0, 6) AS total_score_pct
FROM reportbusiness_es_old
WHERE scoring_yn = 'Y'
GROUP BY region, country, year, week
ORDER BY year, week, region, country;
