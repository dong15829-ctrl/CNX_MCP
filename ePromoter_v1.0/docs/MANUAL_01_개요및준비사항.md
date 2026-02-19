# 매뉴얼 01: 개요 및 준비사항

## 1. 문서 목적

본 매뉴얼은 **Samsung Global Dashboard**(globalsess.com)를 다른 환경에서 동일하게 재구현하기 위한 준비사항과 개요를 정리한 것입니다.

## 2. 대시보드 개요

| 항목 | 내용 |
|------|------|
| **대상 URL** | https://www.globalsess.com/globaldashboard/ |
| **로그인 URL** | 동일 (로그인 후 `/globaldashboard/main`으로 리다이렉트) |
| **구성** | 메인(인덱스) + 10개 Summary 페이지 |
| **인증** | ID(이메일) + 비밀번호, 세션 쿠키 유지 |

## 3. 재현 시 필요 환경

### 3.1 프론트엔드

- **jQuery** (2.x 또는 3.x)
- **Moment.js** (날짜 처리, daterangepicker 의존)
- **daterangepicker** (날짜 범위 선택)
- **Google Charts** (Summary 페이지 차트; loader.js + corechart)
- (선택) **blueimp-md5** — 비밀번호 변경 시 MD5 등 사용 가능

### 3.2 백엔드/API

- 로그인 API: `POST /login` (또는 `/globaldashboard/login`)
- 각 Summary별 데이터 API: `POST /.../ajax/getXXXData`, `getXXXGraphData` 등
- 공통 API: `getCountry`, `getSiteCode`, `checkPending`, `switchTable`
- 다운로드: `POST /globaldashboard/CommonExcelDownload` (form 제출)

### 3.3 자산

- CSS: reset, layout, style, daterangepicker
- 이미지: 로고, 메인 메뉴 아이콘(icon_01_off ~ icon_16_off 등), GNB/LNB 아이콘, 차트 placeholder
- 경로: `replication/config/asset_list.txt` 및 `scripts/download_assets.py` 참고

## 4. 사전 준비 체크리스트

- [ ] 베이스 URL 결정 (예: `https://your-domain.com/globaldashboard`)
- [ ] 로그인 API 연동 가능 여부 확인
- [ ] getCountry / getSiteCode 응답 형식 확인 (Region/Local/Site 목록)
- [ ] 각 Summary별 Data/Graph API 스펙 확인 (request body, response 구조)
- [ ] 세션(쿠키 또는 토큰) 유지 방식 결정
- [ ] CSS/이미지 배치 경로 결정 (`css/`, `img/` 등)

## 5. 관련 문서

| 문서 | 설명 |
|------|------|
| [MANUAL_02_로그인및인증.md](MANUAL_02_로그인및인증.md) | 로그인 플로우, API 스펙, 예시 코드 |
| [MANUAL_03_레이아웃및공통UI.md](MANUAL_03_레이아웃및공통UI.md) | GNB/LNB 구조, HTML/CSS 참고 |
| [MANUAL_04_메뉴별구현가이드.md](MANUAL_04_메뉴별구현가이드.md) | 메뉴별 API, 파라미터, 화면 구성 |
| [MANUAL_05_API레퍼런스.md](MANUAL_05_API레퍼런스.md) | API 목록, request/response 예시 |

## 6. 소스/설정 파일 위치

| 경로 | 용도 |
|------|------|
| `replication/config/menu_config.json` | 메뉴 전체 정의 (path, label, icon, api) |
| `replication/config/api_endpoints.json` | API 엔드포인트 정리 |
| `replication/templates/` | HTML 템플릿 조각 |
| `replication/samples/` | 샘플 JS (로그인, getCountry, getExecutiveData 등) |
| `replication/schemas/` | API 요청 body 예시 JSON |
| `replication/scripts/download_assets.py` | 이미지/자산 다운로드 스크립트 |
