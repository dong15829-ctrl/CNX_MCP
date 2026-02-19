# DI_CDMlabs — Architecture

`DI_CDMlabs/`는 엑셀 기반 SKU(ASIN) 목록을 입력으로 받아, 검색 컨텍스트를 수집하고 LLM으로 스펙을 추출해 DB에 이력으로 누적 저장한 뒤, 최신 결과를 엑셀로 Export하는 파이프라인입니다.

- 작업 명세/운영: `DI_CDMlabs/System_Architecture_and_Task_Spec.md`
- 데이터 구조/스키마: `DI_CDMlabs/DATA_MODEL.md`

## 1) 구성요소
### 실행/오케스트레이션
- `DI_CDMlabs/enrich_data.py`
  - 엑셀 로드 → 시트별 병렬 처리 → DB 기록 → Export
  - 병렬 처리: `ThreadPoolExecutor(max_workers=5)`
  - 출력 규칙은 프롬프트(`tv_prompt.txt`, `mo_prompt.txt`)를 “정의서”로 사용

### 검색(컨텍스트 수집)
- Serper(Google): `https://google.serper.dev/search`
  - 상위 3개 결과의 title/link/snippet을 컨텍스트로 사용
- DuckDuckGo: `duckduckgo_search.DDGS`
  - 상위 3개 결과의 title/link/body를 컨텍스트로 사용

검색 전략(한 SKU에 대해 순차 실행):
1. `ASIN`: `site:amazon.{tld} {sku}`
2. `MODEL`: `{brand} {model_code} specifications` (+ `site:displayspecifications.com ...` 타겟 쿼리)
3. `TITLE`: `{title} specs`
4. `AGGRESSIVE`: `{title} resolution refresh rate specifications datasheet manual`

### LLM(스펙 추출)
- Gemini: `google-generativeai`
  - 모델: `models/gemini-3-pro-preview`
  - 프롬프트: 시트에 따라 `tv_prompt.txt` 또는 `mo_prompt.txt`
  - 출력: 헤더 없는 TSV(프롬프트에서 강제)

### 저장(History DB)
- `DI_CDMlabs/db_manager.py`
  - SQLite `enrichment_history` 테이블에 append-only 저장(행 단위 커밋)
  - Resume를 위해 `batch_id` 기준으로 처리된 SKU Set을 조회
  - Export 시 `update_time` 기준 최신값을 dedupe 후 엑셀로 저장

## 2) 데이터 플로우
### SKU 단위 처리 흐름
```mermaid
flowchart TD
  A[Load Excel new_sku_nov.xlsx] --> B{Sheet: TV/Monitor}
  B --> C[For each row: sku,country,title,model_code,brand]
  C --> D{Already processed in batch?}
  D -- yes --> E[Skip]
  D -- no --> F[Search: ASIN/MODEL/TITLE/AGGRESSIVE]
  F --> G[Combine context (Serper + DDG)]
  G --> H[Gemini extract TSV]
  H --> I[Parse TSV -> dict]
  I --> J{Validate (Others or inch present)}
  J -- fail --> K[Drop/Log]
  J -- ok --> L[Insert into enrichment_history (commit)]
  L --> M[After all: Export latest per SKU -> new_sku_nov_filled.xlsx]
```

## 3) Resume/재실행 정책
- Resume의 기준은 `batch_id`입니다.
  - 동일 `batch_id`로 재실행하면, DB에 이미 기록된 SKU는 스킵합니다.
  - 새 실행을 “새 이력”으로 남기려면 `BATCH_ID`를 변경합니다.
- 레거시 마이그레이션 로직
  - 과거 `products` 테이블이 존재하는 경우 `enrichment_history`로 이동 후 drop합니다.

## 4) 병렬성/스레드 안전성
- 워커 5개로 SKU 단위 작업을 병렬 제출합니다.
- 출력(print)은 `PRINT_LOCK`으로 섞임을 방지합니다.
- DB insert는 “호출마다 새 connection”을 열어 커밋하므로 스레드 충돌을 피합니다(동시성 성능은 제한될 수 있음).

## 5) 실패 모드/트러블슈팅 관점
- 네트워크/API 키 문제:
  - Serper/Gemini 키 누락 또는 레이트리밋 → 컨텍스트 부족/결과 없음 증가
- 출력 포맷 문제:
  - LLM이 TSV 규칙을 어기면 “컬럼 수 불일치”로 해당 SKU는 저장되지 않음
  - `clean_data.py`는 문자열 아티팩트(예: `plaintext`) 제거용 후처리
- 유효성 판단:
  - 현재 구현은 `others_yn=Others`이거나 `inch`가 존재해야 유효로 간주합니다.
  - Monitor에서도 `inch`가 비어있으면 실패로 처리될 수 있으므로(스펙 일부만 추출된 경우) 운영 시 주의가 필요합니다.

## 6) 보안/컴플라이언스 메모
- `.env`에 외부 서비스 API 키를 저장하며, 레포에 키를 커밋하지 않아야 합니다.
- 검색/LLM 결과에 대한 출처 링크를 저장하지 않으므로(현재 구현), 추적성 요구가 있다면 DB 스키마/저장 로직 확장이 필요합니다.

