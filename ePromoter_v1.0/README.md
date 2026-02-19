# ePromoter v1.0 — Samsung Global Dashboard 분석·재현

globalsess.com **Samsung Global Dashboard**(Promoter Dashboard)의 메뉴·기능·API·지표를 분석하고, 동일 기능 재현에 필요한 명세·데이터를 정리한 프로젝트입니다.

---

## 1. 대상

| 항목 | 내용 |
|------|------|
| **URL** | http://www.globalsess.com/globaldashboard/ |
| **구성** | 로그인 → Main(Home) + 10개 Summary 메뉴 |
| **목적** | 대시보드 기능 파악, 테이블/그래프→API 역참조, 지표 정의·재현용 명세 확보 |

---

## 2. 폴더 구조

```
ePromoter_v1.0/
├── README.md                 # 본 문서
├── dashboard_deep_analysis.py   # 크롤: 로그인 → 메뉴별 수집 (API 응답, 툴팁, 차트 스펙)
├── globalsess_dashboard_crawl.py # 간단 크롤 (메뉴·기능 추출)
├── globalsess_dashboard_정리.md  # 메뉴·경로·공통 기능 요약
├── analysis/                 # 분석 결과물
│   ├── api_responses/        # Data/Graph API 응답 JSON (26개)
│   ├── menu_globaldashboard_*.json  # 메뉴별 구조, table_headers, filter_elements, chart_spec, header_tooltips
│   ├── table_api_spec.json   # 테이블 → API 역참조
│   ├── graph_api_spec.json   # 그래프 → API 역참조
│   ├── indicator_list.json   # 지표 이름·정의(부분)
│   ├── all_apis.json, login_api.json, crawl_meta.json
│   ├── screenshots/, html/   # 스크린샷·HTML 스냅샷
│   └── ...
├── docs/                     # 문서
│   ├── 대시보드_기능_파악_결과.md   # 기능·메뉴·관련 파일 인덱스
│   ├── 테이블_그래프_API_역참조_명세.md  # 테이블/그래프 → API 명세
│   ├── 데이터_지표_정의_가이드.md  # 지표 이름·정의(보강 방법)
│   ├── API_응답_필드_지표_참조.md  # API 응답 필드 → 지표 참조
│   ├── 재현_체크리스트_및_구현순서.md  # 재현 시 API 호출 순서·체크리스트
│   ├── MANUAL_01~05, README_매뉴얼.md, DASHBOARD_상세분석_재현가이드.md
│   └── ...
├── replication/              # 재현용 설정·템플릿
│   ├── config/               # menu_config.json, api_endpoints.json
│   ├── templates/, schemas/, samples/, scripts/
│   └── ...
└── scripts/
    ├── build_indicator_list.py   # 지표 목록·정의 가이드 생성
    └── build_reverse_spec.py     # 테이블/그래프 → API 역참조 명세 생성
```

---

## 3. 분석 결과물 인덱스

| 용도 | 파일/폴더 |
|------|-----------|
| **기능·메뉴 요약** | `docs/대시보드_기능_파악_결과.md`, `globalsess_dashboard_정리.md` |
| **테이블/그래프 → API** | `docs/테이블_그래프_API_역참조_명세.md`, `analysis/table_api_spec.json`, `analysis/graph_api_spec.json` |
| **지표·데이터 항목** | `docs/데이터_지표_정의_가이드.md`, `analysis/indicator_list.json`, `docs/API_응답_필드_지표_참조.md` |
| **API 응답 샘플** | `analysis/api_responses/*.json` |
| **재현 순서·체크리스트** | `docs/재현_체크리스트_및_구현순서.md` |
| **로그인·레이아웃·메뉴별 구현** | `docs/MANUAL_02~04`, `docs/MANUAL_05_API레퍼런스.md` |
| **메뉴 설정** | `replication/config/menu_config.json`, `api_endpoints.json` |

---

## 4. 실행 방법

### 크롤 (최신 데이터 수집)

```bash
# 가상환경 + Playwright (최초 1회)
python3 -m venv .venv
.venv/bin/pip install playwright
.venv/bin/playwright install chromium

# 크롤 실행 (로그인 → 메뉴별 방문, API 응답·스크린샷·툴팁·차트 스펙 수집)
.venv/bin/python dashboard_deep_analysis.py
```

### 역참조·지표 목록 재생성

```bash
python3 scripts/build_reverse_spec.py   # table_api_spec, graph_api_spec, 역참조 명세서
python3 scripts/build_indicator_list.py # indicator_list.json, 데이터_지표_정의_가이드.md
```

---

## 5. 관련 문서

- 매뉴얼 목차: `docs/README_매뉴얼.md`
- 상세 재현 가이드: `docs/DASHBOARD_상세분석_재현가이드.md`
