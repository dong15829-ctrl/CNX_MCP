# Samsung Global Dashboard (globalsess.com) 메뉴·기능 정리

**접속 URL:** https://www.globalsess.com/globaldashboard/  
**로그인 후 메인:** https://www.globalsess.com/globaldashboard/main  
**수집 일시:** 스크립트 실행 기준

---

## 1. 대시보드 메뉴 (좌측/상단 네비게이션)

| 메뉴명 | 경로 | 비고 |
|--------|------|------|
| **Executive Summary** | `/globaldashboard/executiveSummary` | 경영진 요약 |
| **Division Summary** | `/globaldashboard/divisionSummary` | 사업부별 요약 |
| **Sales Summary** | `/globaldashboard/sales_all2` | 영업 요약 |
| **Operation Summary** | `/globaldashboard/operation_all2` | 운영 요약 |
| **ShopApp Summary** | `/globaldashboard/shopapp_operation` | ShopApp 운영 |
| **Bot / AI Summary** | `/globaldashboard/botjourney_operation` | 봇/AI 저니 운영 |
| **EPP / SMB Summary** | `/globaldashboard/epp_operation` | EPP/SMB 운영 |
| **Retailer Summary** | `/globaldashboard/retailer_operation` | 리테일러 운영 |
| **MX Flagship Summary** | `/globaldashboard/mxFlagshipSummary_pre` | MX 플래그십 요약 |
| **Performance Summary** | `/globaldashboard/performanceSummary` | 성과 요약 |

---

## 2. 공통 기능 (버튼/액션)

- **Update** – 데이터/화면 갱신
- **Change Password** – 비밀번호 변경
- **Confirm** – 확인
- **Log out** – 로그아웃
- **Download** – 다운로드 (여러 화면에서 제공)
- **Cancel** – 취소
- **Apply** – 적용

---

## 3. 서브 내비게이션 (Executive Summary 등 내부)

동일 메뉴를 JavaScript로 이동하는 링크:

- Home → `moveMain()`
- Executive Summary → `moveExecutive()`
- Division Summary → `moveDevision()`
- Sales Summary → `moveSalesAll()`
- Operation Summary → `moveOperationAll()`
- ShopApp Summary → `moveShopappOperation()`
- Bot / AI Summary → `moveBotjourneyOperation()`
- EPP / SMB Summary → `moveEpp_operation()`
- Retailer Summary → `moveRetailer_operation()`
- MX Flagship Summary → `moveMxFlagshipSummary()`
- Performance Summary → `movePerformanceSummary()`
- **Manual & FAQ Download** → `fileDown()`

---

## 4. 요약

- **Samsung Global Dashboard**는 Concentrix Promoter Dashboard 로그인 후 사용하는 대시보드이며, **Executive / Division / Sales / Operation / ShopApp / Bot·AI / EPP·SMB / Retailer / MX Flagship / Performance** 등 10개 Summary 메뉴로 구성됩니다.
- 각 Summary는 해당 영역별 요약·운영 지표를 보여 주는 구조로 보이며, **Download**, **Update**, **Log out**, **Change Password** 등 공통 기능을 제공합니다.
- 매뉴얼·FAQ는 **Manual & FAQ Download** 링크(`fileDown()`)로 다운로드할 수 있습니다.

---

*수집 스크립트: `ePromoter_v1.0/globalsess_dashboard_crawl.py`*
