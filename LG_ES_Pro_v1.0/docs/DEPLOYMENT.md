# LG ES v3.0 — 배포 및 운영 가이드

> **문서 버전**: 1.0  
> **최종 수정**: 2026-02-11  
> **상태**: 설계 완료 → 구현 대기

---

## 1. 배포 환경

### 1.1 권장 사양

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 2 GB | 4 GB |
| 디스크 | 20 GB | 40 GB |
| Python | 3.10 | 3.12 |
| MySQL | 8.0 (Docker) | 8.0 |
| 네트워크 | EC2 → 원격 MySQL 접근 가능 | 동일 |

### 1.2 배포 토폴로지

```
[인터넷]
    │
    ▼
[EC2 인스턴스]
    │
    ├── [Uvicorn :8010]  ← FastAPI 앱
    │       │
    │       ├── 정적 파일 서빙 (frontend/)
    │       └── API 엔드포인트
    │
    ├── [MySQL :3306]    ← Docker 컨테이너 (로컬 복제본)
    │
    └── [Cron]           ← 동기화 스케줄러
            │
            └──→ [원격 MySQL :10080]  (원천 데이터)
```

---

## 2. 설치 절차

### 2.1 사전 요구사항

```bash
# Python 3.10+ 확인
python3 --version

# pip 업데이트
python3 -m pip install --upgrade pip

# Docker (로컬 MySQL용) - 선택
docker --version
```

### 2.2 프로젝트 설정

```bash
# 프로젝트 디렉터리 이동
cd /home/ubuntu/DI/LG_ES_v3.0

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

### 2.3 로컬 MySQL 설정 (Docker)

```bash
# MySQL 컨테이너 실행
docker run -d \
  --name lg_ha_local \
  --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=local_root_secret \
  -e MYSQL_DATABASE=lg_ha \
  -e MYSQL_USER=lg_ha \
  -e MYSQL_PASSWORD=your_local_password \
  -p 3306:3306 \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

# 컨테이너 상태 확인
docker ps

# MySQL 접속 확인 (잠시 후)
docker exec -it lg_ha_local mysql -u lg_ha -p lg_ha
```

### 2.4 DB 초기화

```bash
# 1. 애플리케이션 테이블 생성 (users, refresh_tokens, sync_log, audit_log)
.venv/bin/python scripts/init_db.py

# 2. 집계 VIEW 생성
docker exec -i lg_ha_local mysql -u lg_ha -p lg_ha < scripts/create_views.sql

# 3. 원격 → 로컬 데이터 동기화
.venv/bin/python pipeline/sync.py --force

# 4. 관리자 계정 생성
.venv/bin/python scripts/create_admin.py admin@example.com SecurePassword123
```

### 2.5 서버 실행

```bash
# 개발 모드 (자동 리로드)
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload

# 운영 모드
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8010 --workers 4
```

---

## 3. 환경 변수 (.env)

### 3.1 전체 환경 변수 목록

```ini
# ═══════════════════════════════════════
# LG ES v3.0 환경 변수
# ═══════════════════════════════════════

# ─── 앱/API용: 로컬 MySQL ───
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=lg_ha
MYSQL_PASSWORD=your_local_password
MYSQL_DATABASE=lg_ha

# ─── 동기화용: 원격 MySQL (원천) ───
REMOTE_MYSQL_HOST=mysql.cnxkr.com
REMOTE_MYSQL_PORT=10080
REMOTE_MYSQL_USER=lg_ha
REMOTE_MYSQL_PASSWORD=your_remote_password
REMOTE_MYSQL_DATABASE=lg_ha

# ─── 인증 ───
SECRET_KEY=your-secret-key-at-least-32-chars-long
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── 초기 관리자 (최초 실행 시) ───
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=SecureAdminPassword123

# ─── 집계 VIEW (선택, 속도 개선) ───
SUMMARY_VIEW_B2B=v_summary_b2b
SUMMARY_VIEW_B2C=v_summary_b2c

# ─── 캐싱 ───
SUMMARY_CACHE_TTL=60
# REDIS_URL=redis://localhost:6379/0  # Redis 사용 시

# ─── 테이블 설정 ───
TABLE_B2B=reportbusiness_es_old_v2
TABLE_B2C=report_es_old
# B2B_SCORE_SCHEMA=v2  # v2 또는 legacy (자동 감지)

# ─── 서버 ───
APP_HOST=0.0.0.0
APP_PORT=8010
LOG_LEVEL=info
# CORS_ORIGINS=https://yourdomain.com  # 운영 시 제한
```

### 3.2 환경 변수 설명

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `MYSQL_HOST` | Yes | `127.0.0.1` | 로컬 MySQL 호스트 |
| `MYSQL_PORT` | No | `3306` | 로컬 MySQL 포트 |
| `MYSQL_USER` | Yes | `lg_ha` | MySQL 사용자 |
| `MYSQL_PASSWORD` | **Yes** | - | MySQL 비밀번호 (**반드시 설정**) |
| `MYSQL_DATABASE` | No | `lg_ha` | DB 이름 |
| `REMOTE_MYSQL_*` | 동기화 시 | - | 원격 MySQL (동기화 스크립트용) |
| `SECRET_KEY` | **Yes** | 랜덤 생성 | JWT 서명 키 (운영 시 고정값 필수) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access Token 유효시간 (분) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh Token 유효시간 (일) |
| `ADMIN_EMAIL` | No | `admin@example.com` | 초기 관리자 이메일 |
| `ADMIN_PASSWORD` | No | `admin` | 초기 관리자 비밀번호 |
| `SUMMARY_VIEW_B2B` | No | - | B2B 집계 VIEW 이름 (속도 개선) |
| `SUMMARY_VIEW_B2C` | No | - | B2C 집계 VIEW 이름 (속도 개선) |
| `SUMMARY_CACHE_TTL` | No | `60` | API 캐시 TTL (초, 0=비활성) |
| `TABLE_B2B` | No | `reportbusiness_es_old_v2` | B2B RAW 테이블명 |
| `TABLE_B2C` | No | `report_es_old` | B2C RAW 테이블명 |
| `B2B_SCORE_SCHEMA` | No | 자동 감지 | `v2` 또는 `legacy` |
| `LOG_LEVEL` | No | `info` | 로그 레벨 (debug/info/warning/error) |

---

## 4. 운영 가이드

### 4.1 서비스 등록 (systemd)

```ini
# /etc/systemd/system/lg-es-dashboard.service
[Unit]
Description=LG ES v3.0 Dashboard
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/DI/LG_ES_v3.0
ExecStart=/home/ubuntu/DI/LG_ES_v3.0/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8010 --workers 4
Restart=always
RestartSec=5
Environment=PATH=/home/ubuntu/DI/LG_ES_v3.0/.venv/bin:/usr/bin
EnvironmentFile=/home/ubuntu/DI/LG_ES_v3.0/.env

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable lg-es-dashboard
sudo systemctl start lg-es-dashboard

# 상태 확인
sudo systemctl status lg-es-dashboard

# 로그 확인
sudo journalctl -u lg-es-dashboard -f
```

### 4.2 동기화 크론 설정

```bash
# crontab 편집
crontab -e

# 매일 새벽 2시 동기화
0 2 * * * cd /home/ubuntu/DI/LG_ES_v3.0 && .venv/bin/python pipeline/sync.py >> logs/sync.log 2>&1

# 매 6시간마다 동기화 (선택)
0 */6 * * * cd /home/ubuntu/DI/LG_ES_v3.0 && .venv/bin/python pipeline/sync.py >> logs/sync.log 2>&1
```

### 4.3 로그 관리

```bash
# 로그 디렉터리 생성
mkdir -p /home/ubuntu/DI/LG_ES_v3.0/logs

# logrotate 설정 (선택)
# /etc/logrotate.d/lg-es-dashboard
/home/ubuntu/DI/LG_ES_v3.0/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0640 ubuntu ubuntu
}
```

### 4.4 백업

```bash
# MySQL 데이터 백업 (매일)
0 3 * * * docker exec lg_ha_local mysqldump -u lg_ha -p'password' lg_ha > /home/ubuntu/backups/lg_ha_$(date +\%Y\%m\%d).sql

# 14일 이전 백업 삭제
0 4 * * * find /home/ubuntu/backups -name "lg_ha_*.sql" -mtime +14 -delete
```

---

## 5. 모니터링

### 5.1 헬스체크

```bash
# 헬스체크 (수동)
curl http://localhost:8010/health

# 기대 응답
# { "status": "healthy", "version": "3.0.0", "db": "connected", ... }
```

### 5.2 모니터링 체크리스트

| 항목 | 명령어 | 기대값 |
|------|--------|--------|
| 앱 프로세스 | `systemctl status lg-es-dashboard` | active (running) |
| 헬스체크 | `curl -s localhost:8010/health \| jq .status` | "healthy" |
| MySQL 컨테이너 | `docker ps --filter name=lg_ha_local` | Up |
| 디스크 사용량 | `df -h /` | < 80% |
| 메모리 | `free -h` | 사용 가능 > 500MB |
| 동기화 로그 | `tail -5 logs/sync.log` | 최근 성공 기록 |
| API 응답 시간 | `curl -o /dev/null -s -w '%{time_total}' localhost:8010/health` | < 1초 |

### 5.3 알림 설정 (선택)

```bash
# 간단한 헬스체크 스크립트 (cron으로 5분마다 실행)
#!/bin/bash
STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/health)
if [ "$STATUS" != "200" ]; then
    echo "LG ES Dashboard is DOWN (HTTP $STATUS)" | mail -s "ALERT: Dashboard Down" admin@example.com
fi
```

---

## 6. 트러블슈팅

### 6.1 일반 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| 서버 시작 안 됨 | `.env` 미설정 | `.env` 파일 확인, `MYSQL_PASSWORD` 설정 |
| 422 Field required | 서버 캐시된 코드 | 서버 완전 종료 후 재시작 |
| 로그인 안 됨 | 관리자 미생성 | `python scripts/create_admin.py` 실행 |
| 데이터 없음 | 동기화 미실행 | `python pipeline/sync.py --force` 실행 |
| 점수 전부 0 | 컬럼명 불일치 | `B2B_SCORE_SCHEMA` 확인, 서버 재시작 |
| API 느림 | VIEW 미설정 | `SUMMARY_VIEW_B2B`/`B2C` 설정 |
| 401 Unauthorized | 토큰 만료 | 재로그인 또는 `CORS_ORIGINS` 확인 |

### 6.2 DB 진단

```bash
# DB 연결 확인
.venv/bin/python scripts/check_db.py

# 테이블 행 수 확인
docker exec -it lg_ha_local mysql -u lg_ha -p lg_ha \
  -e "SELECT 'B2B' as type, COUNT(*) as cnt FROM reportbusiness_es_old_v2 UNION ALL SELECT 'B2C', COUNT(*) FROM report_es_old;"

# VIEW 존재 확인
docker exec -it lg_ha_local mysql -u lg_ha -p lg_ha \
  -e "SHOW FULL TABLES WHERE Table_type = 'VIEW';"

# 동기화 로그 확인
docker exec -it lg_ha_local mysql -u lg_ha -p lg_ha \
  -e "SELECT * FROM sync_log ORDER BY started_at DESC LIMIT 5;"
```

### 6.3 서버 재시작

```bash
# systemd 서비스
sudo systemctl restart lg-es-dashboard

# 수동 실행 (디버그)
cd /home/ubuntu/DI/LG_ES_v3.0
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload --log-level debug
```

---

## 7. Docker Compose (선택)

### 7.1 `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    container_name: lg_ha_local
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-local_root_secret}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-lg_ha}
      MYSQL_USER: ${MYSQL_USER:-lg_ha}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./scripts/create_views.sql:/docker-entrypoint-initdb.d/01-views.sql
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci

  app:
    build: .
    container_name: lg_es_v3
    restart: unless-stopped
    ports:
      - "8010:8010"
    env_file:
      - .env
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
      - ./pipeline_output:/app/pipeline_output

volumes:
  mysql_data:
```

### 7.2 `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libmariadb-dev && \
    rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 로그/출력 디렉터리
RUN mkdir -p logs pipeline_output

EXPOSE 8010

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8010", "--workers", "4"]
```

### 7.3 Docker Compose 실행

```bash
# 전체 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f app

# 중지
docker-compose down

# DB 데이터 유지하면서 재시작
docker-compose restart app
```

---

## 8. 업그레이드 절차

### 8.1 코드 업데이트

```bash
# 1. 서비스 중지 (선택, 무중단 시 skip)
sudo systemctl stop lg-es-dashboard

# 2. 코드 업데이트
cd /home/ubuntu/DI/LG_ES_v3.0
git pull origin main

# 3. 의존성 업데이트 (변경 시)
source .venv/bin/activate
pip install -r requirements.txt

# 4. DB 마이그레이션 (변경 시)
.venv/bin/python scripts/migrate.py

# 5. 서비스 재시작
sudo systemctl start lg-es-dashboard

# 6. 헬스체크
curl http://localhost:8010/health
```

### 8.2 롤백

```bash
# 이전 버전으로 롤백
git checkout <previous-commit-hash>
sudo systemctl restart lg-es-dashboard
```

---

## 9. 보안 체크리스트

| # | 항목 | 확인 |
|---|------|------|
| 1 | `.env` 파일 권한이 600 (owner only read/write)인가? | `chmod 600 .env` |
| 2 | `SECRET_KEY`가 최소 32자 랜덤 문자열인가? | `python -c "import secrets; print(secrets.token_hex(32))"` |
| 3 | `ADMIN_PASSWORD`가 안전한 비밀번호인가? | 영문+숫자+특수 12자 이상 |
| 4 | `.env`가 `.gitignore`에 포함되어 있는가? | `.gitignore` 확인 |
| 5 | 운영 시 `CORS_ORIGINS`가 특정 도메인으로 제한되어 있는가? | `.env` 확인 |
| 6 | MySQL 비밀번호가 기본값이 아닌가? | `.env` 확인 |
| 7 | EC2 보안 그룹에서 8010 포트 접근이 제한되어 있는가? | AWS 콘솔 확인 |
| 8 | MySQL 3306 포트가 외부에 노출되지 않았는가? | `127.0.0.1:3306`만 바인딩 |
