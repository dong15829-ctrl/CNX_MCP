# 매뉴얼 03: 레이아웃 및 공통 UI

## 1. 페이지 유형

### 1.1 메인(인덱스) 페이지 (`/globaldashboard/main`)

- **역할**: 로고 + 10개 Summary 메뉴만 표시. 클릭 시 해당 Summary 페이지로 이동.
- **레이아웃**: `.body_wrap` > `.index_wrap` > `.index_tit`(로고) + `ul.index_menu_wrap`.

### 1.2 Summary 페이지 (Executive, Division, … Performance)

- **공통 구조**: **GNB(상단)** + **LNB(좌측)** + **본문(콘텐츠)**.
- **GNB**: 햄버거, 페이지 제목, Region/Local/Site, Date, Daily/Weekly/Monthly/Quarterly, Update, 사용자(Change Password / Log out), Download, Last Update.
- **LNB**: Home + 10개 Summary 메뉴 링크 + Manual & FAQ Download.

## 2. 메인(인덱스) 메뉴 마크업

- 각 메뉴: `li.index_menu` > `a[href="/globaldashboard/..."]` > `.icon_wrap` > `.icon_area.{img01|img02|...}` + `.index_txt`(메뉴명, `<br>` 가능).
- 아이콘 클래스와 경로는 `replication/config/menu_config.json` 참고.
- 실제 HTML 템플릿: `replication/templates/main_index.html`.

## 3. GNB (상단 헤더) 구조

| 영역 | 선택자 / 요소 | 설명 |
|------|----------------|------|
| 햄버거 | `button.gnb_hbg` | LNB 열기/닫기 |
| 제목 | `.gnb_tit` | 페이지 제목 (예: Executive Summary) |
| Region/Local/Site | `.gnb_option_wrap` 내 `#region`, `#country`, `#site` | 선택 값 표시 (All / 개수 등) |
| 필터 패널 | `.region_wrap` | Region/Country/Site 체크박스 목록 (display:none으로 숨김 후 토글) |
| Update | `button.gnb_btn_update`, `onclick="getUpdate()"` | 데이터 재요청 |
| Date | `input#date`, `name="daterange"` | daterangepicker 연동 |
| Daily/Weekly/Monthly/Quarterly | `td.data_type[data-period="day|week|month|quarter"]` | 기간 타입 선택 |
| 사용자 | `.gnb_user_wrap` | `.user_name`, Change Password, Log out |
| Download | `button#headerDownload` | CommonExcelDownload form 제출 |
| Last Update | `.last_update span` | 마지막 업데이트 날짜 텍스트 |

## 4. LNB (좌측 서브 내비) 구조

- **래퍼**: `.lnb_wrap`, `.lnb_close`(닫기), `.lnb_logo`(로고).
- **메뉴**: `ul.lnb_menu` > `li` > `a[href="javascript:moveXXX()"]`.
  - Home: `moveMain()`
  - Executive Summary: `moveExecutive()` … Performance Summary: `movePerformanceSummary()`
  - Manual & FAQ Download: `fileDown()`
- 현재 페이지 표시: 해당 `li`에 `class="menu_li active"`.

## 5. 공통 필터 파라미터 (getParam 등)

대부분의 데이터 API에서 사용하는 공통 필드:

- `title`: 페이지 제목 (예: "Executive Summary")
- `from`, `to`: 날짜 (YYYY-MM-DD 또는 "Jan 2026" 등)
- `period`: "custom" 등
- `site_code`: 선택된 사이트 코드, 쉼표 구분 (예: "AE,AU,BR,...")
- `period_date`: 주 단위 등 (빈 문자열 또는 "28")
- `switch_table`: `{ "chat": 1, "sales14": 2, "sales": 1 }`

Region/Country/Site 체크박스 선택 결과를 위 필드로 조합해 각 API에 전달합니다.

## 6. 공통 기능 동작

| 기능 | 동작 |
|------|------|
| **Update** | `getUpdate()` 호출 → 현재 페이지의 Data/Graph API를 현재 필터로 재요청 후 화면 갱신 |
| **Change Password** | 현재/새/재입력 비밀번호를 `POST /changePassword`로 전송 (MD5 등 사용 가능) |
| **Log out** | 로그아웃 처리 후 로그인 페이지로 이동 |
| **Download** | `getParam()`으로 폼 파라미터 구성 후 form method=POST, action=`/globaldashboard/CommonExcelDownload` 제출. 파일 다운로드 시 쿠키 기반으로 처리 |

## 7. 템플릿/소스 위치

- `replication/templates/main_index.html` — 메인 페이지 메뉴
- `replication/templates/gnb_snippet.html` — GNB 영역 참고용 조각
- `replication/templates/lnb_snippet.html` — LNB 메뉴 조각
- `replication/templates/login_form.html` — 로그인 폼
