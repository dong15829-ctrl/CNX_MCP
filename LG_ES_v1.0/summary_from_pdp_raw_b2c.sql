-- =============================================================================
-- B2C Summary by Country 시트와 동일한 집계 (엑셀 PDP_Raw 시트 기반)
-- 수식: AVERAGEIFS(PDP_Raw!AK:AT, PDP_Raw!$B:$B, Summary.C, PDP_Raw!$F:$F, "Y", PDP_Raw!$E:$E, Summary.D)
-- B2B와 다름: Division(E) 조건, Monitoring(F)='Y', 10개 점수 컬럼(AK~AT), 만점 100
-- =============================================================================

-- [엑셀 PDP_Raw 시트 컬럼 매핑]
-- A=1:Region, B=2:Country, C=3:Locale, D=4:Page Type, E=5:Division, F=6:Monitoring
-- AK=37:1. UFN, AL=38:2. Basic Assets, AM=39:3. Spec Summary, AN=40:4. FAQ
-- AO=41:5. Tag <Title>, AP=42:6. Tag <Description>, AQ=43:7. Tag <H1>
-- AR=44:8. Tag <Canonical Link>, AS=45:9. Tag <Alt text>_(Feature Cards), AT=46:10. Tag <Alt text>_(Front Image)

-- 테이블 가정: PDP_Raw를 엑셀과 동일 구조로 적재한 경우
-- 컬럼(논리명): region(A), country(B), division(E), monitoring(F),
--   ufn_score(AK), basic_assets_score(AL), spec_summary_score(AM), faq_score(AN),
--   title_score(AO), description_score(AP), h1_score(AQ), canonical_score(AR),
--   alt_feature_score(AS), alt_front_score(AT)

-- (1) 국가·Division별 평균 점수 (Summary by Country K~T에 해당, 10개 항목)
SELECT
    region,
    country,
    division,
    COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score), 6)              AS ufn_avg,              -- K (1. UFN)
    ROUND(AVG(basic_assets_score), 6)     AS basic_assets_avg,     -- L (2. Basic Assets)
    ROUND(AVG(spec_summary_score), 6)     AS spec_summary_avg,     -- M (3. Spec Summary)
    ROUND(AVG(faq_score), 6)             AS faq_avg,              -- N (4. FAQ)
    ROUND(AVG(title_score), 6)           AS title_avg,            -- O (5. Tag Title)
    ROUND(AVG(description_score), 6)      AS description_avg,      -- P (6. Tag Description)
    ROUND(AVG(h1_score), 6)              AS h1_avg,               -- Q (7. Tag H1)
    ROUND(AVG(canonical_score), 6)       AS canonical_avg,         -- R (8. Canonical Link)
    ROUND(AVG(alt_feature_score), 6)     AS alt_feature_avg,      -- S (9. Alt Feature Cards)
    ROUND(AVG(alt_front_score), 6)       AS alt_front_avg,         -- T (10. Alt Front Image)
    ROUND(
        (AVG(ufn_score) + AVG(basic_assets_score) + AVG(spec_summary_score) + AVG(faq_score)
         + AVG(title_score) + AVG(description_score) + AVG(h1_score) + AVG(canonical_score)
         + AVG(alt_feature_score) + AVG(alt_front_score)) / 100.0 * 100.0,
        6
    ) AS total_score_pct   -- 만점 10*10 = 100
FROM pdp_raw
WHERE monitoring = 'Y'
GROUP BY region, country, division
ORDER BY region, country, division;


-- (2) 엑셀 컬럼 인덱스(1-based)로 참조하는 경우 (PDP_Raw 엑셀 시트 그대로 적재 시)
-- A=1, B=2, E=5, F=6, AK=37, AL=38, AM=39, AN=40, AO=41, AP=42, AQ=43, AR=44, AS=45, AT=46
/*
SELECT
    col_1  AS region,    -- A
    col_2  AS country,   -- B
    col_5  AS division,  -- E
    COUNT(*) AS sku_count,
    ROUND(AVG(col_37), 6)  AS ufn_avg,              -- AK (1. UFN)
    ROUND(AVG(col_38), 6)  AS basic_assets_avg,     -- AL (2. Basic Assets)
    ROUND(AVG(col_39), 6)  AS spec_summary_avg,     -- AM (3. Spec Summary)
    ROUND(AVG(col_40), 6)  AS faq_avg,              -- AN (4. FAQ)
    ROUND(AVG(col_41), 6)  AS title_avg,             -- AO (5. Tag Title)
    ROUND(AVG(col_42), 6)  AS description_avg,       -- AP (6. Tag Description)
    ROUND(AVG(col_43), 6)  AS h1_avg,                -- AQ (7. Tag H1)
    ROUND(AVG(col_44), 6)  AS canonical_avg,         -- AR (8. Canonical Link)
    ROUND(AVG(col_45), 6)  AS alt_feature_avg,       -- AS (9. Alt Feature Cards)
    ROUND(AVG(col_46), 6)  AS alt_front_avg,         -- AT (10. Alt Front Image)
    ROUND((AVG(col_37)+AVG(col_38)+AVG(col_39)+AVG(col_40)+AVG(col_41)
     +AVG(col_42)+AVG(col_43)+AVG(col_44)+AVG(col_45)+AVG(col_46)) / 100.0 * 100.0, 6) AS total_score_pct
FROM pdp_raw
WHERE col_6 = 'Y'   -- F: Monitoring
GROUP BY col_1, col_2, col_5
ORDER BY col_1, col_2, col_5;
*/


-- (3) 전체 평균 한 행 (Summary 행 10: AVERAGE(K11:K60) 등에 해당, Division별 또는 단일)
SELECT
    'TOTAL' AS region,
    NULL    AS country,
    division,
    SUM(sku_count) AS sku_count,
    ROUND(AVG(ufn_avg), 6)           AS ufn_avg,
    ROUND(AVG(basic_assets_avg), 6)  AS basic_assets_avg,
    ROUND(AVG(spec_summary_avg), 6)  AS spec_summary_avg,
    ROUND(AVG(faq_avg), 6)           AS faq_avg,
    ROUND(AVG(title_avg), 6)         AS title_avg,
    ROUND(AVG(description_avg), 6)   AS description_avg,
    ROUND(AVG(h1_avg), 6)            AS h1_avg,
    ROUND(AVG(canonical_avg), 6)     AS canonical_avg,
    ROUND(AVG(alt_feature_avg), 6)  AS alt_feature_avg,
    ROUND(AVG(alt_front_avg), 6)     AS alt_front_avg,
    ROUND(AVG(total_score_pct), 6)   AS total_score_pct
FROM (
    SELECT
        region,
        country,
        division,
        COUNT(*) AS sku_count,
        AVG(ufn_score)              AS ufn_avg,
        AVG(basic_assets_score)     AS basic_assets_avg,
        AVG(spec_summary_score)     AS spec_summary_avg,
        AVG(faq_score)              AS faq_avg,
        AVG(title_score)            AS title_avg,
        AVG(description_score)      AS description_avg,
        AVG(h1_score)               AS h1_avg,
        AVG(canonical_score)        AS canonical_avg,
        AVG(alt_feature_score)      AS alt_feature_avg,
        AVG(alt_front_score)        AS alt_front_avg,
        (AVG(ufn_score)+AVG(basic_assets_score)+AVG(spec_summary_score)+AVG(faq_score)
         +AVG(title_score)+AVG(description_score)+AVG(h1_score)+AVG(canonical_score)
         +AVG(alt_feature_score)+AVG(alt_front_score)) / 100.0 * 100.0 AS total_score_pct
    FROM pdp_raw
    WHERE monitoring = 'Y'
    GROUP BY region, country, division
) t
GROUP BY division;

-- 참고: report_es(뷰) 컬럼명이 엑셀 헤더와 다르면 위 ufn_score 등은 실제 컬럼명으로 치환.
-- 예: `1. UFN`, `2. Basic Assets` 등은 MySQL에서 백틱으로 감싸서 사용.
