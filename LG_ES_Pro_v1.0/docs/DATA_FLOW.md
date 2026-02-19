# LG ES v3.0 — 데이터 흐름 문서

> **문서 버전**: 1.0  
> **최종 수정**: 2026-02-11  
> **상태**: 설계 완료 → 구현 대기

---

## 1. 전체 데이터 흐름도

```
┌─────────────────────────────────────────────────────────────────────┐
│                        원천 데이터 (원격 MySQL)                       │
│                                                                     │
│   ┌──────────────────────────┐  ┌──────────────────────────┐        │
│   │  reportbusiness_es_old_v2│  │  report_es_old           │        │
│   │  (B2B RAW)               │  │  (B2C RAW)               │        │
│   │  ~12,500+ rows           │  │  ~8,900+ rows            │        │
│   └────────────┬─────────────┘  └────────────┬─────────────┘        │
│                │                              │                     │
└────────────────┼──────────────────────────────┼─────────────────────┘
                 │        동기화 (sync.py)       │
                 │   ┌──────────────────────┐   │
                 └──►│  행 수 비교           │◄──┘
                     │  차이 시 TRUNCATE     │
                     │  + INSERT 복사        │
                     └──────────┬────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│                     로컬 MySQL (EC2)          │                     │
│                                               ▼                     │
│   ┌──────────────────────────┐  ┌──────────────────────────┐        │
│   │  reportbusiness_es_old_v2│  │  report_es_old           │        │
│   │  (B2B 복제본)             │  │  (B2C 복제본)             │        │
│   └────────────┬─────────────┘  └────────────┬─────────────┘        │
│                │                              │                     │
│        ┌───────▼──────────────────────────────▼───────┐             │
│        │              집계 VIEW                        │             │
│        │  ┌─────────────────┐  ┌─────────────────┐    │             │
│        │  │ v_summary_b2b   │  │ v_summary_b2c   │    │             │
│        │  │ GROUP BY:       │  │ GROUP BY:       │    │             │
│        │  │ region, country,│  │ region, country,│    │             │
│        │  │ year, month     │  │ division,       │    │             │
│        │  │                 │  │ year, month     │    │             │
│        │  └────────┬────────┘  └────────┬────────┘    │             │
│        └───────────┼────────────────────┼─────────────┘             │
│                    │                    │                            │
└────────────────────┼────────────────────┼────────────────────────────┘
                     │                    │
         ┌───────────▼────────────────────▼───────────────┐
         │              백엔드 API (FastAPI)                │
         │                                                 │
         │   조회 우선순위:                                  │
         │   ① 캐시 → ② VIEW → ③ SQL 직접 → ④ pandas      │
         │                                                 │
         │   ┌──────────────────────────────────────────┐  │
         │   │  /api/summary  → data_service.py          │  │
         │   │  /api/stats    → data_service.py          │  │
         │   │  /api/trend    → data_service.py          │  │
         │   │  /api/filters  → data_service.py          │  │
         │   │  /api/export/* → export_service.py        │  │
         │   └──────────────────┬───────────────────────┘  │
         └──────────────────────┼───────────────────────────┘
                                │ JSON 응답
                                ▼
         ┌──────────────────────────────────────────────────┐
         │              프론트엔드 (브라우저)                  │
         │                                                  │
         │   api.js → state.js → Components 렌더링           │
         │                                                  │
         │   ┌────────────┬────────────┬───────────────────┐│
         │   │ ScoreCards │ BarChart   │ TrendChart        ││
         │   │ DataTable  │ MultiSelect│ Toast             ││
         │   └────────────┴────────────┴───────────────────┘│
         └──────────────────────────────────────────────────┘
```

---

## 2. B2B 데이터 흐름 상세

### 2.1 원천 테이블

| 항목 | 값 |
|------|-----|
| **테이블** | `reportbusiness_es_old_v2` |
| **DB** | `lg_ha` |
| **필터 조건** | `scoring = 'Y'` (대소문자 무관) |
| **집계 키** | `region`, `country` |
| **시계열 키** | `year`, `month`, `week` |

### 2.2 스코어 계산 방식

**B2B 스코어 항목 (만점 85점)**:

| No | 항목 | DB 컬럼 (v2) | DB 컬럼 (legacy) | 만점 |
|----|------|-------------|-----------------|------|
| 1 | Title Tag | `title_tag_score` | - (없으면 0) | 20 |
| 2 | Description Tag | `description_tag_score` | - (없으면 0) | 20 |
| 3 | H1 Tag | `h1_tag_score` | `h1_tag_pf` | 15 |
| 4 | Canonical Link | `canonical_link_score` | `canonical_link_pf` | 15 |
| 5 | Feature Alt Text | `feature_alt_score` | `feature_cards` | 15 |

**Total Score 계산**:

```
Total Score % = (Title + Description + H1 + Canonical + Feature Alt) / 85 × 100
```

**예시**:
```
Title=18.5, Description=17.2, H1=14.1, Canonical=14.8, Feature Alt=12.3
Sum = 76.9
Total Score % = 76.9 / 85 × 100 = 90.47%
```

### 2.3 집계 로직 (region·country 별)

```python
# 의사 코드
filtered = raw_data[raw_data.scoring == 'Y']
grouped = filtered.groupby(['region', 'country']).agg(
    sku_count = count(*),
    title_tag_score = AVG(title_tag_score),
    description_tag_score = AVG(description_tag_score),
    h1_tag_score = AVG(h1_tag_score),
    canonical_link_score = AVG(canonical_link_score),
    feature_alt_score = AVG(feature_alt_score),
)
grouped.total_score_pct = SUM(5개 항목) / 85.0 × 100.0
```

### 2.4 NULL 처리 규칙

| 상황 | 처리 |
|------|------|
| DB 값이 NULL | → `COALESCE(..., 0)` 로 **0** 대체 |
| DB 값이 빈 문자열 | → `pd.to_numeric(errors='coerce')` → NaN → **0** |
| 컬럼이 테이블에 없음 | → 해당 항목 **0** 처리 (Title/Description 등) |
| region 또는 country가 빈 문자열 | → 해당 행 **제외** |

### 2.5 컬럼명 자동 매핑

파이프라인은 테이블 구조에 따라 자동으로 컬럼을 매핑한다:

```
[DB 실제 컬럼]              [표준 컬럼]
h1_tag_pf              →    h1_tag_score
canonical_link_pf      →    canonical_link_score
feature_cards          →    feature_alt_score
scoring                →    scoring_yn
```

매핑 우선순위:
1. v2 스키마 컬럼이 존재하면 그대로 사용 (`h1_tag_score`)
2. legacy 컬럼이 존재하면 표준명으로 rename (`h1_tag_pf` → `h1_tag_score`)
3. `.env`의 `B2B_SCORE_SCHEMA=v2|legacy`로 강제 지정 가능

---

## 3. B2C 데이터 흐름 상세

### 3.1 원천 테이블

| 항목 | 값 |
|------|-----|
| **테이블** | `report_es_old` |
| **DB** | `lg_ha` |
| **필터 조건** | `monitoring = 'Y'` |
| **집계 키** | `region`, `country`, `division` |
| **시계열 키** | `year`, `month`, `week` |

### 3.2 스코어 계산 방식

**B2C 스코어 항목 (만점 100점)**:

| No | 항목 | DB 컬럼 | 만점 |
|----|------|---------|------|
| 1 | UFN | `ufn_score` | 10 |
| 2 | Basic Assets | `basic_assets_score` (`basic_asset_score`) | 10 |
| 3 | Spec Summary | `spec_summary_score` (`summary_spec_score`) | 10 |
| 4 | FAQ | `faq_score` (`faqs_score`) | 10 |
| 5 | Title Tag | `title_score` (`title_tag_score`) | 10 |
| 6 | Description Tag | `description_score` (`description_tag_score`) | 10 |
| 7 | H1 Tag | `h1_score` (`h1_tag_score`) | 10 |
| 8 | Canonical Link | `canonical_score` (`canonical_link_score`) | 10 |
| 9 | Alt Feature | `alt_feature_score` (`feature_alt_score`) | 10 |
| 10 | Alt Front | `alt_front_score` (`front_image_alt_score`) | 10 |

> 괄호 안은 DB에서 올 수 있는 대체 컬럼명 (자동 매핑 대상)

**Total Score 계산**:

```
Total Score % = (10개 항목 합계) / 100 × 100
             = 10개 항목 합계 (%)
```

### 3.3 집계 로직 (region·country·division 별)

```python
# 의사 코드
filtered = raw_data[raw_data.monitoring == 'Y']
grouped = filtered.groupby(['region', 'country', 'division']).agg(
    sku_count = count(*),
    ufn_score = AVG(ufn_score),
    basic_assets_score = AVG(basic_assets_score),
    # ... 나머지 8개 항목
)
grouped.total_score_pct = SUM(10개 항목) / 100.0 × 100.0
```

### 3.4 B2C 컬럼명 자동 매핑

```
[DB 실제 컬럼]              [표준 컬럼]
basic_asset_score      →    basic_assets_score
summary_spec_score     →    spec_summary_score
faqs_score             →    faq_score
front_image_alt_score  →    alt_front_score
```

---

## 4. 데이터 조회 우선순위

API 요청이 들어올 때 데이터를 가져오는 전략:

```
┌─────────────────────────────────────────────────────────┐
│  GET /api/summary?report_type=B2B&year=2025&month=3     │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
              ┌──── ① 캐시 확인 ────┐
              │  키 = (B2B, 2025, 3, │
              │        [], [])       │
              └──────┬──────────────┘
                     │
              ┌──────▼──────┐
              │  캐시 히트?   │
              │  TTL 이내?   │
              └──┬──────┬───┘
              Yes│      │No
                 ▼      ▼
         [캐시 반환]  ┌──── ② VIEW 조회 ────┐
                     │  SUMMARY_VIEW_B2B    │
                     │  설정 여부 확인        │
                     └──────┬──────────────┘
                            │
                     ┌──────▼──────┐
                     │  VIEW 있음?  │
                     └──┬──────┬───┘
                     Yes│      │No
                        ▼      ▼
               [VIEW 조회]  ┌──── ③ SQL 직접 집계 ────┐
                     │      │  RAW 테이블에서           │
                     │      │  GROUP BY + AVG           │
                     │      └──────┬───────────────────┘
                     │             │
                     │      ┌──────▼──────┐
                     │      │  SQL 성공?   │
                     │      └──┬──────┬───┘
                     │      Yes│      │No
                     │         ▼      ▼
                     │  [SQL 결과]  ┌──── ④ pandas 폴백 ────┐
                     │      │      │  SELECT * → preprocess  │
                     │      │      │  → aggregate             │
                     │      │      └──────┬─────────────────┘
                     │      │             │
                     ▼      ▼             ▼
              ┌──────────────────────────────────┐
              │  결과 후처리:                      │
              │  - Decimal → float 변환            │
              │  - NULL → 0.0 보정                 │
              │  - 소수점 6자리 반올림              │
              │  - region/country 필터 적용         │
              │  - 캐시에 저장                      │
              └──────────────┬───────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  JSON 응답 반환               │
              │  { data: [...], meta: {...} } │
              └──────────────────────────────┘
```

---

## 5. 트렌드 데이터 흐름

### 5.1 월별 트렌드

- **집계**: `GROUP BY region, country, year, month`
- **결과**: 각 region·country 조합의 월별 평균 점수 추이
- **프론트엔드**: Region별로 시리즈를 만들어 라인 차트 표시

```
[VIEW / SQL]
    │
    ├─ 2025-01: { ASIA: 90.2, EU: 86.5, NA: 83.1, ... }
    ├─ 2025-02: { ASIA: 92.5, EU: 88.1, NA: 85.3, ... }
    └─ 2025-03: { ASIA: 94.8, EU: 89.7, NA: 87.0, ... }
    │
    ▼
[프론트엔드 TrendChart.js]
    Series: ASIA ──●──●──●
            EU   ──●──●──●
            NA   ──●──●──●
```

### 5.2 주별 트렌드

- **집계**: `GROUP BY region, country, year, week`
- 동일 구조, X축이 주차(W01, W02, ...)로 변경

---

## 6. 파이프라인 전처리 상세

### 6.1 B2B 전처리 단계

```
[1] 컬럼명 표준화
    - DB/엑셀의 다양한 컬럼명 → 표준명 매핑
    - 예: h1_tag_pf → h1_tag_score

[2] 필터링
    - scoring_yn IN ('Y', 'YES', '1') 인 행만 유지
    - region, country 가 빈 값인 행 제외

[3] 타입 정규화
    - 점수 컬럼: pd.to_numeric(errors='coerce') → float
    - year, month, week: int로 변환

[4] 결측 처리
    - 점수 컬럼 NaN → 0.0
    - 존재하지 않는 점수 컬럼 → 0으로 채운 새 컬럼 생성
```

### 6.2 B2C 전처리 단계

```
[1] 컬럼명 표준화
    - basic_asset_score → basic_assets_score
    - summary_spec_score → spec_summary_score
    - faqs_score → faq_score
    - front_image_alt_score → alt_front_score

[2] 필터링
    - monitoring = 'Y' 인 행만 유지
    - region, country 가 빈 값인 행 제외

[3] 타입 정규화
    - 10개 점수 컬럼: pd.to_numeric(errors='coerce') → float
    - year, month, week: int로 변환

[4] 결측 처리
    - 점수 컬럼 NaN → 0.0
```

---

## 7. 동기화 흐름 상세

### 7.1 체크 + 증분 동기화 (기본)

```
[sync.py 실행]
    │
    ▼
[원격 DB 연결] ── 실패 → 에러 로그 → 종료
    │
    ▼
[행 수 비교]
    ├─ 원격 B2B 행 수 vs 로컬 B2B 행 수
    └─ 원격 B2C 행 수 vs 로컬 B2C 행 수
    │
    ├─ 차이 없음 → sync_log에 'skipped' 기록 → 종료
    │
    └─ 차이 있음 → 해당 테이블만:
         │
         ├─ TRUNCATE 로컬 테이블
         ├─ 원격 SELECT * → 로컬 INSERT (배치)
         ├─ VIEW 갱신 (VIEW는 자동 반영)
         └─ sync_log에 'success' + rows_synced 기록
```

### 7.2 강제 전체 동기화

```bash
python pipeline/sync.py --force
```

- 행 수 비교 없이 B2B/B2C 모두 TRUNCATE + 재복사

### 7.3 스케줄링

```
# crontab 예시: 매일 새벽 2시 동기화
0 2 * * * cd /home/ubuntu/DI/LG_ES_v3.0 && .venv/bin/python pipeline/sync.py >> logs/sync.log 2>&1

# 또는 APScheduler로 앱 내부 스케줄링 (선택)
```

---

## 8. 프론트엔드 데이터 흐름

### 8.1 초기 로드 시퀀스

```
[1] app.js: init()
    │
    ├─ api.getReports()            → GET /api/reports
    │   → 사용 가능한 연도/월 목록 확인
    │   → state.year, state.month 설정
    │
    ├─ api.getFilters(type, year, month) → GET /api/filters
    │   → Region/Country 목록 가져오기
    │   → MultiSelect 컴포넌트 초기화
    │
    └─ loadDashboard()
        │
        ├─ api.getSummary(...)      → GET /api/summary
        │   → ScoreCards 렌더링
        │   → DataTable 렌더링
        │   → BarChart 렌더링
        │
        └─ api.getTrend(...)        → GET /api/trend
            → TrendChart 렌더링
```

### 8.2 필터 변경 시 흐름

```
[사용자 필터 변경]
    │
    ├─ B2B/B2C 탭 변경 → state.type 업데이트
    │                     → getFilters() 재호출 (Region/Country 갱신)
    │                     → loadDashboard() 재실행
    │
    ├─ Year/Month 변경 → state.year/month 업데이트
    │                    → getFilters() 재호출
    │                    → loadDashboard() 재실행
    │
    └─ Region/Country 변경 → state.selectedRegions/Countries 업데이트
                             → loadDashboard() 재실행 (필터 파라미터 포함)
```

### 8.3 상태 구조

```javascript
// state.js
const state = {
  // 인증
  user: null,              // { id, email, name, role }
  isAuthenticated: false,

  // 필터
  type: 'b2b',             // 'b2b' | 'b2c'
  year: 2026,              // 현재 연도
  month: 2,                // 현재 월
  selectedRegions: [],     // [] = 전체
  selectedCountries: [],   // [] = 전체

  // 네비게이션
  section: 'dashboard',    // 'dashboard' | 'summary' | 'detail' | 'checklist'

  // 데이터
  reports: [],             // 사용 가능한 리포트 목록
  filters: {},             // { regions, countries, divisions }
  summaryData: [],         // 현재 Summary 행 목록
  trendData: {},           // { labels, series }
  statsData: {},           // 집계 통계

  // 테이블 상태
  sortCol: null,
  sortDir: 'asc',
  scoreFilter: '',         // '' | 'top30' | 'bottom30'

  // UI 상태
  loading: false,
  error: null,
};
```

---

## 9. 데이터 변환 매핑 (API → 프론트엔드)

### 9.1 B2B Summary 테이블

| 테이블 열 | API 키 | 표시 형식 | 비고 |
|----------|--------|----------|------|
| Region | `region` | 문자열 | |
| Country | `country` | 문자열 | |
| SKU | `sku_count` | 정수 (콤마 구분) | |
| 1. Title (20) | `title_tag_score` | 소수 1자리 | 만점 20 |
| 2. Description (20) | `description_tag_score` | 소수 1자리 | 만점 20 |
| 3. H1 (15) | `h1_tag_score` | 소수 1자리 | 만점 15 |
| 4. Canonical (15) | `canonical_link_score` | 소수 1자리 | 만점 15 |
| 5. Feature Alt (15) | `feature_alt_score` | 소수 1자리 | 만점 15 |
| Total Score % | `total_score_pct` | 소수 1자리 + `%` | 컬러 코딩 |

### 9.2 B2C Summary 테이블

| 테이블 열 | API 키 | 표시 형식 | 비고 |
|----------|--------|----------|------|
| Region | `region` | 문자열 | |
| Country | `country` | 문자열 | |
| Division | `division` | 문자열 | B2C만 |
| SKU | `sku_count` | 정수 (콤마 구분) | |
| UFN (10) | `ufn_score` | 소수 1자리 | |
| Basic Assets (10) | `basic_assets_score` | 소수 1자리 | |
| Spec Summary (10) | `spec_summary_score` | 소수 1자리 | |
| FAQ (10) | `faq_score` | 소수 1자리 | |
| Title (10) | `title_score` | 소수 1자리 | |
| Description (10) | `description_score` | 소수 1자리 | |
| H1 (10) | `h1_score` | 소수 1자리 | |
| Canonical (10) | `canonical_score` | 소수 1자리 | |
| Alt Feature (10) | `alt_feature_score` | 소수 1자리 | |
| Alt Front (10) | `alt_front_score` | 소수 1자리 | |
| Total Score % | `total_score_pct` | 소수 1자리 + `%` | 컬러 코딩 |

### 9.3 컬러 코딩 규칙

| Total Score % 범위 | 색상 | CSS 변수 |
|-------------------|------|----------|
| ≥ 90% | 녹색 | `var(--green)` = `#16a34a` |
| ≥ 70% ~ < 90% | 주황 | `var(--orange)` = `#ea580c` |
| < 70% | 빨강 | `var(--red-200)` = `#c70805` |

---

## 10. CSV 다운로드 데이터 흐름

### 10.1 Summary CSV (프론트엔드 생성)

```
[버튼 클릭: Download CSV]
    │
    ▼
[현재 state.summaryData 가져오기]
    │
    ▼
[CSV 변환]
    - 헤더: 테이블 컬럼 라벨
    - 행: 각 데이터 행의 값
    - BOM 추가 (Excel 한글 호환)
    │
    ▼
[Blob 생성 → 브라우저 다운로드]
    파일명: ES_{B2B|B2C}_{YEAR}_M{MONTH}.csv
```

### 10.2 RAW 데이터 다운로드 (서버 생성)

```
[버튼 클릭: Download RAW]
    │
    ▼
[GET /api/export/raw?report_type=B2B&format=csv]
    │
    ▼
[서버: DB에서 RAW 데이터 조회]
    │
    ▼
[StreamingResponse로 CSV 스트리밍]
    │
    ▼
[브라우저 파일 다운로드]
```
