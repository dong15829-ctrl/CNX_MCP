# LG ES Pro v1.0 — 프론트엔드 적용 명세 (v2.0 기반)

> **문서 버전**: 1.1  
> **최종 수정**: 2026-02-15  
> **상태**: v2.0 기반 재구성 진행

---

## 0. 변경 요약

- **기본 구현은 LG_ES_v2.0 프론트엔드(index.html 단일 파일)를 그대로 활용**한다.
- **변경 범위는 GNB 영역 + 주요 데이터셋**으로 제한한다.
- 나머지 UI/로직(차트 렌더링, 필터 동작, 테이블 정렬/필터, Raw 모달, 다운로드 등)은 v2.0 방식을 유지한다.

---

## 1. 베이스라인 (LG_ES_v2.0 유지 항목)

- 구조: `index.html` 단일 파일 + inline CSS/JS
- 차트: Chart.js CDN
- 데이터 로딩/렌더링 흐름: v2.0의 `getSummary → renderScoreSummary → renderTable → renderChart` 흐름 유지
- 기능: Summary, Monitoring Detail, Checklist, Raw Modal, 다운로드(Excel) 기본 동작 유지

---

## 2. GNB 변경 (v2.0 헤더 구조 유지, 항목/필터만 변경)

### 2.1 헤더 레이아웃 (3-Row 구조 유지)

```
Row 1: [LG Logo + ES Contents Monitoring]                 [Download ▼] [User ▼]
Row 2: [Dashboard] [Summary Table] [Monitoring Detail] [Checklist & Criteria]    [Year ▼] [Month ▼]
Row 3: [B2B] [B2C]                                                      [Region ▼] [Country ▼]
```

### 2.2 변경 포인트

- 기존 v2.0 `Summary / INFO` 탭 구조를 **위 4개 탭으로 변경**
- `Week` 필터는 **제거** (Year/Month만 유지)
- `INFO` 탭 하위의 `Notice / Q&A`는 **GNB에서 제외** (필요 시 추후 별도 복구)
- `Download`는 헤더 우측에 배치 (v2.0의 report 카드 내부 다운로드는 유지)

### 2.3 ID/클래스 변경 가이드 (적용 예정)

- `#tabSummary`, `#tabInfo` → `#tabDashboard`, `#tabSummaryTable`, `#tabMonitoringDetail`, `#tabChecklist`
- `#weekB2B` 필터 제거
- `#subNavInfo` 제거 (또는 비활성)
- `#headerUtilsWrap`에 Download/User 메뉴 추가

---

## 3. 주요 데이터셋 변경

### 3.1 Summary Table Columns

**B2B**

| key | label | 비고 |
|---|---|---|
| region | REGION | 텍스트 |
| country | COUNTRY | 텍스트 |
| sku_count | SKU | 숫자 |
| title_tag_score | 1. Title | 숫자 |
| description_tag_score | 2. Description | 숫자 |
| h1_tag_score | 3. H1 | 숫자 |
| canonical_link_score | 4. Canonical Link | 숫자 |
| feature_alt_score | 5. Alt text (Feature Cards) | 숫자 |
| total_score_pct | Total Score % | 숫자 |

**B2C**

| key | label | 비고 |
|---|---|---|
| region | REGION | 텍스트 |
| country | COUNTRY | 텍스트 |
| division | DIVISION | 텍스트 |
| sku_count | SKU | 숫자 |
| ufn_score | 1. UFN | 숫자 |
| basic_assets_score | 2. Basic Assets | 숫자 |
| spec_summary_score | 3. Spec Summary | 숫자 |
| faq_score | 4. FAQ | 숫자 |
| title_score | 5. Tag <Title> | 숫자 |
| description_score | 6. Tag <Description> | 숫자 |
| h1_score | 7. Tag <H1> | 숫자 |
| canonical_score | 8. Tag <Canonical Link> | 숫자 |
| alt_feature_score | 9. Tag <Alt text> (Feature) | 숫자 |
| alt_front_score | 10. Tag <Alt text> (Front) | 숫자 |
| total_score_pct | Total Score % | 숫자 |

**변경점**

- v2.0의 `Rank`, `Rank Change` 컬럼 **삭제**
- 표 헤더/정렬/필터 로직은 v2.0 구조 유지하되 컬럼 정의만 교체

### 3.2 Score Summary Keys

**B2B**: `total_score_pct`, `title_tag_score`, `description_tag_score`, `h1_tag_score`, `canonical_link_score`, `feature_alt_score`

**B2C**: `total_score_pct`, `ufn_score`, `basic_assets_score`, `spec_summary_score`, `faq_score`, `title_score`, `description_score`, `h1_score`, `canonical_score`, `alt_feature_score`, `alt_front_score`

### 3.3 Chart Aggregation Keys

- **B2B**: `title_tag_score`, `description_tag_score`, `h1_tag_score`, `canonical_link_score`, `feature_alt_score`
- **B2C**: `ufn_score`, `basic_assets_score`, `spec_summary_score`, `faq_score`, `title_score`, `description_score`, `h1_score`, `canonical_score`, `alt_feature_score`, `alt_front_score`

---

## 4. 구현 변경 위치 (v2.0 기준)

아래 항목을 `LG_ES_Pro_v1.0/frontend/index.html`로 이관 후 수정한다.

- **GNB**: `.page-header` 내부 Row 구조, 탭/필터/다운로드/유저 메뉴
- **컬럼 정의**: `SUMMARY_TABLE_COLS_B2B`, `SUMMARY_TABLE_COLS_B2C`
- **요약 카드**: `SCORE_SUMMARY_KEYS_B2B`, `SCORE_SUMMARY_KEYS_B2C`
- **차트 집계**: `AGGREGATE_CHART_KEYS_B2B`, `AGGREGATE_CHART_KEYS_B2C`
- **차트 라벨/색상**: `CHART_SCORE_KEYS_B2B`, `CHART_SCORE_KEYS_B2C`

---

## 5. 확인 필요 사항

- GNB의 **다운로드/유저 메뉴 구성**(텍스트/아이콘/드롭다운 항목)
- `Notice/Q&A` 유지 여부
- `Week` 필터 제거 확정 여부
- Summary 외 부가 패널(PLP/Blog/Product Category) 유지 여부

---

## 6. Menu Navigation (레퍼런스: 사이드바)

> 제공된 시안 기준의 **좌측 사이드바 메뉴** 참고 섹션.  
> 실제 구현은 v2.0 GNB 구조를 우선 적용하되, 사이드바 요구 발생 시 아래 항목을 기준으로 한다.

### 6.1 메뉴 구조

- Monitoring Item  
- Summary Dashboard  
- B2C Dashboard  
- B2B Dashboard  
- FAQ

### 6.2 상태 규칙

- 활성화된 메뉴는 **배경색 강조**로 구분한다.
- 비활성 메뉴는 기본 텍스트 컬러를 유지한다.

### 6.3 팔레트 (시안 기준)

- `#F0ECE4` (배경 톤)
- `#A50034` (LG Red)
- `#BE0D3E` (LG Red Dark)
- `#FEEBF1` (LG Red Background)
- `#9CA3AF` (텍스트 회색)
- `#CCD2D8` (보더)
- `#008000` (성공/긍정)
- `#000000` (텍스트)
