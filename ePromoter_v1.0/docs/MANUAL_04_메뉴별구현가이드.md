# 매뉴얼 04: 메뉴별 구현 가이드

## 1. 공통 초기화 순서 (Summary 페이지)

각 Summary 페이지 로드 시 권장 순서:

1. **getCountry** 호출 → `rhqArray`, `title` 전달 → Region 체크박스 목록 구성
2. **getSiteCode** 호출 → `localArray`, `title` 전달 → Local/Site 체크박스 목록 구성
3. **해당 메뉴의 Data API** 호출 (from, to, site_code, switch_table 등)
4. **해당 메뉴의 Graph API** 호출 (동일 파라미터) → 차트 렌더링

Update 클릭 시 3–4만 동일 파라미터로 재호출.

## 2. 메뉴별 API 및 파라미터 요약

### 2.1 Executive Summary

| API | Method | 경로 | 비고 |
|-----|--------|------|------|
| 데이터 | POST | `/executiveSummary/ajax/getExecutiveData` | 테이블/요약 |
| 차트 | POST | `/executiveSummary/ajax/getExecutiveGraphData` | 그래프 |

- 공통 파라미터: title, from, to, period, site_code, period_date, switch_table.

### 2.2 Division Summary

| API | Method | 경로 |
|-----|--------|------|
| 채팅 타입 | POST | `/getChatType` |
| 데이터 | POST | `/divisionSummary/ajax/getDivisionData` |
| 테이블 | POST | `/divisionSummary/ajax/getDivisionTableData` |
| 차트 | POST | `/divisionSummary/ajax/getDivisionGraphData` |

- getDivisionData / getDivisionTableData: `title: "All"` 사용 가능.

### 2.3 Sales Summary

| API | Method | 경로 |
|-----|--------|------|
| 타입 | POST | `/getHybrisType` |
| 데이터 | POST | `/Sales/ajax/getSalesSummaryDataNew` |
| 차트 | POST | `/Sales/ajax/getSalesSummaryGraphDataNew` |

- body에 `period_date: "28"`, `custom_order_type: "ALL"`, `chat: "Text Chat,Video Call,..."` 등 추가.

### 2.4 Operation Summary

| API | Method | 경로 |
|-----|--------|------|
| 타입 | POST | `/getHybrisType` |
| 데이터 | POST | `/operationSummary/ajax/getOperationDataNew` |
| 테이블 | POST | `/operationSummary/ajax/getOperationTableData` |
| 차트 | POST | `/operationSummary/ajax/getOperationAllGraphData` |

- body에 `hybris_epp_category`, `chat`, `chat_missed` 등 추가 가능.

### 2.5 ShopApp Summary

| API | Method | 경로 |
|-----|--------|------|
| 데이터 | POST | `/ShopApp/ajax/getShopAppOperationSummaryData` |
| 테이블 | POST | `/ShopApp/ajax/getOperationTableData` |
| 차트 | POST | `/ShopApp/ajax/getOperationAllGraphData` |

### 2.6 Bot / AI Summary

| API | Method | 경로 |
|-----|--------|------|
| 데이터 | POST | `/BotJourney/ajax/getBotJourneyOperationSummaryData` |
| 테이블 | POST | `/BotJourney/ajax/getOperationTableData` |
| 차트 | POST | `/BotJourney/ajax/getOperationAllGraphData` |

### 2.7 EPP / SMB Summary

| API | Method | 경로 |
|-----|--------|------|
| 데이터 | POST | `/Epp/ajax/getOperationData` |
| 테이블 | POST | `/Epp/ajax/getOperationTableData` |
| 차트 | POST | `/Epp/ajax/getOperationGraphData` |

- body에 `chat: "Text Chat,Video Call,..."` 등.

### 2.8 Retailer Summary

| API | Method | 경로 |
|-----|--------|------|
| 데이터 | POST | `/Retailer/ajax/getRetailerOperationData` |
| 차트 | POST | `/Retailer/ajax/getRetailerOperationGraphData` |

- getCountry/getSiteCode의 rhqArray·localArray가 일부만 사용됨 (Americas, APAC, EHQ, G.CN 등). site_code 값도 Retailer 전용 코드 세트.

### 2.9 MX Flagship Summary

| API | Method | 경로 |
|-----|--------|------|
| 테이블 | POST | `/MxFlagship/ajax/getFlagshipPreTableData` |

- body에 `country`(쉼표 구분), `from`, `to`, `switch_table` 등. `title: "MX Flagship Summary"`.

### 2.10 Performance Summary

| API | Method | 경로 |
|-----|--------|------|
| 퍼널 | POST | `/PerformanceSummary/ajax/getPerformanceFunnelData` |
| 트래픽 테이블 | POST | `/PerformanceSummary/ajax/getPerformanceTrafficTableData` |
| Missed Chat 테이블 | POST | `/PerformanceSummary/ajax/getPerformanceMissedChatTableData` |
| Handled Chat 테이블 | POST | `/PerformanceSummary/ajax/getPerformanceHandledChatTableData` |

- from/to가 "Jan 2026" 형태일 수 있음. body에 `country` 사용.

## 3. 화면 구성 공통 사항

- **테이블**: `table.data_type_table` 또는 메뉴별 테이블 클래스. 정렬 아이콘: `img/images/sort_both.png`, `sort_asc.png`, `sort_desc.png`.
- **차트**: Google Charts. 각 Graph API 응답을 DataTable/options로 변환해 렌더링. `js/googleChart.js` 참고.
- **로딩**: `#loading-page` 표시 후 API 완료 시 숨김.

## 4. 설정 파일

- 메뉴별 path, label, icon, 사용 API 목록: `replication/config/menu_config.json`
- 전체 API 경로·메서드: `replication/config/api_endpoints.json`
