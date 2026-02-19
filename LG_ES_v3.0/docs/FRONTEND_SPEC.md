# LG ES v3.0 — 프론트엔드 UI/UX 설계서

> **문서 버전**: 1.0  
> **최종 수정**: 2026-02-11  
> **상태**: 설계 완료 → 구현 대기

---

## 1. 디자인 시스템

### 1.1 디자인 토큰 (CSS Custom Properties)

```css
:root {
  /* ── Gray Scale ── */
  --gray-50:  #FAFAFA;
  --gray-100: #F5F5F5;
  --gray-200: #EEEEEE;
  --gray-300: #E0E0E0;
  --gray-400: #BDBDBD;
  --gray-500: #9E9E9E;
  --gray-600: #757575;
  --gray-700: #616161;
  --gray-800: #424242;
  --gray-900: #212121;

  /* ── Brand Colors ── */
  --lg-red:        #C41E3A;    /* LG 브랜드 레드 (Primary) */
  --lg-red-hover:  #A01830;    /* 호버 상태 */
  --lg-red-muted:  rgba(196, 30, 58, 0.10);  /* 배경용 */

  /* ── Semantic Colors ── */
  --green:         #16a34a;
  --green-muted:   rgba(22, 163, 74, 0.10);
  --blue:          #2563eb;
  --blue-muted:    rgba(37, 99, 235, 0.10);
  --orange:        #ea580c;
  --orange-muted:  rgba(234, 88, 12, 0.10);
  --red-danger:    #c70805;

  /* ── Layout ── */
  --bg:            var(--gray-50);
  --card:          #FFFFFF;
  --border:        var(--gray-300);
  --text:          var(--gray-900);
  --text-secondary: var(--gray-600);

  /* ── Header (Dark Theme) ── */
  --header-bg:     #181c22;
  --header-text:   #f0f2f5;
  --header-muted:  #9ca3af;
  --header-border: rgba(255, 255, 255, 0.08);
  --header-input-bg: #1e2329;
  --header-input-border: rgba(255, 255, 255, 0.12);

  /* ── Spacing ── */
  --radius:    8px;
  --radius-sm: 6px;

  /* ── Shadows ── */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow:    0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.12);

  /* ── Transitions ── */
  --transition: 150ms ease;

  /* ── Typography ── */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-size-xs:  0.75rem;    /* 12px */
  --font-size-sm:  0.8125rem;  /* 13px */
  --font-size-base: 0.875rem;  /* 14px */
  --font-size-md:  1rem;       /* 16px */
  --font-size-lg:  1.1rem;     /* 17.6px */
  --font-size-xl:  1.2rem;     /* 19.2px */
}
```

### 1.2 타이포그래피

| 용도 | 크기 | 굵기 | 색상 |
|------|------|------|------|
| 페이지 제목 | `--font-size-xl` | 700 | `--header-text` |
| 카드 제목 | `--font-size-md` | 600 | `--text` |
| 카드 부제목 | `--font-size-base` | 600 | `--text-secondary` |
| 본문 | `--font-size-base` | 400 | `--text` |
| 테이블 헤더 | `--font-size-sm` | 600 | `--text` |
| 테이블 셀 | `--font-size-sm` | 400 | `--text` |
| 필터 라벨 | `--font-size-sm` | 600 | `--header-muted` |
| 점수 카드 라벨 | `--font-size-xs` | 600 | `--text-secondary` |
| 점수 카드 값 | `--font-size-lg` | 700 | (semantic color) |

### 1.3 Region별 차트 색상

| Region | 색상 | Hex |
|--------|------|-----|
| NA | 파란색 | `#2563eb` |
| EU | 녹색 | `#16a34a` |
| ASIA | 주황색 | `#ea580c` |
| LATAM | 보라색 | `#8b5cf6` |
| MEA | 분홍색 | `#ec4899` |

---

## 2. 페이지 구조

### 2.1 로그인 페이지 (`login.html`)

```
┌───────────────────────────────────────────────┐
│                                               │
│           ┌─────────────────────┐             │
│           │   [LG Logo]         │             │
│           │                     │             │
│           │   ES Contents       │             │
│           │   Monitoring        │             │
│           │                     │             │
│           │   ┌───────────────┐ │             │
│           │   │ Email         │ │             │
│           │   └───────────────┘ │             │
│           │   ┌───────────────┐ │             │
│           │   │ Password      │ │             │
│           │   └───────────────┘ │             │
│           │                     │             │
│           │   [   Login    ]    │             │
│           │                     │             │
│           │   Don't have an     │             │
│           │   account? Register │             │
│           └─────────────────────┘             │
│                                               │
└───────────────────────────────────────────────┘
```

**기능**:
- 이메일/비밀번호 로그인
- 회원가입 (관리자 승인 후 사용 가능)
- 에러 메시지 표시 (Toast)
- 로그인 성공 시 `index.html`로 리다이렉트

---

### 2.2 메인 대시보드 (`index.html`)

#### 2.2.1 헤더 영역 (Sticky, Dark Theme)

```
┌──────────────────────────────────────────────────────────────┐
│  Row 1: [LG|ES Logo] ES Contents Monitoring     [⬇ Download]│
│                                                   [👤 User ▼]│
├──────────────────────────────────────────────────────────────┤
│  Row 2: [Dashboard] [Summary Table] [Monitoring Detail]      │
│         [Checklist & Criteria]           [Year ▼] [Month ▼] │
├──────────────────────────────────────────────────────────────┤
│  Row 3: [B2B] [B2C]              [Region ▼] [Country ▼]     │
└──────────────────────────────────────────────────────────────┘
```

**Row 1 구성**:
| 요소 | 위치 | 설명 |
|------|------|------|
| LG 로고 + 타이틀 | 좌측 | SVG 로고 + "ES Contents Monitoring" |
| Download 버튼 | 우측 | 드롭다운: Summary CSV, RAW CSV |
| User 메뉴 | 우측 | 사용자명 표시, 클릭 시 드롭다운 (로그아웃, 관리자 메뉴) |

**Row 2 구성**:
| 요소 | 위치 | 설명 |
|------|------|------|
| 메인 네비게이션 | 좌측 | 4개 탭 (활성 탭 하단에 LG Red 라인) |
| Year/Month 필터 | 우측 | `<select>` 드롭다운 |

**Row 3 구성**:
| 요소 | 위치 | 설명 |
|------|------|------|
| B2B/B2C 서브 탭 | 좌측 | 2개 탭 |
| Region/Country 필터 | 우측 | MultiSelect 컴포넌트 |

---

#### 2.2.2 Dashboard 섹션

```
┌─────────────────────────────────────────────────────────┐
│  Average Total Score by Region (B2B)                    │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │ Overall  │ │ Total    │ │ NA   │ │ EU   │ │ ASIA │ │
│  │ Average  │ │ SKUs     │ │      │ │      │ │      │ │
│  │ 87.5%    │ │ 3,150    │ │86.5% │ │89.1% │ │93.2% │ │
│  │ (primary)│ │ (blue)   │ │      │ │      │ │(green│ │
│  └──────────┘ └──────────┘ └──────┘ └──────┘ └──────┘ │
│                                                         │
│  ┌─────────────────────────┐ ┌─────────────────────────┐│
│  │ Average SEO & Content   │ │ Total Score Trend (2025)││
│  │ Items by Region         │ │                         ││
│  │                         │ │    ASIA ──●──●──●       ││
│  │  ████ ████ ████ ████    │ │    EU   ──●──●──●       ││
│  │  ████ ████ ████ ████    │ │    NA   ──●──●──●       ││
│  │  NA   EU  ASIA  ...    │ │                         ││
│  │  [Grouped Bar Chart]    │ │    [Line Chart]         ││
│  └─────────────────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

**Score Cards**:
- `score-grid`: CSS Grid, `auto-fill`, `minmax(150px, 1fr)`
- 첫 번째: Overall Average (LG Red 테두리, 빨간 배경)
- 두 번째: Total SKUs (파란 테두리)
- 나머지: Region별 평균 (≥90% 시 녹색 테두리)

**Bar Chart** (왼쪽):
- Chart.js Grouped Bar
- X축: Region
- Y축: 점수 (0 ~ max_score + 2)
- 데이터셋: 각 스코어 항목 (B2B: 5개, B2C: 10개)
- 색상: HSL 균등 분배

**Trend Chart** (오른쪽):
- Chart.js Line
- X축: 월 (YYYY-MM 형식)
- Y축: Total Score % (50 ~ 100%)
- 시리즈: Region별 라인 (Region 색상)
- Fill: 반투명 영역

---

#### 2.2.3 Summary Table 섹션

```
┌─────────────────────────────────────────────────────────┐
│  B2B Monitoring Report by Country                       │
│                               [Total Score: All ▼]      │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Region│Country│SKU │Title│Desc │H1  │Canon│F.Alt│Tot ││
│  │       │       │    │(20) │(20) │(15)│(15) │(15) │ % ││
│  ├───────┼───────┼────┼─────┼─────┼────┼─────┼─────┼───┤│
│  │ ASIA  │ KR    │340 │20.0 │19.2 │15.0│15.0 │14.8 │98%││  ← 녹색
│  │ EU    │ DE    │225 │19.5 │18.5 │14.8│15.0 │14.0 │96%││  ← 녹색
│  │ NA    │ US    │260 │19.0 │17.8 │14.5│15.0 │13.2 │93%││  ← 녹색
│  │ LATAM │ BR    │155 │17.5 │16.5 │13.2│13.8 │11.5 │85%││  ← 주황
│  │ MEA   │ SA    │120 │16.8 │16.0 │12.8│13.5 │11.2 │82%││  ← 주황
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  * 정렬: 헤더 클릭 (▲ 오름차순, ▼ 내림차순)               │
│  * 필터: Top 30% / Bottom 30% / All                     │
│  * 컬러: Total Score ≥90% 녹색, ≥70% 주황, <70% 빨강     │
└─────────────────────────────────────────────────────────┘
```

**테이블 기능**:
| 기능 | 설명 |
|------|------|
| 정렬 | 모든 컬럼 헤더 클릭으로 정렬 (asc ↔ desc 토글) |
| Score 필터 | Top 30% / Bottom 30% 드롭다운 |
| 컬러 코딩 | Total Score % 셀 색상 변경 |
| 스크롤 | 헤더 고정, 바디 세로 스크롤 (`max-height: calc(100vh - 280px)`) |
| 숫자 포맷 | 점수: 소수 1자리, SKU: 콤마 구분 |
| 빈 데이터 | "No data found." 빈 상태 메시지 |

---

#### 2.2.4 Monitoring Detail 섹션

```
┌─────────────────────────────────────────────────────────┐
│  Monitoring Detail                                      │
│  SEO & Content quality monitoring criteria and examples │
│                                                         │
│  ▎ B2B SEO Monitoring Items                             │
│  ┌──────────────────────┐ ┌──────────────────────┐      │
│  │ 1. Title Tag         │ │ 4. Canonical Link    │      │
│  │ (설명 텍스트)         │ │ (설명 텍스트)         │      │
│  │ 2. Description Tag   │ │ 5. Feature Alt Text  │      │
│  │ (설명 텍스트)         │ │ (설명 텍스트)         │      │
│  │ 3. H1 Tag            │ └──────────────────────┘      │
│  │ (설명 텍스트)         │                               │
│  └──────────────────────┘                               │
│                                                         │
│  ▎ B2C Additional Monitoring Items                      │
│  ┌──────────────────────┐ ┌──────────────────────┐      │
│  │ UFN                  │ │ FAQ                  │      │
│  │ Basic Assets         │ │ Alt Feature/Front    │      │
│  │ Spec Summary         │ └──────────────────────┘      │
│  └──────────────────────┘                               │
└─────────────────────────────────────────────────────────┘
```

**레이아웃**: `detail-grid` — CSS Grid, `auto-fill`, `minmax(300px, 1fr)`

---

#### 2.2.5 Checklist & Criteria 섹션

```
┌─────────────────────────────────────────────────────────┐
│  B2B Scoring Criteria (Total: 85 points)                │
│  ┌────┬────────────────┬────────────────────┬──────────┐│
│  │ No │ Item           │ Description        │Max Score ││
│  ├────┼────────────────┼────────────────────┼──────────┤│
│  │ 1  │ Title Tag      │ (상세 설명)         │    20    ││
│  │ 2  │ Description    │ (상세 설명)         │    20    ││
│  │ 3  │ H1 Tag         │ (상세 설명)         │    15    ││
│  │ 4  │ Canonical Link │ (상세 설명)         │    15    ││
│  │ 5  │ Feature Alt    │ (상세 설명)         │    15    ││
│  └────┴────────────────┴────────────────────┴──────────┘│
│                                                         │
│  B2C Scoring Criteria (Total: 100 points)               │
│  ┌────┬────────────────┬────────────────────┬──────────┐│
│  │ No │ Item           │ Description        │Max Score ││
│  ├────┼────────────────┼────────────────────┼──────────┤│
│  │ 1  │ UFN            │ (상세 설명)         │    10    ││
│  │... │ ...            │ ...                │   ...    ││
│  │ 10 │ Alt Front      │ (상세 설명)         │    10    ││
│  └────┴────────────────┴────────────────────┴──────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## 3. 컴포넌트 상세 설계

### 3.1 Header (`components/Header.js`)

```javascript
// 책임: 헤더 렌더링, 네비게이션 이벤트, 필터 이벤트 바인딩
export class Header {
  constructor(containerEl) { ... }

  render(state) {
    // Row 1: 로고, 다운로드, 사용자 메뉴
    // Row 2: 메인 네비게이션 탭, Year/Month 필터
    // Row 3: B2B/B2C 탭, Region/Country MultiSelect
  }

  // 이벤트
  onNavChange(callback)       // 탭 변경 시
  onTypeChange(callback)      // B2B/B2C 변경 시
  onYearChange(callback)      // Year 변경 시
  onMonthChange(callback)     // Month 변경 시
  onRegionChange(callback)    // Region 필터 변경 시
  onCountryChange(callback)   // Country 필터 변경 시
  onDownload(callback)        // 다운로드 클릭 시
  onLogout(callback)          // 로그아웃 클릭 시

  updateFilters(filters)      // Region/Country 옵션 업데이트
  updateMonths(months)        // Month 옵션 업데이트
}
```

### 3.2 ScoreCards (`components/ScoreCards.js`)

```javascript
// 책임: 점수 카드 그리드 렌더링
export class ScoreCards {
  constructor(containerEl) { ... }

  render(data, config) {
    // data: summaryData (전체 행)
    // config: { type, scoreColumns, totalMax }
    //
    // 렌더링:
    // 1. Overall Average (primary 스타일)
    // 2. Total SKUs (blue 스타일)
    // 3. Region별 평균 (≥90%: green 스타일)
  }
}
```

### 3.3 BarChart (`components/BarChart.js`)

```javascript
// 책임: Region별 스코어 항목 Grouped Bar Chart
export class BarChart {
  constructor(canvasEl) { ... }

  render(data, config) {
    // data: summaryData (현재 월)
    // config: { scoreColumns, scoreLabels, maxScores }
    //
    // 로직:
    // 1. Region별 그룹핑
    // 2. 각 Region에서 scoreColumn별 평균 계산
    // 3. Chart.js Grouped Bar 렌더링
  }

  destroy() { ... }  // 차트 인스턴스 파괴 (재렌더링 전)
}
```

### 3.4 TrendChart (`components/TrendChart.js`)

```javascript
// 책임: 월별 Total Score 트렌드 라인 차트
export class TrendChart {
  constructor(canvasEl) { ... }

  render(trendData) {
    // trendData: { labels: ['2025-01', ...], series: [{ region, data: [...] }] }
    //
    // 로직:
    // 1. 각 Region을 시리즈로 생성
    // 2. Region 색상 적용
    // 3. Chart.js Line 렌더링 (fill, tension, pointRadius)
  }

  destroy() { ... }
}
```

### 3.5 DataTable (`components/DataTable.js`)

```javascript
// 책임: 정렬·필터 가능한 범용 데이터 테이블
export class DataTable {
  constructor(containerEl) { ... }

  render(data, config) {
    // data: summaryData (현재 필터링된 행)
    // config: {
    //   columns: ['region', 'country', ...],
    //   labels: ['Region', 'Country', ...],
    //   scoreColumns: [...],
    //   sortCol, sortDir,
    //   scoreFilter  // 'top30' | 'bottom30' | ''
    // }
    //
    // 렌더링:
    // 1. <thead> 생성 (정렬 화살표 포함)
    // 2. Score Filter 적용
    // 3. 정렬 적용
    // 4. <tbody> 생성 (컬러 코딩 포함)
  }

  onSort(callback)          // 정렬 헤더 클릭 시
  onScoreFilter(callback)   // Score Filter 변경 시
}
```

### 3.6 MultiSelect (`components/MultiSelect.js`)

```javascript
// 책임: 다중 선택 드롭다운 (Region, Country)
export class MultiSelect {
  constructor(wrapEl, options = {}) {
    // options: { label, items, onChange }
  }

  render(items, selectedItems) {
    // items: ['ASIA', 'EU', 'NA', ...]
    // selectedItems: [] (빈 = 전체)
    //
    // 렌더링:
    // 1. 버튼 (All / N selected / 선택된 항목명)
    // 2. 드롭다운 패널 (체크박스 목록)
    // 3. Select All / Deselect All 버튼
  }

  getSelected()             // 현재 선택된 항목 반환
  setItems(items)           // 항목 목록 갱신
  onChange(callback)        // 선택 변경 시 콜백
  close()                  // 드롭다운 닫기
}
```

### 3.7 Toast (`components/Toast.js`)

```javascript
// 책임: 알림 토스트 메시지
export class Toast {
  static show(message, type = 'info', duration = 3000) {
    // type: 'info' | 'success' | 'warning' | 'error'
    //
    // 동작:
    // 1. 토스트 요소 생성 (우측 상단)
    // 2. 슬라이드 인 애니메이션
    // 3. duration 후 자동 제거
    // 4. 닫기 버튼
  }
}
```

---

## 4. 상태 관리 (`js/state.js`)

### 4.1 상태 구조

```javascript
const initialState = {
  // 인증
  user: null,
  isAuthenticated: false,

  // 필터
  type: 'b2b',
  year: null,          // API에서 가져온 최신 연도
  month: null,         // API에서 가져온 최신 월
  selectedRegions: [],
  selectedCountries: [],

  // 네비게이션
  section: 'dashboard',

  // 데이터 (API 응답 캐시)
  reports: [],
  filters: { regions: [], countries: {}, divisions: [] },
  summaryData: [],
  trendData: { labels: [], series: [] },
  statsData: {},

  // 테이블 상태
  sortCol: null,
  sortDir: 'asc',
  scoreFilter: '',

  // UI
  loading: false,
  error: null,
};
```

### 4.2 상태 변경 패턴

```javascript
// Pub/Sub 패턴
class StateManager {
  constructor(initialState) {
    this._state = { ...initialState };
    this._listeners = new Map();  // key → Set<callback>
  }

  get(key) { return this._state[key]; }

  set(updates) {
    const changed = [];
    for (const [key, value] of Object.entries(updates)) {
      if (this._state[key] !== value) {
        this._state[key] = value;
        changed.push(key);
      }
    }
    // 변경된 키에 등록된 리스너만 호출
    changed.forEach(key => {
      (this._listeners.get(key) || []).forEach(cb => cb(this._state[key], this._state));
    });
  }

  subscribe(key, callback) {
    if (!this._listeners.has(key)) this._listeners.set(key, new Set());
    this._listeners.get(key).add(callback);
    return () => this._listeners.get(key).delete(callback);  // unsubscribe
  }

  getAll() { return { ...this._state }; }
}

export const state = new StateManager(initialState);
```

### 4.3 상태 변경 → UI 업데이트 매핑

| 상태 변경 | 트리거되는 UI 업데이트 |
|-----------|---------------------|
| `type` | Filters 재로드 → 전체 데이터 재로드 → 전체 UI 재렌더링 |
| `year` | Month 옵션 갱신 → Filters 재로드 → 데이터 재로드 |
| `month` | Filters 재로드 → 데이터 재로드 |
| `selectedRegions` | Country 필터 연동 → 데이터 재로드 |
| `selectedCountries` | 데이터 재로드 |
| `section` | 해당 섹션 표시/숨김 전환 |
| `summaryData` | ScoreCards, BarChart, DataTable 재렌더링 |
| `trendData` | TrendChart 재렌더링 |
| `sortCol` / `sortDir` | DataTable 재렌더링 |
| `scoreFilter` | DataTable 재렌더링 |
| `loading` | 로딩 인디케이터 표시/숨김 |
| `error` | Toast 에러 메시지 표시 |

---

## 5. API 클라이언트 (`js/api.js`)

### 5.1 구현 설계

```javascript
const API_BASE = '';  // 동일 오리진 (FastAPI가 정적 파일 서빙)

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      credentials: 'include',  // 쿠키 전송
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });

    if (response.status === 401) {
      // 토큰 만료 → refresh 시도
      const refreshed = await this.refreshToken();
      if (refreshed) return this.request(endpoint, options);  // 재시도
      window.location.href = '/login';
      throw new Error('AUTH_EXPIRED');
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new ApiError(err.code || 'UNKNOWN', err.message || response.statusText);
    }

    return response.json();
  }

  // 인증
  async login(email, password) { ... }
  async logout() { ... }
  async refreshToken() { ... }
  async getMe() { ... }

  // 데이터
  async getReports() { ... }
  async getFilters(reportType, year, month) { ... }
  async getSummary(reportType, year, month, regions, countries) { ... }
  async getStats(reportType, year, month, regions, countries) { ... }
  async getTrend(reportType, year, by, months, regions) { ... }

  // 다운로드
  async downloadSummary(reportType, year, month, format) { ... }
  async downloadRaw(reportType, format) { ... }
}

export const api = new ApiClient();
```

### 5.2 에러 처리

```javascript
class ApiError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

// 사용 예시
try {
  const data = await api.getSummary('B2B', 2025, 3);
  state.set({ summaryData: data.data, loading: false });
} catch (err) {
  state.set({ error: err.message, loading: false });
  Toast.show(err.message, 'error');
}
```

---

## 6. 라우터 (`js/router.js`)

### 6.1 해시 기반 라우팅

```javascript
// URL 해시 → 섹션 매핑
const ROUTES = {
  '#dashboard':  'dashboard',
  '#summary':    'summary',
  '#detail':     'detail',
  '#checklist':  'checklist',
  '#admin':      'admin',
};

class Router {
  constructor() {
    window.addEventListener('hashchange', () => this.route());
  }

  route() {
    const hash = window.location.hash || '#dashboard';
    const section = ROUTES[hash] || 'dashboard';
    state.set({ section });
  }

  navigate(section) {
    window.location.hash = `#${section}`;
  }

  init() {
    this.route();
  }
}

export const router = new Router();
```

---

## 7. 유틸리티

### 7.1 `utils/format.js`

```javascript
// 숫자 포맷
export function fmtScore(value, decimals = 1) {
  if (value == null || value === '') return '—';
  return Number(value).toFixed(decimals);
}

export function fmtPct(value, decimals = 1) {
  if (value == null) return '—';
  return Number(value).toFixed(decimals) + '%';
}

export function fmtInt(value) {
  if (value == null) return '—';
  return Number(value).toLocaleString();
}

// 점수 색상
export function scoreColor(pct) {
  if (pct >= 90) return 'var(--green)';
  if (pct >= 70) return 'var(--orange)';
  return 'var(--red-danger)';
}

// 평균 계산
export function avg(arr, key) {
  if (!arr.length) return 0;
  return arr.reduce((sum, row) => sum + (row[key] || 0), 0) / arr.length;
}

// 그룹핑
export function groupBy(arr, key) {
  const map = {};
  arr.forEach(row => {
    (map[row[key]] = map[row[key]] || []).push(row);
  });
  return map;
}
```

### 7.2 `utils/csv.js`

```javascript
export function downloadCSV(data, columns, labels, filename) {
  const headers = labels.map(l => l.replace(/\n/g, ' '));
  const rows = data.map(row => columns.map(col => row[col]));
  const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
```

### 7.3 `utils/constants.js`

```javascript
// B2B 설정
export const B2B_CONFIG = {
  columns: ['region','country','sku_count','title_tag_score','description_tag_score',
            'h1_tag_score','canonical_link_score','feature_alt_score','total_score_pct'],
  labels: ['Region','Country','SKU','1. Title\n(20)','2. Description\n(20)',
           '3. H1\n(15)','4. Canonical\n(15)','5. Feature Alt\n(15)','Total Score %'],
  scoreColumns: ['title_tag_score','description_tag_score','h1_tag_score',
                 'canonical_link_score','feature_alt_score'],
  scoreLabels: ['Title','Description','H1','Canonical','Feature Alt'],
  maxScores: [20, 20, 15, 15, 15],
  totalMax: 85,
};

// B2C 설정
export const B2C_CONFIG = {
  columns: ['region','country','division','sku_count','ufn_score','basic_assets_score',
            'spec_summary_score','faq_score','title_score','description_score',
            'h1_score','canonical_score','alt_feature_score','alt_front_score','total_score_pct'],
  labels: ['Region','Country','Division','SKU','UFN\n(10)','Basic\nAssets\n(10)',
           'Spec\nSummary\n(10)','FAQ\n(10)','Title\n(10)','Description\n(10)',
           'H1\n(10)','Canonical\n(10)','Alt\nFeature\n(10)','Alt\nFront\n(10)','Total\nScore %'],
  scoreColumns: ['ufn_score','basic_assets_score','spec_summary_score','faq_score',
                 'title_score','description_score','h1_score','canonical_score',
                 'alt_feature_score','alt_front_score'],
  scoreLabels: ['UFN','Basic Assets','Spec Summary','FAQ','Title','Description',
                'H1','Canonical','Alt Feature','Alt Front'],
  maxScores: [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
  totalMax: 100,
};

// Region 색상
export const REGION_COLORS = {
  NA: '#2563eb',
  EU: '#16a34a',
  ASIA: '#ea580c',
  LATAM: '#8b5cf6',
  MEA: '#ec4899',
};
```

---

## 8. 반응형 디자인

### 8.1 브레이크포인트

| 범위 | 동작 |
|------|------|
| ≥ 1440px | 최대 너비 고정, 좌우 여백 |
| 768px ~ 1439px | 유동적 너비 |
| < 768px (모바일) | 스택 레이아웃 |

### 8.2 모바일 대응 (< 768px)

| 컴포넌트 | 변경 |
|----------|------|
| Charts Row | Flex → Column (세로 정렬) |
| Score Grid | 2열 그리드 |
| Detail Grid | 1열 |
| 헤더 Row | 줄바꿈 허용 (gap 축소) |
| 테이블 | 가로 스크롤 |

```css
@media (max-width: 768px) {
  .container { padding: 0 1rem; }
  .charts-row { flex-direction: column; }
  .chart-half { min-width: 100%; }
  .score-grid { grid-template-columns: repeat(2, 1fr); }
  .header-row, .header-row-2, .header-row-3 { gap: 0.5rem; }
  .detail-grid { grid-template-columns: 1fr; }
}
```

---

## 9. 접근성 (Accessibility)

| 항목 | 구현 |
|------|------|
| 키보드 네비게이션 | 탭, 엔터 키로 모든 인터랙션 가능 |
| ARIA 라벨 | 버튼, 드롭다운, 차트에 `aria-label` 추가 |
| 색상 대비 | WCAG AA 기준 준수 (텍스트 4.5:1, 큰 텍스트 3:1) |
| 스크린 리더 | 테이블에 `<caption>`, 차트에 대체 텍스트 |
| 포커스 표시 | `:focus-visible` 스타일 (outline) |

---

## 10. 성능 최적화

| 항목 | 전략 |
|------|------|
| CSS/JS 로드 | CSS는 `<head>`에서 로드, JS는 `defer` |
| Chart.js | CDN 캐싱 활용, 재렌더링 시 기존 인스턴스 `destroy()` |
| 폰트 | `font-display: swap`, `preconnect` |
| API 호출 | 상태 변경 시 필요한 API만 호출 (불필요한 재호출 방지) |
| DOM 업데이트 | `innerHTML` 일괄 교체 (개별 DOM 조작 최소화) |
| 이벤트 | 이벤트 위임 (delegation) 활용 |
