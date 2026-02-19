# 운영 가이드

## 1. 헬스체크/모니터링
- `GET /health`  
  - 응답: `status`, `records`, `last_updated`, `open_issues`, `high_priority_open`.  
  - 목적: Kubernetes liveness/readiness 혹은 외부 모니터링에 연결.
- `GET /api/summary`  
  - 확장된 KPI를 확인할 때 사용. 주기적 스케줄러로 호출해 지표를 로그에 기록할 수 있음.

권장 알람 조건:
1. `/health` 응답 시간이 2초 이상이거나 status!=ok -> PagerDuty/Slack 알림.
2. `records` 증가가 1시간 이상 정체 -> Webhook/수집 파이프라인 점검 필요.
3. `high_priority_open`이 임계치(예: 20건) 이상 -> 온콜 티켓 확인.

## 2. 로그 정책
- FastAPI 기동 시 `app/logging_config.py`가 적용되어 `jira_monitor` 로거가 JSON 유사 포맷(`timestamp | level | logger | message`)으로 STDOUT에 기록됩니다.
- `RequestLoggingMiddleware`가 모든 요청에 `x-request-id`를 부여하고 처리시간(ms)과 상태코드를 로그에 남깁니다.
- 예시:
  ```
  2025-01-02 10:13:01,123 | INFO | jira_monitor | request complete {'request_id': '...', 'path': '/api/summary', 'status_code': 200, 'duration_ms': 12.3}
  ```
- 장애 시 대응:
 1. `grep request_id`로 관련 요청 전체 추적.
 2. 500 응답이 반복되면 `ingestion_service` 혹은 `repository.upsert_issue` 로그를 확인.

## 3. 텍사노미/분류 확인
- `GET /api/issues/{issue_key}/taxonomy`
  - 분류 결과, confidence, 요구 액션, 담당 팀 추천, 타임라인을 JSON으로 반환.
  - 예) 분류 정확도 모니터링/재학습 자료 수집을 위해 주기적으로 호출 후 데이터 웨어하우스에 적재.
- 사내 룰 변경 시 `ACTION_BY_CATEGORY`, `TEAM_BY_REGION` 매핑(코드 상단)만 바꾸면 프론트 표시가 즉시 반영됩니다.

## 4. 시뮬레이션 워크플로
- 데이터 경로: 기본적으로 `/home/ubuntu/DI/DASH_JIRA_2/processed/dataset_test.csv`.
- 흐름:
  1. `POST /api/simulation/reset` : 커서를 0으로 초기화.
  2. `POST /api/simulation/next?batch=N` : 다음 N건을 In-memory DB에 upsert.
  3. `GET /api/simulation/state` : 총 건수/진행률/최근 처리 목록 확인.
- 프론트 대시보드 좌측의 “신규 티켓 시뮬레이션” 패널도 동일 API를 호출합니다.
- 알람 예시: `remaining`이 0이 아니지만 신규 데이터가 들어오기 전까지 UI 변화가 없다면 ingest 파이프라인 문제로 판단.

## 5. 배포/롤백 체크리스트
1. `pytest` 혹은 최소 `python -m compileall backend/app` 수행.
2. `npm run build` (프론트) 확인 후 `dist/`를 CDN/버킷에 업로드.
3. 컨테이너 배포 시 `docker build -t jira-monitor-backend -f backend/Dockerfile .`.
4. 신규 버전 배포 후 `/health` 및 `/api/summary`를 호출해 정상 여부 확인.
5. 이상 시 직전 이미지로 롤백, `processed/` 데이터 덮어쓰지 않도록 주의.

## 6. 수동 플랜 B (데이터 재적재)
1. 최신 CSV 수신 후 `processed/`에 덮어쓰기.
2. `backend/run_server.sh` 재시작(또는 컨테이너 재배포) → DataFrame이 자동 갱신.
3. 필요 시 `POST /api/ingest/jira-webhook`으로 누락된 이벤트만 부분 보정.

## 7. 향후 모니터링 확장 아이디어
- OpenTelemetry Exporter를 붙여 Trace + Metrics를 Grafana Tempo/Prometheus로 송신.
- 벡터 검색/LLM 호출 로깅 시 `request_id`를 전달해 전체 워크플로 추적.
- SLA Sentinel: `high_priority_open` 추세를 CloudWatch Metric 혹은 Datadog Gauge로 전송해 장기 경향 감시.
