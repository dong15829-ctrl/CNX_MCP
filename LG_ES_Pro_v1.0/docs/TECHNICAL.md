# LG ES v3.0 — 기술 명세서

> **문서 버전**: 1.0  
> **최종 수정**: 2026-02-11  
> **상태**: 설계 완료 → 구현 대기

---

## 1. 기술 스택

| 구분 | 기술 | 버전 | 비고 |
|------|------|------|------|
| **프론트엔드** | HTML5, CSS3, JavaScript (ES Modules) | ES2020+ | 프레임워크 미사용, 빌드 도구 불필요 |
| **차트** | Chart.js | 4.4.x | CDN 로드 |
| **폰트** | Inter (Google Fonts) | Variable | CDN 로드 |
| **백엔드** | FastAPI | ≥ 0.104 | Python ASGI 프레임워크 |
| **ASGI 서버** | Uvicorn | ≥ 0.24 | 운영 시 gunicorn + uvicorn worker |
| **Python** | Python | ≥ 3.10 | 타입 힌트, match-case 활용 |
| **DB** | MySQL | 8.0 | 로컬 복제본 + 원격 원천 |
| **DB 드라이버** | PyMySQL | ≥ 1.0 | + cryptography (SSL) |
| **데이터 처리** | pandas | ≥ 1.5 | 전처리·집계 폴백 |
| **인증** | passlib[bcrypt], PyJWT | latest | bcrypt 해싱, JWT 토큰 |
| **환경 변수** | python-dotenv | ≥ 1.0 | .env 파일 로드 |
| **캐싱** | 인메모리 (dict) 또는 Redis | - | 환경에 따라 선택 |

---

## 2. API 명세

### 2.1 공통 사항

- **Base URL**: `http://<host>:<port>` (기본 포트 8010)
- **Content-Type**: `application/json` (요청/응답)
- **인증**: `Cookie: access_token=<JWT>` 또는 `Authorization: Bearer <JWT>`
- **에러 응답 형식**:

```json
{
  "error": true,
  "code": "AUTH_EXPIRED",
  "message": "Access token expired",
  "detail": "토큰이 만료되었습니다. 재로그인 또는 토큰 갱신이 필요합니다."
}
```

**에러 코드 목록**:

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| `AUTH_REQUIRED` | 401 | 인증 필요 (토큰 없음) |
| `AUTH_EXPIRED` | 401 | Access Token 만료 |
| `AUTH_INVALID` | 401 | 유효하지 않은 토큰 |
| `AUTH_FORBIDDEN` | 403 | 권한 부족 (관리자 전용) |
| `VALIDATION_ERROR` | 422 | 요청 파라미터 유효성 검증 실패 |
| `DB_ERROR` | 503 | 데이터베이스 연결/조회 오류 |
| `NOT_FOUND` | 404 | 리소스 없음 |
| `INTERNAL` | 500 | 내부 서버 오류 |

---

### 2.2 인증 API

#### `POST /auth/login` — 로그인

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response** (200):
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "role": "admin"
  },
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Set-Cookie**: `access_token=<JWT>; HttpOnly; Path=/; Max-Age=1800; SameSite=Lax`  
**Set-Cookie**: `refresh_token=<token>; HttpOnly; Path=/auth; Max-Age=604800; SameSite=Lax`

---

#### `POST /auth/logout` — 로그아웃

**인증 필요**: Yes

**Response** (200):
```json
{ "message": "Logged out" }
```

**동작**: Refresh Token DB에서 삭제, 쿠키 만료 처리

---

#### `POST /auth/refresh` — 토큰 갱신

**Cookie**: `refresh_token=<token>`

**Response** (200):
```json
{
  "access_token": "<new_JWT>",
  "expires_in": 1800
}
```

---

#### `GET /auth/me` — 현재 사용자 정보

**인증 필요**: Yes

**Response** (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "홍길동",
  "role": "admin",
  "created_at": "2026-01-15T09:30:00Z"
}
```

---

#### `POST /auth/register` — 회원가입

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "password": "securePassword123",
  "name": "김철수"
}
```

**Response** (201):
```json
{
  "message": "Registration successful. Awaiting admin approval.",
  "user": {
    "id": 5,
    "email": "newuser@example.com",
    "role": "pending"
  }
}
```

---

### 2.3 대시보드 API (인증 필요)

#### `GET /api/reports` — 사용 가능한 리포트 목록

**Response** (200):
```json
{
  "reports": [
    {
      "type": "B2B",
      "years": [2024, 2025, 2026],
      "months": { "2025": [1,2,3,4,5,6,7,8,9,10,11,12], "2026": [1,2] },
      "latest": { "year": 2026, "month": 2 }
    },
    {
      "type": "B2C",
      "years": [2024, 2025, 2026],
      "months": { "2025": [1,2,3,4,5,6,7,8,9,10,11,12], "2026": [1,2] },
      "latest": { "year": 2026, "month": 2 }
    }
  ]
}
```

---

#### `GET /api/filters` — 필터 옵션 목록

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `report_type` | string | Yes | `B2B` 또는 `B2C` |
| `year` | int | No | 연도 (기본: 최신) |
| `month` | int | No | 월 (기본: 최신) |

**Response** (200):
```json
{
  "regions": ["ASIA", "EU", "LATAM", "MEA", "NA"],
  "countries": {
    "ASIA": ["AU", "IN", "JP", "KR"],
    "EU": ["DE", "FR", "IT", "UK"],
    "NA": ["CA", "MX", "US"]
  },
  "divisions": ["HA", "HE", "BS"]
}
```

---

#### `GET /api/summary` — Summary 테이블 데이터

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `report_type` | string | Yes | `B2B` 또는 `B2C` |
| `year` | int | No | 연도 |
| `month` | int | No | 월 (`latest` 허용) |
| `region` | string[] | No | Region 필터 (다중) |
| `country` | string[] | No | Country 필터 (다중) |

**Response (B2B)** (200):
```json
{
  "data": [
    {
      "region": "ASIA",
      "country": "KR",
      "sku_count": 320,
      "title_tag_score": 19.5,
      "description_tag_score": 18.8,
      "h1_tag_score": 14.8,
      "canonical_link_score": 15.0,
      "feature_alt_score": 14.2,
      "total_score_pct": 96.82
    }
  ],
  "meta": {
    "report_type": "B2B",
    "year": 2025,
    "month": 3,
    "total_rows": 14,
    "max_score": 85,
    "filters_applied": { "region": [], "country": [] }
  }
}
```

**Response (B2C)** (200):
```json
{
  "data": [
    {
      "region": "ASIA",
      "country": "KR",
      "division": "HA",
      "sku_count": 235,
      "ufn_score": 10.0,
      "basic_assets_score": 9.8,
      "spec_summary_score": 9.5,
      "faq_score": 9.0,
      "title_score": 9.8,
      "description_score": 9.5,
      "h1_score": 9.8,
      "canonical_score": 10.0,
      "alt_feature_score": 9.5,
      "alt_front_score": 9.5,
      "total_score_pct": 96.4
    }
  ],
  "meta": {
    "report_type": "B2C",
    "year": 2025,
    "month": 3,
    "total_rows": 11,
    "max_score": 100,
    "filters_applied": { "region": [], "country": [] }
  }
}
```

---

#### `GET /api/stats` — 집계 통계

**Query Parameters**: `report_type`, `year`, `month`, `region[]`, `country[]`

**Response** (200):
```json
{
  "overall_avg": 87.5,
  "total_skus": 3150,
  "by_region": [
    { "region": "ASIA", "avg_score": 93.2, "sku_count": 845, "country_count": 3 },
    { "region": "EU", "avg_score": 89.1, "sku_count": 780, "country_count": 4 },
    { "region": "NA", "avg_score": 86.5, "sku_count": 635, "country_count": 3 },
    { "region": "LATAM", "avg_score": 78.3, "sku_count": 263, "country_count": 2 },
    { "region": "MEA", "avg_score": 81.2, "sku_count": 255, "country_count": 2 }
  ],
  "by_item": {
    "title_tag_score": { "avg": 17.8, "max_possible": 20 },
    "description_tag_score": { "avg": 16.9, "max_possible": 20 },
    "h1_tag_score": { "avg": 13.5, "max_possible": 15 },
    "canonical_link_score": { "avg": 14.1, "max_possible": 15 },
    "feature_alt_score": { "avg": 12.2, "max_possible": 15 }
  }
}
```

---

#### `GET /api/trend` — 트렌드 데이터

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `report_type` | string | Yes | `B2B` 또는 `B2C` |
| `by` | string | No | `month` (기본) 또는 `week` |
| `year` | int | No | 연도 |
| `region` | string[] | No | Region 필터 |
| `months` | int | No | 최근 N개월 (기본 3) |

**Response** (200):
```json
{
  "labels": ["2025-01", "2025-02", "2025-03"],
  "series": [
    {
      "region": "ASIA",
      "data": [90.2, 92.5, 94.8]
    },
    {
      "region": "EU",
      "data": [86.5, 88.1, 89.7]
    }
  ]
}
```

---

### 2.4 다운로드 API (인증 필요)

#### `GET /api/export/summary` — Summary CSV 다운로드

**Query Parameters**: `report_type`, `year`, `month`, `format` (`csv`|`xlsx`)

**Response**: File download (Content-Disposition: attachment)

---

#### `GET /api/export/raw` — RAW 데이터 다운로드

**Query Parameters**: `report_type`, `format` (`csv`)

**Response**: Streaming file download

---

### 2.5 관리자 API (관리자 인증 필요)

#### `GET /admin/users` — 사용자 목록

**Response** (200):
```json
{
  "users": [
    { "id": 1, "email": "admin@example.com", "name": "Admin", "role": "admin", "status": "active", "created_at": "2026-01-01T00:00:00Z", "last_login": "2026-02-11T08:30:00Z" },
    { "id": 2, "email": "user@example.com", "name": "User", "role": "user", "status": "active", "created_at": "2026-01-15T09:30:00Z", "last_login": "2026-02-10T14:20:00Z" },
    { "id": 3, "email": "pending@example.com", "name": "Pending", "role": "pending", "status": "pending", "created_at": "2026-02-10T16:00:00Z", "last_login": null }
  ]
}
```

#### `PUT /admin/users/{user_id}/role` — 사용자 역할 변경

**Request Body**:
```json
{ "role": "user" }
```

#### `GET /admin/activity` — 활동 로그

**Query Parameters**: `limit` (기본 50), `offset`

#### `GET /admin/sync-status` — 동기화 상태

**Response** (200):
```json
{
  "last_sync": "2026-02-11T02:00:15Z",
  "status": "success",
  "b2b_rows": 12500,
  "b2c_rows": 8900,
  "next_scheduled": "2026-02-12T02:00:00Z"
}
```

---

### 2.6 시스템 API

#### `GET /health` — 헬스체크

**인증 필요**: No

**Response** (200):
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "db": "connected",
  "uptime_seconds": 86400,
  "cache_entries": 15
}
```

#### `GET /api/version` — 버전 정보

**Response** (200):
```json
{
  "version": "3.0.0",
  "api_version": "v3",
  "build_date": "2026-02-11"
}
```

---

## 3. 데이터베이스 스키마

### 3.1 MySQL 연결 정보

| 항목 | 로컬 (앱 사용) | 원격 (원천) |
|------|---------------|------------|
| Host | 127.0.0.1 | mysql.cnxkr.com |
| Port | 3306 | 10080 |
| Database | lg_ha | lg_ha |
| User | lg_ha | lg_ha |

### 3.2 RAW 데이터 테이블 (원격 동기화)

#### `reportbusiness_es_old_v2` (B2B RAW)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT AUTO_INCREMENT | PK |
| region | VARCHAR(50) | 지역 (NA, EU, ASIA, LATAM, MEA) |
| country | VARCHAR(100) | 국가 |
| scoring | VARCHAR(10) | 스코어링 대상 여부 ('Y'/'N') |
| h1_tag_pf | VARCHAR(20) / DECIMAL | H1 태그 점수 (legacy) |
| canonical_link_pf | VARCHAR(20) / DECIMAL | Canonical 링크 점수 (legacy) |
| feature_cards | VARCHAR(20) / DECIMAL | Feature Alt 점수 (legacy) |
| title_tag_score | DECIMAL(10,2) | Title 점수 (v2 스키마) |
| description_tag_score | DECIMAL(10,2) | Description 점수 (v2 스키마) |
| h1_tag_score | DECIMAL(10,2) | H1 점수 (v2 스키마) |
| canonical_link_score | DECIMAL(10,2) | Canonical 점수 (v2 스키마) |
| feature_alt_score | DECIMAL(10,2) | Feature Alt 점수 (v2 스키마) |
| year | INT | 연도 |
| month | INT | 월 |
| week | INT | 주차 |

> **참고**: legacy 컬럼(`h1_tag_pf` 등)과 v2 컬럼(`h1_tag_score` 등)이 혼재 가능. 파이프라인에서 자동 감지 및 매핑.

#### `report_es_old` (B2C RAW)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT AUTO_INCREMENT | PK |
| region | VARCHAR(50) | 지역 |
| country | VARCHAR(100) | 국가 |
| division | VARCHAR(50) | 사업부 (HA, HE, BS 등) |
| monitoring | VARCHAR(10) | 모니터링 대상 여부 ('Y'/'N') |
| ufn_score | DECIMAL(10,2) | UFN 점수 |
| basic_assets_score | DECIMAL(10,2) | Basic Assets 점수 |
| spec_summary_score | DECIMAL(10,2) | Spec Summary 점수 |
| faq_score | DECIMAL(10,2) | FAQ 점수 |
| title_score | DECIMAL(10,2) | Title 점수 |
| description_score | DECIMAL(10,2) | Description 점수 |
| h1_score | DECIMAL(10,2) | H1 점수 |
| canonical_score | DECIMAL(10,2) | Canonical 점수 |
| alt_feature_score | DECIMAL(10,2) | Alt Feature 점수 |
| alt_front_score | DECIMAL(10,2) | Alt Front 점수 |
| year | INT | 연도 |
| month | INT | 월 |
| week | INT | 주차 |

### 3.3 집계 VIEW

#### `v_summary_b2b` — B2B Summary VIEW

```sql
CREATE OR REPLACE VIEW v_summary_b2b AS
SELECT
    region,
    country,
    year,
    month,
    COUNT(*) AS sku_count,
    ROUND(COALESCE(AVG(CAST(title_tag_score AS DECIMAL(10,2))), 0), 2) AS title_tag_score,
    ROUND(COALESCE(AVG(CAST(description_tag_score AS DECIMAL(10,2))), 0), 2) AS description_tag_score,
    ROUND(COALESCE(AVG(CAST(h1_tag_score AS DECIMAL(10,2))), 0), 2) AS h1_tag_score,
    ROUND(COALESCE(AVG(CAST(canonical_link_score AS DECIMAL(10,2))), 0), 2) AS canonical_link_score,
    ROUND(COALESCE(AVG(CAST(feature_alt_score AS DECIMAL(10,2))), 0), 2) AS feature_alt_score,
    ROUND(
        (COALESCE(AVG(CAST(title_tag_score AS DECIMAL(10,2))), 0)
       + COALESCE(AVG(CAST(description_tag_score AS DECIMAL(10,2))), 0)
       + COALESCE(AVG(CAST(h1_tag_score AS DECIMAL(10,2))), 0)
       + COALESCE(AVG(CAST(canonical_link_score AS DECIMAL(10,2))), 0)
       + COALESCE(AVG(CAST(feature_alt_score AS DECIMAL(10,2))), 0))
        / 85.0 * 100.0
    , 2) AS total_score_pct
FROM reportbusiness_es_old_v2
WHERE UPPER(TRIM(COALESCE(scoring, ''))) = 'Y'
  AND TRIM(COALESCE(region, '')) != ''
  AND TRIM(COALESCE(country, '')) != ''
GROUP BY region, country, year, month;
```

#### `v_summary_b2c` — B2C Summary VIEW

```sql
CREATE OR REPLACE VIEW v_summary_b2c AS
SELECT
    region,
    country,
    division,
    year,
    month,
    COUNT(*) AS sku_count,
    ROUND(COALESCE(AVG(ufn_score), 0), 2) AS ufn_score,
    ROUND(COALESCE(AVG(basic_assets_score), 0), 2) AS basic_assets_score,
    ROUND(COALESCE(AVG(spec_summary_score), 0), 2) AS spec_summary_score,
    ROUND(COALESCE(AVG(faq_score), 0), 2) AS faq_score,
    ROUND(COALESCE(AVG(title_score), 0), 2) AS title_score,
    ROUND(COALESCE(AVG(description_score), 0), 2) AS description_score,
    ROUND(COALESCE(AVG(h1_score), 0), 2) AS h1_score,
    ROUND(COALESCE(AVG(canonical_score), 0), 2) AS canonical_score,
    ROUND(COALESCE(AVG(alt_feature_score), 0), 2) AS alt_feature_score,
    ROUND(COALESCE(AVG(alt_front_score), 0), 2) AS alt_front_score,
    ROUND(
        (COALESCE(AVG(ufn_score), 0) + COALESCE(AVG(basic_assets_score), 0)
       + COALESCE(AVG(spec_summary_score), 0) + COALESCE(AVG(faq_score), 0)
       + COALESCE(AVG(title_score), 0) + COALESCE(AVG(description_score), 0)
       + COALESCE(AVG(h1_score), 0) + COALESCE(AVG(canonical_score), 0)
       + COALESCE(AVG(alt_feature_score), 0) + COALESCE(AVG(alt_front_score), 0))
        / 100.0 * 100.0
    , 2) AS total_score_pct
FROM report_es_old
WHERE UPPER(TRIM(COALESCE(monitoring, ''))) = 'Y'
  AND TRIM(COALESCE(region, '')) != ''
  AND TRIM(COALESCE(country, '')) != ''
GROUP BY region, country, division, year, month;
```

### 3.4 애플리케이션 테이블

#### `users` — 사용자

```sql
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL DEFAULT '',
    role ENUM('admin', 'user', 'pending') NOT NULL DEFAULT 'pending',
    status ENUM('active', 'suspended', 'pending') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### `refresh_tokens` — Refresh Token

```sql
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(512) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_user (user_id),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### `sync_log` — 동기화 이력

```sql
CREATE TABLE IF NOT EXISTS sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sync_type ENUM('full', 'incremental', 'check') NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    status ENUM('success', 'failed', 'skipped') NOT NULL,
    rows_synced INT DEFAULT 0,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT NULL,
    INDEX idx_started (started_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### `audit_log` — 감사 로그

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    email VARCHAR(255) NULL,
    action VARCHAR(50) NOT NULL,
    detail TEXT NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 4. 인증 상세

### 4.1 JWT 토큰 구조

**Access Token Payload**:
```json
{
  "sub": 1,
  "email": "admin@example.com",
  "role": "admin",
  "iat": 1739260800,
  "exp": 1739262600
}
```

**속성**:
| 항목 | 값 |
|------|-----|
| 알고리즘 | HS256 |
| Access Token 유효기간 | 30분 |
| Refresh Token 유효기간 | 7일 |
| 서명 키 | 환경 변수 `SECRET_KEY` |

### 4.2 인증 미들웨어 플로우

```
요청 → Cookie/Header에서 access_token 추출
    │
    ├─ 토큰 없음 → 공개 경로? → 허용
    │               └─ 아님 → 401 AUTH_REQUIRED
    │
    ├─ 유효 → 사용자 정보 주입 → 요청 처리
    │
    ├─ 만료 → refresh_token 쿠키 확인
    │         ├─ 유효 → 새 access_token 발급, 쿠키 갱신 → 요청 처리
    │         └─ 없음/무효 → 401 AUTH_EXPIRED
    │
    └─ 무효(변조) → 401 AUTH_INVALID
```

### 4.3 역할 기반 접근 제어 (RBAC)

| 역할 | 대시보드 | 데이터 조회 | 다운로드 | 관리자 기능 |
|------|---------|-----------|---------|-----------|
| `pending` | X | X | X | X |
| `user` | O | O | O | X |
| `admin` | O | O | O | O |

---

## 5. 캐싱 전략

### 5.1 캐시 계층

| 계층 | 대상 | TTL | 키 구조 |
|------|------|-----|---------|
| L1 (메모리) | Summary API 응답 | 60초 (설정 가능) | `(report_type, year, month, regions_hash, countries_hash)` |
| L2 (메모리) | Filters API 응답 | 300초 | `(report_type, year, month)` |
| L3 (메모리) | Trend API 응답 | 120초 | `(report_type, by, year, regions_hash)` |

### 5.2 캐시 무효화

- DB 동기화 완료 시 전체 캐시 클리어
- 관리자 수동 캐시 클리어: `POST /admin/cache/clear`
- TTL 만료 시 자동 제거

---

## 6. 의존성 목록 (requirements.txt)

```
# Backend
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
passlib[bcrypt]>=1.7.4
PyJWT>=2.8.0

# Database
pymysql>=1.0.0
cryptography>=41.0.0

# Pipeline
pandas>=1.5.0

# Optional: Production
# gunicorn>=21.0
# redis>=5.0  (캐싱용, 선택)
```
