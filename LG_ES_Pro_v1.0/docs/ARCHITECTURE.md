# LG ES v3.0 — 시스템 아키텍처 문서

> **문서 버전**: 1.0  
> **최종 수정**: 2026-02-11  
> **상태**: 설계 완료 → 구현 대기

---

## 1. 개요

### 1.1 목적

LG.com ES (Enterprise Solutions) Contents Monitoring 대시보드의 3세대 버전.  
B2B/B2C 제품 페이지의 SEO 및 콘텐츠 품질 점수를 **Region → Country → Division** 계층으로 모니터링하고, 시계열 트렌드를 추적하며, 데이터 기반 의사결정을 지원한다.

### 1.2 v3.0 핵심 목표

| # | 목표 | 설명 |
|---|------|------|
| 1 | **프론트엔드 모듈화** | v2.0의 단일 HTML(~2,500행)을 모듈별 JS 파일로 분리하여 유지보수성 확보 |
| 2 | **컴포넌트 기반 UI** | 재사용 가능한 UI 컴포넌트(ScoreCard, DataTable, FilterPanel 등) 설계 |
| 3 | **강화된 데이터 파이프라인** | 전처리·집계·캐싱 계층 명확화, 증분 동기화 지원 |
| 4 | **보안 고도화** | JWT 기반 인증 + Refresh Token, 역할 기반 접근 제어(RBAC) |
| 5 | **운영 안정성** | 헬스체크, 로깅, 에러 핸들링, 모니터링 강화 |
| 6 | **확장 가능 구조** | 새로운 리포트 타입(B2G 등) 추가 시 최소 변경으로 대응 |

### 1.3 v2.0 → v3.0 주요 개선 비교

| 항목 | v2.0 | v3.0 |
|------|------|------|
| 프론트엔드 | 단일 HTML (index.html ~140KB) | 모듈별 분리 (ES Modules) |
| 인증 | 세션 쿠키 (메모리 저장) | JWT + Refresh Token (DB 저장) |
| 캐싱 | 인메모리 dict (TTL 60s) | Redis 또는 인메모리 (계층별 TTL) |
| DB 접근 | pandas 우선 → SQL 폴백 | SQL VIEW 우선 → pandas 폴백 |
| 에러 처리 | 기본 HTTPException | 구조화된 에러 코드 + 프론트 토스트 |
| 관리자 기능 | 기본 사용자 승인 | 대시보드 내 관리자 패널 (사용자·로그·설정) |
| 데이터 동기화 | 수동 스크립트 | 스케줄러 기반 자동 동기화 + 상태 대시보드 |

---

## 2. 시스템 구성도

```
┌──────────────────────────────────────────────────────────────────────┐
│                         사용자 (브라우저)                             │
│    ┌────────────────────────────────────────────────────────┐        │
│    │              프론트엔드 (Vanilla JS + ES Modules)        │        │
│    │  ┌──────────┬──────────┬──────────┬──────────────────┐ │        │
│    │  │ Dashboard│ Summary  │Monitoring│  Checklist &     │ │        │
│    │  │  View    │  Table   │  Detail  │  Criteria        │ │        │
│    │  └──────────┴──────────┴──────────┴──────────────────┘ │        │
│    │  ┌──────────┬──────────┬──────────┬──────────────────┐ │        │
│    │  │  State   │  Router  │  API     │  Components      │ │        │
│    │  │  Manager │          │  Client  │  (Chart, Table)  │ │        │
│    │  └──────────┴──────────┴──────────┴──────────────────┘ │        │
│    └───────────────────────┬────────────────────────────────┘        │
│                            │  HTTP/S (JSON)                          │
└────────────────────────────┼─────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      백엔드 API (FastAPI)                              │
│                                                                        │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│   │  Auth    │  │ Summary  │  │  Trend   │  │  Admin               │  │
│   │  Router  │  │  Router  │  │  Router  │  │  Router              │  │
│   │ /auth/*  │  │ /api/*   │  │ /api/*   │  │ /admin/*             │  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────────────────┘  │
│        │             │             │              │                     │
│   ┌────▼─────────────▼─────────────▼──────────────▼─────────────────┐  │
│   │                     서비스 계층 (Service Layer)                    │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│  │
│   │  │  Auth    │  │  Data    │  │  Export  │  │  Admin            ││  │
│   │  │  Service │  │  Service │  │  Service │  │  Service          ││  │
│   │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────────────┘│  │
│   └───────┼──────────────┼─────────────┼─────────────┼──────────────┘  │
│           │              │             │             │                  │
│   ┌───────▼──────────────▼─────────────▼─────────────▼──────────────┐  │
│   │                       데이터 계층 (Data Layer)                    │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │  │
│   │  │  DB Pool │  │  Cache   │  │ Pipeline │  │  File Storage  │  │  │
│   │  │ (MySQL)  │  │ (Memory/ │  │ (pandas) │  │  (CSV/Export)  │  │  │
│   │  │          │  │  Redis)  │  │          │  │                │  │  │
│   │  └────┬─────┘  └──────────┘  └────┬─────┘  └────────────────┘  │  │
│   └───────┼───────────────────────────┼─────────────────────────────┘  │
│           │                           │                                │
└───────────┼───────────────────────────┼────────────────────────────────┘
            │                           │
            ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│   MySQL (lg_ha)  │        │  원격 MySQL       │
│   (로컬 복제본)    │◄──────│  (원천 데이터)     │
│                  │  동기화  │                  │
│  ┌────────────┐  │        │  ┌────────────┐  │
│  │ V_SUMMARY  │  │        │  │ RAW Tables │  │
│  │ (집계VIEW) │  │        │  │ (B2B/B2C)  │  │
│  ├────────────┤  │        │  └────────────┘  │
│  │ users      │  │        └──────────────────┘
│  ├────────────┤  │
│  │ sessions   │  │
│  └────────────┘  │
└──────────────────┘
```

---

## 3. 계층별 상세 설계

### 3.1 프론트엔드 계층

**기술**: HTML5, CSS3, Vanilla JavaScript (ES Modules), Chart.js 4.x

**디자인 원칙**:
- **LG 브랜드 가이드** 준수 (다크 헤더, LG Red #C41E3A 악센트)
- 프레임워크 없이 **ES Modules**로 모듈화 (빌드 도구 불필요)
- **반응형 레이아웃** (1440px max-width, 768px 이하 모바일 대응)

**모듈 구조**:

```
frontend/
├── index.html              # 메인 엔트리 포인트 (Shell)
├── login.html              # 로그인/회원가입 페이지
├── css/
│   ├── variables.css       # CSS 커스텀 프로퍼티 (디자인 토큰)
│   ├── layout.css          # 헤더, 컨테이너, 반응형
│   ├── components.css      # 카드, 테이블, 버튼, 필터 스타일
│   └── pages.css           # 페이지별 추가 스타일
├── js/
│   ├── app.js              # 앱 초기화, 라우팅
│   ├── state.js            # 전역 상태 관리 (State Machine)
│   ├── api.js              # API 클라이언트 (fetch 래퍼, 인증 헤더)
│   ├── router.js           # 해시 기반 라우터 (#dashboard, #summary ...)
│   ├── components/
│   │   ├── Header.js       # 헤더 (로고, 네비게이션, 필터, 다운로드)
│   │   ├── ScoreCards.js   # 대시보드 점수 카드 그리드
│   │   ├── BarChart.js     # Region별 항목 평균 막대 차트
│   │   ├── TrendChart.js   # 시계열 트렌드 라인 차트
│   │   ├── DataTable.js    # 정렬·필터·페이지네이션 범용 테이블
│   │   ├── MultiSelect.js  # 다중 선택 드롭다운 (Region/Country)
│   │   └── Toast.js        # 알림 토스트 메시지
│   ├── views/
│   │   ├── DashboardView.js   # 대시보드 섹션
│   │   ├── SummaryView.js     # Summary Table 섹션
│   │   ├── DetailView.js      # Monitoring Detail 섹션
│   │   ├── ChecklistView.js   # Checklist & Criteria 섹션
│   │   └── AdminView.js       # 관리자 패널 (선택)
│   └── utils/
│       ├── format.js       # 숫자 포맷, 날짜 포맷
│       ├── csv.js          # CSV 생성/다운로드 유틸
│       └── constants.js    # B2B/B2C 설정 상수 (컬럼, 라벨, 만점)
└── images/
    ├── lg-logo.svg         # LG 로고 (컬러)
    └── lg-logo-white.svg   # LG 로고 (화이트)
```

### 3.2 백엔드 계층

**기술**: FastAPI (Python 3.10+), Uvicorn, SQLAlchemy (선택), PyMySQL

**설계 원칙**:
- **라우터 분리**: 기능별 라우터 모듈 (auth, summary, trend, admin, export)
- **서비스 패턴**: 비즈니스 로직은 서비스 계층에 집중
- **의존성 주입**: FastAPI Depends로 인증·DB 세션 관리
- **구조화된 에러**: 일관된 에러 응답 형식

**모듈 구조**:

```
backend/
├── main.py                 # FastAPI 앱 생성, 미들웨어, 라우터 마운트
├── config.py               # 환경 변수 로드, 설정 클래스
├── database.py             # DB 커넥션 풀, 세션 관리
├── models.py               # Pydantic 스키마 (요청/응답 모델)
├── dependencies.py         # 공통 의존성 (인증, DB 세션)
├── routers/
│   ├── auth.py             # POST /auth/login, /auth/logout, /auth/register, /auth/me
│   ├── summary.py          # GET /api/summary, /api/stats, /api/filters, /api/reports
│   ├── trend.py            # GET /api/trend (월별/주별 트렌드)
│   ├── export.py           # GET /api/export/summary, /api/export/raw (다운로드)
│   └── admin.py            # GET/POST /admin/* (사용자 관리, 로그, 설정)
├── services/
│   ├── auth_service.py     # 인증·토큰·사용자 관리 로직
│   ├── data_service.py     # 데이터 집계·조회 로직 (VIEW 우선 → pandas 폴백)
│   ├── cache_service.py    # 캐싱 로직 (인메모리 또는 Redis)
│   └── export_service.py   # CSV/Excel 생성 로직
└── utils/
    ├── security.py         # 비밀번호 해싱, JWT 생성/검증
    └── logger.py           # 구조화된 로깅 설정
```

### 3.3 데이터 파이프라인 계층

**기술**: Python, pandas, PyMySQL

**모듈 구조**:

```
pipeline/
├── config.py               # DB 연결, 테이블/컬럼 매핑, 스코어 상수
├── preprocess.py           # RAW 데이터 전처리 (필터, 컬럼 매핑, 타입 정규화)
├── aggregate.py            # 집계 로직 (스냅샷, 월별/주별 트렌드)
├── sync.py                 # 원격 → 로컬 DB 동기화 (증분/전체)
├── scheduler.py            # 동기화 스케줄러 (cron/APScheduler)
└── run.py                  # 파이프라인 실행 엔트리 포인트
```

### 3.4 데이터 계층

**MySQL 스키마**:

```
lg_ha (Database)
├── reportbusiness_es_old_v2    # B2B RAW 데이터 (원격 동기화)
├── report_es_old               # B2C RAW 데이터 (원격 동기화)
├── v_summary_b2b               # B2B 집계 VIEW (region/country 별)
├── v_summary_b2c               # B2C 집계 VIEW (region/country/division 별)
├── users                       # 사용자 테이블 (인증)
├── refresh_tokens              # JWT Refresh Token 저장
├── sync_log                    # 동기화 이력 로그
└── audit_log                   # 활동 감사 로그
```

---

## 4. 데이터 흐름 요약

### 4.1 일반 조회 흐름

```
사용자 → 프론트엔드 → API (GET /api/summary)
                          │
                          ├─① 캐시 히트? → 캐시 응답 반환
                          │
                          ├─② 집계 VIEW 존재? → VIEW에서 조회 → 캐시 저장 → 응답
                          │
                          └─③ VIEW 없음 → RAW 테이블에서 SQL 집계
                                          → 실패 시 pandas 집계 폴백
                                          → 캐시 저장 → 응답
```

### 4.2 데이터 동기화 흐름

```
[스케줄러 / 수동 트리거]
    │
    ▼
[sync.py] ── 원격 DB 행 수 비교 ──→ 차이 없음 → 종료
    │
    │ (차이 있음)
    ▼
[원격 DB] → SELECT * → 로컬 DB TRUNCATE → INSERT → VIEW 갱신
    │
    ▼
[sync_log] 에 동기화 결과 기록
```

### 4.3 인증 흐름

```
[로그인] POST /auth/login
    │
    ▼
비밀번호 검증 (bcrypt)
    │
    ├─ 성공 → Access Token (JWT, 30분) + Refresh Token (7일) 발급
    │         Set-Cookie: access_token, refresh_token
    │
    └─ 실패 → 401 에러

[API 요청] Authorization: Bearer <access_token>
    │
    ├─ 유효 → 요청 처리
    ├─ 만료 → 자동으로 Refresh Token으로 갱신 시도
    └─ 무효 → 401 → 프론트엔드가 로그인 페이지로 리다이렉트
```

---

## 5. 대시보드 화면 구성

### 5.1 전체 레이아웃

```
┌─────────────────────────────────────────────────────────┐
│  HEADER (Sticky, Dark)                                  │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Row 1: [LG Logo] ES Contents Monitoring  [Download]││
│  ├─────────────────────────────────────────────────────┤│
│  │ Row 2: [Dashboard|Summary|Detail|Checklist]  [Year]││
│  │         [Month]                                     ││
│  ├─────────────────────────────────────────────────────┤│
│  │ Row 3: [B2B|B2C]  [Region ▼] [Country ▼]          ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│  MAIN CONTENT (max-width: 1440px)                       │
│                                                         │
│  [각 섹션은 네비게이션 탭에 따라 전환]                      │
│                                                         │
│  ┌─ Dashboard ──────────────────────────────────────┐   │
│  │  Score Cards (Overall, Total SKUs, Region별)      │   │
│  │  ┌──────────────────┬───────────────────────┐     │   │
│  │  │ Bar Chart        │ Trend Chart            │     │   │
│  │  │ (항목별 × Region) │ (월별 Total Score %)   │     │   │
│  │  └──────────────────┴───────────────────────┘     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ Summary Table ──────────────────────────────────┐   │
│  │  [Score Filter: All|Top 30%|Bottom 30%]           │   │
│  │  ┌──────────────────────────────────────────────┐ │   │
│  │  │  Region | Country | SKU | 항목1 | ... | Total│ │   │
│  │  │  정렬 가능, 컬러 코딩 (≥90% 녹색 | ≥70% 주황)│ │   │
│  │  └──────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ Monitoring Detail ──────────────────────────────┐   │
│  │  B2B: 5개 항목 설명 (Title, Description, H1 ...)  │   │
│  │  B2C: 추가 5개 항목 설명 (UFN, Assets, Spec ...)  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ Checklist & Criteria ───────────────────────────┐   │
│  │  B2B: 5항목, 만점 85점                             │   │
│  │  B2C: 10항목, 만점 100점                            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 5.2 B2B/B2C 탭 동작

| 모드 | 집계 키 | 스코어 항목 | 만점 |
|------|---------|------------|------|
| **B2B** | Region, Country | Title(20), Description(20), H1(15), Canonical(15), Feature Alt(15) | **85** |
| **B2C** | Region, Country, Division | UFN(10), Basic Assets(10), Spec Summary(10), FAQ(10), Title(10), Description(10), H1(10), Canonical(10), Alt Feature(10), Alt Front(10) | **100** |

---

## 6. 비기능 요구사항

### 6.1 성능

| 항목 | 목표치 |
|------|--------|
| Dashboard 초기 로드 | ≤ 2초 (집계 VIEW 사용 시) |
| API 응답 (캐시 히트) | ≤ 100ms |
| API 응답 (DB 직접 조회) | ≤ 1초 |
| 동시 사용자 | ≥ 50명 |

### 6.2 보안

| 항목 | 구현 |
|------|------|
| 비밀번호 저장 | bcrypt 해시 (passlib) |
| 토큰 | JWT (HS256), Access 30분, Refresh 7일 |
| API 접근 | 인증 필수 (Public: /auth/login, /login, / 만 허용) |
| CORS | 허용 Origin 화이트리스트 (운영 시) |
| DB 비밀번호 | 환경 변수, 코드 미포함 |

### 6.3 가용성

| 항목 | 구현 |
|------|------|
| 헬스체크 | GET /health (DB 연결, 디스크 사용량, 메모리) |
| 에러 처리 | 구조화된 JSON 에러 응답, 프론트 토스트 표시 |
| 로깅 | 구조화된 JSON 로그 (요청 ID, 시간, 사용자, 에러) |
| 재시작 | systemd 또는 Docker restart policy |

---

## 7. 디렉터리 전체 구조

```
LG_ES_v3.0/
├── docs/                      # 설계 문서
│   ├── ARCHITECTURE.md        # 시스템 아키텍처 (본 문서)
│   ├── TECHNICAL.md           # 기술 명세 (API, DB 스키마)
│   ├── DATA_FLOW.md           # 데이터 흐름 상세 (B2B/B2C 스코어 계산)
│   ├── FRONTEND_SPEC.md       # 프론트엔드 UI/UX 설계
│   ├── DEPLOYMENT.md          # 배포·운영 가이드
│   └── CHANGELOG.md           # v2.0 → v3.0 변경 이력
│
├── frontend/                  # 프론트엔드
│   ├── index.html             # 메인 대시보드 셸
│   ├── login.html             # 로그인/회원가입
│   ├── css/                   # 스타일시트 (모듈별)
│   ├── js/                    # JavaScript (ES Modules)
│   └── images/                # 로고, 아이콘
│
├── backend/                   # 백엔드 API
│   ├── main.py                # FastAPI 앱
│   ├── config.py              # 설정
│   ├── database.py            # DB 커넥션
│   ├── models.py              # Pydantic 스키마
│   ├── dependencies.py        # 공통 의존성
│   ├── routers/               # API 라우터 모듈
│   ├── services/              # 비즈니스 로직
│   └── utils/                 # 유틸리티
│
├── pipeline/                  # 데이터 파이프라인
│   ├── config.py              # 파이프라인 설정
│   ├── preprocess.py          # 전처리
│   ├── aggregate.py           # 집계
│   ├── sync.py                # DB 동기화
│   └── run.py                 # 실행 엔트리
│
├── scripts/                   # 운영 스크립트
│   ├── create_admin.py        # 관리자 생성
│   ├── create_views.sql       # 집계 VIEW 생성 SQL
│   ├── check_db.py            # DB 연결 진단
│   └── sync_remote.py         # 원격 → 로컬 동기화
│
├── pipeline_output/           # 파이프라인 결과 CSV (자동 생성)
├── requirements.txt           # Python 의존성
├── .env.example               # 환경 변수 템플릿
├── Dockerfile                 # Docker 이미지 (선택)
├── docker-compose.yml         # Docker Compose (선택)
└── README.md                  # 프로젝트 개요 (구현 시 작성)
```

---

## 8. 기술적 결정 사항 (ADR)

### ADR-001: 프론트엔드 프레임워크 미사용

- **결정**: React/Vue 대신 Vanilla JS + ES Modules 유지
- **이유**: 
  - 빌드 도구(webpack/vite) 없이 즉시 배포 가능
  - v2.0 프로토타입 코드 재활용 최대화
  - 팀 학습 비용 최소화
  - 대시보드 규모에 프레임워크 오버헤드 불필요
- **단점**: 상태 관리 직접 구현 필요 → `state.js` 모듈로 해결

### ADR-002: JWT + Refresh Token 인증

- **결정**: v2.0의 세션 쿠키 → JWT 기반으로 전환
- **이유**:
  - 서버 재시작 시 세션 유실 방지
  - 수평 확장(다중 인스턴스) 대응
  - Refresh Token으로 UX 향상 (자동 갱신)
- **구현**: Access Token 쿠키(HttpOnly) + Refresh Token DB 저장

### ADR-003: SQL VIEW 우선 전략

- **결정**: 집계 조회 시 VIEW → SQL → pandas 순서 (v2.0: pandas → SQL)
- **이유**:
  - VIEW가 가장 빠름 (DB 엔진 최적화)
  - pandas는 대용량 시 메모리 부하
  - VIEW 없는 환경에서도 SQL 폴백으로 동작

### ADR-004: 프론트엔드 CSS 분리

- **결정**: 인라인 `<style>` → 별도 CSS 파일 4개로 분리
- **이유**:
  - 브라우저 캐싱 활용
  - 디자인 토큰(CSS Custom Properties) 중앙 관리
  - 코드 가독성 및 유지보수 향상
