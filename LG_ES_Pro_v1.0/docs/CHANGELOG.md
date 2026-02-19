# LG ES v3.0 — 변경 이력 (Changelog)

> **문서 버전**: 1.0  
> **최종 수정**: 2026-02-11  
> **상태**: 설계 완료 → 구현 대기

---

## v3.0.0 (설계 완료 — 구현 예정)

### v2.0 → v3.0 주요 변경 사항

---

### 1. 프론트엔드 아키텍처 전면 개편

#### 1.1 모듈 분리

| v2.0 | v3.0 | 이유 |
|------|------|------|
| 단일 `index.html` (~2,500행, ~140KB) | HTML + CSS 4파일 + JS 15+ 모듈 | 유지보수성, 코드 가독성 |
| `<style>` 인라인 CSS (~163행) | `css/variables.css`, `layout.css`, `components.css`, `pages.css` | 브라우저 캐싱, 디자인 토큰 중앙 관리 |
| `<script>` 인라인 JS (~520행) | `js/` ES Modules (`app.js`, `state.js`, `api.js`, `router.js` + components + views + utils) | 재사용, 테스트 용이성 |

#### 1.2 컴포넌트 기반 UI

| 기능 | v2.0 | v3.0 |
|------|------|------|
| Score Cards | 인라인 함수 `renderScoreCards()` | `components/ScoreCards.js` 클래스 |
| Bar Chart | 인라인 함수 `renderCharts()` 내부 | `components/BarChart.js` 클래스 |
| Trend Chart | 인라인 함수 `renderCharts()` 내부 | `components/TrendChart.js` 클래스 |
| Data Table | 인라인 함수 `renderSummaryTable()` | `components/DataTable.js` 클래스 (범용) |
| MultiSelect | 인라인 함수 `buildMultiselect()` | `components/MultiSelect.js` 클래스 |
| Toast | 없음 | `components/Toast.js` 클래스 (신규) |

#### 1.3 상태 관리

| v2.0 | v3.0 |
|------|------|
| 전역 `state` 객체 (단순 변수) | `StateManager` 클래스 (Pub/Sub 패턴) |
| 수동 `refresh()` 호출 | 상태 변경 → 자동 UI 업데이트 (subscribe) |
| 상태 변경 추적 불가 | 변경된 키만 리스너 호출 (성능 최적화) |

#### 1.4 라우팅

| v2.0 | v3.0 |
|------|------|
| DOM 직접 show/hide | 해시 기반 라우터 (`#dashboard`, `#summary`, ...) |
| URL 공유 불가 | URL 해시로 특정 섹션 직접 접근 가능 |

#### 1.5 API 클라이언트

| v2.0 | v3.0 |
|------|------|
| 각 함수에서 `fetch()` 직접 호출 | `ApiClient` 클래스 (공통 에러 처리, 인증 헤더) |
| 401 시 수동 리다이렉트 | 자동 토큰 갱신 (Refresh Token) + 실패 시 리다이렉트 |
| 에러 메시지 미표시 | `Toast.show()` 로 사용자에게 에러 표시 |

---

### 2. 백엔드 구조 개선

#### 2.1 모듈 분리

| v2.0 | v3.0 | 변경 내용 |
|------|------|----------|
| `main.py` (전체 ~648행) | `main.py` + `routers/` + `services/` + `utils/` | 라우터·서비스 계층 분리 |
| `data.py` (전체 ~483행) | `services/data_service.py` | 데이터 조회 로직 |
| `auth_user.py` | `services/auth_service.py` + `utils/security.py` | 인증 로직 분리 |
| `db.py` | `database.py` | 커넥션 풀 관리 개선 |

#### 2.2 라우터 분리

| v2.0 | v3.0 |
|------|------|
| `main.py`에 모든 엔드포인트 | `routers/auth.py` — 인증 관련 |
| | `routers/summary.py` — Summary/Stats/Filters |
| | `routers/trend.py` — 트렌드 데이터 |
| | `routers/export.py` — 다운로드 |
| | `routers/admin.py` — 관리자 기능 |

#### 2.3 API 응답 형식 개선

| v2.0 | v3.0 |
|------|------|
| `list[dict]` 바로 반환 | `{ data: [...], meta: {...} }` 구조화 |
| 에러: `{"detail": "..."}` | `{"error": true, "code": "...", "message": "..."}` 표준 에러 |
| 버전 정보 없음 | `GET /api/version` + 모든 응답에 `meta` 포함 |

---

### 3. 인증 시스템 강화

| 항목 | v2.0 | v3.0 |
|------|------|------|
| **방식** | 세션 쿠키 (서버 메모리) | JWT + Refresh Token |
| **토큰 저장** | 메모리 dict (`sessions`) | Access: HttpOnly 쿠키, Refresh: DB |
| **서버 재시작** | 모든 세션 유실 → 재로그인 필수 | JWT 검증만으로 유지 (SECRET_KEY 동일 시) |
| **토큰 갱신** | 없음 (만료 시 재로그인) | 자동 Refresh Token 갱신 |
| **다중 인스턴스** | 미지원 (세션 공유 불가) | 지원 (JWT는 stateless) |
| **역할** | `admin` / `user` | `admin` / `user` / `pending` |
| **회원가입** | 있음 (관리자 승인) | 유지 + 역할 변경 API 추가 |

---

### 4. 데이터 파이프라인 개선

| 항목 | v2.0 | v3.0 |
|------|------|------|
| **조회 우선순위** | pandas → SQL | VIEW → SQL → pandas (VIEW 우선) |
| **동기화** | 수동 스크립트 | 자동 스케줄러 + 수동 트리거 |
| **동기화 이력** | 없음 | `sync_log` 테이블에 기록 |
| **동기화 상태** | 없음 | `GET /admin/sync-status` API |
| **감사 로그** | 메모리 list | `audit_log` DB 테이블 |
| **활동 로그** | 메모리 list | `audit_log` DB 테이블 (통합) |

---

### 5. 캐싱 전략 개선

| 항목 | v2.0 | v3.0 |
|------|------|------|
| **구현** | 단일 dict (`_summary_cache`) | 계층별 캐시 (Summary/Filters/Trend 분리) |
| **TTL** | 60초 고정 | 엔드포인트별 TTL (60s/300s/120s) |
| **무효화** | TTL 만료만 | 동기화 완료 시 클리어 + 관리자 수동 클리어 |
| **확장** | 메모리만 | Redis 지원 준비 (인터페이스 추상화) |

---

### 6. 보안 개선

| 항목 | v2.0 | v3.0 |
|------|------|------|
| CORS | `allow_origins=["*"]` | 환경 변수로 Origin 제한 |
| 쿠키 | `session_id` (일반 쿠키) | HttpOnly, SameSite=Lax, Secure (HTTPS 시) |
| 비밀번호 | bcrypt 해시 | 유지 |
| API 키 | 없음 | JWT (HS256) |
| 감사 추적 | 메모리 로그 | DB 기반 감사 로그 (IP, 액션, 시간) |

---

### 7. 운영 안정성 개선

| 항목 | v2.0 | v3.0 |
|------|------|------|
| **헬스체크** | `GET /api/version` (기본) | `GET /health` (DB, 메모리, uptime) |
| **에러 처리** | 기본 HTTPException | 구조화된 에러 코드 시스템 |
| **로깅** | print / 기본 로그 | 구조화된 JSON 로그 (요청 ID, 시간, 사용자) |
| **프로세스 관리** | 수동 실행 | systemd + 자동 재시작 |
| **백업** | 없음 | cron 기반 MySQL 백업 + 로테이션 |

---

### 8. UI/UX 개선

| 항목 | v2.0 | v3.0 |
|------|------|------|
| **알림** | 없음 (콘솔 로그만) | Toast 알림 (성공/에러/경고) |
| **로딩 상태** | 없음 | 로딩 인디케이터 |
| **사용자 메뉴** | 단순 로그아웃 버튼 | 드롭다운 메뉴 (프로필, 로그아웃, 관리자) |
| **다운로드** | 단일 CSV 버튼 | 드롭다운 (Summary CSV, RAW CSV) |
| **URL 공유** | 불가 | 해시 기반 라우팅 (`#dashboard`, `#summary`) |
| **에러 표시** | 콘솔 + "No data found" | Toast + 상세 에러 메시지 |

---

### 9. 새로운 기능 (v3.0 신규)

| 기능 | 설명 |
|------|------|
| **관리자 패널** | 사용자 관리, 역할 변경, 활동 로그, 동기화 상태 |
| **동기화 상태 대시보드** | 마지막 동기화 시간, 행 수, 성공/실패 상태 |
| **자동 토큰 갱신** | Access Token 만료 시 Refresh Token으로 자동 갱신 |
| **구조화된 에러 시스템** | 에러 코드 기반 일관된 에러 처리 |
| **감사 로그** | 모든 인증·데이터 접근·관리 활동 기록 |
| **캐시 관리** | 관리자 캐시 수동 클리어 |

---

### 10. 파일 구조 변경

```
v2.0                              v3.0
────                              ────
docs/                             docs/
├── ARCHITECTURE.md               ├── ARCHITECTURE.md    (갱신)
├── TECHNICAL.md                  ├── TECHNICAL.md       (갱신)
├── B2B_DATA_FLOW.md              ├── DATA_FLOW.md       (통합·확장)
├── B2B_SUMMARY_FLOW.md           ├── FRONTEND_SPEC.md   (신규)
├── ADMIN_LOGIN.md                ├── DEPLOYMENT.md      (신규, LOCAL_MYSQL_SYNC 통합)
└── LOCAL_MYSQL_SYNC.md           └── CHANGELOG.md       (신규)

backend/                          backend/
├── main.py (전체)                 ├── main.py            (앱 생성만)
├── auth_user.py                  ├── config.py          (신규)
├── db.py                         ├── database.py        (개선)
└── data.py                       ├── models.py          (신규)
                                  ├── dependencies.py    (신규)
                                  ├── routers/           (신규)
                                  │   ├── auth.py
                                  │   ├── summary.py
                                  │   ├── trend.py
                                  │   ├── export.py
                                  │   └── admin.py
                                  ├── services/          (신규)
                                  │   ├── auth_service.py
                                  │   ├── data_service.py
                                  │   ├── cache_service.py
                                  │   └── export_service.py
                                  └── utils/             (신규)
                                      ├── security.py
                                      └── logger.py

frontend/                         frontend/
├── index.html (전체)              ├── index.html         (Shell만)
├── login.html                    ├── login.html         (개선)
└── images/                       ├── css/               (신규)
                                  │   ├── variables.css
                                  │   ├── layout.css
                                  │   ├── components.css
                                  │   └── pages.css
                                  ├── js/                (신규)
                                  │   ├── app.js
                                  │   ├── state.js
                                  │   ├── api.js
                                  │   ├── router.js
                                  │   ├── components/
                                  │   ├── views/
                                  │   └── utils/
                                  └── images/

pipeline/                         pipeline/
├── config.py                     ├── config.py          (유지)
├── preprocess.py                 ├── preprocess.py      (유지)
├── aggregate.py                  ├── aggregate.py       (유지)
└── run.py                        ├── sync.py            (scripts에서 이동)
                                  ├── scheduler.py       (신규)
                                  └── run.py             (유지)

scripts/                          scripts/
├── check_db.py                   ├── check_db.py        (유지)
├── create_admin.py               ├── create_admin.py    (유지)
├── create_summary_views.sql      ├── create_views.sql   (개선)
├── diagnose_b2b_summary.py       ├── init_db.py         (신규)
└── sync_remote_to_local.py       └── migrate.py         (신규)
```

---

## 버전 히스토리

| 버전 | 날짜 | 설명 |
|------|------|------|
| v1.0 (LG_ES_v1.0_2602) | 2025 | 초기 버전 (파이프라인 + 기본 대시보드) |
| v2.0 (LG_ES_v2.0) | 2025-2026 | 통합 버전 (로그인 + B2B/B2C + 다운로드 + 관리자) |
| **v3.0 (LG_ES_v3.0)** | **2026-02** | **모듈화, JWT 인증, VIEW 우선, 컴포넌트 UI** |
