# B2B 데이터 흐름: DB → Summary Dashboard

## 1. 데이터 소스

| 단계 | 위치 | 설명 |
|------|------|------|
| **DB 테이블** | MySQL `lg_ha.reportbusiness_es_old_v2` | B2B RAW 데이터 (region, country, scoring, h1_tag_pf, canonical_link_pf, feature_cards, year, month, week 등) |

## 2. 스코어 계산 방식 (엑셀과 동일)

- **만점**: Title(20) + Description(20) + H1(15) + Canonical Link(15) + Feature Alt(15) = **85점**
- **Total Score %** = (1. Title + 2. Description + 3. H1 + 4. Canonical Link + 5. Alt text_ Feature Cards) / 85 × 100
- **DB 컬럼**: `reportbusiness_es_old` 에서 `h1_tag_pf`, `canonical_link_pf`, `feature_cards` 를 숫자로 해석해 region·country 별 **평균**으로 집계. Title/Description 점수 컬럼이 없으면 0으로 두고 위 식 적용.
- **NULL 처리**: DB에 값이 없으면 SQL/응답에서 **0**으로 채워 "—" 대신 **0.00**으로 표시.

## 3. 백엔드: DB → SUMMARY 집계

| 단계 | 파일/엔드포인트 | 설명 |
|------|-----------------|------|
| **pandas 우선** | `get_b2b_raw_df()` → `preprocess_b2b` → `aggregate_b2b_snapshot` | 컬럼 매핑(h1_tag_pf→h1_tag_score 등), `scoring_yn in ('Y','YES','1')` 필터, to_numeric 후 region·country 별 평균·total_score_pct 계산 |
| **SQL 폴백** | `backend/data.py` → `SQL_B2B_SNAPSHOT` | `WHERE scoring = 'Y'` 필터, `GROUP BY region, country`, AVG에 COALESCE(..., 0) 적용해 NULL 없이 반환 |
| **함수** | `get_summary_b2b_snapshot(region_filter, country_filter)` | pandas 결과 또는 SQL 결과 반환. 반환 전 `_b2b_fill_scores()` 로 스코어 null→0 보정 |
| **API** | `GET /api/summary?report_type=B2B&month=latest&region=...&country=...` | `get_summary_snapshot('B2B', ...)` 호출 → JSON 배열 반환 |
| **함수** | `get_summary_b2b_snapshot_sql(region_filter, country_filter)` | 위 SQL 실행 후 list[dict] 반환. 실패 시 pandas 경로로 폴백 |
| **API** | `GET /api/summary?report_type=B2B&month=latest&region=...&country=...` | `get_summary_snapshot('B2B', region_filter, country_filter)` 호출 → JSON 배열 반환 |

**반환 행 예시:**
```json
{
  "region": "EMEA",
  "country": "Germany",
  "sku_count": 120,
  "title_tag_score": 0,
  "description_tag_score": 0,
  "h1_tag_score": 12.5,
  "canonical_link_score": 14.2,
  "feature_alt_score": 15.0,
  "total_score_pct": 92.56
}
```

## 4. 프론트엔드: API → Dashboard 표시

| 단계 | 함수/요소 | 설명 |
|------|-----------|------|
| **초기화** | `init()` | `getReports()` → `getFilters('B2B', month, [])` → `fillRegionCountryPanels()` → `loadDashboard('B2B', month, [], [])` |
| **데이터 로드** | `loadDashboard(reportType, month, regions, countries)` | `getSummary(reportType, month, regions, countries)` 호출 → `GET /api/summary?report_type=B2B&month=latest` (쿠키로 인증) |
| **표시** | `renderTableB2B(rows)` | 테이블 `#tableBodyB2B` 에 행 채움. 각 행: region, country, sku_count, total_score_pct, title_tag_score, description_tag_score, h1_tag_score, canonical_link_score, feature_alt_score |
| **차트** | `renderChartScoreByRegion(rows)` | `aggregateByRegion(rows)` 로 region별 평균 계산 후 막대 차트 (chartScoreByRegion) |
| **요약 숫자** | `renderScoreSummaryB2B(rows)` | SCORE_SUMMARY_KEYS 기준으로 전체 평균 표시 |

## 5. 집계 VIEW로 속도 개선 (권장)

API가 매 요청마다 RAW 테이블을 집계하면 데이터가 클수록 느려집니다. **서버에 미리 집계 VIEW(또는 테이블)를 만들어 두고** 그곳에서만 읽으면 훨씬 빠릅니다.

### 동작 순서 (backend/data.py)

| 순서 | B2B | B2C |
|------|-----|-----|
| 1 | `SUMMARY_VIEW_B2B` 설정 시 → VIEW에서만 읽기 (**가장 빠름**) | `SUMMARY_VIEW_B2C` 설정 시 → VIEW에서만 읽기 |
| 2 | VIEW 없으면 RAW 테이블에 대해 **SQL로 집계** (pandas보다 빠름) | VIEW 없으면 RAW 테이블에 대해 SQL 집계 |
| 3 | SQL 실패/비정상 시에만 pandas 폴백 | SQL 실패 시 pandas 폴백 |

### 설정 방법

1. **MySQL에서 집계 VIEW 생성**  
   프로젝트 루트의 `scripts/create_summary_views.sql` 을 DB에서 실행합니다.
   - `v_summary_b2b`: B2B Summary (region/country 별, 만점 85 반영)
   - `v_summary_b2c`: B2C Summary (region/country/division 별)

2. **.env 에 VIEW 이름 설정**
   ```env
   SUMMARY_VIEW_B2B=v_summary_b2b
   SUMMARY_VIEW_B2C=v_summary_b2c
   ```
   설정 후 서버를 재시작하면 API는 RAW 테이블 대신 해당 VIEW에서만 읽어 응답 속도가 개선됩니다.

3. **테이블명이 다른 경우**  
   `scripts/create_summary_views.sql` 상단의 `reportbusiness_es_old_v2` / `report_es_old` 를 실제 RAW 테이블명으로 수정한 뒤 VIEW를 생성하면 됩니다.

### 속도 개선 요약

| 항목 | 설명 |
|------|------|
| **집계 VIEW** | `SUMMARY_VIEW_B2B` / `SUMMARY_VIEW_B2C` 사용 시 DB 집계 부하 감소 → **가장 효과 큼** |
| **Summary API 캐시** | `.env` 에 `SUMMARY_CACHE_TTL=60` (기본 60초). 동일 조건 재요청 시 DB 없이 캐시 반환. `0` 이면 비활성화. |
| **프론트엔드** | 대시보드 로드 시 **요약 테이블을 먼저 표시**하고, 트렌드 차트·리포트 목록은 백그라운드에서 비동기 로드. |

## 6. 문제 발생 시 확인 순서

1. **"Field required" 422**  
   - 서버가 예전 코드로 떠 있을 수 있음. **서버를 완전히 종료(Ctrl+C) 후 다시 실행**하세요.  
   - `http://localhost:8010/api/version` 에서 `{"version":"2.0", ...}` 이 보이면 최신 코드 동작 중.

2. **로그인**  
   대시보드는 쿠키 인증이 필요함. `/login` 에서 로그인 후 `/` 로 이동해야 함.

3. **API 응답**  
   - 브라우저 F12 → Network → `reports` / `summary?report_type=B2B` 요청 확인.  
   - 401: 로그인 안 됨 또는 쿠키 미전송 (같은 도메인/포트로 접속했는지 확인).  
   - 503: DB 미연동 또는 DB 오류. 응답 body 의 `detail` 메시지 확인.  
   - 200 이어도 body 가 배열이 아니면(예: `{detail: "..."}`) 테이블이 비어 보일 수 있음.

4. **DB / 속도**  
   - `python scripts/check_db.py` 로 연결·테이블·SUMMARY 행 수 확인.  
   - `.env` 에 `MYSQL_PASSWORD` 등 설정 여부 확인.  
   - **속도 이슈**: 원격 DB 대신 EC2에 로컬 MySQL을 두고 동기화해 조회하면 지연이 크게 줄어듦. → **`docs/LOCAL_MYSQL_SYNC.md`** 참고.

5. **컬럼명**  
   - `reportbusiness_es_old_v2` 실제 컬럼: `scoring`, `h1_tag_pf`, `canonical_link_pf`, `feature_cards` (legacy)  
     또는 `h1_tag_score`, `canonical_link_score`, `feature_alt_score` (_score).  
   - legacy면 `SQL_B2B_SNAPSHOT`, _score 컬럼만 있으면 .env 에 `B2B_SCORE_SCHEMA=v2` 추가 후 재시작.

6. **Summary 점수가 전부 0.00일 때 (데이터·API·파이프라인 연결)**  
   - **반드시**: 백엔드 서버를 **완전히 종료(Ctrl+C) 후 다시 실행**해야 최신 코드(v2 스키마, Decimal→float 정규화)가 적용됩니다.  
   - **진단**: 프로젝트 루트에서 `python scripts/diagnose_b2b_summary.py` (또는 `.venv/bin/python scripts/diagnose_b2b_summary.py`) 실행 → 테이블 실제 컬럼명, scoring='Y' 행 샘플, **API와 동일한 집계 결과(첫 2행)** 확인. 여기서 점수가 나오면 백엔드/DB는 정상이며, **서버 재시작** 후 브라우저 새로고침으로 해결됩니다.  
   - **원인 후보**:  
     - 테이블에 점수 컬럼명이 다름 (legacy: `h1_tag_pf` 등 vs v2: `h1_tag_score` 등) → 테이블명에 `v2`가 있으면 자동으로 v2 스키마 사용. 필요 시 `.env` 에 `B2B_SCORE_SCHEMA=v2` 설정.  
     - `scoring='Y'` 인 행이 없거나, 점수 컬럼이 NULL/빈 문자열 → 파이프라인·적재 데이터에서 해당 컬럼이 채워지도록 확인.  
     - VIEW 사용 중인데 VIEW 정의가 이전 테이블명/컬럼 기준 → `scripts/create_summary_views.sql` 로 VIEW 재생성.
