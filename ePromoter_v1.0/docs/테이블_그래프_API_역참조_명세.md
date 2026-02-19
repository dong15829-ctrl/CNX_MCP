# 테이블·그래프 → API 역참조 명세서

대시보드 **테이블/그래프**가 **어느 API**를 참조하는지, 요청/응답 구조 샘플을 역추적한 명세입니다.

---

## 1. 테이블 → API 참조

| 메뉴 | 테이블(class/id) | 컬럼(헤더) | Data/Table API | 요청 | 응답 스키마 샘플 |
|------|------------------|------------|----------------|------|------------------|
| Bot / AI Summary | data_type_table | Daily, Weekly, Monthly, Quarterly | /BotJourney/ajax/getBotJourneyOperationSummaryData | from apis_this_page.post_data | — |
| Bot / AI Summary | — | date, Bot Total Chat, ePromoter Total Chat, 02.08, | /BotJourney/ajax/getBotJourneyOperationSummaryData | from apis_this_page.post_data | — |
| Bot / AI Summary | f_t_table rank_type4 dataTable | Rank, Country, Offered Chat, Handled Chat, Missed  | /BotJourney/ajax/getBotJourneyOperationSummaryData | from apis_this_page.post_data | — |
| Bot / AI Summary | f_t_table rank_type4 dataTable rank_type | Rank, Country, Offered Chat, Handled Chat, Missed  | /BotJourney/ajax/getBotJourneyOperationSummaryData | from apis_this_page.post_data | — |
| Bot / AI Summary | f_t_table rank_type4 dataTable | -, Total, 128, 128, 0% | /BotJourney/ajax/getBotJourneyOperationSummaryData | from apis_this_page.post_data | — |
| Division Summary | data_type_table | Daily, Weekly, Monthly, Quarterly | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | — | date, Total, MX, VD, DA | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type3 dataTable | Rank, Country, Conversion Rate (Order), Contributi | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type3 dataTable rank_type | Rank, Country, Conversion Rate (Order), Contributi | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type3 dataTable | -, Total, 12.9%, 4.7% | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | — | date, Promoter Revenue, Premium Portion, 02/08, 40 | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | — | date, Galaxy S / Z, QLED, Bespoke, 02/08 | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type4 dataTable | Rank, Country, Promoter revenue, Promoter H/C, Rev | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type4 dataTable rank_type | Rank, Country, Promoter revenue, Promoter H/C, Rev | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type4 dataTable | Total, 404,092, 289, 1,398 | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type5 dataTable | Rank, Country, Conversion (Order), Contribution, V | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type5 dataTable rank_type | Rank, Country, Conversion (Order), Contribution, V | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | f_t_table rank_type5 dataTable | -, Total, 12.9%, 4.7%, 0.00% | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| Division Summary | hce_table | Subsidiary | /divisionSummary/ajax/getDivisionData | from apis_this_page.post_data | ok, data |
| EPP / SMB Summary | data_type_table | Daily, Weekly, Monthly, Quarterly | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | — | date, Missed Chat Rate, Offered Chat, Handled Chat | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | — | date, IRT, ART, Handled Chat, 02/08 | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | — | date, CSAT, Answered, Satisfied, 02/08 | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | f_t_table rank_type1 dataTable | Rank, Subsidiary, EPP store name
(EPP partner ID), | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | f_t_table rank_type1 dataTable rank_type | Rank, Subsidiary, EPP store name
(EPP partner ID), | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | f_t_table rank_type1 dataTable | Total # of store count, -, -, Avg. value, Avg. val | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | — | date, Missed Chat Rate, Offered Chat, Handled Chat | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | — | date, IRT, ART, Handled Chat, 02/08 | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| EPP / SMB Summary | — | date, CSAT, Answered, Satisfied, 02/08 | /Epp/ajax/getOperationData | from apis_this_page.post_data | — |
| Executive Summary | data_type_table | Daily, Weekly, Monthly, Quarterly | /executiveSummary/ajax/getExecutiveData | from apis_this_page.post_data | ok, data |
| Executive Summary | — | date, Visit to Chat Rate, 02.08, 0% | /executiveSummary/ajax/getExecutiveData | from apis_this_page.post_data | ok, data |
| Executive Summary | — | date, Visit to Chat Rate, 02.08, 0% | /executiveSummary/ajax/getExecutiveData | from apis_this_page.post_data | ok, data |
| Executive Summary | — | date, Missed Chat Rate, Offered Chat, Missed Chat, | /executiveSummary/ajax/getExecutiveData | from apis_this_page.post_data | ok, data |
| Executive Summary | — | date, Contribution Rate, Conversion Rate, 02.08, 4 | /executiveSummary/ajax/getExecutiveData | from apis_this_page.post_data | ok, data |
| Executive Summary | — | date, Revenue per Promoter, Promoter Revenue, 02.0 | /executiveSummary/ajax/getExecutiveData | from apis_this_page.post_data | ok, data |
| Executive Summary | — | date, CSAT, 02.08, 87.4% | /executiveSummary/ajax/getExecutiveData | from apis_this_page.post_data | ok, data |
| MX Flagship Summary | f_t_table mx_list dataTable | Rank, Region, Subsidiary, Date Period, Contributio | /MxFlagship/ajax/getFlagshipPreTableData | from apis_this_page.post_data | — |
| MX Flagship Summary | f_t_table mx_list dataTable mx_type4 | Rank, Region, Subsidiary, Date Period, Contributio | /MxFlagship/ajax/getFlagshipPreTableData | from apis_this_page.post_data | — |
| MX Flagship Summary | f_t_table mx_list dataTable | Total # of
Sub count, -, -, -, Total value | /MxFlagship/ajax/getFlagshipPreTableData | from apis_this_page.post_data | — |
| MX Flagship Summary | f_t_table mx_list dataTable | Rank, Region, Subsidiary, Pre-order Period, Contri | /MxFlagship/ajax/getFlagshipPreTableData | from apis_this_page.post_data | — |
| MX Flagship Summary | f_t_table mx_list dataTable mx_type3 | Rank, Region, Subsidiary, Pre-order Period, Contri | /MxFlagship/ajax/getFlagshipPreTableData | from apis_this_page.post_data | — |
| MX Flagship Summary | f_t_table mx_list dataTable | Total # of
Sub count, -, -, -, Total value | /MxFlagship/ajax/getFlagshipPreTableData | from apis_this_page.post_data | — |
| Operation Summary | data_type_table | Daily, Weekly, Monthly, Quarterly | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | — | date, Visit to Chat Rate, Missed Chat, 02.08, 0% | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | f_t_table rank_type4 dataTable | Rank, Country, Offered Chat, Handled Chat, Missed  | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | f_t_table rank_type4 dataTable rank_type | Rank, Country, Offered Chat, Handled Chat, Missed  | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | f_t_table rank_type4 dataTable | -, Total, 5,296, 5,224, 1.4% | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | — | date, Proactive Chat Usage(%), Reactive Chat Usage | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | — | date, Rate, Video, 0 | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | f_t_table rank_type3 dataTable | Rank, Country, CS to ePromoter Chat, ePromoter to  | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | f_t_table rank_type3 dataTable rank_type | Rank, Country, CS to ePromoter Chat, ePromoter to  | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Operation Summary | f_t_table rank_type3 dataTable | -, Total, 255, 18 | /operationSummary/ajax/getOperationDataNew | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceFunnelData | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceTrafficTabl | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceMissedChatT | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceHandledChat | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceFunnelData | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceTrafficTabl | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceMissedChatT | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Traffic
(D2C), Traffic
(All), To | /PerformanceSummary/ajax/getPerformanceHandledChat | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 2,300,730, 2,951,682, 32,502 | /PerformanceSummary/ajax/getPerformanceFunnelData | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 2,300,730, 2,951,682, 32,502 | /PerformanceSummary/ajax/getPerformanceTrafficTabl | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 2,300,730, 2,951,682, 32,502 | /PerformanceSummary/ajax/getPerformanceMissedChatT | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 2,300,730, 2,951,682, 32,502 | /PerformanceSummary/ajax/getPerformanceHandledChat | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceFunnelData | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceTrafficTabl | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceMissedChatT | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceHandledChat | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceFunnelData | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceTrafficTabl | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceMissedChatT | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable deccending | Rank, Subsidiary, Total Chat, Missed Chat, Missed  | /PerformanceSummary/ajax/getPerformanceHandledChat | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 32,502, 100, 1.5% | /PerformanceSummary/ajax/getPerformanceFunnelData | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 32,502, 100, 1.5% | /PerformanceSummary/ajax/getPerformanceTrafficTabl | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 32,502, 100, 1.5% | /PerformanceSummary/ajax/getPerformanceMissedChatT | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | -, Avg., 32,502, 100, 1.5% | /PerformanceSummary/ajax/getPerformanceHandledChat | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Handled Chat, Promoter H/C, Chat | /PerformanceSummary/ajax/getPerformanceFunnelData | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Handled Chat, Promoter H/C, Chat | /PerformanceSummary/ajax/getPerformanceTrafficTabl | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Handled Chat, Promoter H/C, Chat | /PerformanceSummary/ajax/getPerformanceMissedChatT | from apis_this_page.post_data | — |
| Performance Summary | f_t_table no-footer dataTable | Rank, Subsidiary, Handled Chat, Promoter H/C, Chat | /PerformanceSummary/ajax/getPerformanceHandledChat | from apis_this_page.post_data | — |
| … | … | … | … | … | 외 32건은 `analysis/table_api_spec.json` 참고 |

---

## 2. 그래프 → API 참조

| 메뉴 | 차트(id/class) | 섹션 제목(그래프 설명) | Graph API | 응답 스키마 샘플 |
|------|----------------|-------------------------|-----------|------------------|
| Bot / AI Summary | half_2nd sum layout_border chart_pb | Bot Total Chat (=Offered Chat, Handled Chat)
Downl | /BotJourney/ajax/getOperationAllGraphData | — |
| Division Summary | half_1st overview layout_border cha | Promoter Handled Chat – by Division 
Download
Tota | /divisionSummary/ajax/getDivisionGraphData | ok, data |
| Division Summary | half_1st overview layout_border cha | Promoter Revenue / Promoter H/C / Revenue per Prom | /divisionSummary/ajax/getDivisionGraphData | ok, data |
| EPP / SMB Summary | — — | (메뉴별 차트 영역) | /Epp/ajax/getOperationGraphData | — |
| Executive Summary | — — | (메뉴별 차트 영역) | /executiveSummary/ajax/getExecutiveGraphData | ok, data |
| Operation Summary | half_2nd sum layout_border chart_pb | Visit to Chat Ratio / Missed Chat
Download
Visit t | /operationSummary/ajax/getOperationAllGraphDa | — |
| Operation Summary | half_1st sum mg_r20 layout_border c | — | /operationSummary/ajax/getOperationAllGraphDa | — |
| Retailer Summary | — — | (메뉴별 차트 영역) | /Retailer/ajax/getRetailerOperationGraphData | — |
| Sales Summary | — — | (메뉴별 차트 영역) | /Sales/ajax/getSalesSummaryGraphDataNew | — |
| ShopApp Summary | half_2nd sum layout_border chart_pb | Visit to Chat Ratio / Missed Chat
Download
Visit t | /ShopApp/ajax/getOperationAllGraphData | — |

---

## 3. 파이프라인 요약

- **테이블**: 메뉴별 Data/Table API (`menu_config.json`의 `dataApi`, `tableApi`, `dataApis`) → 요청 body는 `menu_*.json`의 `apis_this_page[].post_data` 참고.
- **그래프**: 메뉴별 Graph API (`menu_config.json`의 `graphApi`) → 동일한 필터 body 사용.
- **응답 스키마**: `analysis/api_responses/*.json` 수집 시 해당 파일의 최상위 키가 응답 필드 샘플로 사용됨.

*생성: scripts/build_reverse_spec.py | 테이블 112건, 그래프 10건*