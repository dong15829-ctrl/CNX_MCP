# LG ES v2.0 통합 대시보드 아키텍처

## 1. 개요

- **목적**: LG.com ES Contents Monitoring 대시보드 통합 버전 (로그인 + B2B/B2C SUMMARY·트렌드·RAW·다운로드).
- **참조**: UI/플로우는 **LG_ES** 목업, 데이터/파이프라인은 **LG_ES_v1.0_2602** 기반.

---

## 2. 시스템 구성도

```
[사용자]
    │
    ▼
[프론트엔드]  ← 로그인 페이지 → [백엔드 /auth]
    │
    │  (인증 후)
    ▼
[대시보드]  Summary / Monitoring Detail / Checklist & Criteria
    │
    │  API 호출 (B2B, B2C, Month, Region, Country 필터)
    ▼
[백엔드 API]  FastAPI
    │
    ├── /api/summary, /api/stats, /api/filters  ← [파이프라인 출력 CSV] 또는 [MySQL 직접 조회]
    ├── /api/summary/trend?by=month|week
    ├── /api/raw/download (RAW 다운로드)
    └── /api/summary/download, /api/raw/download (파일 다운로드)
    │
    ▼
[데이터 소스]
    ├── pipeline_output/  (SUMMARY 스냅·트렌드 CSV — 파이프라인 실행 결과)
    └── MySQL (lg_ha)     report_es_old, reportbusiness_es_old_v2 (필요 시 직접 조회)
```

- **로그인**: 세션 또는 JWT. 인증 후에만 대시보드 접근.
- **데이터**: 파이프라인이 생성한 CSV를 API가 읽거나, MySQL을 직접 조회.

---

## 3. 로그인 플로우

1. 사용자가 `/` 또는 `/login` 접속 → 로그인 페이지.
2. ID/비밀번호 제출 → `POST /auth/login` → 검증 성공 시 세션 쿠키 또는 JWT 발급.
3. 이후 요청은 쿠키/Authorization 헤더로 인증. 실패 시 401 → 로그인 페이지로 리다이렉트.
4. 로그아웃: `POST /auth/logout` → 세션 무효화 또는 토큰 블랙리스트.

---

## 4. 대시보드 플로우 (LG_ES 목업 기준)

1. **헤더**
   - B2B / B2C 탭 전환.
   - Month 선택, Region·Country 다중 선택 필터.
   - 다운로드(집계 테이블 / RAW) 버튼.

2. **Summary**
   - **Dashboard**: Region별 평균 Total Score, 차트(Region별 항목 평균, 최근 3개월 트렌드).
   - **SUMMARY 테이블**: region, country, sku_count, 점수 컬럼, total_score_pct. (B2C는 division 포함.)
   - 데이터 소스: `/api/summary`, `/api/stats` (파이프라인 출력 또는 DB).

3. **Monitoring Detail**
   - 상세 설명·스크린샷 등 정적/동적 콘텐츠.

4. **Checklist & Criteria**
   - 체크리스트·기준 표 (API 또는 정적 데이터).

5. **다운로드**
   - **집계 테이블**: 현재 화면 SUMMARY 데이터를 CSV/Excel로 내려받기 (프론트 변환 또는 `/api/summary/download`).
   - **RAW**: `/api/raw/download?report_type=B2B|B2C&format=csv` 등으로 서버에서 생성·스트리밍.

---

## 5. 데이터 흐름

- **파이프라인** (LG_ES_v1.0_2602 동일 로직):
  - MySQL `report_es_old`, `reportbusiness_es_old_v2` 조회 → 전처리 → SUMMARY 집계 (스냅, 월별, 주차별) → `pipeline_output/*.csv` 저장.
- **백엔드**:
  - 옵션 A: 주기적으로 파이프라인 실행 후 `pipeline_output/` CSV만 읽어 API 응답.
  - 옵션 B: API 요청 시 MySQL에서 동일 집계 쿼리 실행 (summary_from_db_b2b.sql, summary_from_db_b2c.sql).
- **트렌드**: `summary_*_trend_month.csv`, `summary_*_trend_week.csv` 또는 DB trend 쿼리로 제공.

---

## 6. 디렉터리 구조 (v2.0_통합)

```
LG_ES_v2.0_통합/
├── docs/                 # 아키텍처·기술 문서
│   ├── ARCHITECTURE.md
│   └── TECHNICAL.md
├── pipeline/             # 데이터 전처리·집계 (v1.0_2602 복사)
│   ├── config.py
│   ├── preprocess.py
│   ├── aggregate.py
│   └── run.py
├── pipeline_output/      # 파이프라인 결과 CSV
├── backend/              # FastAPI (로그인 + API)
│   └── main.py
├── frontend/             # 로그인 + 대시보드 (LG_ES 형태)
│   ├── index.html
│   ├── login.html
│   └── assets/
├── run_pipeline.py
├── requirements.txt
└── .env.example
```

---

## 7. 보안 요약

- 로그인: 비밀번호 해시 저장, 세션 또는 JWT.
- API: 인증된 사용자만 SUMMARY/RAW/다운로드 접근.
- DB 비밀번호: 환경 변수, 코드/저장소에 미포함.
