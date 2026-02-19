# LG ES Pro v2.0 — Backend Specification

> LG_ES_v2.0 백엔드를 기준으로 작성한 사양서입니다.
> LG_ES_Pro_v2.0 프로젝트는 이 문서를 참고하여 새로 구현합니다.

---

## 1. 기술 스택

| 항목 | 기술 |
|------|------|
| 프레임워크 | FastAPI |
| 서버 | Uvicorn (0.0.0.0:8010) |
| DB | MySQL (pymysql) |
| 인증 | 세션 기반 (HTTP-only 쿠키) |
| 비밀번호 | bcrypt (passlib) |
| 환경변수 | python-dotenv |
| Python | 3.12+ |

---

## 2. 프로젝트 구조

```
LG_ES_Pro_v2.0/
├── backend/
│   └── main.py          # FastAPI 앱 + 모든 엔드포인트
├── frontend/
│   ├── index.html        # 메인 대시보드 SPA
│   ├── login.html        # 로그인 페이지
│   └── assets/
│       └── images/
│           ├── lg-logo.svg
│           ├── lg-logo-white.svg
│           └── monitoring-detail.png
├── docs/
│   ├── FRONTEND_SPEC.md  # 프론트엔드 사양서
│   └── BACKEND_SPEC.md   # 백엔드 사양서 (이 문서)
├── .env                  # 환경변수 (비밀 포함)
├── .env.example          # 환경변수 예시
├── requirements.txt      # Python 의존성
└── run_server.sh         # 서버 실행 스크립트
```

---

## 3. 환경변수 (.env)

### 필수
| 변수 | 설명 | 예시 |
|------|------|------|
| `MYSQL_HOST` | MySQL 호스트 | `127.0.0.1` |
| `MYSQL_PORT` | MySQL 포트 | `3306` |
| `MYSQL_USER` | MySQL 사용자 | `lg_ha` |
| `MYSQL_PASSWORD` | MySQL 비밀번호 | `local_lg_ha_secret` |
| `MYSQL_DATABASE` | MySQL 데이터베이스 | `lg_ha` |

### 선택
| 변수 | 설명 | 기본값 |
|------|------|--------|
| `ADMIN_EMAIL` | 초기 관리자 이메일 | `admin@example.com` |
| `ADMIN_PASSWORD` | 초기 관리자 비밀번호 | `admin` |
| `SECRET_KEY` | 세션 시크릿 | 자동 생성 |
| `SUMMARY_CACHE_TTL` | 요약 캐시 TTL (초) | `60` |

---

## 4. DB 테이블

### 4.1 `reportbusiness_es_old_v2` (B2B 리포트)
- `region`, `country`, `year`, `month`, `scoring` (Y/N)
- 점수: `title_tag_score`, `description_tag_score`, `h1_tag_score`, `canonical_link_score`, `feature_alt_score`
- 필터: `scoring = 'Y'`, region/country 비어있지 않은 것

### 4.2 `report_es_old` (B2C 리포트)
- `region`, `country`, `division`, `year`, `month`, `monitoring` (Y/N)
- 점수: `ufn_score`, `basic_asset_score`, `summary_spec_score`, `faqs_score`, `title_tag_score`, `description_tag_score`, `h1_tag_score`, `canonical_link_score`, `feature_alt_score`, `front_image_alt_score`
- 필터: `monitoring = 'Y'`, region/country/division 비어있지 않은 것

### 4.3 `dashboard_users` (사용자)
- `id`, `email` (unique), `password_hash`, `role` (admin/user), `is_active`, `created_at`, `updated_at`
- 서버 시작 시 자동 생성

---

## 5. API 엔드포인트

### 5.1 인증
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| POST | `/auth/login` | 로그인 | X |
| POST | `/auth/logout` | 로그아웃 | X |
| GET | `/auth/me` | 현재 사용자 | O |
| POST | `/auth/register` | 회원가입 (승인 대기) | X |

### 5.2 데이터 API
| 메서드 | 경로 | 파라미터 | 설명 |
|--------|------|----------|------|
| GET | `/api/reports` | - | 사용 가능 리포트 목록 |
| GET | `/api/filters` | `report_type`, `month`, `region[]` | 필터 옵션 |
| GET | `/api/summary` | `report_type`, `month`, `region[]`, `country[]` | 요약 데이터 |
| GET | `/api/stats` | `report_type`, `month`, `region[]`, `country[]` | 통계 데이터 |
| GET | `/api/raw` | `report_type`, `region`, `country`, `limit` | Raw 데이터 |
| GET | `/api/raw/download` | `report_type`, `region[]`, `country[]` | Raw CSV 다운로드 |
| GET | `/api/sheet` | `month`, `sheet` | 시트 데이터 (Blog 등) |
| GET | `/api/checklist` | `month` | 체크리스트 |

### 5.3 관리자 API
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/admin/users` | 사용자 목록 |
| POST | `/api/admin/users` | 사용자 추가 |
| PATCH | `/api/admin/users/{id}` | 사용자 수정 |
| DELETE | `/api/admin/users/{id}` | 사용자 삭제 |
| GET | `/api/admin/usage` | 사용 현황 |
| GET | `/api/admin/pipeline-status` | 파이프라인 상태 |
| GET | `/api/admin/download-log` | 다운로드 로그 |
| GET | `/api/admin/activity-log` | 활동 로그 |
| POST | `/api/admin/log-download` | 다운로드 이벤트 로깅 |

### 5.4 시스템 API
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | DB 연결 상태 |
| GET | `/api/version` | API 버전 정보 |

---

## 6. 정적 파일 서빙

```python
# Frontend assets
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")

# Pages
GET /login  → frontend/login.html
GET /       → frontend/index.html (미인증 시 /login 리다이렉트)
```

---

## 7. Python 의존성 (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
passlib[bcrypt]>=1.7.4
pandas>=1.5.0
pymysql>=1.0.0
cryptography>=41.0.0
```

---

## 8. 실행 스크립트 (run_server.sh)

```bash
#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo ".venv 없음."
  exit 1
fi
exec .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8010
```

---

## 9. Blog 샘플 데이터

`GET /api/sheet?sheet=Blog` 요청 시 반환되는 샘플:

```
Header: Region, Country, URL, '25, '26, Latest Blog Date, Jan~Dec
Data: 16개 국가의 블로그 현황 (LATAM, ASIA, NA, EU, MEA, INDIA)
```

다른 시트(PLP_BUSINESS, Product Category)는 빈 배열 반환.
