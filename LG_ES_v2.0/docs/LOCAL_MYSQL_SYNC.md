# 로컬 MySQL 동기화로 속도 개선

## 개요

- **원격 MySQL** (기존): 데이터 소스·히스토리. **업데이트 여부 확인용**으로만 사용.
- **로컬 MySQL** (EC2 등 앱 서버): 원격에서 동기화된 복사본. **대시보드/API는 전부 로컬 DB만 조회** → 지연 최소화.

연동 흐름:

1. 앱은 항상 **로컬 MySQL** (`MYSQL_HOST=127.0.0.1`) 에만 연결해 Summary/집계 조회.
2. 주기적으로(또는 수동) **동기화 스크립트** 실행: 원격과 로컬 비교 → 필요 시에만 원격 → 로컬 복사.
3. 업데이트가 없으면 동기화 생략 → 원격 DB 부하는 “체크” 수준만 발생.

## 아키텍처

```
[원격 MySQL]  ← 동기화 스크립트: 업데이트 체크 + 필요 시 테이블 복사
     ↑
     | (체크만 또는 풀 동기화)
     |
[EC2 로컬 MySQL]  ← FastAPI/대시보드: 모든 /api/summary, /api/filters 등 조회
     ↑
     |
[사용자 브라우저]
```

## 1. EC2에 로컬 MySQL 준비

### 방법 A: Docker (권장)

```bash
# 프로젝트 루트에서
docker run -d \
  --name lg_ha_local \
  -e MYSQL_ROOT_PASSWORD=local_root_secret \
  -e MYSQL_DATABASE=lg_ha \
  -e MYSQL_USER=lg_ha \
  -e MYSQL_PASSWORD=your_local_password \
  -p 3306:3306 \
  mysql:8.0 \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

- 포트 3306이 이미 쓰이면 `-p 3307:3306` 등으로 변경 후 아래 `.env`의 `MYSQL_PORT`에 맞춤.

### 방법 B: 스크립트 사용

```bash
bash scripts/setup_local_mysql.sh
```

(스크립트는 Docker 방식으로 컨테이너 + DB/유저 생성 until 완료)

## 2. 환경 변수 (.env)

앱이 **로컬**만 보게 하고, 동기화 스크립트가 **원격**에 접속해 복사하도록 나눕니다.

```ini
# ----- 앱/API용: 로컬 MySQL (EC2 내부) -----
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=lg_ha
MYSQL_PASSWORD=your_local_password
MYSQL_DATABASE=lg_ha

# ----- 동기화 스크립트용: 원격 MySQL (업데이트 체크 + 복사 소스) -----
REMOTE_MYSQL_HOST=mysql.cnxkr.com
REMOTE_MYSQL_PORT=10080
REMOTE_MYSQL_USER=lg_ha
REMOTE_MYSQL_PASSWORD=your_remote_password
REMOTE_MYSQL_DATABASE=lg_ha

# 테이블명 (원격/로컬 동일)
# TABLE_B2B / TABLE_B2C 는 backend/db.py 기본값 사용
```

- 대시보드/API는 위 `MYSQL_*` 만 사용 → 항상 로컬 조회.
- `sync_remote_to_local.py` 는 `REMOTE_MYSQL_*` 로 원격 접속, `MYSQL_*` 로 로컬 접속해 동기화.

## 3. 동기화 스크립트

### 업데이트 체크 + 동기화 (권장)

```bash
cd /home/ubuntu/DI/LG_ES_v2.0_통합
.venv/bin/python scripts/sync_remote_to_local.py
```

- 원격과 로컬의 **테이블별 행 수**를 비교.
- 차이가 있으면 해당 테이블만 **TRUNCATE 후 원격 → 로컬 복사**.
- 차이가 없으면 스킵 → 원격 부하 최소.

### “강제 전체 동기화”

```bash
.venv/bin/python scripts/sync_remote_to_local.py --force
```

- 체크 생략, B2B/B2C 테이블 전부 다시 복사.

### 크론 예시 (매일 새벽 동기화)

```cron
0 2 * * * cd /home/ubuntu/DI/LG_ES_v2.0_통합 && .venv/bin/python scripts/sync_remote_to_local.py >> /var/log/sync_mysql.log 2>&1
```

## 4. 동작 요약

| 항목 | 설명 |
|------|------|
| **속도** | API/대시보드는 로컬 MySQL만 사용 → 네트워크 지연 제거. |
| **원격 부하** | 동기화 시에만 원격 접속. 업데이트 없으면 체크만 수행. |
| **데이터** | 로컬은 원격의 “최신 스냅샷”. 동기화 주기에 따라 최신화. |
| **히스토리** | 원격 DB는 그대로 두고, 필요 시 원격에서 추가 조회 가능. |

## 5. 트러블슈팅

- **로컬 MySQL 연결 실패**: Docker 컨테이너 실행 여부(`docker ps`), `MYSQL_PORT`/방화벽 확인.
- **동기화 실패**: `REMOTE_MYSQL_*` 접속 가능 여부(EC2 → 원격 네트워크/보안그룹), 테이블명이 `backend/db.py`의 `TABLE_B2B`/`TABLE_B2C`와 동일한지 확인.
- **VIEW 사용 시**: 로컬 DB에 `scripts/create_summary_views.sql` 로 VIEW 생성 후 `SUMMARY_VIEW_B2B`/`SUMMARY_VIEW_B2C` 설정하면 집계 속도 추가 개선.
