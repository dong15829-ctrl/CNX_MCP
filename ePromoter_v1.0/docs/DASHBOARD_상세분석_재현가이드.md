# Samsung Global Dashboard 상세 분석 및 재현 가이드

다른 환경에서 동일한 대시보드를 개발하기 위한 분석 결과 문서입니다.  
수집 스크립트: `dashboard_deep_analysis.py`  
수집 결과물: `analysis/` 폴더 (HTML, JSON, 스크린샷, API 목록)

---

## 목차

1. [대시보드 메뉴 전체](#1-대시보드-메뉴-전체)
2. [공통 기능 전체](#2-공통-기능-전체)
3. [서브 내비게이션 전체](#3-서브-내비게이션-전체)
4. [API 및 연동](#4-api-및-연동)
5. [프론트엔드 스택·자산](#5-프론트엔드-스택자산)
6. [재현 구현 가이드](#6-재현-구현-가이드)

---

## 1. 대시보드 메뉴 전체

### 1.1 라우트·경로

| 순서 | 메뉴명 | URL 경로 | 비고 |
|------|--------|----------|------|
| 0 | Main (Home) | `/globaldashboard/main` | 인덱스, 메뉴 선택만 |
| 1 | Executive Summary | `/globaldashboard/executiveSummary` | 경영진 요약 |
| 2 | Division Summary | `/globaldashboard/divisionSummary` | 사업부별 요약 |
| 3 | Sales Summary | `/globaldashboard/sales_all2` | 영업 요약 |
| 4 | Operation Summary | `/globaldashboard/operation_all2` | 운영 요약 |
| 5 | ShopApp Summary | `/globaldashboard/shopapp_operation` | ShopApp 운영 |
| 6 | Bot / AI Summary | `/globaldashboard/botjourney_operation` | 봇/AI 저니 |
| 7 | EPP / SMB Summary | `/globaldashboard/epp_operation` | EPP/SMB 운영 |
| 8 | Retailer Summary | `/globaldashboard/retailer_operation` | 리테일러 운영 |
| 9 | MX Flagship Summary | `/globaldashboard/mxFlagshipSummary_pre` | MX 플래그십 |
| 10 | Performance Summary | `/globaldashboard/performanceSummary` | 성과 요약 |

### 1.2 메인(Home) 페이지 메뉴 구조 (HTML)

- **레이아웃**: `.body_wrap` > `.index_wrap` > `.index_tit`(로고) + `.index_menu_wrap`(메뉴 리스트)
- **메뉴 아이템**: `ul.index_menu_wrap` > `li.index_menu` > `a[href="/globaldashboard/..."]`
  - 내부: `.icon_wrap` > `.icon_area.img01` 등 (아이콘 클래스), `.index_txt`(메뉴 텍스트, `<br>`로 줄바꿈)

### 1.3 메뉴별 아이콘 클래스 (메인 페이지)

| 메뉴 | 아이콘 클래스 |
|------|----------------|
| Executive Summary | `icon_area img01` |
| Division Summary | `icon_area img12` |
| Sales Summary | `icon_area img02` |
| Operation Summary | `icon_area img03` |
| ShopApp Summary | `icon_area img15` |
| Bot / AI Summary | `icon_area img16` |
| EPP / SMB Summary | `icon_area img11` |
| Retailer Summary | `icon_area img10` |
| MX Flagship Summary | `icon_area h75 img14` |
| Performance Summary | `icon_area img13` |

### 1.4 아이콘 이미지 경로 (자산)

- 로고: `img/new_logo.jpg`
- 메인 메뉴 아이콘: `img/main_icon/icon_01_off.png`, `icon_02_off.png`, … `icon_16_off.png`, `icon_10.png`(Retailer 활성 등)
- Summary 페이지 공통: `img/icon_hbg.png`, `img/icon_global.png`, `img/icon_arrow_down.png`, `img/icon_date.png`, `img/icon_noti.png`, `img/icon_user.png`, `img/btn_down.png`, `img/icon_download.png`, `img/icon_up_arrow.png`, `img/icon_summary_up.png`, `img/icon_close.png`, `img/icon_b_arrow.png`, `img/icon_down_arrow.png`, `img/icon_summary_down.png`, `img/icon_down_arrow_type2.png`, `img/icon_up_arrow_type2.png`
- 차트/그래프 placeholder: `img/epromoter/new/graph_30.jpg`, `graph_31.jpg`, … (메뉴별 상이)
- 기타: `img/images/dimmed.png`, `img/images/sort_both.png`, `sort_asc.png`, `sort_desc.png`, `img/funnel/funnel_bg.png`, `img/red_down.png`, `img/green_up.png`

---

## 2. 공통 기능 전체

Summary 페이지(Executive 등) 상단 GNB에서 공통으로 제공하는 기능입니다.

### 2.1 헤더(GNB) 구조

- **영역**: `.gnb_wrap` > `.gnb_top`
- **햄버거**: `button.gnb_hbg`
- **페이지 제목**: `.gnb_tit` (예: "Executive Summary")
- **Region / Local / Site 필터**: `.gnb_option_wrap` > Region/Local/Site 체크박스 + `#region`, `#country`, `#site` 표시
- **날짜**: `.gnb_option_wrap` > `input#date` (daterangepicker, `name="daterange"`)
- **Daily/Weekly/Monthly/Quarterly**: `table.data_type_table` > `td.data_type[data-period="day|week|month|quarter"]`
- **Update 버튼**: `button.gnb_btn_update` → `onclick="getUpdate()"`
- **사용자 영역**: `.gnb_user_wrap` > `.icon_user`, `.user_name`, `.wrap_pop_user_pwd`
  - **Change Password**: `button.btn_chg_pwd`  
    - 비밀번호 입력: `#current_pw`, `#new_pw`, `#renew_pw`  
    - 확인: `button#passwordChange` → `ajax.post("/changePassword", param, ...)`
  - **Log out**: `button.btn_logout`
- **Download**: `button#headerDownload` → form POST to `/globaldashboard/CommonExcelDownload`
- **Last Update**: `.last_update` > `span` (날짜 텍스트)

### 2.2 공통 기능 목록 (동작 기준)

| 기능 | 트리거 | 연동 |
|------|--------|------|
| Update | `getUpdate()` | 현재 페이지 데이터/그래프 재요청 |
| Change Password | `#passwordChange` 클릭 | POST `/changePassword` (current_pw, new_pw 등) |
| Confirm | 비밀번호 변경 확인 | 위와 동일 |
| Log out | `button.btn_logout` | 로그아웃 처리 후 로그인 페이지로 |
| Download | `#headerDownload` | POST `/globaldashboard/CommonExcelDownload` (getParam() 기반 폼) |
| Cancel | 모달/팝업 취소 | UI만 |
| Apply | 필터 적용 | Region/Site 선택 후 Update와 연계 |

### 2.3 필터 파라미터 공통 구조

대부분의 데이터 API는 아래와 유사한 JSON body를 사용합니다.

- `title`: 페이지 제목 (예: "Executive Summary")
- `from`, `to`: 날짜 (예: "2026-02-06")
- `period`: "custom" 등
- `site_code`: 선택된 사이트 코드 (쉼표 구분)
- `period_date`: 주 단위 등 (빈 문자열 또는 "28" 등)
- `switch_table`: `{ "chat": 1, "sales14": 2, "sales": 1 }` 형태

---

## 3. 서브 내비게이션 전체

Summary 페이지 좌측 LNB(사이드 메뉴)에서 사용하는 JavaScript 함수 및 링크입니다.

### 3.1 함수 → URL 매핑

| 함수명 | 이동 경로 |
|--------|-----------|
| `moveMain()` | `/globaldashboard/main` |
| `moveExecutive()` | `/globaldashboard/executiveSummary` |
| `moveDevision()` | `/globaldashboard/divisionSummary` |
| `moveSalesAll()` | `/globaldashboard/sales_all2` |
| `moveOperationAll()` | `/globaldashboard/operation_all2` |
| `moveShopappOperation()` | `/globaldashboard/shopapp_operation` |
| `moveBotjourneyOperation()` | `/globaldashboard/botjourney_operation` |
| `moveEpp_operation()` | `/globaldashboard/epp_operation` |
| `moveRetailer_operation()` | `/globaldashboard/retailer_operation` |
| `moveMxFlagshipSummary()` | `/globaldashboard/mxFlagshipSummary_pre` |
| `movePerformanceSummary()` | `/globaldashboard/performanceSummary` |
| `fileDown()` | Manual & FAQ 다운로드 (별도 엔드포인트) |

### 3.2 LNB HTML 구조

- **래퍼**: `.lnb_wrap` (`.lnb_close` 버튼, `.lnb_logo` > `img`)
- **메뉴**: `ul.lnb_menu` > `li` > `a[href="javascript:moveXXX()"]`
  - Home: `li.home`
  - 현재 메뉴: `li.menu_li.active`
- **Manual & FAQ Download**: `a[href="javascript:fileDown()"]`

재현 시에는 위 함수를 해당 경로로의 `location.href` 또는 SPA 라우팅으로 매핑하면 됩니다.

---

## 4. API 및 연동

### 4.1 로그인

| 항목 | 내용 |
|------|------|
| URL | `POST /globaldashboard/login` (또는 `//login`) |
| Body | `application/json`: `{ "user_id": "이메일", "user_pw": "비밀번호" }` |
| 성공 시 | `respon.ok` true, `respon.data == 1`이면 데이터 처리 중 안내 후에도 진행, `location.href = '/globaldashboard/main'` |
| 실패 시 | `respon.data`에 메시지, alert 표시 |

### 4.2 공통 API (여러 메뉴에서 사용)

| 메서드 | 경로 | 용도 | Body 예시 |
|--------|------|------|-----------|
| POST | `/ajax/getCountry` | Region 목록/필터 | `{ "rhqArray": ["AFRICA","Americas",...], "title": "Executive Summary" }` |
| POST | `/ajax/getSiteCode` | Local/Site 목록 | `{ "localArray": ["SAMCOL",...], "title": "Executive Summary" }` |
| POST | `/switchTable` | 테이블 스위치 설정 | (빈 body 가능) |
| POST | `/checkPending` | 데이터 처리 중 여부 | (빈 body 가능) |

### 4.3 메뉴별 데이터·그래프 API

**Executive Summary**

- `POST /executiveSummary/ajax/getExecutiveData` — 테이블/요약 데이터
- `POST /executiveSummary/ajax/getExecutiveGraphData` — 차트 데이터

**Division Summary**

- `POST /getChatType` — 채팅 타입
- `POST /divisionSummary/ajax/getDivisionData` — 요약 데이터
- `POST /divisionSummary/ajax/getDivisionTableData` — 테이블
- `POST /divisionSummary/ajax/getDivisionGraphData` — 차트

**Sales Summary**

- `POST /getHybrisType` — Hybris 타입
- `POST /Sales/ajax/getSalesSummaryDataNew` — 요약 데이터
- `POST /Sales/ajax/getSalesSummaryGraphDataNew` — 차트

**Operation Summary**

- `POST /getHybrisType`
- `POST /operationSummary/ajax/getOperationDataNew` — 요약 데이터
- `POST /operationSummary/ajax/getOperationTableData` — 테이블
- `POST /operationSummary/ajax/getOperationAllGraphData` — 차트

**ShopApp Summary**

- `POST /ShopApp/ajax/getShopAppOperationSummaryData`
- `POST /ShopApp/ajax/getOperationTableData`
- `POST /ShopApp/ajax/getOperationAllGraphData`

**Bot / AI Summary**

- `POST /BotJourney/ajax/getBotJourneyOperationSummaryData`
- `POST /BotJourney/ajax/getOperationTableData`
- `POST /BotJourney/ajax/getOperationAllGraphData`

**EPP / SMB Summary**

- `POST /Epp/ajax/getOperationData`
- `POST /Epp/ajax/getOperationTableData`
- `POST /Epp/ajax/getOperationGraphData`

**Retailer Summary**

- `POST /Retailer/ajax/getRetailerOperationData`
- `POST /Retailer/ajax/getRetailerOperationGraphData`  
  (Retailer는 getCountry/getSiteCode의 rhqArray/localArray가 일부만 사용됨)

**MX Flagship Summary**

- `POST /MxFlagship/ajax/getFlagshipPreTableData`  
  (body에 `country` 사용, `from`/`to` 등)

**Performance Summary**

- `POST /PerformanceSummary/ajax/getPerformanceFunnelData`
- `POST /PerformanceSummary/ajax/getPerformanceTrafficTableData`
- `POST /PerformanceSummary/ajax/getPerformanceMissedChatTableData`
- `POST /PerformanceSummary/ajax/getPerformanceHandledChatTableData`  
  (from/to가 "Jan 2026" 형태 등)

### 4.4 다운로드·기타

- **공통 엑셀 다운로드**: `POST /globaldashboard/CommonExcelDownload` — form 제출, `getParam()` 기반 파라미터 + `type`, `product_division` 등
- **메뉴별 엑셀**: 예) `POST /globaldashboard/ExecutiveExcelDownload` (Executive 등)
- **Manual & FAQ**: `fileDown()` 호출 시 해당 파일 다운로드 URL/엔드포인트로 이동 또는 다운로드
- **비밀번호 변경**: `POST /changePassword` (현재 비밀번호, 새 비밀번호 등, MD5 등 암호화 사용 가능성 있음 — `blueimp-md5` 로드됨)

---

## 5. 프론트엔드 스택·자산

### 5.1 스크립트

| 경로 | 용도 |
|------|------|
| `js/jquery.js` | jQuery |
| `js/util.js` | 공통 유틸(ajax 등) |
| `js/common.js` | Summary 공통 (메뉴별) |
| `js/googleChart.js` | Google Charts 래퍼 (Summary) |
| `js/daterangepicker.js` | 날짜 범위 선택 |
| `https://www.gstatic.com/charts/loader.js` | Google Charts |
| `https://cdn.jsdelivr.net/jquery/latest/jquery.min.js` | jQuery (중복 로드 가능) |
| `https://cdn.jsdelivr.net/momentjs/latest/moment.min.js` | Moment.js |
| `//cdnjs.cloudflare.com/ajax/libs/blueimp-md5/2.10.0/js/md5.min.js` | MD5 (비밀번호 등) |

### 5.2 스타일시트

- `css/reset.css`, `css/layout.css`, `css/style.css`
- `css/daterangepicker.css`
- Google Charts: `https://www.gstatic.com/charts/51/css/core/tooltip.css`, `util.css`

### 5.3 페이지별 구조 요약

- **Main**: 메뉴만 있음. 스크립트는 jQuery, util, daterangepicker.
- **Summary 공통**: GNB(헤더) + LNB(사이드) + 본문(테이블, 차트). 테이블 클래스 `data_type_table`, 차트는 Google Charts + `js/googleChart.js`. Region/Country/Site는 체크박스로 선택 후 API로 반영.

### 5.4 수집된 자산 위치 (본 프로젝트)

- 스크린샷: `analysis/screenshots/*.png`
- HTML 스냅샷: `analysis/html/globaldashboard_*.html`
- API 목록: `analysis/all_apis.json`, `analysis/login_api.json`
- 메뉴별 상세: `analysis/menu_globaldashboard_*.json`
- 이미지(일부): `analysis/assets/images/`

---

## 6. 재현 구현 가이드

### 6.1 라우팅

- 로그인: `POST /login` → 성공 시 `/globaldashboard/main`으로 리다이렉트.
- 위 [1.1 라우트·경로](#11-라우트경로) 테이블대로 11개 라우트 구현 (서버 렌더 또는 SPA 라우트).

### 6.2 인증

- 로그인 성공 후 세션 쿠키 또는 토큰 유지.
- 모든 데이터 API는 동일 오리진 + 쿠키/Authorization으로 인증한다고 가정하고, 재현 환경에서도 동일하게 세션/토큰 처리.

### 6.3 공통 레이아웃

1. **Main**: 로고 + 메뉴 리스트(10개 Summary + Home 아님). 각 메뉴는 `/globaldashboard/...` 링크.
2. **Summary 공통**:
   - 상단 GNB: 제목, Region/Local/Site, Date, Daily/Weekly/Monthly/Quarterly, Update, 사용자(Change Password, Log out), Download, Last Update.
   - 좌측 LNB: Home + 10개 Summary + Manual & FAQ Download (서브 내비 [3.1](#31-함수--url-매핑) 참고).
   - 본문: 메뉴별 테이블 + 차트 영역.

### 6.4 데이터 연동

- 각 Summary 페이지 로드 시:
  1. `getCountry` → Region 체크박스/옵션 구성.
  2. `getSiteCode` → Local/Site 체크박스/옵션 구성.
  3. 해당 메뉴의 Data/Table/Graph API 호출 (from, to, site_code, switch_table 등 [2.3](#23-필터-파라미터-공통-구조) 참고).
- Update 클릭 시 동일 파라미터로 Data/Graph API 재호출.
- Download 클릭 시 `/globaldashboard/CommonExcelDownload` 또는 메뉴별 Excel API로 form 제출 또는 fetch + blob 다운로드.

### 6.5 차트

- Google Charts (Loader + corechart 등) 사용. `analysis/html` 내 script 태그 및 `js/googleChart.js` 참고.
- 각 메뉴별 `getXXXGraphData` 응답 구조에 맞춰 차트 옵션/데이터 테이블 구성.

### 6.6 자산

- 로고·아이콘·placeholder 이미지는 원본 URL 기준으로 `img/` 경로 구조 유지하거나, 재현 환경에서 `analysis/assets/images` 및 수집된 HTML 내 `img` src 목록을 참고해 동일 경로/이름으로 배치.

### 6.7 참고 파일

- 상세 API 요청 body는 `analysis/all_apis.json`의 `post_data` 필드 참고.
- 메뉴별 구조·스크립트·폼: `analysis/menu_globaldashboard_*.json`, `analysis/html/globaldashboard_*.html` 참고.

---

---

## 7. 매뉴얼 및 소스 위치

- **단계별 매뉴얼**: `docs/MANUAL_01_개요및준비사항.md` ~ `MANUAL_05_API레퍼런스.md`
- **매뉴얼 목차**: `docs/README_매뉴얼.md`
- **재현용 설정·템플릿·샘플**: `replication/` (config, templates, schemas, samples, scripts)

---

*문서 생성: ePromoter_v1.0 상세 분석 결과 기반. 수집일 기준 구조·API를 반영하였으며, 실제 서버 스펙과 차이가 있을 수 있습니다.*
