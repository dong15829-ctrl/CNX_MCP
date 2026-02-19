# RUNBOOK (DI_Monitoring)

## 1) 세션 시작/종료

- 시작: `./start_work.sh`
- 종료: `exit`

## 2) 로그 위치

- 기본 위치: `DI_Monitoring/sessions/<session_id>/`
- 마지막 세션 ID: `DI_Monitoring/.state/last_session`

## 3) 자주 하는 작업

- 최근 세션 목록: `DI_Monitoring/bin/di list`
- 특정 세션 보기: `DI_Monitoring/bin/di show <session_id>`
- 터미널 로그 재생: `scriptreplay -t <timing> <log>`
- CNX_MCP 접속 시 자동 시작: `DI_Monitoring/bin/di autostart enable`

## 4) 문제 해결

### `script`가 실패하거나 로그가 안 남을 때

- 환경 확인: `command -v script`
- `DI_Monitoring/bin/di start --no-terminal`로 터미널 로그 없이 명령어 로그만 우선 확인

### 명령어 로그가 비어있을 때

- bash 기반 세션인지 확인 (`DI_Monitoring/bin/di start`는 bash를 실행)
- 프롬프트가 비정상적으로 커스텀되어 `PROMPT_COMMAND`가 덮이는 경우가 있으면, `DI_Monitoring/lib/bash_logger.sh`의 훅 설치 방식을 조정해야 합니다.
