# LLM으로 기획기사 퀄리티 리포트 만들기

기본 리포트는 고정 템플릿으로 생성됩니다. **LLM을 사용하면** 동일한 데이터를 바탕으로 제목·리드·본문을 AI가 자유롭게 작성해 기획기사 수준의 퀄리티를 높일 수 있습니다.

## 사용 방법

### 1) API 키 설정

**SLCC_Stage2/.env** 파일에 다음을 넣으면 자동으로 사용됩니다.

```
OPENAI_API_KEY=sk-...
```

다른 엔드포인트를 쓰는 경우(예: 로컬 서버)에도 .env에 추가:

```
OPENAI_BASE_URL=https://your-api/v1
OPENAI_API_KEY=your-key
```

**모델**: 무조건 **최고 성능 모델(gpt-4o)** 로 연동됩니다. (코드에서 고정)

### 2) 패키지 설치

```bash
cd SLCC_Stage2
python3 -m venv .venv
.venv/bin/pip install openai reportlab beautifulsoup4
```

### 3) 리포트 생성

**LLM 사용 (기사 본문 자동 생성):**

```bash
.venv/bin/python3 scripts/build_report.py --llm
```

**LLM 미사용 (기존 템플릿):**

```bash
.venv/bin/python3 scripts/build_report.py
```

생성 파일: `output/2026.1H_데일리모니터링_주간분석_2월1일-6일.html`, `.pdf`

## 동작 방식

- `--llm` 사용 시 `llm_report_writer.py`가 `data/parsed/all_days.json` 요약을 만들어 LLM에 넘깁니다.
- LLM은 **제목**, **리드**, **본문 섹션 4개**(일별 버즈·턴닝포인트, 채널·드라이버, 제품·AI, 요약·전망)를 JSON으로 반환합니다.
- `build_report.py`는 이 JSON으로 HTML/PDF 본문을 채웁니다. **일별 버즈 표**는 항상 실제 데이터로 생성됩니다.

데이터만 바꾸면 같은 방식으로 다른 기간·다른 이벤트 리포트도 LLM으로 작성할 수 있습니다.
