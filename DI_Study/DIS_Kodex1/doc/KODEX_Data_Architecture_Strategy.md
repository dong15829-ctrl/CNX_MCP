# KODEX 데이터 아키텍처 및 수집 전략 (Data Architecture & Collection Strategy)

## 1. 개요 (Overview)
본 문서는 KODEX 마케팅 인텔리전스 시스템의 핵심인 **"100% 크롤링 기반 데이터 파이프라인"**을 정의합니다. 최근 1년치 데이터를 안정적으로 수집하고, 7대 가설 검증을 위한 분석 가능한 형태로 가공하기 위한 **데이터 아키텍처(Architecture)**와 **수집 설계(Collection Design)**를 포함합니다.

---

## 2. 데이터 아키텍처 (Data Architecture)
데이터는 **수집(Raw) -> 가공(Processed) -> 분석(Mart)**의 3단계 레이어로 관리됩니다.

### 2.1 Layer 1: Raw Data (Bronze) - "있는 그대로 저장"
- **목적**: 원본 데이터 보존 및 재처리 가능성 확보.
- **저장 방식**: 파일 시스템 (JSON/HTML/Image) + 메타데이터 DB (SQLite/DuckDB).
- **구조**:
  ```text
  /data/raw/
  ├── youtube/
  │   ├── video_meta/ {YYYYMMDD}_{video_id}.json
  │   ├── comments/   {YYYYMMDD}_{video_id}_comments.json
  │   ├── thumbnails/ {video_id}.jpg
  │   └── transcripts/{video_id}_cc.txt
  ├── naver/
  │   ├── search_rank/{YYYYMMDD}_{keyword}.json
  │   └── blog_posts/ {blog_id}_{post_id}.html
  └── google/
      └── serp/       {YYYYMMDD}_{keyword}.html
  ```

### 2.2 Layer 2: Processed Data (Silver) - "구조화 및 정제"
- **목적**: 분석 가능한 형태(Table)로 변환, 중복 제거, 결측치 처리.
- **저장 방식**: RDBMS (PostgreSQL) 또는 DuckDB (로컬 분석용).
- **주요 테이블**:
  - `TB_VIDEO_META`: 영상 기본 정보 (조회수, 좋아요, 업로드일, 채널명).
  - `TB_COMMENTS`: 댓글 내용, 작성자, 작성일, 감성분석 결과.
  - `TB_VISUAL_FEATURES`: 썸네일 분석 결과 (OCR 텍스트, 주요 색상, 객체 탐지 결과).
  - `TB_SEARCH_RANK`: 키워드별/날짜별 노출 순위 (SOV).

### 2.3 Layer 3: Analysis Mart (Gold) - "가설 검증용 지표"
- **목적**: H1~H7 가설 검증을 위한 집계 데이터.
- **주요 마트**:
  - `MART_H1_SOV`: 일별 검색 점유율 추이.
  - `MART_H2_CTR_FACTORS`: 썸네일 특징별 평균 조회수/반응률.
  - `MART_H3_KEYWORD_DENSITY`: 브랜드별 이성/감성 키워드 비중.

---

## 3. 데이터 수집 설계 (Collection Design)
**최근 1년치 데이터**를 확보하기 위한 채널별 상세 수집 전략입니다.

### 3.1 YouTube (영상/쇼츠)
- **대상**:
  - 키워드: "미국 S&P500", "미국배당다우존스", "TIGER 미국", "KODEX 미국" 등 50개.
  - 채널: 주요 경쟁사 채널 (미래에셋, 삼성자산운용, 한국투자 등) + 주요 인플루언서.
- **수집 범위**: 최근 1년 (2024.11 ~ 2025.11 기준).
- **기술 전략 (Stealth)**:
  - **Infinite Scroll**: Playwright로 `window.scrollTo`를 반복 실행하여 1년 전 영상까지 로딩.
  - **Filter**: 검색 필터에서 "업로드 날짜 > 이번 달/올해" 옵션 활용 불가 시, 스크롤 후 날짜 파싱하여 1년 이전 데이터 도달 시 중단(Break).
  - **Transcript**: `yt-dlp`의 `--write-auto-sub` 옵션으로 자동 생성 자막 추출 (없을 경우 HTML 파싱).

### 3.2 Naver (블로그/카페/검색)
- **대상**:
  - 블로그/카페: 상위 노출 1~100위 게시글.
  - 통합검색: 모바일/PC 버전 각각 수집 (UI가 다름).
- **수집 범위**: 검색 옵션에서 "기간 설정(1년)" 적용하여 정확도 순/최신순 수집.
- **기술 전략**:
  - **Iframe Handling**: 네이버 블로그는 `iframe` 안에 본문이 있으므로, `src` URL을 추출하여 재요청.
  - **Anti-Bot 회피**: User-Agent 로테이션 및 랜덤 대기 시간(Random Sleep 2~5s) 적용.

### 3.3 Google (SERP)
- **대상**: "ETF 추천", "미국 주식 사는법" 등 정보성 키워드.
- **수집 범위**: 상위 1~3페이지 (Top 30).
- **기술 전략**:
  - **DOM Parsing**: CSS Selector가 자주 바뀌므로, 텍스트 기반(XPath `contains`) 탐색 병행.

---

## 4. 파이프라인 워크플로우 (Pipeline Workflow)

1.  **Scheduler (Airflow/Cron)**
    - `Daily`: 신규 영상/게시글 수집 (증분 수집).
    - `One-off`: 최초 실행 시 최근 1년치 과거 데이터 수집 (Full Load).

2.  **Collector (Crawler)**
    - `Input`: 키워드 리스트.
    - `Process`: 브라우저 실행 -> 검색 -> 스크롤 -> 파싱 -> Raw 저장.
    - `Control`: IP 차단 감지 시 10분 대기 후 재시도.

3.  **Processor (ETL)**
    - `Trigger`: 수집 완료 후 실행.
    - `Task`: JSON 파싱 -> 날짜 표준화(YYYY-MM-DD) -> DB 적재.

4.  **Analyzer (AI Models)**
    - `Trigger`: DB 적재 후 배치 실행.
    - `Task`:
        - 이미지 파일 로드 -> GPT-4o Vision API 호출 -> 결과 DB 업데이트.
        - 텍스트 로드 -> 형태소 분석/감성 분석 -> 결과 DB 업데이트.

---

## 5. 기술 스택 (Tech Stack)
- **Language**: Python 3.10+
- **Crawling**: Playwright (동적), Scrapy (정적/고속), yt-dlp (유튜브 특화).
- **Database**: SQLite (초기/로컬), DuckDB (분석용).
- **AI/ML**: OpenAI API (Vision/NLP), KoNLPy (형태소 분석).
