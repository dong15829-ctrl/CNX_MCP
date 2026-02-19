# 매뉴얼 05: API 레퍼런스

## 1. 공통 사항

- **Base URL**: 재현 환경에 따라 변경 (예: `https://www.globalsess.com/globaldashboard`).
- **인증**: 세션 쿠키. POST 요청 시 `Content-Type: application/json`, body는 JSON.
- **에러**: 서버 응답에 따라 `ok: false`, `data: "메시지"` 등 처리.

## 2. 로그인

```
POST /login  (또는 /globaldashboard/login)
Body: { "user_id": "string", "user_pw": "string" }
성공: { "ok": true, "data": 0|1 }
실패: { "ok": false, "data": "메시지" }
```

## 3. 공통 API

### 3.1 getCountry

```
POST /ajax/getCountry
Body: { "rhqArray": ["AFRICA","Americas","APAC","EHQ","G.CN","KOREA","MENA","SWA"], "title": "Executive Summary" }
```

- **용도**: Region 목록/필터. 응답으로 Region 체크박스 데이터 구성.

### 3.2 getSiteCode

```
POST /ajax/getSiteCode
Body: { "localArray": ["SAMCOL","SAVINA", ...], "title": "Executive Summary" }
```

- **용도**: Local/Site 목록. 응답으로 Country/Site 체크박스 구성.

### 3.3 checkPending

```
POST /checkPending
Body: (빈 객체 또는 null)
```

- **용도**: 데이터 처리 중 여부 확인.

### 3.4 switchTable

```
POST /switchTable
Body: (빈 객체 또는 null)
```

- **용도**: 테이블 스위치 설정.

## 4. 필터 공통 Body 예시

대부분의 Data/Graph API에 공통으로 들어가는 필드:

```json
{
  "title": "Executive Summary",
  "from": "2026-02-06",
  "to": "2026-02-06",
  "period": "custom",
  "site_code": "AE,AU,BR,DE,...",
  "period_date": "",
  "switch_table": { "chat": 1, "sales14": 2, "sales": 1 }
}
```

- **period_date**: 주 단위 시 "28" 등.
- **switch_table**: 화면에서 선택한 값에 따라 변경.

## 5. 메뉴별 Data/Graph API 경로만 정리

| 메뉴 | Data / Table API | Graph API |
|------|-------------------|-----------|
| Executive | `/executiveSummary/ajax/getExecutiveData` | `/executiveSummary/ajax/getExecutiveGraphData` |
| Division | `/divisionSummary/ajax/getDivisionData`, `getDivisionTableData` | `/divisionSummary/ajax/getDivisionGraphData` |
| Sales | `/Sales/ajax/getSalesSummaryDataNew` | `/Sales/ajax/getSalesSummaryGraphDataNew` |
| Operation | `/operationSummary/ajax/getOperationDataNew`, `getOperationTableData` | `/operationSummary/ajax/getOperationAllGraphData` |
| ShopApp | `/ShopApp/ajax/getShopAppOperationSummaryData`, `getOperationTableData` | `/ShopApp/ajax/getOperationAllGraphData` |
| Bot/AI | `/BotJourney/ajax/getBotJourneyOperationSummaryData`, `getOperationTableData` | `/BotJourney/ajax/getOperationAllGraphData` |
| EPP/SMB | `/Epp/ajax/getOperationData`, `getOperationTableData` | `/Epp/ajax/getOperationGraphData` |
| Retailer | `/Retailer/ajax/getRetailerOperationData` | `/Retailer/ajax/getRetailerOperationGraphData` |
| MX Flagship | `/MxFlagship/ajax/getFlagshipPreTableData` | (없음) |
| Performance | getPerformanceFunnelData, getPerformanceTrafficTableData, getPerformanceMissedChatTableData, getPerformanceHandledChatTableData | (별도) |

## 6. 기타

- **비밀번호 변경**: `POST /changePassword` — body에 현재 비밀번호, 새 비밀번호 등 (MD5 사용 가능).
- **공통 엑셀 다운로드**: `POST /globaldashboard/CommonExcelDownload` — form 제출, getParam() 기반 필드 + type, product_division 등.
- **Manual & FAQ**: `fileDown()` 호출 시 해당 다운로드 URL로 이동 또는 다운로드.

## 7. 스키마/샘플 위치

- `replication/schemas/request_login.json`
- `replication/schemas/request_filter_common.json`
- `replication/config/api_endpoints.json` (전체 URL·메서드 정리)
