# Samsung Global Dashboard 재현 매뉴얼 및 소스

## 문서 (docs/)

| 파일 | 내용 |
|------|------|
| [MANUAL_01_개요및준비사항.md](MANUAL_01_개요및준비사항.md) | 개요, 필요 환경, 준비 체크리스트 |
| [MANUAL_02_로그인및인증.md](MANUAL_02_로그인및인증.md) | 로그인 플로우, API 스펙, 폼 구조 |
| [MANUAL_03_레이아웃및공통UI.md](MANUAL_03_레이아웃및공통UI.md) | GNB/LNB, 메인 메뉴, 공통 필터·기능 |
| [MANUAL_04_메뉴별구현가이드.md](MANUAL_04_메뉴별구현가이드.md) | 메뉴별 API, 초기화 순서, 화면 구성 |
| [MANUAL_05_API레퍼런스.md](MANUAL_05_API레퍼런스.md) | API 목록, request/response 요약 |
| [DASHBOARD_상세분석_재현가이드.md](DASHBOARD_상세분석_재현가이드.md) | 통합 상세 분석·재현 가이드 |

## 소스 (replication/)

### config/

| 파일 | 용도 |
|------|------|
| `menu_config.json` | 메뉴 전체 정의(path, label, icon, dataApi, graphApi, subnavFunctions) |
| `api_endpoints.json` | 로그인·공통·다운로드·메뉴별 API 경로 정리 |
| `asset_list.txt` | 다운로드할 이미지 상대 경로 목록 |

### templates/

| 파일 | 용도 |
|------|------|
| `main_index.html` | 메인(인덱스) 페이지 전체 HTML |
| `login_form.html` | 로그인 폼 + login() 스크립트 |
| `gnb_snippet.html` | Summary 페이지 상단 GNB 조각 |
| `lnb_snippet.html` | 좌측 LNB + moveXXX(), fileDown() 스크립트 |

### schemas/

| 파일 | 용도 |
|------|------|
| `request_login.json` | 로그인 API 요청 body 예시 |
| `request_filter_common.json` | Data/Graph 공통 필터 body 예시 |
| `request_getCountry.json` | getCountry 요청 body 예시 |

### samples/

| 파일 | 용도 |
|------|------|
| `api_login.js` | fetch 로그인 샘플 |
| `api_getCountry.js` | getCountry 호출 샘플 |
| `api_getExecutiveData.js` | getExecutiveData / getExecutiveGraphData 샘플 |

### scripts/

| 파일 | 용도 |
|------|------|
| `download_assets.py` | asset_list.txt 기준 이미지 다운로드 → `replication/assets/img/` |

## 사용 순서

1. **MANUAL_01** 로 환경·준비 확인  
2. **MANUAL_02** 로 로그인 연동 구현 (templates/login_form.html, samples/api_login.js 참고)  
3. **MANUAL_03** 로 메인·GNB·LNB 레이아웃 구현 (templates/*.html)  
4. **MANUAL_04**, **MANUAL_05** 와 config/menu_config.json, api_endpoints.json으로 메뉴별 API 연동  
5. `replication/scripts/download_assets.py` 실행 후 `replication/assets/img/` 를 프로젝트 `img/` 로 복사하거나 서빙

## 분석 결과물 (analysis/)

- `analysis/html/*.html` — 페이지 HTML 스냅샷  
- `analysis/screenshots/*.png` — 메뉴별 스크린샷  
- `analysis/all_apis.json` — 수집된 API 목록  
- `analysis/menu_*.json` — 메뉴별 구조·API  

재현 시 세부 DOM·스타일 참고용으로 활용하세요.
