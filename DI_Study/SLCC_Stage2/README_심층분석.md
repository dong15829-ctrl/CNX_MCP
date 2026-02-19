# SLCC 심층 분석 · 자유 질의

데일리 모니터링 데이터를 바탕으로 **자유 질의** → **심층 분석·핵심 이슈·기사형 리포트**를 받는 간단한 프론트 + API입니다.

## 구조

- **프론트** (`frontend/index.html`): 질의 입력, 응답 스타일 선택(자유/핵심 이슈/인사이트/기사형 리포트), 결과 표시
- **API** (`app/main.py`): `POST /api/analyze` — 질의 + 스타일 → 컨텍스트(데이터 요약) + LLM(gpt-4o) → 심층 분석 텍스트 반환
- **데이터**: `data/parsed/all_days.json` (기존 파싱 결과)를 컨텍스트로 사용

## 실행 방법

### 1) 패키지 설치

```bash
cd /home/ubuntu/DI/SLCC_Stage2
.venv/bin/pip install fastapi uvicorn openai
```

### 2) 데이터 준비 (아직 없을 때)

```bash
.venv/bin/python3 scripts/parse_daily_reports.py
```

### 3) 서버 실행

```bash
cd /home/ubuntu/DI/SLCC_Stage2
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### 4) 접속

- 브라우저에서 **http://localhost:8002** (또는 서버 IP:8002) 접속
- 질의 입력 후 **응답 스타일** 선택 → **분석 요청** 클릭

## API

- `GET /` — 프론트 페이지
- `POST /api/analyze` — Body: `{ "query": "질의 내용", "style": "free"|"issues"|"insight"|"report" }`  
  응답: `{ "answer": "...", "style": "...", "has_context": true }`
- `GET /api/health` — 상태 확인

`.env`의 `OPENAI_API_KEY`를 사용하며, 모델은 **gpt-4o**로 고정됩니다.
