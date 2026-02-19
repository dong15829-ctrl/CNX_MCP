# Jira Monitoring Web

FastAPI + React 기반으로 Jira CSV(`processed/dataset_modeling.csv`)를 로드해
모니터링 대시보드를 제공합니다.

## 1. 백엔드 (FastAPI)
1. 가상환경 생성 후 의존성 설치
   ```bash
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. API 실행
   ```bash
   uvicorn app.main:app --reload
   ```
   또는 준비된 실행 스크립트를 사용할 수 있습니다.
   ```bash
   ./backend/run_server.sh
   ```
   - 기본 포트: `8000`
   - 주요 엔드포인트
     - `GET /api/summary` : KPI 카드용 요약
     - `GET /api/metrics/time-series?days=30` : 일자별 생성/종결 추이
     - `GET /api/metrics/{status|priority|region|category}` : 분포 데이터
     - `GET /api/issues` : 필터/페이지네이션 가능 목록 (status/priority/region/text)
     - `GET /api/issues/{issue_key}` : 상세 정보
     - `GET /api/issues/{issue_key}/taxonomy` : 텍사노미/처리 타임라인 정보
     - `GET /api/filters` : UI 드롭다운 소스
     - `POST /api/ingest/jira-webhook` : Jira Webhook JSON을 수신해 데이터 프레임에 upsert
     - `GET /api/simulation/state` + `POST /api/simulation/{reset|next}` : 테스트 데이터셋 기반 신규 티켓 시뮬레이션
     - `GET /health` : 레코드 수·마지막 업데이트 기반 헬스체크

### Docker 실행
백엔드만 빠르게 컨테이너로 띄우고 싶다면 `backend/Dockerfile`을 사용합니다.
```bash
docker build -t jira-monitor-backend -f backend/Dockerfile .
docker run --rm -p 8000:8000 jira-monitor-backend
```
Webhook 테스트 예시는 다음과 같습니다.
```bash
curl -X POST http://localhost:8000/api/ingest/jira-webhook \
  -H "Content-Type: application/json" \
  -d '{
        "webhookEvent": "jira:issue_created",
        "issue": {
          "id": "2876816",
          "key": "GTA-99999",
          "fields": {
            "summary": "LC Request - Sample",
            "description": "Webhook로 유입된 테스트 이슈",
            "issuetype": {"name": "Task"},
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "assignee": {"emailAddress": "ops@example.com"},
            "created": "2024-11-30T02:12:00Z",
            "updated": "2024-11-30T02:12:00Z",
            "customfield_10013": "EU",
            "customfield_10014": "FR"
          }
        }
      }'
```

## 2. 프론트엔드 (React + Vite)
1. 의존성 설치 및 개발 서버 실행
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. 개발 서버는 `http://localhost:5173`에서 동작하며, `/api` 요청은 Vite proxy를
   통해 `http://localhost:8000` FastAPI 서버로 전달됩니다.
3. 운영/배포 시에는 `VITE_API_BASE` 환경 변수를 설정해 API 엔드포인트를 직접 지정할 수 있습니다.

## 3. 주요 기능
- KPI 카드: 전체/미해결/고우선 미해결/평균 해결시간.
- 추이 차트: 최근 N일 일자별 생성/종결/고우선 추적 (Recharts).
- 분포 패널: 상태, 우선순위, 지역, 카테고리 Top-N.
- 티켓 테이블: 상태/우선순위/지역/카테고리/키워드 필터 + 페이지네이션, 즐겨찾기 토글.
- 상세 패널: 행 선택 시 요약, SLA 관련 필드, 텍사노미/처리 타임라인 표시.
- 시뮬레이션 패널: `/processed/dataset_test.csv`(혹은 `JIRA_TEST_DATASET` 지정) 기반으로 신규 티켓 유입을 재현하고, 결과를 즉시 대시보드에 반영.

## 4. 폴더 구조
```
backend/
  app/
    main.py
    config.py
    services/data_loader.py
  requirements.txt
frontend/
  src/
    api/..
    components/..
    hooks/..
    pages/Dashboard.jsx
processed/
  dataset_modeling.csv
  dataset_test.csv
```

## 5. CI & 추가 참고
- `.github/workflows/backend.yml` GitHub Actions가 `backend` 변경 시 의존성 설치, 정적 점검, 데이터셋 로딩 스모크 테스트를 수행합니다.
- 백엔드는 CSV를 메모리에 적재한 후 재사용하므로 서버 시작 시 데이터가 로딩됩니다.
- 날짜 파싱은 다양한 포맷을 수용하도록 2단계 파서를 사용합니다.
- React 빌드 산출물은 `frontend/dist` (npm run build) 경로에 생성됩니다.
- 데이터 경로는 기본적으로 `/home/ubuntu/DI/DASH_JIRA_2/processed/*.csv`를 사용하며, `JIRA_MODEL_DATASET`/`JIRA_TEST_DATASET` 환경 변수를 통해 교체 가능합니다.
- 운영/모니터링 시 참고 사항은 `OPERATIONS.md`에 정리되어 있습니다.
