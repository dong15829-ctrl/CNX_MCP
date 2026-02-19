# 🎼 DI DIS1.1 주식 AI 오케스트레이션 청사진 (v0.1)

## 1. 프로젝트 개요
- **목표**: 국내/미국 보유·관심 종목을 대상으로 하루 6회(07·11·14·17·20·22시) AI 전략 리포트를 생성하고, 웹/텔레그램/히스토리 아카이브에서 실시간 확인·검증하도록 하는 통합 오케스트레이션 시스템 구축.
- **범위**:
  - 멀티 데이터 소스(KIS, 공시/뉴스/커뮤니티, 거시지표, 섹터/테마) 수집 → S3 데이터 레이크 적재 → 피처/모델 파이프라인 → FastAPI/Next.js 대시보드/텔레그램 알림.
  - 시뮬레이션·백테스트·MLOps를 통한 지속 학습/재학습과 배치 모니터링, 히스토리 비교/다운로드 기능.
- **핵심 가치 제안**:
  1. LLM 기반 서술형 전략(보유/매도/신규)과 3일 전망, 리스크·근거 설명.
  2. 섹터·테마 텍사노미, 감성/거시/수급 피처를 활용한 고도화된 AI 시그널.
  3. Airflow·S3·MLOps로 관리되는 투명한 배치 로그와 시뮬레이션 추적.
  4. Maestro 15 에이전트 체계를 통한 역할 분담, 문서/로그 표준화.

## 2. 요구사항 요약
| 구분 | 내용 |
| --- | --- |
| 업데이트 빈도 | 07·11·14·17·20·22시 (KST) 6회 자동 실행, 필요 시 수동 재생성 |
| 전략 범위 | 보유 종목 액션(Hold/Trim/Sell, 목표/매도 가격, 추천 수량, 3일 전망) + 신규 매수 후보(추천가·수량·손절/익절·근거) |
| 데이터 소스 | KIS 계좌/시세/주문 API(실거래·실시간), 공시/뉴스/커뮤니티/ETF/거시 지표 등 100% 크롤링 + 공개 API, 내부 포지션/시뮬레이션 DB |
| 데이터 레이크 | AWS S3 (Raw/Bronze/Silver/Analytics) + Glue/Athena + pgvector Feature Store(Feast 기반), 버전 관리/암호화 필수 |
| 분석/모델링 | 시계열+감성+RL 하이브리드 모델, 섹터·테마 텍사노미, 시뮬레이션/백테스트 및 MLOps 재학습 파이프라인(학습 12개월, 검증 1개월) |
| 대상 종목 | KOSPI 전 종목 + S&P500 구성 종목(필수), 필요 시 다른 시장은 보조 데이터로만 활용 |
| 산출물 채널 | 웹 대시보드, 텔레그램 요약 알림, Markdown/PDF 히스토리, API/WebSocket |
| 히스토리/감사 | PostgreSQL/pgvector에 슬롯별 결과/텍스트/로그 저장, 날짜·슬롯·종목 필터 및 PDF 다운로드 |
| 모니터링 | D3 기반 배치/리스크/성과 시각화, CloudWatch/Prometheus/Grafana 알림, Sentinel 보안 로깅 |
| 사용자/권한 | 단일 개인 계정(Owner) 기반, RBAC 단순화 |

## 3. 사용자 여정
1. **접속 & 인증**: 단일 사용자(Owner) 계정으로 로그인/JWT 발급 → 대시보드 진입.
2. **실시간 타임라인 확인**: 오늘 슬롯(06개) 상태/성공 여부/ETA를 타임라인·히트맵으로 확인하고, 최신 슬롯 카드 클릭.
3. **전략 열람**: 보유 종목 카드에서 액션/가격/수량/3일 전망·서술형 근거 확인, 신규 매수 테이블에서 추천가·근거·리스크 검토.
4. **히스토리/비교**: 날짜/슬롯/종목/테마 필터 → 과거 리포트 비교 차트, Markdown/PDF 다운로드, LLM 서술 변화를 체크.
5. **알림 연동**: 슬롯 완료 시 텔레그램 알림 링크 클릭 → 모바일 웹/앱에서 해당 리포트 세부 화면 자동 이동.
6. **배치 모니터링 & 피드백**: Batch Monitor에서 DAG 상태/로그 확인, 문제 발생 시 Guardian/Deployer에게 에스컬레이션, 사용자 피드백은 Planner에게 전달.

## 4. 시스템 아키텍처
```
                ┌───────────────┐
     외부 소스  │  KIS API      │
   (공시/뉴스/  │  공개 API/CSV │
    커뮤니티)   │  크롤러       │
                └──────┬────────┘
                       │  (Airflow di_data_harvest 전용)
                       ▼
                ┌───────────────┐
                │   S3 Data Lake│  (Raw/Bronze/Silver/Analytics)
                └──────┬────────┘
                       │  (Spark/EMR/Glue ETL)
                       ▼
                ┌───────────────┐
                │ Feature Store │ (Feast + pgvector)
                └──────┬────────┘
                       │
        ┌──────────────┴──────────────┐
        │      Brain/Insight Model    │  (MLFlow/SageMaker, RAG/LLM)
        └──────────────┬──────────────┘
                       │  (Airflow di_maestro_report / di_model_refresh)
             ┌─────────┴───────────┐
             │   FastAPI Core      │ (Reports/History/Batch APIs)
             └─────────┬───────────┘
                       │
        ┌──────────────┴──────────────┐
        │ Next.js + D3 Dashboard      │
        │  (Dashboard/History/Batch)  │
        └──────────────┬──────────────┘
                       │
                 [Telegram Bot / Webhook]

Monitoring & Ops: CloudWatch/Prometheus, Grafana, GitHub Actions CI/CD, IAM/Sentinel Guardrails
```
- **인프라 계층**
  - 컴퓨트: AWS EC2 (CNX_MCP) + 컨테이너화(FastAPI, Next.js), Airflow 전용 노드(모든 배치/크롤링/재학습 오케스트레이션은 Airflow 단일 스택으로 운영).
  - 데이터: AWS S3 데이터 레이크, Managed PostgreSQL (OLTP + metadata), Redis/Elasticache(옵션) for cache, pgvector 확장.
  - MLOps: MLflow/SageMaker Registry, ECR 이미지, GitHub Actions CI/CD.
  - 모니터링: CloudWatch + Prometheus + Grafana, Telegram/Slack 경보.

### 4.1 상위 요구사항 반영 매트릭스
| 상위 항목(1~4장) | 구현 섹션 | 반영 내용 |
| --- | --- | --- |
| 6회 슬롯 AI 리포트 & 웹/텔레그램 제공 | §7, §9, §10, §11 | Airflow `di_maestro_report`, FastAPI Report API, Next.js 타임라인/D3, 텔레그램 알림 |
| 멀티 데이터 소스 + S3 레이크 + 피처 스토어 | §6 전체, §7 | 확장형 크롤링, API 수집 계획, 시뮬레이션 데이터 요구, S3/Glue/pgvector 구조 |
| LLM 서술형 전략 + 섹터/테마 텍사노미 | §8, §6.5.1, §15.3 | 하이브리드 모델, 텍사노미 스키마, 시뮬레이션/전략 설계 |
| MLOps/모니터링/배치 투명성 | §7, §12, §12.1, §15.5 | 배치 로그, CloudWatch/Prometheus, 재학습 DAG, CI/CD, 운영 지침 |
| Maestro 15 에이전트 운영 | §5, §5.1, §15 | 역할/브랜치, 상세 지시문, 단계별 스펙/액션 아이템 |
| 사용자 여정(대시보드-히스토리-알림) | §9~§11, §15.4 | FastAPI/Next.js API, 히스토리/비교, 배치 모니터링 UI, 다운로드 |

## 5. 에이전트 역할 & Git 브랜치
| 그룹 | 에이전트 | 주요 임무 | Git 브랜치 |
| --- | --- | --- | --- |
| 지휘/기획 | Maestro | 전체 로드맵 관리, 승인 | `main` 보호 |
| Vision | ROI/리스크 정의, KPI | `feature/vision-kpi` |
| Planner | 기능 명세, 화면 Flow | `feature/spec-ui` |
| 데이터 | Architect | ERD/DB 설계 | `feature/db-schema` |
|  | Pipeline | Airflow DAG, 데이터 수집기 | `feature/data-pipeline` |
|  | Insight | 통계 지표, 리스크 커브 계산 | `feature/insight-metrics` |
|  | Brain | 시계열+RAG+LLM 전략 엔진 | `feature/ai-engine` |
| 개발 | Core | FastAPI, 인증, 리포트 API | `feature/backend-api` |
|  | Interface | Next.js UI, 히스토리 뷰 | `feature/frontend-ui` |
|  | Canvas | D3 배치 모니터링/차트 | `feature/d3-visual` |
| 품질/운영 | Guardian | 테스트, 백테스트 검증 | `feature/qa-suite` |
|  | Deployer | CI/CD, 인프라 IaC | `feature/devops` |
|  | Sentinel | 보안 스캔, 키 관리 가드라인 | `feature/security` |
| 지원 | Scribe | 리포트 템플릿, 문서화 | `feature/docs` |
|  | Counsel | 규제/데이터 사용 정책 | `feature/compliance` |
|  | Mediator | 의견 충돌 중재, 결정 기록 | `feature/pm-notes` |

### 5.1 에이전트 상세 역할 지시문
- **Maestro**: 주간 실행 계획 승인, 의사결정 로그 유지, 에이전트간 의존성 조정. Deliverable: 주간 오케스트레이션 노트, 리스크 요약.
- **Vision**: ROI 모델, KPI 정합성 검토, 신규 기능 요구 Prioritization. Deliverable: KPI 대시보드, 투자 대비 효과 분석.
- **Planner**: 사용자 스토리, 화면 플로우, 요구 명세서 작성 및 변경 관리. Deliverable: FSD, 와이어플로우, JIRA 티켓.
- **Architect**: 전체 ERD/데이터 레이크 스키마, API 계약, 인프라 토폴로지 정의. Deliverable: 다이어그램, 마이그레이션 스크립트, IaC 초안.
- **Pipeline**: Airflow DAG 및 크롤러 구현, 데이터 품질 모니터링, S3 적재 자동화. Deliverable: DAG 코드, 크롤링 템플릿, 데이터 SLA 리포트.
- **Insight**: 통계 지표/리스크 커브 산출, 품질 검증 룰 정의, 분석용 SQL/노트북 제공. Deliverable: 리스크 리포트, Feature QA 결과.
- **Brain**: 모델 연구·훈련·시뮬레이션, LLM 프로빙, 전략 룰북 작성. Deliverable: 모델 카드, 실험 기록, 시뮬레이션 결과 문서.
- **Core**: FastAPI 도메인 모듈, 인증/RBAC, 캐시/웹훅 구현, 텔레그램 통합. Deliverable: API 스펙, OpenAPI 문서, 서비스 로그 포맷.
- **Interface**: Next.js 페이지/상태 관리, 사용자 흐름 테스트, 접근성 검토. Deliverable: UI 프로토타입, Storybook 캡처, UX 테스트 결과.
- **Canvas**: D3 컴포넌트(타임라인/히트맵/성과 차트) 개발, 퍼포먼스 튜닝. Deliverable: Visualization 라이브러리, 성능 측정 리포트.
- **Guardian**: 단위/E2E/백테스트 TC 설계, 자동화 시나리오, 품질 게이트 운영. Deliverable: QA 플랜, 테스트 증적, 승인 체크리스트.
- **Deployer**: CI/CD 파이프라인, IaC 배포, 모니터링/알람 설정. Deliverable: GitHub Actions 워크플로, Terraform/CloudFormation 템플릿, 런북.
- **Sentinel**: 비밀/접근 통제, 취약점 스캔, 감사 대응. Deliverable: 보안 검사 리포트, 키 로테이션 계획, 침해 대응 시나리오.
- **Scribe**: 리포트 템플릿, 사용자 매뉴얼, 변경 이력 관리. Deliverable: 문서 저장소, 릴리스 노트, Markdown 리포트 아카이브.
- **Counsel**: 데이터 라이선스/규제 검토, Privacy Impact Assessment. Deliverable: 준법 검토서, 데이터 사용 동의 체커.
- **Mediator**: 분쟁 중재, 의사결정 기록, 리스크 에스컬레이션. Deliverable: 회의록, 결정 매트릭스, 분쟁 해결 로그.

## 6. 데이터 아키텍처
### 6.1 ERD 개요
- `report_runs`: `id`, `slot_time`, `market_scope`, `status`, `summary_md`, `llm_version`, `created_at`.
- `positions_snapshot`: `run_id` FK, `symbol`, `market`, `quantity`, `avg_price`, `current_price`, `action`, `target_price`, `sell_price`, `expected_3d_return`, `narrative`.
- `recommendations`: `run_id`, `symbol`, `entry_price`, `qty`, `stop_loss`, `take_profit`, `confidence`, `rationale`.
- `news_insights`: `run_id`, `source`, `sentiment`, `embedding_id`, `summary`.
- `batch_logs`: `dag_id`, `slot_time`, `step`, `status`, `duration_ms`, `error_payload`.

### 6.2 데이터 흐름
1. **수집**: Pipeline Agent가 KIS 시세·계좌, 뉴스 API, 거시 데이터, 크롤링 파이프라인 결과를 pull.
2. **정제/적재**: S3 Raw → Spark/Pandas 처리 → PostgreSQL & pgvector.
3. **피처 스토어**: Brain Agent가 Feast 기반 피처 스토어에 시계열 특징/감성 벡터 저장(pgvector 연동).
4. **리포트 저장**: Core가 각 슬롯 결과를 `report_runs` 이하 테이블에 commit.

### 6.3 확장형 데이터 수집·크롤링 전략
- **수집 범위**: 국내/미국 증권사 리포트, DART·SEC 공시 전문, 주요 커뮤니티(Clien, Reddit r/stocks 등), ETF·섹터/원자재 지표, 공매도·수급 데이터.
- **크롤러 설계**: Airflow 서브 DAG `di_data_harvest`에서 Selenium/Playwright + Requests 조합으로 15분~4시간 주기의 크롤러 실행, 중복 필터·로봇배제 준수.
- **저장 계층**: Raw HTML/JSON은 S3, 정제 텍스트와 메타는 PostgreSQL `raw_sources`, 임베딩은 pgvector `news_insights` 확장 테이블.
- **데이터 품질**: 항목별 스키마 검증, 스팸 필터링, 감성 라벨링에 활용될 QA 표본 추출. 수집 실패 시 재시도 및 Sentinel 경보.
- **RAG 운영**: 문서 chunking + 메타데이터(섹터, 타임스탬프, 출처)를 부여하고 LLM 질의 시 최신 크롤링 데이터까지 포함하도록 폴백 전략 구성.

### 6.4 API·크롤링 수집 계획
| 구분 | 소스 | 방식 | 빈도/SLA | 핵심 필드 | 활용 목적 |
| --- | --- | --- | --- | --- | --- |
| 시세/API | KIS 실시간·일봉, 체결·잔고 | REST/WebSocket | 1~5분 / <1s | 가격, 거래량, 미체결, 잔고 | 포트폴리오 상태, 주문 시뮬 |
| 계좌/API | KIS 계좌/주문, 투자자 구분 수급 | REST | 슬롯 시작 전 | 잔고, 가능액, 주문 체결 | 전략별 포지션 크기 계산 |
| 공시/리포트 | DART, SEC, 증권사 PDF | Open API + 크롤링 | 15분~2시간 | 본문, 섹터, 이벤트 타입 | 이벤트 드리븐 전략, RAG |
| 뉴스/커뮤니티 | 연합·블룸버그 RSS, Reddit, 국내 커뮤니티 | RSS + Playwright | 5분~1시간 | 제목, 본문, 감성, 언급 종목 | 감성 피처, LLM 내러티브 |
| 거시·지표 | FRED, Investing, 환율/채권 | Open API/크롤 | 1시간/일 | 금리, 원자재, 지수 | 시장 컨텍스트 피처 |
| 수급/파생 | 공매도, 프로그램 매매, 옵션/선물 | 크롤링/CSV | 1시간/일 | 순매수, 베이시스 | 리스크 지표, 합성 시그널 |
| 기술 지표 | TradingView/TA-Lib 계산 | 내부 계산 | 슬롯별 | MA, RSI, ATR, VWAP | 전통 시그널 검증 |
- **동기화 정책**: 각 소스별 타임스탬프 정렬, 레이트 제한 대응(Exponential backoff), 누락 시 최근 데이터 보간.
- **보안/법적 검토**: Robots.txt 준수, API 키 암호화, 이용 약관 검토 후 Counsel 승인 기록.

### 6.5 분석 지표 및 모델링 피처 정의
- **시장 컨텍스트 피처**
  - 지수/섹터 수익률(1h/1d/5d), 변동성 지수(VIX/KOSPI200 V-KOSPI), 금리·환율 변화율.
  - 글로벌 이벤트 엔코딩(연준 발언, CPI 발표 등)을 원-핫/시간 가중치로 반영.
- **종목 마이크로 피처**
  - 가격: 로그수익률, 모멘텀(5/20/60), 고저갭, VWAP 괴리.
  - 거래: 거래대금, 체결강도, 호가스프레드, 공매도 비중, 프로그램 순매수.
  - 리스크: ATR, Garman-Klass 변동성, 베타, 상관 네트워크 중심성.
- **감성/텍스트 피처**
  - LLM 요약 감성 점수(긍/부/중립), 토픽 분류, 이벤트 태그(리콜, 증자 등).
  - 커뮤니티 버즈 지수(언급량 z-score), 뉴스 신뢰도 가중치.
- **재무/펀더멘털 피처**
  - 분기 재무 비율(ROE, 부채비율, FCF), 성장률(매출/영업이익), 밸류에이션(PER/PBR) 트렌드.
  - ETF/섹터 흐름과의 상관, 동종 업계 대비 상대 지표.
- **전략/모델 방법론**
  1. **시계열**: Prophet/TFT로 3일 수익률 예측, 불확실성 밴드 생성.
  2. **감성 융합**: 텍스트 임베딩 + 가격 피처를 Transformer Cross-Attention으로 결합.
  3. **강화학습**: PPO/Deep Hedging으로 포지션 크기·매도 시점 최적화.
  4. **리스크 엔진**: CVaR 제약 최적화, Kelly fraction 기반 포지션 캡.
  5. **설명 가능성**: SHAP/Integrated Gradients로 Top Factors 산출, 리포트 내 구문 자동 생성.
- **분석 지표**
  - 퍼포먼스: CAGR, MDD, Calmar, Sortino, Hit Ratio, Turnover, Transaction Cost.
  - 리스크/품질: Drift Score(PSI), Coverage(전략 적용 종목 비중), Latency(슬롯별 처리 시간).
  - 운영: 알림 전달 성공률, 데이터 결측률, 모델 재학습 주기.

### 6.5.1 섹터·테마 텍사노미 전략
- **분류 체계**
  - 1차: GICS/KSIC 기반 11대 섹터 (IT, 헬스케어, 금융 등).
  - 2차: 세부 산업(반도체, 2차전지, 방산, 바이오시밀러 등) 60~80개 카테고리.
  - 3차: 테마/모멘텀 태그(메타버스, ESG, IRA 수혜, 우주항공 등) 가변 분류.
- **생성 방식**
  - 공식 섹터는 상장사 메타데이터/공시에서 매핑하고, 테마는 뉴스/커뮤니티 텍스트를 LLM으로 요약→키워드 추출→토픽 모델(LDA/BERTopic)로 자동 생성.
  - ETF 구성종목, 리서치 보고서에서 테마 시드 리스트를 수집해 사전(lexicon) 구축.
- **활용**
  1. **시그널 가중치**: 같은 테마 내 종목들의 평균 수익률/감성 지수를 계산해 개별 종목 시그널에 가중치로 적용.
  2. **분산 관리**: 포트폴리오 내 섹터/테마별 익스포저 한도를 설정하여 리스크 캡.
  3. **설명력**: 리포트에서 “2차전지 테마 전반이 약세” 등 내러티브를 자동 생성.
  4. **경보**: 특정 테마의 감성 급변/거래대금 폭증 시 텔레그램 알림 트리거.
- **데이터 구조**
  - `taxonomy_nodes`: `id`, `level`, `name`, `parent_id`, `keywords`, `source`.
  - `symbol_taxonomy_map`: `symbol`, `taxonomy_id`, `confidence`, `last_updated`.
  - 태그는 버전 관리하며, 테마 추가/삭제 시 히스토리를 보존해 백테스트 시점 일관성을 유지.

### 6.6 시뮬레이션 데이터 요구사항
- **기간/해상도 (Learning 12개월 + Validation 1개월 중심)**
  - **국내(KOSPI)**: 최근 12개월 일봉/분봉(1/5분) 필수, 추가로 1개월 검증 세트 분리. 체결·수급 데이터는 12개월 확보, 검증 구간 별도 보존.
  - **미국(S&P500)**: 최근 12개월 일봉 및 프리/애프터마켓 분봉, 1개월 검증 구간. 필수 대상은 S&P500 구성 종목이며, 그 외 시장은 참고용.
  - (옵션) 과거 1년 이전 데이터는 보조 참고용으로 Glacier에 보관하되, 모델 학습 파이프라인은 12M+1M 슬라이딩 방식으로 고정.
- **데이터 출처**
  - 가격/체결: KRX/NYSE 공식 페이지, 증권사 HTS 웹, 야후파이낸스·Investing 등 공개 사이트를 **크롤링**으로 적재 (KIS API는 실계좌·실시간용에 한정).
  - 수급/공매도/프로그램: KRX 정보데이터시스템, FINRA, Quandl 등 무료 페이지 크롤링.
  - 거시/ETF/섹터: 각 거래所/ETF 운용사 페이지, 경제통계국 크롤링 및 CSV 다운로드 자동화.
  - 커뮤니티/뉴스: RSS/HTML을 주기적으로 스냅샷 저장해 과거 감성 재현 가능하게 함.
- **스키마**
  - `ohlcv_kr/us`: `symbol`, `date`, `interval`, `open/high/low/close`, `volume`, `turnover`, `adjusted_flag`.
  - `orderflow`: `symbol`, `timestamp`, `bid/ask_depth`, `program_buy/sell`, `short_volume`.
  - `macro_events`: `event_id`, `country`, `event_type`, `value`, `surprise`, `text_blob`.
  - `text_corpus`: `doc_id`, `source`, `language`, `timestamp`, `raw_text`, `clean_text`, `sentiment`.
- **데이터 품질/충분성 체크**
  - 커버리지: 국내 상장사 95% 이상, 미국 S&P500 전체 필수 확보.
  - 결측 허용치: 일봉 데이터 결측률 <0.5%, 분봉 <2%; 초과 시 재크롤/보간 플래그.
  - 스냅샷 검증: 매일 장 마감 후 KIS 레퍼런스 가격과 샘플 비교해 오차율 <0.05%.
- **시뮬레이션 입력 구성**
  - 과거 가격/체결 + 수급 + 텍스트 감성을 시점별 텐서로 변환.
  - 슬리피지·거래비용은 크롤링한 체결강도/스프레드를 기반으로 동적으로 산정.
  - 이벤트 라벨(공시, 뉴스, 경제지표)과 가격 반응을 매핑해 이벤트드리븐 전략 학습.
- **확장 전략**
  - 추가 API 확보가 어려울 경우, 공개 CSV/ZIP 파일 다운로드 및 버전관리(크롤링)로 대체.
  - 신규 데이터 소스 제안 시 Counsel 검토 후 Pipeline DAG에 편성하고, 데이터 카탈로그에 즉시 반영.

### 6.7 S3 데이터 레이크 및 운영
- **버킷 구조**
  - `di-data-raw`: 크롤링 원본(HTML/PDF/JSON), API 덤프, 대용량 CSV. 파티션 `source/date/hour`.
  - `di-data-processed`: 정제된 Bronze/Silver 데이터, 파티션 `domain=ohlcv|macro|text/...`.
  - `di-data-analytics`: 시뮬레이션용 특성 텐서, 모델 입력/출력, 리포트 PDF.
- **버전 관리 & 거버넌스**
  - Object tagging으로 데이터 버전/출처/민감도 표시, S3 Object Lock으로 변경 이력 유지.
  - Glue Data Catalog에 테이블 등록 → Athena/EMR/Spark에서 질의.
  - IAM 정책으로 에이전트별 접근(읽기/쓰기) 제한, VPC Endpoint를 통해 사설 접근.
- **라이프사이클 관리**
  - Raw는 90일 후 Glacier로 이동, 중요 데이터는 S3 Intelligent-Tiering.
  - 일별 스냅샷을 S3 Versioning으로 보존, 주간 백업을 Cross-Region 복제.
- **보안**
  - Server-Side Encryption(SSE-KMS), CloudTrail 로깅, Access Analyzer로 퍼블릭 정책 검사.
- **운영 자동화**
  - Airflow 태스크가 S3 업로드/검증을 처리하고, 실패 시 retry + 텔레그램 경보.
  - Cost Explorer 모니터링을 Sentinel/Deployer가 월간 리뷰.

## 7. Airflow 기반 배치 파이프라인
- DAG: `di_maestro_report`
- 스케줄: `0 7,11,14,17,20,22 * * *`
- 태스크
  1. `fetch_market_data`
  2. `update_embeddings`
  3. `run_strategy_engine`
  4. `persist_report`
  5. `notify_telegram`
  6. `refresh_cache` (웹 실시간 반영)
- 각 태스크는 CloudWatch 로그와 `.md` 실행 리포트 작성.
- **운영 원칙**: 모든 배치/크롤링/재학습 파이프라인은 Airflow 단일 스택에서만 실행하며, 별도 Lambda/Step Functions는 사용하지 않는다.

## 8. AI/전략 엔진
- **모델**: Prophet/LSTM + Transformer 기반 감성 분석 + RL 포지션 사이징.
- **LLM**: Gemini/OpenAI 혼합, RAG 컨텍스트(뉴스 요약, 이벤트) 제공.
- **LLM Fact-check**: 규칙 기반(가격/수치 검증, 금칙어) + 샘플형 QA 모델 이중 검증을 적용해 서술 오류를 Guardian에게 에스컬레이션.
- **출력 형태**
  - 보유 종목: `Action`, `Sell Price`, `Qty`, `3일 시나리오`, `Narrative`.
  - 신규 매수: `Entry`, `Qty`, `Stop/Take`, `근거`, `리스크`.
- **XAI**: SHAP 상위 요인, 시각적 요약.
- **검증**: Guardian가 백테스트 결과와 실제 알파 비교, Drift 감지 후 재학습.

### 8.1 시뮬레이션·백테스트 프레임워크
- **데이터 레이크**: 최근 12개월 + 검증 1개월 데이터를 S3 Iceberg/Hudi 테이블로 구성하고, 필요 시 과거 데이터는 Glacier에서 온디맨드 복구해 참조.
- **전략 샌드박스**: Brain Agent가 `simulation_engine` 모듈에서 다중 전략(모멘텀, 페어트레이딩, 이벤트드리븐)을 병렬로 실험, Hyperopt/Optuna로 파라미터 튜닝.
- **성과 지표**: CAGR, MDD, Calmar, 히트비율, 거래비용 반영한 순알파, LLM 서술에 필요한 리스크 요약 자동 산출.
- **시뮬레이션 주기**: 주 1회 전체 재학습 파이프라인(훈련 12M, 검증 1M), 슬롯별 마이크로 시뮬레이션은 최근 30일 슬라이딩으로 전략 점검.
- **업데이트 전략**: Drift 감지 시 Planner/Maestro 승인하에 모델 버전 승격, `report_runs.llm_version` 및 모델 해시 기록.

## 9. Backend (FastAPI) 명세
- **프로토콜 원칙**: 모든 API는 REST(JSON)로만 제공하며 GraphQL/JSON-RPC는 사용하지 않는다. 실시간 갱신은 별도 WebSocket 엔드포인트에서 제공.
| API | 설명 |
| --- | --- |
| `POST /auth/login` | JWT 기반 인증 |
| `GET /reports?date=YYYY-MM-DD` | 슬롯 리스트 + 상태 |
| `GET /reports/{run_id}` | 리포트 상세(보유/신규/브리핑/로그) |
| `GET /history` | 필터(종목/슬롯) 기반 검색 |
| `GET /batch/status` | DAG 실행 현황/통계 |
| `POST /reports/refresh` | 수동 재생성 트리거(권한 필수) |
| `WS /stream/updates` | WebSocket 기반 최신 슬롯 실시간 push |
- **인증/권한**: 단일 사용자 전용 시스템으로, `owner` 롤만 존재하며 RBAC/Gruop 기능은 구현하지 않는다.

## 10. Frontend (Next.js + D3)
- **페이지**
  1. Dashboard: 오늘 타임라인, 최신 리포트 카드, 시장 브리핑.
  2. History: 날짜·슬롯 필터, 비교 보기, 다운로드.
  3. Batch Monitor: 슬롯별 단계 차트, 성공률/시간 그래프.
- **컴포넌트**: TimelineBar, PositionCard, RecommendationTable, NarrativePanel, BatchStatusHeatmap(D3), PerformanceTrendChart(D3).
- **상태관리**: React Query/SWR로 REST 응답 캐시, WebSocket 스트림으로 슬롯 상태 실시간 반영(SSE 미사용).
- **디자인 원칙**: 다크/라이트 지원, 중요 액션 색상 구분(Hold=blue, Sell=red 등).

### 10.1 화면 기획 요약
- **Dashboard**
  - 상단 헤더: 날짜 선택, 최근 슬롯 배지, 사용자 알림 센터.
  - 메인 영역: 좌측 `TimelineBar`(슬롯 상태), 우측 `Market Brief` 카드(국내/미국 핵심 지표 + 감성 요약).
  - 보유 섹션: 카드형 리스트(종목명, 현재가, 액션, 목표/매도 가격, 3일 전망 스파크라인, 서술형 근거 펼침).
  - 신규 섹션: 테이블(추천가, 수량, 손절/익절, 테마, 신뢰도 게이지).
  - 하단: 이벤트 로그(전 슬롯 대비 변경 요약), 텔레그램 링크 버튼.
- **History**
  - 좌측 필터 패널: 날짜 범위, 슬롯, 종목, 테마, 액션 타입.
  - 우측: 리포트 카드 타임라인 + 비교 뷰(두 슬롯 선택 → 지표/내러티브 비교), CSV/PDF 다운로드 버튼.
  - 세부 모달: LLM 서술 변경 diff, 감성/수익률 차트.
- **Batch Monitor**
  - 상단 요약 KPI: 성공률, 평균 처리 시간, 재시도 횟수.
  - 중앙: D3 히트맵(슬롯 × 태스크, 색상으로 상태), 각 태스크 클릭 시 CloudWatch 로그 링크. 모든 시각화 데이터는 백엔드 집계(API `/batch/status`)만 사용해 프런트 메모리 사용 최소화.
  - 하단: 트렌드 차트(7일 처리 시간, 실패 원인 파이차트).
- **반응형/모바일**
  - 모바일에서는 타임라인을 캐러셀, 카드 정보를 스택으로 축약, 텔레그램 링크와 연동.
- **UX 노트**
  - 사용자 액션 최소 2클릭 이내로 정보 접근, Alert/Toast로 실시간 알림.
  - 접근성: 색상 대비, 키보드 내비게이션, ARIA 레이블 정의.

### 10.2 예시 와이어프레임 (텍스트)
```text
┌──────────────────────────────────────────────────────────────┐
│ 날짜/슬롯 선택 ▽ │ 알림🔔 │ 사용자 │                          │
├───────────────┬──────────────────────────────────────────────┤
│ TimelineBar   │  Market Brief                                │
│ [07✅][11⏳]   │  국내: KOSPI +0.8%  VIX 15.2 (-0.4)           │
│ [14✅][17🕒]   │  미국: NASDAQ Fut +0.5%                      │
│ [20🕒][22⏳]   │  감성: 긍정 ↑ 2.3                             │
├───────────────┴──────────────────────────────────────────────┤
│ 보유 종목 액션                                                  │
│ ┌────────────┬───────────┬──────────┬──────────────┬───────┐ │
│ │005930 삼성전자│ Hold     │ 목표 82,000│ 3일 +1.2%      │보기│ │
│ │Narrative: 메모리 ASP 회복                                  │ │
│ ├────────────┼───────────┼──────────┼──────────────┼───────┤ │
│ │AAPL        │ Trim 30% │ 매도 210  │ 3일 +0.6%      │보기│ │
│ └────────────┴───────────┴──────────┴──────────────┴───────┘ │
│ 신규 매수 제안                                                 │
│ ┌────────────┬────────┬───────┬────────┬────────────┬──────┐ │
│ │티커        │ Entry  │ 수량 │ 손절   │ 테마       │근거│ │
│ │TSLA        │ 205    │ 5    │ 190    │ 전기차     │보기│ │
│ └────────────┴────────┴───────┴────────┴────────────┴──────┘ │
│ 이벤트 로그 / 텔레그램 링크                                   │
└──────────────────────────────────────────────────────────────┘

History 페이지 (요약)
┌─────────────┬───────────────────────────────────────────────┐
│ 필터        │  달력/슬롯/종목/테마 체크                     │
├─────────────┴───────────────────────────────────────────────┤
│ [22:00 11/21] 카드  ─ 비교 선택 □                           │
│ [20:00 11/21] 카드  ─ 비교 선택 ☑                           │
├─────────────────────────────────────────────────────────────┤
│ 비교 뷰: Slot A vs Slot B                                   │
│ - 지표 스파크라인, 내러티브 Diff                            │
│ - 다운로드 버튼 (PDF / MD)                                  │
└─────────────────────────────────────────────────────────────┘
```

## 11. 텔레그램 알림 설계
- 메시지 포맷: `[22:00] 🇺🇸 신규 2건 / 보유 3건 액션. 주요: AAPL Trim @210 (3일 +1.8%).` + 웹 링크.
- 실패 시 3회 재시도, 실패 로그는 `batch_logs` 테이블과 CloudWatch에 기록.
- 중요 이벤트 시 Mediator/Guardian에게 별도 경보.

## 12. 모니터링 & 로그
- CloudWatch 지표: DAG 성공률, 처리 시간, API 응답, 텔레그램 성공률.
- 배치 모니터링 UI와 연동, 알림 기준선 초과 시 Slack/이메일(옵션).
- 표준 로그 포맷: `timestamp | agent | action | input | output | status`.

### 12.1 MLOps 파이프라인
- **모델 레지스트리**: SageMaker Model Registry 혹은 MLflow에 버전/메타데이터/성능 지표 저장, `report_runs`에 참조 키 기록.
- **데이터/모델 모니터링**: 데이터 드리프트(Kolmogorov-Smirnov, PSI), 성능 드리프트(실제 수익률 vs 예측) 자동 계산 후 Threshold 초과 시 Alert 및 재학습 티켓 생성.
- **재학습 오케스트레이션**: Airflow `di_model_refresh` DAG가 주간 전체 학습 + 슬롯별 소규모 파인튜닝 실행, 성공 시 자동 배포 전 Guardian 검증 단계 거침.
- **CI/CD for ML**: GitHub Actions → 모델 빌드/테스트 → 스테이징 환경 배포 → Canary 테스트 후 운영 전환. 실패 시 이전 버전 자동 롤백.
- **실험 추적**: Optuna/Weights & Biases 연동, 하이퍼파라미터·데이터 스냅샷·주석을 자동 기록해 추후 감사/재현 가능.
- **Observability**: Prometheus + Grafana로 모델 latency, 추론 오류율, 리포트 생성 성공률 대시보드화.

### 12.2 운영 정책 체크리스트
1. **배치/크롤링/재학습 실행**: Airflow 단일 스택에서만 실행, ad-hoc 스크립트 금지.
2. **데이터 범위**: 학습 12M + 검증 1M, 대상 종목은 KOSPI + S&P500 우선. 추가 시장은 별도 승인 후 편입.
3. **API/프로토콜**: FastAPI REST + WebSocket만 사용, GraphQL/SSE 금지.
4. **실시간 알림**: 텔레그램 전송 실패 시 5분 이내 자동 재시도, 3회 실패 시 Guardian/Deployer 알림.
5. **보안**: `.env` 비밀은 AWS Secrets Manager에서 KMS 기반 30일 로테이션, 로컬에는 암호화 파일만 허용.
6. **문서/로그**: 모든 슬롯 실행 결과와 의사결정은 `Decision Board`와 `batch_logs`에 기록, 미기록 시 배포 금지.

### 12.3 SLA 정의
| 영역 | 목표 지표 | 상세 기준 | 에스컬레이션 |
| --- | --- | --- | --- |
| 데이터 수집 | 슬롯 시작 10분 전까지 핵심 소스 100% 수집 완료 | 실패 시 Airflow에서 자동 재시도(3~5회), 10분 내 복구 안 되면 Pipeline→Sentinel | Pipeline ▶ Maestro |
| 전략 생성 | 슬롯 시작 후 5분 이내 `report_runs` 완료 | 처리 시간 >5분 또는 실패 2회 이상 시 Guardian 알림 | Brain/Core ▶ Guardian |
| 텔레그램 알림 | 리포트 확정 후 2분 이내 발송, 성공률 99% | 실패 시 1분 간격 3회 재시도, 15분 초과 시 긴급 경보 | Core ▶ Deployer |
| 웹/API 가용성 | 월간 99.5% 이상, REST 응답 < 1초(P95) | 5분 이상 장애 시 Status 페이지/텔레그램 공지 | Deployer ▶ Maestro |
| WebSocket 스트림 | 95% 이상 지속 연결, 재연결 < 30초 | Heartbeat 미수신 30초 시 클라이언트 재연결 권장 | Core ▶ Interface |
| 인시던트 대응 | 중요 알림 15분 내 triage, 2시간 내 복구 계획 | Guardian 책임하에 RCA 작성, Decision Board 기록 | Guardian ▶ Maestro |
| 문서 업데이트 | 변경 후 24시간 내 관련 Markdown/Decision Board 반영 | 미준수 시 Scribe가 개선 계획 제출 | Scribe ▶ Planner |

## 13. 보안/거버넌스
### 13.1 비밀 관리 & 키 로테이션
- 민감 키/토큰은 **AWS Secrets Manager**에 저장하고, 30일 주기로 자동 로테이션(KMS CMK 사용).
- 배포 시 GitHub Actions가 Secrets Manager에서 임시 토큰을 받아 `.env`를 생성하며, 로컬(개발)에서는 암호화된 `.env.enc`만 허용.
- Sentinel은 월 1회 비밀 재고조사를 수행하고, 미사용/만료 키는 즉시 폐기.

### 13.2 접근 제어 & 네트워크
- IAM Role 기반 최소 권한 원칙: Airflow/Pipeline/Brain/Core 각각 전용 Role 사용, S3/DB에 세분화된 정책 부여.
- VPC 보안 그룹: FastAPI/Next.js는 ALB를 통해 443만 허용, Airflow Webserver는 VPN/IP Allowlist(`API_ALLOWED_IPS`)로 제한.
- Bastion/SSH 접근 금지, 필요 시 SSM Session Manager 사용.

### 13.3 데이터 보호 & 감사
- 모든 S3 버킷, PostgreSQL, EBS는 KMS 암호화, 데이터 이동 시 TLS 1.2 이상.
- CloudTrail/CloudWatch Logs로 API 호출 및 IAM 활동을 1년 보관, Athena로 감사 쿼리.
- 개인정보(계좌/주문)는 6개월 후 익명화, 삭제 로그는 Counsel/Sentinel이 서명.

### 13.4 취약점 관리 & 규정 준수
- 주 1회 자동 취약점 스캔(Trivy/Snyk) + 월 1회 수동 점검, 결과는 Guardian/Security Slack 채널 공유.
- 크롤링/데이터 사용은 Counsel이 유지하는 ToS/라이선스 리스트에 따라 허용 여부 결정, 변경 시 Decision Board 기록.
- 보안 인시던트 발생 시 30분 이내 Maestro에 보고하고, 24시간 내 RCA/완화 조치 문서를 Scribe가 게시.

## 14. 단계별 마일스톤 (초안)
| 주차 | 작업 | 담당 |
| --- | --- | --- |
| W1 | 상세 기획, ERD, 데이터 소스 인증 | Planner, Architect |
| W2 | Airflow DAG PoC, 모델 프로토타입 | Pipeline, Brain |
| W3 | FastAPI 기본 API, DB 연동 | Core |
| W4 | Frontend Dashboard/History 초안 | Interface, Canvas |
| W5 | AI 리포트 LLM 통합, XAI 시각화 | Brain, Canvas |
| W6 | 배치 모니터링, 텔레그램 알림, QA | Guardian, Deployer |
| W7 | 전체 E2E 테스트, 문서화, 배포 | Maestro, Scribe |

## 15. 단계별 상세 스펙 & 설계
### 15.1 데이터 수집·크롤링 확장 (Pipeline/Architect/Sentinel)
- **목표**: KIS + 멀티 크롤링 + 공개 API를 통합해 시뮬레이션까지 가능한 데이터 레이크 확보.
- **세부 작업**
  1. 소스 인벤토리 정의: API, RSS, HTML 크롤링, 파일 업로드 등 30+ 채널 메타데이터 카탈로그화.
  2. 크롤러 템플릿: 정적/동적/폼기반 3종 파이프라인, 헤더/프록시/캡차 대책 포함.
  3. 스케줄링: Airflow `di_data_harvest`에서 SLA·재시도·우선순위 큐 설정, 실패 시 Sentinel 알림.
  4. 정제 규칙: 스키마 검증, 언어 감지, 중복 제거, 토픽 태깅, 임베딩 파이프라인 연결.
  5. 저장: S3 Raw, PostgreSQL `raw_sources`, pgvector 인덱스, 메타데이터 카탈로그(Glue/Athena) 구성.
- **산출물**: 데이터 카탈로그 문서, 크롤러 코드, SLA/알림 정의서, 보안/윤리 체크리스트.

### 15.2 데이터 파이프라인 & 피처 스토어 (Pipeline/Insight/Brain)
- **목표**: 실시간/배치 데이터를 정규화하여 전략 엔진과 시뮬레이션에서 재사용 가능한 피처 제공.
- **세부 작업**
  1. ETL 계층 분리: Raw → Bronze → Silver → Gold 레이어 정의 및 스키마 버저닝.
  2. 피처 정의: 가격·거래량·수급·거시·감성 피처와 라벨(수익률, 변동성, 이벤트) 스키마.
  3. 피처 백필/재계산 로직, 슬라이딩 윈도우 처리, 결측/비정상치 처리 규칙 작성.
  4. 피처 스토어 API: Feast 기반 서비스로 온라인(실시간 슬롯) / 오프라인(시뮬레이션) 서빙.
  5. 품질 모니터링: Great Expectations/DBT 테스트, 데이터 지연 알림.
- **산출물**: 피처 스펙 시트, ETL DAG 다이어그램, 품질 테스트 케이스, API 스펙.

### 15.3 AI 전략 엔진 & 시뮬레이션 (Brain/Insight/Guardian)
- **목표**: 멀티 모델 조합(시계열 + 감성 + RL)과 시뮬레이션 엔진으로 전략을 평가·선택.
- **세부 작업**
  1. 모델 포트폴리오: ARIMA/Prophet, Temporal Fusion Transformer, BERT 감성, PPO/Deep Hedging 등 후보 세트 정의(학습 윈도우 12M, 검증 1M 고정).
  2. 학습 파이프라인: 데이터 스플릿, Hyperopt 실험 관리, 멀티 GPU/분산 학습 정책.
  3. 전략 조합 로직: 시그널 앙상블, 리스크 패리티, 포지션 사이징, 이벤트 룰 엔진.
  4. 시뮬레이션 엔진: 주문 체결 모델, 수수료/슬리피지 반영, 멀티 시나리오(불/약/변동) 평가.
  5. 검증/승격: Guardian가 Acceptance Criteria(Sharpe>1.2 등) 확인, Mediator 승인 후 배포.
- **산출물**: 모델 카드, 시뮬레이션 리포트, 전략 룰북, 승인 기록.

### 15.4 Backend & Frontend 통합 (Core/Interface/Canvas)
- **목표**: 리포트 API·웹 대시보드·실시간 스트림을 연결해 사용자 경험 구현.
- **세부 작업**
  1. FastAPI 서비스: 도메인 모듈(Reports/History/Batch/Telemetry), 단일 사용자 RBAC, 캐시, Rate Limit (모든 엔드포인트 REST/JSON 고정).
  2. WebSocket 전용 실시간 채널: 슬롯 완료 이벤트 push, 텔레그램 링크 생성(SSE 미사용).
  3. Next.js 라우팅: Dashboard/History/Batch Monitor/Settings, React Query 캐싱 전략.
  4. D3 시각화: Timeline/Heatmap/Performance Chart, 반응형 + 접근성 지표 준수, 데이터는 FastAPI 집계 API에서만 수급해 프런트 계산 최소화.
  5. 다운로드/엑스포트: Markdown/PDF 생성기, S3 아카이브 연동.
- **산출물**: API 스펙 문서, 컴포넌트 컷(Storybook), UX 플로우, 통합 테스트 케이스.

### 15.5 MLOps & 운영 (Deployer/Guardian/Sentinel/Scribe)
- **목표**: 모델/데이터/서비스 전 과정을 모니터링하고 자동 재학습·감사 지원.
- **세부 작업**
  1. Model Registry & CI/CD: MLflow/SageMaker 파이프라인, GitHub Actions 연동.
  2. 모니터링: Prometheus + Grafana + CloudWatch 지표, 이상 탐지 알람.
  3. 재학습 DAG: `di_model_refresh` 세부 태스크(데이터 준비 → 학습 → 평가 → 배포 → 롤백).
  4. 감사/문서화: Scribe가 실행 로그, 결정 기록, 규제 대응 레포트 유지.
  5. 보안/컴플라이언스: 키 관리, 접근제어, 데이터 사용 정책 체크리스트.
- **산출물**: MLOps 런북, 알람 시나리오, 감사 로그 정책, 보안 가이드.

## 16. 다음 액션
1. Planner: 화면/기능 상세 스펙 문서화.
2. Architect: ERD 상세 다이어그램 + 마이그레이션 스크립트 초안 + 크롤링 데이터 레이크 스키마 정의.
3. Pipeline: Airflow DAG 스캐폴드, KIS 인증 모듈, 크롤러 PoC 및 재시도 로직 개발.
4. Core: FastAPI 프로젝트 부트스트랩, `.env` 로딩/보안 모듈 구현.
5. Interface/Canvas: 디자인 시안 + D3 프로토타입.
6. Brain: 모델 학습 데이터 정의, RAG 컨텍스트 스키마, 시뮬레이션 엔진 초안 작성.

## 17. Decision Board (v0.2)
| 결정 항목 | 상태 | 세부 내용 | 승인자 |
| --- | --- | --- | --- |
| 대상 종목 범위 | 확정 | KOSPI 전 종목 + S&P500 종목을 필수 커버, 기타 시장은 보조 | Maestro |
| 데이터 윈도우 | 확정 | 학습 12개월 + 검증 1개월, 슬라이딩 방식 | Maestro |
| 오케스트레이션 스택 | 확정 | Airflow 단일 스택에서 모든 배치/크롤링/재학습 실행 | Maestro |
| 실시간 프로토콜 | 확정 | REST + WebSocket만 사용 (GraphQL/SSE 금지) | Maestro |
| Feature Store 방식 | 확정 | Feast + pgvector 조합 | Maestro |
| 단일 사용자 정책 | 확정 | Owner 1명, 추가 RBAC 없음 | Maestro |
| LLM Fact-check | 확정 | 규칙 기반 수치 검증 + QA 모델 교차 검사, Guardian가 룰세트 유지(§8) | Maestro/Guardian |
| 문서/로그 게시 위치 | 확정 | `/docs` 구조 및 Decision Board(§18) 준수, 변경 24h 내 업데이트 | Maestro/Scribe |
| 보안 비밀 저장소 | 확정 | AWS Secrets Manager + KMS 로테이션, 로컬 암호화 파일만 허용(§13) | Sentinel |
| SLA 정책 | 확정 | §12.3 지표 준수, 미달 시 Incident 기록 | Maestro |
| 문서 리뷰 프로세스 | 확정 | PR + Scribe/Planner 동시 승인, 주 1회 릴리스 노트 | Planner/Scribe |

## 18. 문서 거버넌스 & Decision Workflow
### 18.1 저장소 구조
```
/docs
  /blueprint        # Master 설계 문서(본 파일)
  /spec             # 기능/화면/API 세부 명세
  /ops              # 런북, SLA, 보안 정책
  /decisions        # Decision Board 스냅샷(RFC-style)
/logs
  /batch            # Airflow 실행 요약(.md)
  /incidents        # RCA/장애 보고서
```
- 모든 Markdown 파일은 날짜-슬롯 포맷(`YYYYMMDD-slot.md`) 또는 버전 태그(`v1.2`)를 포함.

### 18.2 변경 프로세스
1. 변경 제안 → Issue 생성 & Decision Board 후보 항목 추가.
2. 관련 에이전트가 PR 작성, **Scribe + Planner** 2인 승인 후 `main` 병합.
3. 병합 24시간 이내 `/docs` 갱신 및 Decision Board 상태 업데이트.
4. 주요 변경은 텔레그램/Slack `#di-notice` 채널에 요약 공유.

### 18.3 Decision Board 운영
- Scribe가 주간 회의 직후 최신 상태를 `Project_Blueprint.md`와 `/docs/decisions/YYYYWW.md`에 동기화.
- 상태 값: `제안중 / 진행중 / 확정 / 보류 / 폐기`. 보류 이상 항목은 사유와 담당자 필수.
- 미결 항목은 2주 안에 책임 에이전트를 지정하고, 마감 초과 시 Mediator가 중재.

### 18.4 감사 & 리뷰
- Planner는 2주마다 문서 일관성 리뷰, Guardian은 SLA/RCA 문서 최신 여부 확인.
- Counsel은 분기마다 `/docs/ops/legal`을 검토하고 결과를 Decision Board에 기록.
- Scribe는 주 1회 릴리스 노트와 문서 변경 Summary를 발행.

## 19. Maestro 피드백 (2023-11-22)
1. **SLA 실행**: §12.2~12.3을 즉시 적용, Guardian/Deployer가 KPI 대시보드·알림 구성. SLA 미달 시 Decision Board Incident 항목 필수 기록.
2. **보안 거버넌스**: Secrets Manager+KMS, IAM Role 분리, 30일 로테이션, CloudTrail/Athena 감사 흐름 확정. Sentinel은 월간 비밀 재고 및 주간 크롤러 정책 검증, Counsel은 ToS/라이선스 리스트 유지.
3. **문서 체계**: `/docs` 구조, PR 2인 승인, 24h 내 갱신, 주간 Decision Board 동기화를 준수. Scribe 주 1회 릴리스 노트, Planner 2주 리뷰, Mediator가 미결(2주 초과) 중재.
4. **UX 결정**: 히스토리 비교 2슬롯 고정, 텔레그램 알림 상위 3건, 모바일 대시보드는 Timeline+상위 카드 축약. TimelineBar에 6슬롯+수동 배지, D3 데이터는 백엔드 집계 API만 사용.
5. **데이터/모델 범위**: KOSPI+S&P500, 학습 12M/검증 1M, Feast 기반 피처 스토어 확정. Guardian은 Sharpe/Drift 기준으로 재학습 게이트 운영.
6. **LLM Fact-check**: 규칙 기반 수치 검증 + QA 모델 교차 검사. Brain/Guardian이 룰세트 문서화(`/docs/spec/llm-factcheck.md`).
7. **추가 미결**: Redis 사용, Glue 비용 한도, API Rate Limit 등은 각 담당이 다음 스프린트에 제안안을 상정해 Decision Board 경유.

---
문서는 Maestro 운영 원칙에 따라 지속 업데이트됩니다.
