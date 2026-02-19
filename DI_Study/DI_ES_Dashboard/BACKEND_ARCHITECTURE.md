# DI_ES Dashboard Backend Architecture (Draft)

- 작성일: 2026-01-30
- 상태: Draft v0.1
- 목표: Excel 업로드 기반 MVP를 빠르게 제공하면서, 운영 DB(MySQL) 연동 “준실시간”으로 확장 가능한 구조

---

## 1. 핵심 요구사항 정리

- Excel 업로드를 통해 월별 리포트(B2B/B2C)를 적재한다.
- 대시보드 조회는 DB(MySQL) 기반으로 동작한다(옵션 B).
- 동일 기간(`report_type`, `year`, `month`) 재업로드가 발생할 수 있다(덮어쓰기/버전관리 정책 필요).
- 장기적으로 운영 DB(MySQL)에서 view/집계를 통해 준실시간으로 조회한다.

---

## 2. 권장 기술 스택

- API: FastAPI + Uvicorn
- ORM/Migration: SQLAlchemy 2.x + Alembic
- DB: MySQL 8.x (InnoDB)
- Excel parsing: openpyxl (필수), pandas(선택)
- Background jobs: Celery(+Redis) 또는 RQ(+Redis)
- 캐시(옵션): Redis (핵심 API 응답 캐시 + 업로드 완료 시 invalidation)

> Excel 파싱/정제 로직은 Python이 유리하므로 API도 Python으로 정렬하는 구성이 운영/개발 난이도가 낮습니다.

---

## 3. 컴포넌트/런타임 구성

### 3.1 서비스 구성
- `api` (동기 HTTP)
  - 조회 API(`/api/...`)
  - Admin API(`/api/admin/...`)
- `worker` (비동기 배치)
  - Excel 파싱/검증/적재
  - (v2+) 운영 DB 동기화/집계
- `mysql`
  - 원천/집계/이슈 테이블
  - (v2+) view/프로시저/집계 테이블
- `redis` (선택)
  - job queue/broker
  - cache

### 3.2 로컬 개발(제안)
- docker-compose로 `mysql`, `redis` 실행
- `api`/`worker`는 로컬에서 실행(또는 컨테이너)

---

## 4. 데이터 적재 파이프라인(Excel Upload)

### 4.1 처리 단계(권장)
1) Upload 수신
2) 파일 메타 추출: report_type(B2B/B2C), year, month, 원본 파일명
3) Validation
   - 파일명 패턴/중복 기간 정책/필수 시트 존재
   - 필수 컬럼 존재(헤더 탐지 포함)
4) Parsing/Transform
   - 시트별 파서 적용(예: Summary, Summary by Country, Bottom 30%, Alt Text Error)
   - 공통 단위(Period/Country/Metric)로 정규화
5) Load
   - raw(필요 시) → summary/issue 테이블 upsert
6) Aggregate/View refresh
   - 조회 최적화를 위한 집계 테이블/뷰 갱신
7) 결과 기록
   - 상태: pending → processing → completed/failed
   - 경고/에러 로그 저장

### 4.2 헤더 탐지(필수)
- “1행이 헤더가 아닌” 케이스가 있어, 아래 전략 중 하나로 통일 필요
  - (권장) 시트별로 **헤더 행 탐지 규칙**을 둠(키 컬럼 텍스트가 포함된 행)
  - 대안: 수동 매핑(관리 화면에서 헤더 row 지정) — 초기 구축 비용↑

---

## 5. 스키마 초안(확장 가능 형태)

> 실제 컬럼은 시트 분석 후 확정. 아래는 MVP 기준 최소 테이블.

### 5.1 `report_files`
- 업로드/적재 단위(감사/추적)
- 예시 필드
  - `id`(PK), `report_type`, `year`, `month`, `file_name`, `file_sha256`(옵션)
  - `revision`(옵션), `is_active`
  - `status`(pending/processing/completed/failed)
  - `warnings_count`, `error_message`, `ingested_at`

### 5.2 `country_summary`
- 국가 단위 요약 지표(대시보드의 80%는 이 테이블로 커버)
- 예시 필드
  - `report_file_id`(FK), `region`, `country`
  - `total_score`, `seo_score`
  - `title_score`, `desc_score`, `h1_score`, `canonical_score`, `alt_score`, `category_score`, `blog_score`

### 5.3 `issues_alt_text`, `issues_bottom30`
- 이슈/작업 리스트(필요한 필드만 저장)
- 예시 필드
  - `report_file_id`(FK), `country`, `url_or_key`, `issue_type`, `details_json`, `count`

### 5.4 인덱스(권장)
- `report_files`: `(report_type, year, month, is_active)`
- `country_summary`: `(report_file_id, country)`, `(report_file_id, total_score)`
- `issues_*`: `(report_file_id, country)`, `(report_file_id, issue_type)`

---

## 6. API 설계(권장)

### 6.1 조회 API
- `GET /api/periods`
- `GET /api/overview`
- `GET /api/countries/ranking` (pagination, sort, filters)
- `GET /api/countries/{country}/detail`
- `GET /api/issues/alt-text`
- `GET /api/issues/bottom30`

### 6.2 Admin API
- `POST /api/admin/uploads` (업로드)
- `GET /api/admin/uploads` (이력)
- `GET /api/admin/uploads/{id}` (상세/로그)
- `POST /api/admin/uploads/{id}/reprocess`

### 6.3 응답 원칙(제안)
- 프론트는 “그대로 렌더링” 가능하도록, 백엔드에서:
  - Δ/증감(Compare) 계산
  - 정렬/필터/페이지네이션 처리
  - 단위/라벨(항목명)을 메타로 제공(툴팁/legend)

---

## 7. 운영 DB(MySQL) 연동(궁극 목표) 제안

### 7.1 선택지
1) **Direct Read(단순/빠름)**  
   - 대시보드 API가 운영 DB의 view를 직접 조회(읽기 전용 계정)
   - 리스크: 운영 DB 부하/쿼리 튜닝 필요
2) **Replicated Analytics DB(권장)**  
   - 운영 DB → (복제/ETL) → 대시보드 전용 DB에서 조회
   - 장점: 운영 DB 보호, 인덱스/집계 자유도↑
3) **CDC 기반(고도화)**  
   - binlog/CDC로 변경 이벤트를 받아 집계 갱신 → UI까지 push

### 7.2 “view/집계” 운영 방식(권장)
- 실시간에 가까운 조회가 필요하면 “원천 테이블을 그대로 읽는 것”보다,
  - (a) 운영 DB 측 view(또는 집계 테이블)를 제공하거나
  - (b) 대시보드 DB에 materialized summary를 유지하는 방식이 안정적입니다.

---

## 8. 보안/운영 고려사항(요약)

- 업로드 파일 크기 제한, 확장자/콘텐츠 타입 검증
- Admin 라우트 인증(사내망/Reverse proxy 또는 앱 레벨)
- 처리 로그/에러 메시지에 민감 정보 포함 금지
- 백업/데이터 보관 정책(원본 파일 저장 여부, 보관 기간)

---

## 9. 다음 논의 포인트

1) 업로드 재처리 정책(덮어쓰기 vs revision + 활성 버전)
2) 운영 DB 연동 시 “직접조회” vs “분리된 대시보드 DB” 중 선호
3) 준실시간 주기(5/10/15/60분)와 허용 지연 시간

