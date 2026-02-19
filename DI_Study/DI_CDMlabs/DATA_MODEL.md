# DI_CDMlabs — Data Model

이 문서는 `DI_CDMlabs/` 데이터 보강 파이프라인의 **입력/중간저장/출력 데이터 구조**를 정의합니다.

## 1) 입력 데이터 (Excel)
### 파일
- 입력: `DI_CDMlabs/new_sku_nov.xlsx`
- 시트: `TV`, `Monitor`

### 공통 컬럼(현재 파일 기준)
`new_sku_nov.xlsx`는 두 시트 모두 아래 컬럼을 가집니다.

| 컬럼 | 의미 | 사용처 |
|---|---|---|
| `sku` | Amazon ASIN | 키(처리/저장/merge 기준) |
| `country` | 국가 코드(예: US, DE) | amazon TLD 결정 및 검색 쿼리 |
| `title` | 상품명(Title) | 검색/추론 근거 |
| `model_code` | 모델 코드(있으면) | MODEL 전략 쿼리 |
| `model_number` | 모델 넘버(있으면) | 현재 코드에서는 미사용(참조용) |
| `brand_1`, `brand_2` | 브랜드(있으면) | MODEL 전략 및 보조 정보 |
| `resolution_1`, `resolution_2`, `inch`, `led_type`, `display_technology`, `others_yn` | 기존 값(대개 공란/노이즈) | 현재 실행에서는 “입력 보조/참고” 수준(출력은 LLM/룰 기반) |

## 2) 중간 저장 (SQLite: History DB)
### 파일/테이블
- DB 파일: `DI_CDMlabs/enrichment_archive.db`
- 테이블: `enrichment_history` (append-only)

### 스키마
`DI_CDMlabs/db_manager.py`의 `init_db()`에서 생성합니다.

| 컬럼 | 타입 | 의미 |
|---|---|---|
| `id` | INTEGER PK | 자동 증가 ID |
| `batch_id` | TEXT | 실행 배치 식별자(Resume/이력 분리 단위) |
| `sku` | TEXT | Amazon ASIN |
| `category` | TEXT | `TV` 또는 `Monitor` |
| `country` | TEXT | 입력의 `country` |
| `title` | TEXT | 입력의 `title` |
| `brand_1`, `brand_2` | TEXT | 브랜드 |
| `resolution_1`, `resolution_2` | TEXT | 표준 해상도(예: `3840 x 2160`) 및 라벨 |
| `inch` | TEXT | 인치(정수 문자열 또는 `-`) |
| `display_technology` | TEXT | TV: `OLED`/`LCD`, Monitor: `OLED`/`-` |
| `led_type` | TEXT | TV용(`OLED`/`QLED`/`Mini LED`/`-`) |
| `refresh_rate` | TEXT | Monitor용(숫자 문자열) |
| `response_time` | TEXT | 현재 코드에서는 미기록(확장용) |
| `segment` | TEXT | Monitor용(`Gaming`/`HRM`/`Mainstream`/`Others`) |
| `others_yn` | TEXT | `-` 또는 `Others` |
| `update_time` | TEXT | 저장 시각(`YYYY-mm-dd HH:MM:SS`) |
| `raw_gpt_response` | TEXT | 현재 코드에서는 미기록(확장용) |
| `execution_time` | REAL | SKU 1건 처리 소요 시간(초) |

### 키/중복 정책
- PK는 `id`이며, `sku`는 전역 유니크가 아닙니다.
- 같은 `sku`라도 **여러 배치/여러 재시도 결과가 누적**됩니다(append-only).
- “최신값”은 Export 시 `update_time` 기준으로 계산합니다.

### Resume(재개) 기준
- `get_processed_skus(batch_id)`는 `enrichment_history`에서 해당 `batch_id`의 `sku` 목록을 읽어 Set으로 반환합니다.
- 따라서 **같은 배치ID를 유지하면 재실행 시 이미 처리된 SKU를 건너뜁니다.**

## 3) 출력 데이터 (Excel Export)
### 파일
- 기본 출력: `DI_CDMlabs/new_sku_nov_filled.xlsx`

### Export 로직
`DI_CDMlabs/db_manager.py`의 `export_to_excel()`이 수행합니다.
- `enrichment_history` 전체(또는 batch 필터) 조회
- `update_time` 내림차순 정렬 후, `sku` 기준 dedupe(`keep='first'`)
- 시트별로 일부 컬럼을 선별해 저장

#### TV 시트(주요 컬럼)
- `sku`, `country`, `title`, `brand_1`, `brand_2`, `resolution_1`, `resolution_2`, `inch`, `display_technology`, `led_type`, `others_yn`, `update_time`, `batch_id`, `execution_time`

#### Monitor 시트(주요 컬럼)
- `sku`, `country`, `title`, `brand_1`, `brand_2`, `resolution_1`, `resolution_2`, `refresh_rate`, `inch`, `display_technology`, `segment`, `others_yn`, `update_time`, `batch_id`, `execution_time`

## 4) 검증 리포트(부가 출력) — compare_data.py
`DI_CDMlabs/compare_data.py`는 아래 동작을 수행합니다.
- 마스터: `DI_CDMlabs/modelmaster_new_sku.xlsx`
- 타깃: `DI_CDMlabs/new_sku_nov_filled.xlsx`
- `sku` 기준 merge 후, 컬럼별 비교 결과를 아래 컬럼으로 기록합니다.
  - `validation_result`: `Correct`/`Incorrect`/`Correct (Others)`
  - `validation_details`: 불일치한 필드 상세
- 그리고 `*_master` 접미사 컬럼들이 함께 포함된 형태로 **`new_sku_nov_filled.xlsx`를 덮어씁니다.**

운영상 “순수 export 결과 파일”이 필요하면, `compare_data.py` 실행 전에 `new_sku_nov_filled.xlsx`를 별도 파일명으로 복사해 두는 것을 권장합니다.

