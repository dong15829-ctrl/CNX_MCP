# 작업 문서: DI_Monitoring

## 목표

- DI 폴더에서의 작업 이력을 **세션 단위**로 남긴다.
  - 터미널 출력(terminal typescript)
  - 실행한 명령어 이력(시간/종료코드/작업경로/명령어)
  - 실행 파일(스크립트) 이력(가능하면 해시)
- 향후 DI 하위에 어떤 폴더를 만들고 작업하더라도, 동일한 방식으로 기록할 수 있게 한다.
- 로그 저장소는 `DI_Monitoring/`로 고정하고, 커밋/배포 대상과 분리한다.

## 현재 구현 (v0)

- 세션 실행: `./start_work.sh` 또는 `DI_Monitoring/bin/di start`
- 자동 실행(접속 시): `DI_Monitoring/bin/di autostart enable`
- 로그 저장: `DI_Monitoring/sessions/<session_id>/`
- 터미널 로그: `script(1)` 기반 `terminal.log` + `terminal.timing`
- 명령어 로그: bash `PROMPT_COMMAND` 훅으로 `commands.tsv`
- 실행 파일 이력: 단순 규칙 기반으로 `executed_files.tsv`에 `sha256`(최대 10MB) 기록
- 세션 요약: 종료 시 `summary.md` 생성
- Git 커밋/상태: 대용량 repo에서도 멈추지 않도록 `timeout` 기반 best-effort 수집

## 사용 원칙

- 모니터링이 필요한 작업은 **반드시** 모니터링 세션으로 시작한다.
- 민감정보(토큰/비밀번호)는 로그에 남을 수 있으니 세션 내 입력을 주의한다.
- `DI_Monitoring/sessions/`는 Git에 커밋하지 않는다(이미 `.gitignore` 처리).

## 다음 후보 (v1 아이디어)

- `di start --name <tag>` 외에 `--project`/`--ticket` 등 메타 확장
- 세션 `summary.md`에 “변경 파일 목록/커맨드 상위 N개/실행 파일 목록” 자동 정리 강화
- 세션 로그 export(압축/암호화) 기능
- 자동 redaction(환경변수/토큰 패턴) 옵션
- `inotify` 기반 파일 변경 이벤트 로그(환경에 패키지 설치 필요)
