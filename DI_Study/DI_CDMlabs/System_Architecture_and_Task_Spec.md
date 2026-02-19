# DI_CDMlabs — Product Data Enrichment (TV/Monitor)

이 문서는 `DI_CDMlabs/` 폴더의 “상품 스펙 데이터 보강” 파이프라인을 **Codex(에이전트/자동화) 관점에서 재현 가능하게 실행·운영**하기 위한 작업 명세서입니다.

- 아키텍처 상세: `DI_CDMlabs/ARCHITECTURE.md`
- 데이터 구조/스키마: `DI_CDMlabs/DATA_MODEL.md`

## 1) 목표 (Goals)
- 입력 엑셀(`new_sku_nov.xlsx`)의 SKU(ASIN) 목록을 기준으로 TV/Monitor 스펙을 보강한다.
- 검색 기반 컨텍스트 + LLM 추출을 통해 컬럼 규칙(프롬프트)을 만족하는 결과를 생성한다.
- 결과는 **DB에 이력(append-only)** 으로 누적하고, 최신값을 엑셀로 내보낸다.
- 중단/재실행 시 **Batch 단위로 Resume** 가능해야 한다.

## 2) 비목표 (Non-Goals)
- UI/대시보드 제공(현 단계에서는 스크립트 운영).
- 인간 검수/수정 워크플로우 자동화(검증 리포트는 제공하되 승인 단계는 수동).
- 데이터 소스(검색/LLM) 자체의 품질 보장(프롬프트/검증 로직으로 리스크를 낮춤).

## 3) 입력/출력 정의 (I/O)
### 입력
- 엑셀: `DI_CDMlabs/new_sku_nov.xlsx`
  - 시트: `TV`, `Monitor`
  - 필수 컬럼(최소): `sku`, `country`, `title`
  - 보조 컬럼: `model_code`, `brand_1/brand_2` 등(검색 쿼리 품질 향상용)

### 출력
- 히스토리 DB: `DI_CDMlabs/enrichment_archive.db`
  - 테이블: `enrichment_history` (append-only)
- 엑셀 Export: `DI_CDMlabs/new_sku_nov_filled.xlsx`
  - DB에서 “SKU별 최신 update_time” 기준으로 dedupe 후 TV/Monitor 시트로 출력
  - `compare_data.py` 실행 시, `*_master` 및 `validation_*` 컬럼이 추가된 형태로 같은 파일에 저장됨(주의)

## 4) 구성요소 (What runs)
- 실행 엔트리포인트: `DI_CDMlabs/enrich_data.py`
  - 검색: Serper(Google) + DuckDuckGo
  - LLM: Gemini (`google-generativeai`)
  - 병렬 처리: `ThreadPoolExecutor(max_workers=5)`
  - 저장: `db_manager.insert_result(...)`로 SKU 처리 결과를 1행씩 커밋
- DB 유틸: `DI_CDMlabs/db_manager.py`
  - `init_db()`, `get_processed_skus(batch_id)`, `export_to_excel(...)`
- 검증/후처리:
  - `DI_CDMlabs/compare_data.py`: `modelmaster_new_sku.xlsx`와 비교해 정확도/불일치 사유를 `new_sku_nov_filled.xlsx`에 기록
  - `DI_CDMlabs/clean_data.py`: LLM 응답에 섞인 `plaintext/tsv` 같은 아티팩트 제거
- 프롬프트(정의된 컬럼·매핑·Others 규칙):
  - TV: `DI_CDMlabs/tv_prompt.txt`
  - Monitor: `DI_CDMlabs/mo_prompt.txt`

## 5) 환경설정 (Configuration)
### 필수 환경변수 (`DI_CDMlabs/.env`)
- `GEMINI_API_KEY`: Gemini API 키
- `SERPER_API_KEY`: serper.dev API 키

### 런타임 파라미터(코드 상수)
- `BATCH_ID` (`DI_CDMlabs/enrich_data.py` 상단)
  - **Resume는 batch_id 단위**로 동작하므로, 같은 배치를 이어서 돌릴 때는 동일한 `BATCH_ID`를 유지한다.
  - 새 실험/재수행은 `BATCH_ID`를 변경해 이력을 분리한다.

## 6) 실행 절차 (Runbook)
> 시스템 Python 환경에는 `openpyxl`이 없을 수 있으므로, 폴더 내 `.venv` 사용을 권장합니다.

### 6.1 데이터 보강 실행
```bash
cd DI_CDMlabs
.venv/bin/python enrich_data.py
```

### 6.2 최신 결과 엑셀로 Export(언제든 가능)
```bash
cd DI_CDMlabs
.venv/bin/python -c "import db_manager; db_manager.export_to_excel()"
```

### 6.3 결과 검증(마스터 대비)
```bash
cd DI_CDMlabs
.venv/bin/python compare_data.py
```

### 6.4 엑셀 문자열 아티팩트 정리(선택)
```bash
cd DI_CDMlabs
.venv/bin/python clean_data.py
```

## 7) 품질/안전 기준 (Quality & Safety)
- Others 분류/segment 판정, resolution_2 강제 매핑 등은 프롬프트 파일을 “정의서”로 간주한다.
- LLM 결과는 TSV 파싱 후 **컬럼 수 일치** 및 **기본 유효성**(예: inch 존재 또는 Others) 체크를 통과해야 DB에 기록된다.
- DB는 append-only로 운영하며, “최신 결과”는 export 시점에 dedupe로 계산한다.

## 8) 운영상 주의사항 (Ops Notes)
- 네트워크가 필요하다(Serper/ DuckDuckGo/ Gemini). 실행 환경의 네트워크 정책(프록시/차단/레이트리밋)을 확인한다.
- `compare_data.py`는 `new_sku_nov_filled.xlsx`를 “검증 리포트 형태”로 덮어쓴다. 순수 결과 파일이 필요하면 export 직후 별도 파일로 백업한다.

## 9) 다음 작업 후보 (Backlog)
- `BATCH_ID`, 입력/출력 파일, 워커 수를 CLI 인자로 노출(`argparse`)
- DB 인덱스/쿼리 최적화(배치별 조회 속도)
- 검색 결과 URL 본문 수집(trafilatura 등)과 출처(링크) 저장을 표준화
