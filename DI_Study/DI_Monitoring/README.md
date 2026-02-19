# DI_Monitoring

DI 폴더에서 수행하는 작업(터미널 출력/명령어 이력/실행 스크립트 해시 등)을 **세션 단위**로 남기기 위한 로컬 모니터링 도구입니다.

## 빠른 시작

- (DI 루트) 모니터링 세션 시작: `./start_work.sh`
- (DI_Monitoring) 모니터링 세션 시작: `./DI_Monitoring/start_work.sh` 또는 `./start_work.sh`
- 또는: `DI_Monitoring/bin/di start` (경로만 맞으면 어디서든 실행 가능)
- 세션 종료: 쉘에서 `exit`

세션 로그는 기본적으로 `DI_Monitoring/sessions/<session_id>/` 아래에 저장됩니다.

## 생성되는 로그

- `meta.env`: 시작 환경/식별 정보
- `terminal.log`: `script(1)`로 기록된 터미널 세션 로그
- `terminal.timing`: `scriptreplay(1)`용 타이밍 로그
- `commands.tsv`: 프롬프트 단위의 명령 실행 이력(ts/exit/pwd/command)
- `executed_files.tsv`: 실행 파일 추정 + (가능하면) `sha256` 기록
- `notes.md`: 세션 메모 템플릿
- `summary.md`: 세션 종료 시 요약

## 유의사항 (중요)

- 터미널/명령어 로그에는 토큰/비밀번호 등 민감정보가 포함될 수 있습니다. 필요 시 `DI_Monitoring/sessions/`를 정리하거나, 세션 중에는 민감정보 입력을 피해주세요.
- `DI_Monitoring/sessions/`는 `.gitignore` 처리되어 Git에 커밋되지 않습니다.

## 팁

- 재생: `scriptreplay -t DI_Monitoring/sessions/<id>/terminal.timing DI_Monitoring/sessions/<id>/terminal.log`
- 목록: `DI_Monitoring/bin/di list`
- 상세: `DI_Monitoring/bin/di show <id>`
- 자주 쓸 경우: `alias diwork="/home/ubuntu/DI/DI_Monitoring/bin/di start"` (환경에 맞게 경로 수정)

## CNX_MCP(접속 서버) 자동 시작

CNX_MCP 서버에 SSH/터미널로 접속할 때마다 자동으로 모니터링 세션이 시작되게 하려면:

- 활성화: `DI_Monitoring/bin/di autostart enable`
- 비활성화: `DI_Monitoring/bin/di autostart disable`
- 상태 확인: `DI_Monitoring/bin/di autostart status`
