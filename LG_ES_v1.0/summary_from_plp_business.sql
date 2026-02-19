-- =============================================================================
-- B2B Summary 시트와 동일한 집계 (PLP_BUSINESS 단일 소스)
-- 수식: AVERAGEIFS(PLP_BUSINESS!X:AB, Country=Summary.C, Scoring Y/N='Y')
-- =============================================================================

-- 테이블/뷰 가정: PLP_BUSINESS
-- 컬럼: region, country, locale, page_type, cat_plp, scoring_yn, url, ...
--       total_score (W열), title_tag_score (X), description_tag_score (Y),
--       h1_tag_score (Z), canonical_link_score (AA), feature_alt_score (AB)

-- (1) 국가별 평균 점수 (Summary K~O에 해당)
SELECT
    region,
    country,
    COUNT(*) AS sku_count,
    ROUND(AVG(title_tag_score), 6)       AS title_avg,           -- Summary K (out of 20)
    ROUND(AVG(description_tag_score), 6) AS description_avg,     -- Summary L (out of 20)
    ROUND(AVG(h1_tag_score), 6)          AS h1_avg,              -- Summary M (out of 15)
    ROUND(AVG(canonical_link_score), 6)  AS canonical_avg,       -- Summary N (out of 15)
    ROUND(AVG(feature_alt_score), 6)     AS feature_alt_avg,     -- Summary O (out of 15)
    ROUND(AVG(total_score), 6)          AS total_score_avg,    -- PLP 원본 Total Score (W열)
    ROUND(
        (AVG(title_tag_score) + AVG(description_tag_score) + AVG(h1_tag_score)
         + AVG(canonical_link_score) + AVG(feature_alt_score)) / 85.0 * 100.0,
        6
    ) AS total_score_pct   -- 만점 20+20+15+15+15 = 85
FROM plp_business
WHERE scoring_yn = 'Y'
GROUP BY region, country
ORDER BY region, country;


-- (2) 컬럼명을 엑셀 컬럼 인덱스로 쓰는 경우 (헤더 행 2 사용 시)
-- PLP_BUSINESS: A=region, B=country, H=scoring_yn, X=col24, Y=col25, Z=col26, AA=col27, AB=col28
/*
SELECT
    region              AS region,
    country             AS country,
    COUNT(*)            AS sku_count,
    AVG(col24)          AS title_avg,        -- X
    AVG(col25)          AS description_avg,   -- Y
    AVG(col26)          AS h1_avg,            -- Z
    AVG(col27)          AS canonical_avg,    -- AA
    AVG(col28)          AS feature_alt_avg,   -- AB
    (AVG(col24)+AVG(col25)+AVG(col26)+AVG(col27)+AVG(col28)) / 85.0 * 100.0 AS total_score_pct
FROM plp_business
WHERE scoring_yn = 'Y'
GROUP BY region, country
ORDER BY region, country;
*/


-- (3) 전체 평균 한 행 (Summary 행 9: AVERAGEIF(K10:K59, "<>#N/A")에 해당)
SELECT
    'TOTAL' AS region,
    NULL    AS country,
    SUM(sku_count) AS sku_count,
    ROUND(AVG(title_avg), 6)       AS title_avg,
    ROUND(AVG(description_avg), 6)  AS description_avg,
    ROUND(AVG(h1_avg), 6)         AS h1_avg,
    ROUND(AVG(canonical_avg), 6)  AS canonical_avg,
    ROUND(AVG(feature_alt_avg), 6) AS feature_alt_avg,
    ROUND(AVG(total_score_pct), 6) AS total_score_pct
FROM (
    SELECT
        region,
        country,
        COUNT(*) AS sku_count,
        AVG(title_tag_score)       AS title_avg,
        AVG(description_tag_score) AS description_avg,
        AVG(h1_tag_score)          AS h1_avg,
        AVG(canonical_link_score)  AS canonical_avg,
        AVG(feature_alt_score)     AS feature_alt_avg,
        (AVG(title_tag_score)+AVG(description_tag_score)+AVG(h1_tag_score)
         +AVG(canonical_link_score)+AVG(feature_alt_score)) / 85.0 * 100.0 AS total_score_pct
    FROM plp_business
    WHERE scoring_yn = 'Y'
    GROUP BY region, country
) t;
