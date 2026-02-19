# 데이터 전처리 및 파이프라인

## 구성

- **config.py**: DB 연결(환경 변수), 테이블명(`report_es_old`, `reportbusiness_es_old_v2`), 컬럼 매핑
- **preprocess.py**: B2B/B2C RAW 필터(Scoring Y/N·Monitoring='Y'), 타입 정규화, 시계열(year/month/week) 숫자화
- **aggregate.py**: SUMMARY 집계 — 스냅·월별 트렌드·주차별 트렌드
- **run.py**: DB 로드 → 전처리 → 집계 → CSV 저장

## 실행

```bash
# 의존성
pip install -r requirements-pipeline.txt

# 비밀번호 환경 변수로 설정
export MYSQL_PASSWORD=your_password
python run_pipeline.py

# 또는 .env 파일에 MYSQL_PASSWORD=... 저장 후
python run_pipeline.py
```

## 출력

`pipeline_output/` 디렉터리에 CSV 생성:

- `summary_b2b_snapshot.csv` — B2B 현재 스냅
- `summary_b2b_trend_month.csv` — B2B 월별 트렌드
- `summary_b2b_trend_week.csv` — B2B 주차별 트렌드
- `summary_b2c_snapshot.csv` — B2C 현재 스냅
- `summary_b2c_trend_month.csv` — B2C 월별 트렌드
- `summary_b2c_trend_week.csv` — B2C 주차별 트렌드

## SUMMARY 집계 기준 (v1.0 엑셀 수식 분석과 동일)

- **B2B (PLP_BUSINESS → reportbusiness_es_old_v2)**  
  - 조건: `Scoring Y/N = 'Y'`  
  - 집계 키: region, country  
  - 5개 점수 평균: Title Tag Score, Description Tag Score, H1 Tag Score, Canonical Link Score, Feature Alt Score  
  - `total_score_pct` = (5개 점수 합) / 85 × 100 (만점 20+20+15+15+15=85)

- **B2C (PDP_Raw → report_es_old)**  
  - 조건: `Monitoring = 'Y'`  
  - 집계 키: region, country, division  
  - 10개 점수 평균: UFN, Basic Assets, Spec Summary, FAQ, Tag Title/Description/H1/Canonical, Alt Feature/Front  
  - `total_score_pct` = (10개 점수 평균) × 10 (만점 10×10=100)

## DB 컬럼명

실제 테이블 컬럼명이 엑셀/스키마와 다를 수 있어, `config.py`에 **B2B_POSSIBLE_COLUMN_NAMES**, **B2C_POSSIBLE_COLUMN_NAMES** 로 여러 형태(예: `Title Tag Score`, `title_tag_score`, `Scoring Y/N`)를 표준명으로 매핑해 두었습니다.  
DB에만 있는 이름이 있으면 해당 dict에 항목을 추가하세요.
