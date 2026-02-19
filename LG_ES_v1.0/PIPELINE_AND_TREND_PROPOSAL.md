# DB 파이프라인 및 트렌드 분석 최종 제안

## 1. DB 테이블 및 역할

| DB 테이블 | 구분 | 설명 |
|-----------|------|------|
| **report_es_old** | B2C | PDP Raw 데이터. 연도·월·주차 컬럼 포함. |
| **reportbusiness_es_old** | B2B | PLP Business 데이터. 연도·월·주차 컬럼 포함. |

- 두 테이블 **마지막 컬럼**: **연도(year)**, **월(month)**, **주차(week)**  
- 이 컬럼을 기준으로 **기간별 SUMMARY** 및 **트렌드 분석** 수행.

---

## 2. 파이프라인 구조 (전체 흐름)

```
[DB]
  report_es_old (B2C)     ──┐
  reportbusiness_es_old (B2B) ──┼──► [집계 파이프라인] ──► SUMMARY (현재 스냅 + 기간별)
                                    │
                                    └──► RAW 다운로드 / API
```

- **집계 파이프라인**: 기존 SUMMARY 로직(국가별/국가·Division별 평균)을 DB 테이블에 적용.
- **기간 차원 추가**: `year`, `month`, `week` 기준으로 GROUP BY 하여 **트렌드용 SUMMARY** 생성.
- **RAW**: `report_es_old` / `reportbusiness_es_old`를 필터(기간 등) 적용해 그대로 제공.

---

## 3. SUMMARY 집계 (기존 로직 + 기간 반영)

### 3.1 B2B (reportbusiness_es_old)

- **조건**: `Scoring Y/N = 'Y'` (또는 동일 의미 컬럼)
- **집계 키**: `region`, `country` + **(선택) `year`, `month` 또는 `year`, `week`**
- **산출 컬럼**: sku_count, title_avg, description_avg, h1_avg, canonical_avg, feature_alt_avg, total_score_pct

**용도**

- `year, month, week` 없이 집계 → **최신 스냅 SUMMARY** (대시보드 메인 테이블).
- `year, month` 포함 집계 → **월별 트렌드**.
- `year, week` 포함 집계 → **주차별 트렌드**.

### 3.2 B2C (report_es_old)

- **조건**: `Monitoring = 'Y'`
- **집계 키**: `region`, `country`, `division` + **(선택) `year`, `month` 또는 `year`, `week`**
- **산출 컬럼**: sku_count, ufn_avg ~ alt_front_avg (10개), total_score_pct

**용도**

- 기간 없이 → **최신 스냅 SUMMARY**.
- 기간 포함 → **월별/주차별 트렌드**.

---

## 4. 트렌드 분석 반영 방안

### 4.1 제공 데이터 형태

| 구분 | 집계 단위 | 용도 |
|------|-----------|------|
| **현재 SUMMARY** | region, country(, division) | 대시보드 메인 테이블, KPI 카드 |
| **월별 트렌드** | region, country(, division), **year, month** | 월별 추이 차트, 기간 비교 |
| **주차별 트렌드** | region, country(, division), **year, week** | 주차별 추이 차트 |

### 4.2 트렌드용 쿼리 예시 (B2B)

```sql
-- B2B 월별 트렌드 (reportbusiness_es_old)
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
```

- **주차별**: 위에서 `month` 대신 `week` 사용, `GROUP BY ... year, week`.

### 4.3 트렌드용 쿼리 예시 (B2C)

```sql
-- B2C 월별 트렌드 (report_es_old)
SELECT
    region,
    country,
    division,
    year,
    month,
    COUNT(*) AS sku_count,
    ROUND(AVG(ufn_score), 6) AS ufn_avg,
    -- ... 나머지 9개 점수 평균 ...
    ROUND((AVG(ufn_score)+...+AVG(alt_front_score))/100.0*100.0, 6) AS total_score_pct
FROM report_es_old
WHERE monitoring = 'Y'
GROUP BY region, country, division, year, month
ORDER BY year, month, region, country, division;
```

- 실제 컬럼명(year, month, week, 점수 컬럼명)은 DB 스키마에 맞게 치환.

---

## 5. 파이프라인 연동 작업 정리

### 5.1 DB 연결

- **Host**: mysql.cnxkr.com  
- **Port**: 10080  
- **Database**: lg_ha  
- **User**: lg_ha  
- **Password**: 환경 변수(예: `MYSQL_PASSWORD`)로 관리, 코드에는 미기입.

### 5.2 파이프라인에서 수행할 작업

| 순서 | 작업 | 설명 |
|------|------|------|
| 1 | **테이블 스키마 확인** | `report_es_old`, `reportbusiness_es_old`의 컬럼명(연도/월/주차, 점수, 조건 컬럼) 확인 |
| 2 | **SUMMARY 쿼리 매핑** | 기존 `summary_from_plp_business.sql` / `summary_from_pdp_raw_b2c.sql` 로직을 위 두 테이블·컬럼명에 맞게 수정 |
| 3 | **트렌드 쿼리 추가** | 위와 동일 집계에 `year`, `month` 또는 `year`, `week`를 GROUP BY에 포함한 쿼리 작성 |
| 4 | **API 또는 배치** | SUMMARY(스냅)·SUMMARY(월별)·SUMMARY(주차별)·RAW 조회/다운로드용 API 또는 배치 스크립트 구현 |

### 5.3 API(또는 배치) 제안

- **SUMMARY 현재 스냅**  
  - `GET /api/summary/b2b`, `GET /api/summary/b2c`  
  - `reportbusiness_es_old` / `report_es_old`에서 기간 없이 집계한 결과 반환.
- **SUMMARY 트렌드**  
  - `GET /api/summary/b2b/trend?by=month` 또는 `by=week`  
  - `GET /api/summary/b2c/trend?by=month` 또는 `by=week`  
  - 위 월별/주차별 집계 결과 반환 (연도·월/주 필터 옵션 권장).
- **RAW 다운로드**  
  - `GET /api/raw/b2b/download?format=csv&year=2025&month=10`  
  - `GET /api/raw/b2c/download?format=csv&year=2025&month=10`  
  - `report_es_old` / `reportbusiness_es_old`를 연·월(·주차)로 필터 후 CSV 등으로 스트리밍.

---

## 6. 대시보드 연동 요약

- **메인 테이블**: SUMMARY 현재 스냅 API 사용.
- **트렌드 차트**: SUMMARY 트렌드 API(월별/주차별) 사용. x축: year-month 또는 year-week, y축: total_score_pct 등.
- **다운로드**  
  - **집계 테이블**: 이미 로드한 SUMMARY JSON을 프론트에서 CSV/Excel로 변환해 다운로드.  
  - **RAW**: 위 RAW 다운로드 API 호출로 파일 다운로드.

---

## 7. 다음 단계 (실행 순서)

1. **DB에서 연도/월/주차 컬럼명 확인**  
   - `report_es_old`, `reportbusiness_es_old`의 실제 컬럼명 (예: `year`, `month`, `week` 또는 `_year`, `_month`, `_week`).
2. **SUMMARY용 SQL을 두 테이블·컬럼에 맞게 수정**  
   - 소스: `reportbusiness_es_old`(B2B), `report_es_old`(B2C).  
   - 조건/집계 키/점수 컬럼/연도·월·주차 반영.
3. **트렌드용 SQL 추가**  
   - GROUP BY에 `year`, `month` 또는 `year`, `week` 포함.
4. **파이프라인 구현**  
   - 백엔드 또는 배치에서 위 쿼리 실행 후 API 응답/파일로 제공.
5. **대시보드**  
   - SUMMARY/트렌드 API 연동 및 다운로드(집계+RAW) 기능 연결.

이 제안대로 진행하면 **report_es_old(B2C)·reportbusiness_es_old(B2B)** 와 **연도·월·주차**를 활용한 파이프라인 및 트렌드 분석까지 반영한 구조가 됩니다.

---

## 8. 참고: DB 스키마 확인 후 수정

- **summary_from_db_b2b.sql**, **summary_from_db_b2c.sql** 에서 사용한 컬럼명은 가정입니다.
- 실제 DB에서 아래를 확인한 뒤, SQL과 파이프라인 코드의 컬럼명을 맞춰야 합니다.

| 항목 | B2B (reportbusiness_es_old) | B2C (report_es_old) |
|------|-----------------------------|----------------------|
| 조건 컬럼 | scoring_yn 또는 'Scoring Y/N' | monitoring 또는 'Monitoring' |
| 연도 | year / _year / report_year 등 | 동일 |
| 월 | month / _month 등 | 동일 |
| 주차 | week / _week / week_no 등 | 동일 |
| 점수 컬럼 | title_tag_score, description_tag_score, ... | ufn_score, basic_assets_score, ... (또는 `1. UFN` 등) |

- `DESCRIBE report_es_old;`, `DESCRIBE reportbusiness_es_old;` 로 마지막 컬럼(연도·월·주차) 및 점수 컬럼명을 확인 후 위 SQL과 API 쿼리를 수정하면 됩니다.
