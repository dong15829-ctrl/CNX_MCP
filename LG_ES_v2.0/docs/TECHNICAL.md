# LG ES v2.0 통합 기술 문서

## 1. 기술 스택

| 구분 | 기술 |
|------|------|
| **프론트엔드** | HTML5, CSS3, JavaScript (Vanilla). LG_ES 목업과 동일한 단일 페이지 구조. |
| **백엔드** | FastAPI (Python 3.10+). 로그인(세션/JWT), SUMMARY/트렌드/RAW API, 정적 파일 서빙. |
| **데이터** | MySQL (lg_ha, report_es_old, reportbusiness_es_old_v2). 파이프라인 결과 CSV (pipeline_output/). |
| **파이프라인** | Python, pandas, pymysql. 전처리·집계 로직은 LG_ES_v1.0_2602와 동일. |

---

## 2. API 명세

### 2.1 인증

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /auth/login | Body: { "username", "password" }. 성공 시 세션 쿠키 또는 JWT 반환. |
| POST | /auth/logout | 로그아웃. 세션 무효화. |
| GET | /auth/me | 현재 로그인 사용자 정보 (인증 필요). |

### 2.2 대시보드 (인증 필요)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /api/reports | 사용 가능한 리포트 목록 (B2B/B2C, month 등). |
| GET | /api/filters | report_type, month 기준 Region/Country 목록. |
| GET | /api/summary | report_type, month, region[], country[] → SUMMARY 행 목록. |
| GET | /api/stats | report_type, month → Region별 집계 (평균 Total Score 등). |
| GET | /api/summary/trend | report_type, by=month\|week → 트렌드 데이터. |
| GET | /api/summary/download | format=csv\|xlsx → 현재 SUMMARY 파일 다운로드. |
| GET | /api/raw/download | report_type=B2B\|B2C, format=csv → RAW 데이터 다운로드. |

### 2.3 정적·페이지

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | / | 로그인 여부에 따라 로그인 페이지 또는 대시보드(index.html). |
| GET | /login | 로그인 페이지. |
| GET | /assets/* | 프론트 정적 파일. |

---

## 3. 데이터베이스 (MySQL)

- **Host**: mysql.cnxkr.com (환경 변수 MYSQL_HOST)
- **Port**: 10080
- **Database**: lg_ha
- **테이블**: report_es_old (B2C), reportbusiness_es_old_v2 (B2B). 마지막 컬럼: year, month, week.

파이프라인은 위 테이블에서 RAW를 읽어 전처리·집계 후 `pipeline_output/` 에 CSV로 저장. 백엔드는 CSV를 읽거나 필요 시 MySQL 직접 조회.

---

## 4. 파이프라인 (LG_ES_v1.0_2602 동일)

- **입력**: MySQL report_es_old, reportbusiness_es_old_v2.
- **전처리**: B2B scoring_yn='Y', B2C monitoring='Y' 필터, 시계열(year/month/week) 숫자화.
- **집계**: SUMMARY 스냅, 월별 트렌드, 주차별 트렌드.
- **출력**: pipeline_output/summary_b2b_snapshot.csv, summary_b2b_trend_month.csv, summary_b2b_trend_week.csv, summary_b2c_*.csv.

실행: `MYSQL_PASSWORD=xxx python run_pipeline.py`

---

## 5. 로그인·인증 구현

- **세션**: 서버 메모리 또는 Redis. 쿠키에 세션 ID.
- **비밀번호**: bcrypt 또는 passlib 해시. 평문 저장 금지.
- **초기 사용자**: 환경 변수 또는 설정 파일로 관리자 ID/비밀번호 설정. (운영 시 DB 사용자 테이블 권장.)

---

## 6. 프론트엔드 (LG_ES 목업 반영)

- **로그인 페이지**: ID/비밀번호 폼 → POST /auth/login → 성공 시 `/` 로 이동.
- **대시보드**: LG_ES index.html과 동일한 헤더(B2B/B2C, Month, Region, Country), Summary/Dashboard·테이블·차트, Monitoring Detail, Checklist & Criteria.
- **API 베이스**: 동일 오리진 또는 CORS 허용 백엔드. fetch(API_BASE + '/api/...').
- **다운로드**: 집계 테이블은 현재 로드된 JSON을 CSV/Excel로 변환 후 Blob 다운로드. RAW는 `/api/raw/download` 링크로 파일 다운로드.

---

## 7. 환경 변수

| 변수 | 설명 |
|------|------|
| MYSQL_HOST | MySQL 호스트 |
| MYSQL_PORT | MySQL 포트 |
| MYSQL_USER | MySQL 사용자 |
| MYSQL_PASSWORD | MySQL 비밀번호 |
| MYSQL_DATABASE | DB 이름 |
| SECRET_KEY | 세션/JWT 서명용 시크릿 |
| ADMIN_USERNAME | 초기 로그인 ID (선택) |
| ADMIN_PASSWORD | 초기 로그인 비밀번호 (선택, 해시 권장) |
