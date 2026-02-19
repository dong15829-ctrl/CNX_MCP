# DI_ES Dashboard Frontend 화면기획 (Draft)

- 작성일: 2026-01-30
- 상태: Draft v0.1
- 대상 데이터: LG.com ES B2B/B2C Contents Monitoring Report (월별)
- 목표: “요약 → 비교 → 드릴다운 → 이슈 확인/내보내기” 사용자 흐름을 최소 클릭으로 제공

---

## 1. 공통 UX 원칙

- **Filter-first**: 기간/타입/국가 필터를 모든 화면에서 동일 위치(상단 고정)로 제공
- **Drill-down**: 차트/테이블 클릭이 다음 화면의 필터로 자연스럽게 연결
- **Compare-ready**: MoM/YoY 비교는 “토글 + Δ 표시”로 일관되게 노출
- **Traceable**: 숫자/이슈는 가능한 한 원본 근거(해당 시트/행)로 이어지도록 설계(가능 범위 내)
- **Admin 분리**: 업로드/재처리/로그는 `/admin`에 격리

---

## 2. 공통 레이아웃

### 2.1 App Shell
- Left Sidebar
  - Overview
  - Country Ranking
  - Issues
    - Alt Text Error
    - Bottom 30%
  - Admin(권한 필요)
    - Uploads
- Top Bar
  - Global Filter Bar(아래 2.2)
  - (우측) Refresh 상태 / 업로드 상태 뱃지(옵션)
- Main Content
  - 페이지별 카드/차트/테이블 그리드

### 2.2 Global Filter Bar(상단 고정)
- Period: `YYYY-M##` (기본 단일 선택)
- Compare: Off / MoM / YoY
- Report Type: `B2B | B2C`
- Region: Multi-select (옵션, 데이터 제공 시)
- Country: Multi-select
- Actions: Apply / Reset

**동작 규칙(제안)**
- 기본은 “즉시 반영”이 아니라 **Apply 버튼으로 반영**(무거운 쿼리/차트 재로딩 방지)
- URL Querystring에 상태를 반영하여 공유 가능하도록(예: `?type=B2C&period=2025-M11&country=ES`)

---

## 3. 화면 정의(영역별)

각 화면은 “목적/영역 구성/상호작용/필요 데이터(API)” 형태로 기술합니다.

---

## 3.1 Overview (`/`)

### 목적
- 선택한 기간/타입에서 전체 성과를 빠르게 파악하고, 문제 국가로 진입

### 영역 구성
1) KPI Row(카드 4~6개)
   - Avg Total Score
   - Avg SEO Score(존재 시)
   - Countries Count
   - Issues Count(Alt Text Error)
   - Bottom 30% Count(존재 시)
   - Δ(Compare가 켜진 경우)
2) Charts Row
   - Trend: 월별 평균 Total Score(최근 N개월, 선택 기간 강조)
   - Criteria Breakdown: 항목별 평균(또는 비율) 막대/스택
3) Table Row
   - Top/Bottom Countries(탭 또는 세그먼트)

### 상호작용
- Country row 클릭 → `/countries/[country]` 이동(필터 유지)
- Criteria bar 클릭 → Ranking 화면으로 이동 + 해당 항목 정렬/필터 적용(옵션)
- Trend 점 클릭 → Period 변경 제안(옵션)

### 필요 데이터(API)
- `GET /api/overview` (카드+차트 요약)
- `GET /api/countries/ranking` (Top/Bottom 테이블)

---

## 3.2 Country Ranking (`/ranking`)

### 목적
- 국가별 성과를 정렬/필터링하여 “개선 우선순위”를 결정

### 영역 구성
1) Controls Bar
   - Sort by: Total/SEO/Criteria(Title/Desc/H1/Canonical/Alt/Category/Blog)
   - Top N(예: 10/20/50)
   - Threshold(예: Total Score < X)
   - Compare on/off(Δ 컬럼 표시)
2) Ranking Table
   - Country / Region
   - Total Score, SEO Score, Criteria scores
   - Δ(Compare on 시)
   - (옵션) Issues Count

### 상호작용
- 컬럼 헤더 정렬(기본은 서버 정렬 권장)
- 검색(국가명), 컬럼 숨김/표시(옵션)
- row 클릭 → Country Detail 이동

### 필요 데이터(API)
- `GET /api/countries/ranking` (pagination, sort, filters)

---

## 3.3 Country Detail (`/countries/[country]`)

### 목적
- 특정 국가의 점수 구성/변화 원인을 파악하고, 관련 이슈를 확인

### 영역 구성
1) Header Summary
   - Total Score / SEO Score / Criteria score chips
   - Compare가 켜진 경우 Δ 표시(색상 규칙: 상승=green, 하락=red, 0=muted)
2) Charts
   - Δ Waterfall(Compare on 시): 항목별 변화 기여도
   - Criteria Profile: Bar 또는 Radar
3) Tabs
   - `Issues`: Alt Text / Bottom 30% 요약 + 링크
   - `Details`(확장): Monitoring detail / PDP_Raw / PLP_BUSINESS 등 시트 기반 드릴다운(2차 범위)

### 상호작용
- 차트 클릭 → 해당 항목 기준으로 Issues/Details 필터링(옵션)
- Issues 카드 클릭 → 해당 Issues 화면으로 이동 + country filter preset

### 필요 데이터(API)
- `GET /api/countries/{country}/detail`
- `GET /api/issues/alt-text?...&country={country}` (요약 또는 최신 N개)
- `GET /api/issues/bottom30?...&country={country}`

---

## 3.4 Issues: Alt Text Error (`/issues/alt-text`)

### 목적
- Alt Text 관련 오류를 국가/기간별로 필터링하고, 실행 가능한 리스트를 제공

### 영역 구성
1) KPI(옵션)
   - Total errors, Affected countries, Top issue type
2) Filter Bar(추가)
   - Issue Type(가능 시), URL contains(검색), Export
3) Table
   - Country, URL(or key), Issue detail, 발견 위치(가능 시), 발생 횟수(가능 시)

### 상호작용
- row 클릭 → 상세 Drawer/Modal(원본 필드 노출)
- Export CSV(권한/용량 고려)

### 필요 데이터(API)
- `GET /api/issues/alt-text` (pagination + filters)

---

## 3.5 Issues: Bottom 30% (`/issues/bottom30`)

### 목적
- 하위 성과 대상(국가/페이지)을 기준별로 확인하여 개선 작업의 우선순위를 제공

### 영역 구성
1) Controls
   - 기준: Total / 특정 Criteria
   - Threshold(예: Bottom 30, Bottom 10, Top N worst)
2) Table
   - Country, 대상(페이지/키), Score, breakdown(가능 시), Δ(Compare on 시)

### 상호작용
- row 클릭 → Country Detail 또는 상세 Drawer
- Export CSV(옵션)

### 필요 데이터(API)
- `GET /api/issues/bottom30` (pagination + filters)

---

## 3.6 Admin: Uploads (`/admin/uploads`)

### 목적
- Excel 업로드 → 파싱/적재 상태 확인 → 실패 시 원인 확인 및 재처리

### 영역 구성
1) Upload Zone
   - Drag & Drop + 파일명 규칙 안내 + 허용 타입/용량 안내
   - 업로드 후 “처리중” 상태 표시
2) Upload History Table
   - file_name, report_type, period, status, duration, warnings_count
3) Upload Detail Drawer/Modal
   - 처리 로그(경고/에러), 파싱 결과 요약(적재 row 수)
   - 재처리 버튼(옵션)

### 상호작용
- Upload 완료 후 상태 polling(또는 SSE)로 진행률 반영
- 실패 시 에러 메시지/누락 시트/누락 컬럼 목록을 사용자 친화적으로 노출

### 필요 데이터(API)
- `POST /api/admin/uploads`
- `GET /api/admin/uploads`
- `GET /api/admin/uploads/{id}`
- `POST /api/admin/uploads/{id}/reprocess`

---

## 4. 상태/에러/성능 설계(요약)

### 4.1 Loading/Empty/Error UI
- Loading: Skeleton(카드/차트/테이블)
- Empty: “선택한 조건에 데이터가 없습니다” + Reset/가이드
- Error: “데이터를 불러오지 못했습니다” + 재시도 + (admin) request id/log link

### 4.2 성능 가이드(제안)
- Table은 서버 pagination 기본(초기), 필요 시 virtual scroll
- 차트는 “필터 적용 시”에만 재요청(Apply 기반)
- 비교(Δ)는 백엔드에서 계산하여 전달(프론트 계산 최소화)

---

## 5. 다음 논의 포인트

1) KPI/차트에서 “필수”로 보여줘야 하는 지표 5개는 무엇인가요?
2) Country Detail에서 “원인 분석”은 어떤 형태가 가장 유용한가요?
   - Waterfall(Δ 기여도) / Radar(프로파일) / 단순 막대(항목 비교)
3) Issues에서 CSV Export는 필수인가요? (권한/개인정보/URL 공개 정책 포함)

