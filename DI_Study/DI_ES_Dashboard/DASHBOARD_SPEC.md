# DI_ES Dashboard Spec (Draft)

- 작성일: 2026-01-30
- 상태: Draft v0.1
- 범위(데이터): `DI_ES_Dashboard/Data/*.xlsx` (LG.com ES B2B/B2C Contents Monitoring Report, 월별)
- 결정(2026-01-30):
  - 구현 방식: **옵션 B(DB + API)**
  - 현재 운영: **Excel 업로드 → MySQL 적재 → API 조회 → 대시보드**
  - 궁극 목표: **운영 DB(MySQL) 연동 기반으로 view/집계를 통해 “준실시간” 대시보드 구동**

## 0. 이 문서의 목표

엑셀로 제공되는 “LG.com ES B2B/B2C Contents Monitoring Report”를 **월/국가/항목 기준으로 한눈에 비교**하고, **문제(에러/하위 성과)까지 드릴다운**할 수 있는 웹 대시보드의 요구사항·화면·데이터/기술 설계를 합의하는 문서.

> 원칙: “빠르게 요약 → 비교 → 드릴다운 → 근거 데이터 확인” 흐름을 끊지 않는다.

---

## 1. 성공 기준(초안)

- 월별 리포트 업로드/반영이 10분 이내(내부 기준, 파일 1개 기준)로 완료된다.
- 특정 월/국가에서 **총점 하락의 원인(Title/Desc/H1/Canonical/Alt/Category/Blog 등)** 을 3클릭 이내로 확인한다.
- “Bottom 30% / Error 시트” 기반 이슈를 국가/페이지 단위로 추적할 수 있다.

---

## 2. 대상 사용자 & 주요 시나리오

### 2.1 사용자(가정)
- SEO/콘텐츠 운영 담당자: 국가별 성과 확인, 개선 우선순위 도출
- QA/콘텐츠 퍼블리싱 담당자: Alt text 등 오류 리스트 확인/재현
- 매니저: 월간 성과 요약, Top/Bottom 국가 확인

### 2.2 핵심 시나리오
1) 이번 달(예: 2025-M11) B2C에서 **총점이 가장 낮은 국가 Top N** 확인 → 세부 항목 기여도 확인  
2) 전월 대비 하락한 국가를 선택 → 어떤 항목이 하락했는지(예: Canonical) 확인 → 관련 상세 시트/페이지로 이동  
3) “Feature Card Alt Text Error”에서 에러가 많은 국가/페이지를 필터링 → CSV로 내보내기(옵션)

---

## 3. 데이터 이해(현 보유 파일 기준)

### 3.1 파일/업데이트 규칙(가정)
- 월별 신규 `.xlsx` 파일이 추가됨
- 파일명에서 `B2B/B2C`, `YYYY-M##` 식별 가능
- 월별로 시트 구성이 일부 달라질 수 있음(예: `Bottom 30%` 존재 여부)

### 3.2 시트 구성(예시)
- **B2B**: `Summary`, `Summary (최종)`, `Monitoring Detail`, `Checklist & Criteria`, `PLP_BUSINESS`, `Blog`, `Feature Card Alt Text Error`, `Product Category` (+월별 `Bottom 30%`)
- **B2C**: `Summary by Country`, `Monitoring detail`, `Checklist & Criteria`, `PDP_Raw`, `Feature Card Alt Text Error` (+월별 `Bottom 30%`)

### 3.3 리스크/주의점
- 일부 시트는 **1행에 헤더가 없고**, 상단에 제목/메모가 있으며 **멀티 헤더(2~3행)** 일 수 있음 → “헤더 행 자동 탐지”가 필요
- `Summary` vs `Summary (최종)` 중 어떤 값이 “공식 지표”인지 결정 필요
- B2B/B2C 간 용어/시트명이 다름(`Monitoring Detail` vs `Monitoring detail`)

---

## 4. 대시보드 IA(정보구조) 제안

### 4.1 MVP(1차) 메뉴
- Overview
- Country Ranking
- Country Detail
- Issues (Bottom 30% / Alt Text Error)
- Data Admin (업로드/반영 현황, 파싱 로그)

### 4.2 공통 필터(상단 고정)
- Report Type: `B2B | B2C`
- Period: `YYYY-M##` (단일 선택 + 전월/전년동월 비교 토글 옵션)
- Region / Country (다중 선택)
- (가능 시) Page Type: `PDP | PLP | Blog ...` (시트에 따라 노출)

---

## 5. 화면 설계(초안)

### 5.1 Overview
- KPI 카드
  - 평균 Total Score(선택한 필터 기준)
  - 국가 수 / SKU(가능 시)
  - 전월 대비 증감(옵션)
- 차트
  - 월별 평균 Total Score 트렌드(최근 N개월)
  - Criteria Breakdown(국가 평균 기준 막대/스택)
- 테이블
  - Country Ranking(정렬/검색, 클릭 시 Country Detail로)

### 5.2 Country Detail
- 선택한 국가의
  - Total/SEO/Criteria 점수 요약
  - 전월 대비 증감(워터폴/Δ표시)
  - 관련 상세 데이터(가능한 경우: 페이지 목록, 에러 목록)

### 5.3 Issues
- Bottom 30%: 국가/페이지별 하위 성과 리스트, 기준(총점/특정 항목) 선택
- Feature Card Alt Text Error: 에러 유형/URL/콘텐츠 정보 테이블, 국가/기간 필터

---

## 6. 지표 정의(초안: 합의 필요)

> 실제 컬럼명/가중치는 `Checklist & Criteria` 시트 기반으로 “정의 테이블”을 만들고, 화면에도 툴팁으로 노출하는 것을 권장.

- Total Score: 보고서 내 총점(기준 시트 합의 필요)
- SEO Score: 보고서 내 SEO 관련 점수(정의 확인 필요)
- Criteria Score(예시): Title, Description, H1, Canonical, Alt Text, Product Category, Blog
- Bottom 30%: “하위 30%” 산정 기준(총점? 특정 지표?) 확인 필요

---

## 7. 구현 아키텍처 옵션

### 옵션 A) 정적 JSON(가장 빠른 MVP)
- 파이프라인: Excel → (스크립트) JSON 생성 → 프론트에서 로드
- 장점: 구현/배포 간단, 서버 부담 적음
- 단점: 데이터 커지면 로딩/검색 한계, 업데이트 시 빌드 필요

### 옵션 B) DB + API (**선택**)
- 파이프라인(현재): **Excel 업로드 → ETL → MySQL(+집계/뷰) → API → 프론트**
- 파이프라인(궁극): **운영 DB(MySQL) → 집계/뷰(or ETL) → API → 프론트(준실시간)**
- 장점: 필터/검색/페이지네이션, 증분 적재, 감사로그/관리 기능에 유리
- 단점: 초기 구현량 증가, 파싱 규칙/스키마 합의 필요

#### 7.1 구성 요소(권장 아키텍처)
```
┌───────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  Web Frontend │    │     Backend API     │    │        MySQL        │
│   (Next.js)   │◀──▶│ (FastAPI)           │◀──▶│ - report_files       │
└───────┬───────┘    │ - Query endpoints   │    │ - country_summary    │
        │            │ - Admin endpoints   │    │ - issues_*           │
        │            │ - Auth(옵션)        │    │ - (views/aggregates) │
        │            └─────────┬───────────┘    └──────────┬──────────┘
        │                      │                             │
        │                      ▼                             │
        │            ┌─────────────────────┐                 │
        │            │  Ingestion Worker   │                 │
        │            │  (Celery/RQ/cron)   │─────────────────┘
        │            │ - Parse Excel/DB    │
        │            │ - Validate/Transform│
        │            │ - Load/Aggregate    │
        │            └─────────────────────┘
        │
        ▼
┌────────────────┐
│ Excel Upload   │
│ (Admin UI/API) │
└────────────────┘
```

#### 7.2 “준실시간”의 정의(제안)
- **v1(업로드 기반)**: 업로드 완료 시 즉시 ETL 수행 → 대시보드 반영(수 분 단위)
- **v2(운영 DB 연동)**: 스케줄/증분 동기화(예: 5~15분) + 캐시 무효화
- **v3(이벤트 기반)**: DB 변경 이벤트(예: binlog/CDC) → 집계 갱신 → SSE/WebSocket으로 UI 갱신(선택)

#### 7.3 적재 전략(제안)
- **Idempotent key**: `(report_type, year, month, source)` 단위로 “같은 기간 재업로드”를 허용
  - 권장: `report_files`에 `revision`(1,2,3…) 또는 `is_active` 플래그로 “현재 활성 버전” 관리
- **검증(Validate)**: 파일명 규칙/시트 존재/필수 컬럼/값 범위/중복 행 등
- **추적성(Audit)**: 파싱 로그/경고/에러를 DB에 저장 + Admin 화면에서 확인
- **성능**: 상세(행) 데이터는 필요 시에만 저장(예: Issues/Bottom30)하고, MVP는 국가 요약 위주로 시작

---

## 8. 데이터 모델 초안(옵션 B 기준)

> 실제 컬럼은 시트 분석 후 확정. 아래는 “조회에 유리한 최소 정규화” 방향의 초안.

- `report_files`
  - `id`, `report_type(B2B/B2C)`, `year`, `month`, `file_name`, `ingested_at`, `status`, `error_message`
- `country_summary`
  - `report_file_id`, `region`, `country`, `total_score`, `seo_score`, `title_score`, `desc_score`, `h1_score`, `canonical_score`, `alt_score`, `category_score`, `blog_score`, …
- `issues_alt_text` / `issues_bottom30`
  - `report_file_id`, `country`, `url(or key)`, `issue_type`, `details...`

---

## 9. API 초안(옵션 B 기준)

- `GET /api/periods?reportType=B2B`
- `GET /api/overview?reportType=B2B&period=2025-M11&countries=...`
- `GET /api/countries/ranking?reportType=...&period=...&sort=totalScore&order=desc`
- `GET /api/countries/{country}/detail?reportType=...&period=...`
- `GET /api/issues/alt-text?reportType=...&period=...&country=...`
- `GET /api/issues/bottom30?reportType=...&period=...&country=...`

### 9.1 Admin/Upload API(제안)
- `POST /api/admin/uploads` (multipart file 업로드)
- `GET /api/admin/uploads` (업로드 이력/상태)
- `GET /api/admin/uploads/{id}` (상세 로그/경고/에러)
- `POST /api/admin/uploads/{id}/reprocess` (재처리)

---

## 10. 우선순위 제안(MVP 범위)

1) **Country Ranking + Overview**(월/국가/항목 점수)
2) **전월 대비 비교**(국가별 Δ)
3) Issues: `Feature Card Alt Text Error`, `Bottom 30%`
4) (확장) Monitoring detail / PDP_Raw / PLP_BUSINESS 드릴다운

---

## 11. 백엔드 제안(Option B 기준)

> 상세 설계 문서: `DI_ES_Dashboard/BACKEND_ARCHITECTURE.md`

### 11.1 기술 스택(권장)
- Runtime: Python 3.11+ (패키지/운영 안정성 기준)
- API: FastAPI + Uvicorn
- DB: MySQL 8.x
- ORM/Migration: SQLAlchemy 2.x + Alembic
- Excel Parser: `openpyxl`(필수) + `pandas`(선택: 복잡한 변환 시)
- Background jobs: Celery(+Redis) 또는 RQ(+Redis) 또는 cron(초기 단순화)
- Observability: 구조화 로그(JSON), 처리 히스토리 테이블, (선택) Sentry/Prometheus

### 11.2 백엔드 모듈(권장 책임 분리)
- `ingestion/`
  - `sources/` (ExcelAdapter, DBAdapter)
  - `parsers/` (sheet별 파서, 헤더 탐지, 컬럼 매핑)
  - `validators/` (필수 컬럼, 값 범위, 중복, 기간)
  - `loaders/` (bulk insert, upsert, revision 관리)
- `api/`
  - `routes/` (overview, ranking, detail, issues, admin)
  - `schemas/` (Pydantic DTO)
  - `auth/` (옵션)
- `db/` (models, repositories, migrations)

### 11.3 “Excel 업로드 → 반영” 처리 흐름(제안)
1) Admin UI에서 파일 업로드
2) Backend가 `report_files` 레코드 생성(status=`pending`)
3) Worker가 파싱/검증/적재 수행(status=`processing` → `completed/failed`)
4) 완료 시 캐시 무효화(옵션) + 프론트에 상태 반영

---

## 12. 프론트엔드 제안

> 상세 화면 기획 문서: `DI_ES_Dashboard/FRONTEND_SCREENS.md`

### 12.1 기술 스택(권장)
- Framework: Next.js 14+ (App Router) + TypeScript
- UI: Tailwind CSS + shadcn/ui(기본 컴포넌트)
- Data fetching: TanStack Query(React Query)
- Charts: Apache ECharts(권장: 복잡한 비교/워터폴/툴팁 강함) 또는 Recharts(단순)
- Table: TanStack Table(필터/정렬/가상스크롤)
- Auth: 사내망 기준이면 Reverse Proxy 인증(우선) + 앱 레벨 권한은 추후(옵션)

### 12.2 라우팅(초안)
- `/` → Overview
- `/ranking` → Country Ranking
- `/countries/[country]` → Country Detail
- `/issues/alt-text`
- `/issues/bottom30`
- `/admin/uploads`

### 12.3 “준실시간” UI 업데이트 방식(제안)
- v1: 업로드 완료 후 **polling**(예: 5~10초)로 상태/데이터 갱신
- v2+: SSE(Web)로 업로드 상태/데이터 갱신(선택)

---

## 13. 프론트 화면 기획(영역별, 초안)

> 공통 레이아웃: 좌측 사이드바 + 상단 Global Filter Bar + 본문(카드/차트/테이블)

### 13.1 Global Filter Bar(모든 화면 상단)
- Period(단일) + Compare 토글(MoM/Yoy)
- Report Type(B2B/B2C)
- Region/Country 멀티셀렉트
- Apply/Reset
- (Admin 권한) Upload 버튼/상태 뱃지

### 13.2 Overview(요약)
- 상단 KPI Cards(4~6개)
  - Avg Total Score, Avg SEO Score(있다면), Countries count, Issues count(Alt/Error), MoM Δ
- 중단 Charts
  - Trend(월별 평균 Total Score)
  - Criteria Breakdown(항목별 평균/기여도)
- 하단 Table(Top/Bottom Countries)
  - 정렬/검색/필터, row 클릭 → Country Detail

### 13.3 Country Ranking(목록/비교)
- Controls
  - 정렬 기준: Total/SEO/각 항목, Top N, Threshold
  - Compare on/off(Δ 컬럼 추가)
- Table
  - Country, Region, Total Score, 각 항목 점수, Δ(옵션)
  - 행 클릭 → Country Detail

### 13.4 Country Detail(드릴다운)
- Header Summary
  - Total/SEO/항목 점수 + MoM Δ(색/아이콘)
- Charts
  - Waterfall(전월 대비 항목별 변화 기여도) 또는 Δ bar
  - Radar/Bar(항목 점수 프로파일)
- Detail Tabs
  - Issues(Alt Text / Bottom30 요약)
  - (확장) Monitoring detail / PDP_Raw / PLP_BUSINESS (가능 시)

### 13.5 Issues: Alt Text Error
- Filter
  - Country/기간/에러 유형
- Table
  - URL(or key), Issue detail, 발생 위치(가능 시), Export CSV(옵션)

### 13.6 Issues: Bottom 30%
- Filter
  - 기준(총점/항목), Country/기간
- Table
  - 대상, Score, 항목 breakdown, (가능 시) 원본 행 링크

### 13.7 Admin: Uploads
- Upload 영역
  - Drag & Drop + 파일 규칙 안내(예: `..._2025-M11.xlsx`)
- History 테이블
  - 파일명/기간/타입/상태/처리시간/경고 수
  - row 클릭 → 처리 로그(파싱 경고/에러, 누락 시트/컬럼)

---

## 14. 개발 로드맵(단계별)

### v1 (Excel Upload MVP)
- Data
  - 업로드 → 파싱/검증/적재(필수 시트 우선: Summary/Bottom30/AltText)
  - 기간/타입/국가 기준으로 조회 가능한 `country_summary` 중심 스키마 확정
- Backend
  - 조회 API: Overview/Ranking/Detail/Issues
  - Admin API: Uploads(+상태/로그/재처리)
- Frontend
  - Overview/Ranking/Detail/Issues/Admin Uploads 화면 구축
  - Compare(MoM) 기본 지원(가능하면 YoY는 v2)
- 운영
  - 배포 환경 결정(로컬/사내서버/사내망) + 기본 모니터링(로그/업로드 이력)

### v2 (운영 DB 연동)
- Data/Backend
  - 운영 DB → 대시보드 DB(권장) 또는 운영 DB view 직접 조회(선택) 구조 확정
  - 증분 업데이트 스케줄(예: 10~15분) + 캐시 무효화 전략
  - 추세/비교 지표 확대(YoY, 멀티 월 트렌드)
- Frontend
  - Trend/비교 UX 고도화(기간 멀티 선택, Δ 뷰 개선)
  - 드릴다운(가능 시): Monitoring detail / PDP_Raw / PLP_BUSINESS

### v3 (준실시간/운영 고도화)
- 실시간성
  - 업로드/집계 갱신을 SSE/WebSocket으로 push(선택)
  - (고도화) CDC/binlog 기반 이벤트 처리
- 운영/보안
  - 권한(역할 기반) + 감사로그 강화
  - 성능 최적화(인덱스/집계/쿼리 튜닝), 대용량 페이지네이션/가상스크롤

---

## 15. 당장 합의할 질문(Reply로 답 주세요)

1) “공식 점수” 기준 시트는 무엇인가요?  
   - B2B: `Summary` vs `Summary (최종)`  
   - B2C: `Summary by Country` 외 다른 기준이 있나요?
2) 대시보드 1차 사용자는 누구인가요(SEO/QA/매니저 중 우선순위)?
3) 비교는 어디까지 필요할까요?  
   - 전월(MoM) / 전년동월(YoY) / 여러 달 멀티선택
4) Issues 범위: `Alt Text Error`와 `Bottom 30%` 외에도 “필수로 들어가야 하는 시트”가 있나요?
5) 배포 형태: 로컬(개인 PC) / 사내 서버 / 사내망(인증 필요) 중 어디를 목표로 하나요?
6) 업로드 운영 정책: 같은 `YYYY-M##` 파일이 다시 업로드되면 “덮어쓰기”인가요, “버전 관리”인가요?
7) “준실시간” 요구: 실제로는 몇 분 주기의 업데이트면 충분할까요(예: 5/10/15/60분)?
