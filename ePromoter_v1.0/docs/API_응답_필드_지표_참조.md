# API 응답 필드 → 지표 참조

Data/Graph API 응답(`analysis/api_responses/*.json`)에서 추출한 **필드 구조**로, 테이블/그래프에 쓰이는 **데이터 항목**을 역추적할 수 있습니다.

---

## 1. 용도

- **지표 정의 보강**: 응답 필드명(예: `prom_chat_handled_c`, `eStore_all_order_p`)이 곧 해당 API가 제공하는 지표 후보입니다.
- **테이블·그래프 역참조**: `docs/테이블_그래프_API_역참조_명세.md`, `analysis/table_api_spec.json`, `analysis/graph_api_spec.json`에서 **어느 화면이 어느 API를 쓰는지** 확인 후, 여기서 해당 API의 응답 필드를 조회하면 됩니다.

---

## 2. API별 응답 필드 샘플

| API 파일 (api_responses/) | 응답 구조 요약 | 비고 |
|---------------------------|----------------|------|
| executiveSummary_getExecutiveData.json | ok, data | 테이블/요약 데이터 |
| executiveSummary_getExecutiveGraphData.json | ok, data | 차트용 |
| divisionSummary_getDivisionData.json | ok, data (current_date, headCount, divisionData: eStore_*, prom_*, offerd_volume_*, …) | 사업부별 지표 |
| divisionSummary_getDivisionTableData.json | ok, data | 테이블용 |
| divisionSummary_getDivisionGraphData.json | ok, data | 차트용 |
| Sales_getSalesSummaryDataNew.json | ok, data | 영업 요약 |
| Sales_getSalesSummaryGraphDataNew.json | ok, data | 영업 차트 |
| operationSummary_getOperationDataNew.json | ok, data | 운영 요약 |
| operationSummary_getOperationTableData.json | ok, data | 운영 테이블 |
| operationSummary_getOperationAllGraphData.json | ok, data | 운영 차트 |
| ShopApp_*, BotJourney_*, Epp_*, Retailer_*, MxFlagship_*, PerformanceSummary_* | 각 ok, data 내부 필드 | 메뉴별 동일 패턴 |

---

## 3. 응답 필드 → 지표 정의 예시 (Division Summary)

`divisionSummary_getDivisionData.json`의 `data.divisionData` 예:

| 필드명 (API) | 지표 후보 해석 |
|--------------|----------------|
| eStore_all_order_p | eStore 전체 주문 수 (현재) |
| eStore_all_order_count_p / _c | 주문 건수 (현재/이전) |
| eStore_all_sale_rev_p / _c | eStore 매출 (현재/이전) |
| prom_chat_handled_c / total_prom_chat_handled_p | 프로모터 처리 채팅 수 |
| offerd_volume_c / _p | Offered Chat 수 |
| prom_rev_aov_p / _c | 프로모터 매출 AOV 등 |

- **정의·단위**는 매뉴얼·운영 문서로 추가 보강하면 됩니다.
- **테이블 헤더**와 매칭할 때: 화면의 "Visit to Chat Rate", "Missed Chat" 등은 위 필드들을 조합한 **산식 결과**일 수 있으므로, 프론트 소스(`js/googleChart.js`, 메뉴별 JS) 또는 매뉴얼에서 산식 확인이 필요합니다.

---

## 4. 파이프라인 요약

1. **화면** (테이블/그래프) → **역참조 명세**에서 사용 API 확인 (`table_api_spec.json`, `graph_api_spec.json`).
2. **API** → **응답 샘플** 확인 (`api_responses/{메뉴}_{API명}.json`).
3. **응답 필드** → **지표 목록·정의** 보강 (`indicator_list.json`, `데이터_지표_정의_가이드.md`).

*생성: 분석 스크립트 + dashboard_deep_analysis.py (API 응답 캡처)*
