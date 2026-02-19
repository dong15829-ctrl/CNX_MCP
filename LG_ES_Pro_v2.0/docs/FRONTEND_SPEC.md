# LG ES Pro v2.0 — Frontend Specification

> LG_ES_v2.0에서 만든 프론트엔드 UI를 기준으로 작성한 사양서입니다.
> LG_ES_Pro_v2.0 프로젝트는 이 문서를 기반으로 새로 구현합니다.

---

## 1. 전체 레이아웃 구조

```
body
└── .app-layout (flex column, min-height 100vh, background #F0ECE4)
    ├── .app-top-bar (fixed, height 120px, z-index 101)
    │   ├── .gnb-logo (width 297px, LG 로고 + 링크)
    │   └── .page-header (dark theme #181c22)
    │       └── .header-inner
    │           ├── .header-row (페이지 제목 + 유틸리티)
    │           ├── hiddenFilters (Year/Month/Week/Region/Country 셀렉터)
    │           └── #summarySubRow (서브 네비게이션 + 날짜 필드)
    └── .app-body (flex, padding-left 297px, padding-top 120px)
        ├── .gnb-sidebar (fixed left, width 297px)
        │   ├── .gnb-nav (메뉴 목록)
        │   └── .gnb-user-profile (유저 프로필)
        └── .app-main
            └── .container.main-content (max-width 1440px)
                ├── #contentMonitoringItem
                ├── #contentSummary (기본 활성)
                │   ├── .summary-dashboard-layout
                │   │   ├── .summary-dashboard-left
                │   │   │   └── #summaryPanelDashboard
                │   │   └── .summary-dashboard-right (#operationalSummaryWrap)
                │   ├── #summaryTableSection
                │   ├── #rawDataModalOverlay
                │   ├── #summaryPanelPlp
                │   ├── #summaryPanelProductCategory
                │   └── #summaryPanelBlog
                ├── #contentNotice
                ├── #contentQna
                ├── #contentMonitoringDetail
                ├── #contentChecklist
                └── #contentAdminUsers
```

---

## 2. GNB 사이드바

### 2.1 메뉴 구성

| ID | 텍스트 | 동작 |
|----|--------|------|
| `gnbMonitoringItem` | Monitoring Item | 자료 업데이트 예정 플레이스홀더 |
| `gnbSummary` | Summary Dashboard | 요약 대시보드 (기본) |
| `gnbB2C` | B2C Dashboard | B2C 리포트 전환 |
| `gnbB2B` | B2B Dashboard | B2B 리포트 전환 |
| `gnbFaq` | FAQ | Notice / Q&A 섹션 |

### 2.2 스타일
- **기본**: background `#F0ECE4`, border-bottom `1px solid #CCD2D8`
- **Hover**: background `#FEEBF1`
- **Active**: background `#A50034`, color `#fff`, 좌측 6px 검정 세로선 (`::before`)
- **사이드바 / 네비게이션 구분선**: `border-top: 1px solid #CCD2D8`

### 2.3 유저 프로필 (사이드바 하단)

| 요소 | ID | 설명 |
|------|----|------|
| 아바타 | `gnbUserAvatar` | 32px 원형, 이니셜 표시 |
| 이름 | `gnbUserName` | 사용자 이름 |
| 계정 유형 | `gnbUserAccount` | "Admin" 또는 "User" |
| 로그아웃 | `btnLogoutSidebar` | 텍스트 버튼 |

---

## 3. 상단 바 (Top Bar)

### 3.1 GNB 로고 영역
- **너비**: 297px (사이드바와 동일)
- **배경**: `#F0ECE4`
- **이미지**: `assets/images/lg-logo.svg`
- **클릭**: 홈으로 이동

### 3.2 페이지 헤더
- **배경**: `#181c22` (다크 테마)
- **제목 ID**: `pageTitle`
- **기본 텍스트**: "ES Content Monitoring DashBoard"
- **유틸리티**: User Management (관리자만), Login 링크

### 3.3 서브 네비게이션 (summarySubRow)

#### subNavSummary (Summary Dashboard 선택 시)
| ID | 텍스트 |
|----|--------|
| `tabScoreByRegion` | Score by Region (기본) |
| `tabScoreByCountry` | Score by Country |

#### subNavB2C (B2C Dashboard 선택 시)
| ID | 텍스트 |
|----|--------|
| `tabB2CAll` | All (기본) |
| `tabB2CFeatureCard` | Feature Card |
| `tabB2C360` | 360 |
| `tabB2CGnbStructure` | GNB Structure |

#### subNavB2B (B2B Dashboard 선택 시)
| ID | 텍스트 |
|----|--------|
| `tabB2BAll` | All (기본) |
| `tabB2BBlog` | blog |
| `tabB2BNewContents` | New Contents |
| `tabB2BContentsError` | Contents Error |

#### subNavInfo (FAQ 선택 시)
| ID | 텍스트 |
|----|--------|
| `tabNotice` | Notice (기본) |
| `tabQna` | Q&A |

### 3.4 날짜 필드 (headerDateFields)
| ID | 라벨 | 형식 |
|----|------|------|
| `reportDate1` | Report Date | YYYY.MM.DD(Wn) |
| `lastUpdated` | last updated | YYYY.MM.DD(Wn) |

---

## 4. 필터 (숨김 상태, JS로 관리)

| 요소 | ID | 설명 |
|------|----|------|
| 연도 | `yearB2B` | select — 연도 목록 |
| 월 | `monthB2B` | select — 월 목록 (01~12) |
| 주 | `weekB2B` | select — 주 목록 (기본: All) |
| 지역 | `regionB2BWrap` / `regionB2BBtn` / `regionB2BPanel` | 멀티셀렉트 (체크박스) |
| 국가 | `countryB2BWrap` / `countryB2BBtn` / `countryB2BPanel` | 멀티셀렉트 (체크박스) |

---

## 5. Summary Dashboard

### 5.1 대시보드 레이아웃
```
.summary-dashboard-layout (flex row, gap 2rem)
├── .summary-dashboard-left (flex: 1)
│   └── #summaryPanelDashboard
│       └── #dashboardB2B
│           ├── #panelScoreByRegion
│           │   ├── 점수 요약 카드 (#scoreSummaryB2B)
│           │   ├── 차트: Average SEO & Content Items (#chartScoreByRegion)
│           │   └── 차트: Total Score by Region Last 3 Months (#chartTotalVsJul)
│           └── #panelScoreByCountry
│               ├── 지역 선택 버튼 (#countryRegionSelector)
│               ├── Country 드롭다운 (#countryFilterSelect)
│               └── 차트: Score by Country (#chartScoreByCountry)
└── .summary-dashboard-right (#operationalSummaryWrap, width 340px)
    └── Operational Summary 카드
        ├── Top Performers (#topPerformersList)
        ├── Strengths (#strengthsList)
        ├── Weaknesses (#weaknessesList)
        └── Action Plan (#actionPlanList)
```

### 5.2 점수 요약 카드 (#scoreSummaryB2B)
- **레이아웃**: CSS Grid `repeat(auto-fill, minmax(150px, 1fr))`
- **B2B 항목**: Total Score %, 1. Title, 2. Description, 3. H1, 4. Canonical Link, 5. Alt text_ Feature Cards
- **B2C 항목**: Total Score %, 1. UFN, 2. Basic Assets, 3. Spec Summary, 4. FAQ, 5~10. Tag 항목
- **1번째 카드**: 큰 폰트, `#CC3366` 색상, `#DD829F` 테두리

### 5.3 차트 (Chart.js)
| ID | 제목 | 유형 |
|----|------|------|
| `chartScoreByRegion` | Average SEO & Content Items by Region | 막대 차트 |
| `chartTotalVsJul` | Total Score by Region (Last 3 Months) | 막대 차트 (3개월 비교) |
| `chartScoreByCountry` | Score by Country | 막대 차트 (국가별) |

### 5.4 지역 선택 버튼 (#countryRegionSelector)
- 스타일: `border: 1px solid #DD829F`, `border-radius: 12px`
- Active: `background: #FEEBF1`, `border-width: 2px`, `color: #CC3366`

---

## 6. 요약 테이블 (#summaryTableSection)

### 6.1 필터/다운로드 행
| 요소 | ID | 설명 |
|------|----|------|
| 필터 드롭다운 | `tableScoreFilterB2B` | All / Bottom 30% |
| Raw data 버튼 | `btnRawData` | Raw data 모달 열기 |
| Feature Card 버튼 | `btnFeatureCard` | B2C 전용 (숨김) |
| GNB Structure 버튼 | `btnGnbStructure` | B2C 전용 (숨김) |

### 6.2 B2B 테이블 컬럼
| 키 | 라벨 | 유형 |
|----|------|------|
| `region` | REGION | 텍스트 |
| `country` | COUNTRY | 텍스트 |
| `sku_count` | SKU | 숫자 |
| `_rank` | Rank | 숫자 |
| `_rank_change` | ▲▼ | 숫자 |
| `total_score_pct` | Total Score | 숫자 |
| `title_tag_score` | 1. Title | 숫자 |
| `description_tag_score` | 2. Description | 숫자 |
| `h1_tag_score` | 3. H1 | 숫자 |
| `canonical_link_score` | 4. Canonical Link | 숫자 |
| `feature_alt_score` | 5. Alt text_ Feature Cards | 숫자 |

### 6.3 B2C 테이블 컬럼
| 키 | 라벨 (헤더) | 풀 라벨 (툴팁) |
|----|-------------|----------------|
| `region` | REGION | - |
| `country` | COUNTRY | - |
| `sku_count` | SKU | - |
| `_rank` | Rank | Rank by Total Score % |
| `_rank_change` | ▲▼ | Rank change vs. previous period |
| `total_score_pct` | Total Score | Total Score % |
| `ufn_score` | 1 | 1. UFN |
| `basic_assets_score` | 2 | 2. Basic Assets |
| `spec_summary_score` | 3 | 3. Spec Summary |
| `faq_score` | 4 | 4. FAQ |
| `title_score` | 5 | 5. Tag Title |
| `description_score` | 6 | 6. Tag Description |
| `h1_score` | 7 | 7. Tag H1 |
| `canonical_score` | 8 | 8. Tag Canonical Link |
| `alt_feature_score` | 9 | 9. Tag Alt text (Feature Cards) |
| `alt_front_score` | 10 | 10. Tag Alt text (Front Image) |

### 6.4 테이블 기능
- **정렬**: 헤더 클릭 시 오름차순/내림차순 토글
- **Rank 색상**: 상승(녹색), 하락(빨강), 동일(회색)
- **셀 클릭**: 점수 셀 클릭 시 Raw Data 모달 오픈
- **기본 정렬**: colIndex 3 (_rank), 오름차순

---

## 7. Blog 패널 (#summaryPanelBlog)

### 7.1 구조
```
#summaryPanelBlog
└── .blog-panel-card
    ├── .blog-panel-toolbar (우측 정렬)
    │   ├── Country 라벨 + #blogCountryFilter (드롭다운)
    │   └── #btnBlogDownload (Download 버튼)
    ├── #sheetBlogLoading / #sheetBlogError
    └── #sheetBlogWrap
        └── .blog-sheet-table
            ├── thead > #sheetBlogHead
            └── tbody > #sheetBlogBody
```

### 7.2 테이블 스타일
- **헤더**: `background: #4B5563`, `color: #fff`
- **URL 컬럼**: 클릭 가능한 링크 (새 탭)
- **Region 컬럼**: rowspan 병합

### 7.3 Blog 탭 동작 (B2B Dashboard > blog)
- `summary-dashboard-layout` 및 `summaryTableSection` 숨김
- `summaryPanelBlog`만 표시
- API: `GET /api/sheet?sheet=Blog&month={month}`
- Country 필터: 데이터 로드 후 자동 생성
- Download: TSV 파일로 내보내기

---

## 8. 모달

### 8.1 Raw Data 모달 (#rawDataModalOverlay)
- **제목**: "Raw data: {region} / {country}"
- **API**: `GET /api/raw?report_type={type}&region={region}&country={country}&limit=500`
- **URL 셀**: 클릭 가능 링크
- **닫기**: `rawDataModalClose`

### 8.2 공지 작성 모달 (#noticeWriteModalOverlay)
- **필드**: 제목 (`noticeWriteTitle`), 내용 (`noticeWriteBody`)
- **버튼**: Cancel, Submit

### 8.3 비밀번호 변경 모달 (#pwChangeModal)
- **필드**: 새 비밀번호 (최소 6자)
- **버튼**: Cancel, Update

---

## 9. Notice / Q&A

### 9.1 공지사항 (#contentNotice)
- **목록**: No., Title, Date 컬럼
- **상세**: 제목, 날짜, 본문, Back/Delete 버튼
- **작성**: 관리자만 (New Notice 버튼)

### 9.2 Q&A (#contentQna)
- **작성**: 이름, 이메일, 제목, 내용
- **목록**: No., Subject, Author, Date, Reply 컬럼

---

## 10. Admin 관리

### 10.1 사용자 관리 (#adminPanelUsers)
- 사용자 추가: 이메일, 비밀번호, 역할
- 필터: 역할(All/Admin/User), 상태(All/Active/Pending)
- 테이블: Email, Role, Status, Joined, Actions
- Actions: 역할 변경, 활성화/비활성화, 비밀번호 변경, 삭제

### 10.2 사용 현황 (#adminPanelUsageLogs)
- Per-user usage, Pipeline status, Download history, Activity log

---

## 11. 디자인 토큰 (CSS Variables)

```css
/* 메인 색상 */
--lg-accent: #A50034;        /* LG 레드 */
--lg-accent-hover: #BE0D3E;
--lg-border: #CCD2D8;

/* 배경 */
--bg: #F0ECE4;               /* 메인 배경 (베이지) */
--bg-elevated: #FFFFFF;
--card: #FFFFFF;

/* 텍스트 */
--text: var(--gray-900);     /* #212121 */
--text-secondary: var(--gray-700); /* #616161 */

/* GNB Active */
background: #A50034;
color: #fff;
left-border: 6px solid #000;

/* Score 카드 Primary */
color: #CC3366;
border: 2px solid #DD829F;

/* Region 선택 버튼 */
active-background: #FEEBF1;
border: #DD829F;
color: #CC3366;

/* 상단 바 (다크) */
background: #181c22;
text: #f0f2f5;
text-secondary: #9ca3af;
```

---

## 12. 외부 라이브러리

| 라이브러리 | 버전 | CDN | 용도 |
|-----------|------|-----|------|
| Chart.js | latest | jsdelivr | 차트 렌더링 |
| chartjs-plugin-datalabels | 2.x | jsdelivr | 차트 데이터 라벨 |
| jsPDF | 2.x | jsdelivr | PDF 생성 |
| html2canvas | 1.x | jsdelivr | HTML → Canvas 변환 |
| XLSX | 0.18.5 | jsdelivr | Excel 생성 (fallback) |
| ExcelJS | 4.4.0 | cdnjs | Excel 생성 (primary) |
| Inter Font | 400-700 | Google Fonts | UI 폰트 |

---

## 13. API 엔드포인트 (프론트엔드에서 사용)

| 메서드 | 엔드포인트 | 용도 |
|--------|-----------|------|
| GET | `/auth/me` | 현재 사용자 정보 |
| POST | `/auth/logout` | 로그아웃 |
| GET | `/api/reports` | 사용 가능 리포트 목록 |
| GET | `/api/filters` | 필터 옵션 (지역/국가) |
| GET | `/api/summary` | 요약 데이터 |
| GET | `/api/stats` | 통계 데이터 |
| GET | `/api/raw` | Raw 데이터 (모달용) |
| GET | `/api/raw/download` | Raw 데이터 CSV 다운로드 |
| GET | `/api/sheet` | 시트 데이터 (Blog 등) |
| GET | `/api/checklist` | 체크리스트 데이터 |
| GET | `/api/admin/users` | 사용자 목록 (관리자) |
| POST | `/api/admin/users` | 사용자 추가 (관리자) |
| PATCH | `/api/admin/users/{id}` | 사용자 수정 (관리자) |
| DELETE | `/api/admin/users/{id}` | 사용자 삭제 (관리자) |
| GET | `/api/admin/usage` | 사용 현황 (관리자) |
| GET | `/api/admin/pipeline-status` | 파이프라인 상태 (관리자) |
| GET | `/api/admin/download-log` | 다운로드 로그 (관리자) |
| GET | `/api/admin/activity-log` | 활동 로그 (관리자) |
| POST | `/api/admin/log-download` | 다운로드 로깅 |

---

## 14. 주요 JS 함수

### 네비게이션
- `showLv1Summary()` — Summary Dashboard 표시
- `showLv1B2C()` — B2C Dashboard 전환
- `showLv1B2B()` — B2B Dashboard 전환
- `showLv1Info(activeInfoSub)` — FAQ(Notice/Q&A) 표시
- `switchB2BSubTab(tabId)` — B2B 서브탭 전환 (All/Blog/New Contents/Contents Error)
- `updateGnbActive(gnbId)` — GNB 활성 메뉴 업데이트

### 데이터 로드
- `loadDashboard(reportType, month, regions, countries)` — 메인 데이터 로드
- `loadSheetSection(month, cfg)` — 시트 데이터 로드 (Blog/PLP/Product Category)
- `loadSummarySheets(month)` — 모든 시트 로드

### 렌더링
- `renderChartScoreByRegion(rows)` — 지역별 점수 차트
- `renderChartTotalVsJul(monthsWithRows)` — 3개월 비교 차트
- `renderChartScoreByCountry()` — 국가별 점수 차트
- `renderScoreSummaryB2B(rows)` — 점수 요약 카드
- `renderOperationalSummary(rows, reportType)` — Operational Summary
- `renderTableB2B(rows)` — 요약 테이블 렌더링

### 상태 관리
- `currentReportType` — 'B2B' | 'B2C'
- `lastSummary` — 캐시된 요약 데이터
- `summaryTableSort` — `{colIndex, dir}` 테이블 정렬 상태

---

## 15. 반응형 디자인

| 브레이크포인트 | 변경 사항 |
|---------------|----------|
| < 1100px | `summary-dashboard-layout` → column 방향 전환 |
| < 768px | 차트 높이 280px, 점수 카드 그리드 조정 |
