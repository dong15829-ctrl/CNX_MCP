# 데이터 전처리 및 파이프라인

## 구성

- **config.py**: DB 연결(환경 변수), 테이블명(`report_es_old`, `reportbusiness_es_old`), 컬럼 매핑
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

## DB 컬럼명

실제 테이블 컬럼명이 다르면 `pipeline/config.py` 의 `COLUMN_ALIAS_B2B`, `COLUMN_ALIAS_B2C` 를 수정하세요.  
(표준명 → 실제 DB 컬럼명)
