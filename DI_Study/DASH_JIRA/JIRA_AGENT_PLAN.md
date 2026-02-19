# JIRA 기반 에이전트 작업 문서

## 1. 목적
- JIRA 티켓 생성 즉시 핵심 내용을 요약하고 주제를 판별하여 담당 조직/담당자를 자동 추천한다.
- 추천된 내부 담당자에게 1차 알림 메일을 발송해 빠르게 업무를 핸드오프한다.
- 과거 유사 케이스 처리 방법을 함께 공유해 실무자가 즉시 참고할 수 있도록 한다.
- 모델링 데이터와 테스트 데이터를 명확히 분리해 품질을 측정한다.

## 2. 데이터 구성
- 원본: `DATA/jira_data_gta/*.csv`
- 테스트 데이터: `JIRA 2025ыЕД_4Q.csv`
- 모델링 데이터: 나머지 9개 CSV
- 분리 스크립트: `split_dataset.py --dedupe`
- 산출물: `DATA/processed/dataset_modeling.csv`, `DATA/processed/dataset_test.csv`

## 3. 처리 파이프라인 개요
1. **수집/정제**
   - Jira Webhook 혹은 스냅샷 CSV → 공통 스키마 통합.
   - Issue key 기준 최신 스냅샷 유지.
2. **번역**
   - Summary/Description/Comment를 다국어 번역 API로 변환.
   - 원문, 번역문, 언어 감지를 함께 저장하여 감사 가능성 확보.
3. **요약 & 주제 판별**
   - LLM 프롬프트로 “요약 / 요구사항 / 위험 / SLA / 추천 담당 조직” 섹션 생성.
   - Slot/TAXO 매핑을 통해 최적 담당자 후보 리스트를 작성한다.
4. **케이스 임베딩 & 검색**
   - 과거 해결 티켓을 임베딩 후 벡터 스토어(Pinecone/FAISS) 저장.
   - 신규 티켓 임베딩과 KNN 검색으로 Top-K 케이스, 실행 요약 생성.
   - 추천 케이스 ID, 신뢰도 점수, 후속 액션을 Jira 코멘트/메일에 첨부.
5. **담당자 할당 & 메일 알림**
   - 주제/카테고리/지역/부서 룰을 이용해 최종 담당자를 선정하고 1차 알림 메일을 발송한다.
   - 메일에는 요약, 추천 담당자, SLA, 케이스 참고 링크가 포함된다.
6. **로그/모니터링**
   - 번역·요약·케이스 검색·담당자 추천·메일 발송 단계별 성공/실패 기록.
   - SLA Sentinel이 지연 시 재시도 및 수동 검토 알림 제공.

## 4. 주요 에이전트와 역할
| 에이전트 | 역할 |
| --- | --- |
| Triage Agent | 신규 티켓 필수 필드 검증, 담당자 추천, 라우팅 제안 |
| Translator/Summarizer | 다국어 번역, 핵심 요약, 메일 템플릿 작성 |
| Routing Agent | 주제/지역/부서 룰·ML 기반으로 담당자 후보 산출, 배정 로그 관리 |
| Case Matcher | 벡터 검색으로 유사 케이스 탐색 및 실행 요약 |
| SLA Sentinel | 응답/해결 SLA 위반 예상 시 알림 및 Escalation 트리거 |
| Ops Insights Agent | 일/주간 트렌드 리포트 자동화 |

## 5. 개발 로드맵
1. `split_dataset.py` 파이프라인을 자동화하여 최신 CSV가 들어올 때마다 데이터셋을 재생성.
2. Modeling 데이터로 임베딩 인덱스 구축 → 유사 케이스 검색 정확도 검증.
3. 번역·요약 모듈과 메일 발송 모듈을 결합한 MVP 구축.
4. Jira API/Webhook 연동 및 보안 정책(토큰 저장, 감사 로그) 정립.
5. SLA Sentinel 및 Ops Insights 자동 리포트 추가.

## 6. 검증 체크리스트
- [ ] 모델링/테스트 분리 재현 가능 여부 확인.
- [ ] 번역 품질과 요약 정확도 수동 점검.
- [ ] 유사 케이스 추천 정확도(정성 평가)와 신뢰도 임계값 정의.
- [ ] 메일 전송 실패 시 재시도 및 예외 처리 로직 구현.
- [ ] Jira 코멘트 자동 삽입 전 권한/보안 검토 완료.

## 7. 사전적 요약 구조 정의
### 주요 카테고리
- **문의 유형**: {태깅 요청, 유지보수, 신규 기능, 분석 지원, 운영 이슈 등}
- **배경/맥락**: {캠페인명, 지역/국가, 채널, 디바이스, 의존 시스템, 출시 일정 등}
- **원인/문제 유형**: {데이터 누락, 스크립트 오류, 승인 지연, 3rd Party 요구, SLA 위반 위험 등}
- **요청 액션**: {검수, 수정 배포, 승인, 모니터링, 고객 응답, 장애 전파 등}
- **결과/상태**: {해결, 보류 사유, 에스컬레이션 대상, 추가 정보 필요}

### 구조화 방식
1. 티켓 생성 시 LLM 혹은 룰 기반으로 위 카테고리 별 슬롯을 채워 JSON Schema 형태로 저장.
2. 사전 정의 세트를 taxonomy 테이블로 관리하여 신규 값 발생 시 검토 후 승인.
3. 요약 메일/코멘트는 `문의 유형 → 배경 → 원인 → 요청 액션 → 현재 상태` 순으로 고정된 템플릿을 사용.
4. Case Matcher가 동일 슬롯 조합을 인덱싱 키로 활용하여 더 정확한 매칭을 수행.
5. Ops Insights 리포트에서도 같은 카테고리를 사용해 일관된 통계를 제공한다.

## 8. 백엔드/프론트엔드 설계
### 백엔드
- **API 게이트웨이**: REST/GraphQL로 티켓 이벤트 수신, 번역/요약 요청, 케이스 검색, 메일 전송을 통합하고 OAuth2/JWT 기반 인증을 적용한다.
- **데이터 레이어**:  
  - RDB(PostgreSQL): 티켓 메타, 번역 결과, 요약/메일 로그, 카테고리 taxonomy, 에이전트 상태 기록.  
  - Object Storage(S3 등): 원문/번역 첨부, 학습 덤프.  
  - Vector Store(PGVector/FAISS): 임베딩 인덱스 및 케이스 피쳐 저장.
- **서비스 모듈**: Ingestion Service(Jira Webhook·CSV 로더), NLP Service(번역/요약/슬롯 추출), Routing Service(주제 판별 및 담당자 추천), Case Service(임베딩·유사도 검색), Notification Service(메일·Slack 발송), Orchestrator(스케줄·SLA Sentinel·재시도 큐).  
- **보안/감사**: 비밀키는 `.env`→Secrets Manager로 이동, 모든 자동 액션 로그를 Audit 테이블에 저장, Jira 쓰기 권한은 역할별 토큰으로 분리.

#### 백엔드 궤적(Workflow)
1. **API 게이트웨이**가 Webhook/프론트 요청을 수신 → 인증/권한 확인 후 메시지 브로커에 이벤트 게시.
2. **Ingestion Service**가 이벤트를 정규화하여 `issues` 테이블에 upsert, 파일 첨부는 Object Storage에 저장하고 메타데이터를 연결.
3. **Orchestrator**는 워크플로우 정의(Temporal/Celery)로 각 단계 Task를 스케줄링:  
   - Translation Task → NLP Service gRPC 호출 → 결과를 `summaries`에 기록.  
   - Slot/Taxonomy Task → 룰 엔진 호출, 누락 시 재질문 이벤트 생성.  
   - Routing Task → Routing Service가 주제/우선순위 기반 담당자 추천 후 `assignments` 테이블에 저장.  
   - Case Matching Task → Vector Store 질의 결과를 `cases_recommendations` 테이블에 저장.  
   - Notification Task → Notification Service로 전달해 메일/Slack 발송(요약 + 추천 담당자 + 케이스 링크 포함).
4. **Notification Service**는 템플릿 렌더링, SMTP/API 호출, 상태를 `notifications` 테이블에 기록하고 실패 시 재시도 큐에 넣는다.
5. **SLA Sentinel**은 Orchestrator의 보조 워커로 `issues`와 Task 상태를 모니터링해 지연/실패 이벤트를 Ops Insights 및 Alerting 채널로 전달한다.
6. **Ops Insights Service**는 배치/스트리밍 ETL로 PostgreSQL→Parquet/DuckDB에 지표를 적재하고, 프론트 대시보드와 리포트 API를 제공한다.
7. **Audit/Observability Stack**이 모든 API 호출, Task 전환, 외부 통신을 추적하여 Trace ID로 연결, 프론트의 트러블슈팅 패널과 연동된다.

### 프론트엔드
- **대시보드**: 실시간 생성/해결 트렌드, SLA 위험 지표, On Hold 포켓, 알림 성공률을 카드형으로 표시.
- **티켓 상세 뷰**: 원문/번역 토글, “문의/배경/원인/액션/상태” 요약, 추천 케이스 카드(유사도·과거 조치), 에이전트 액션 타임라인.
- **담당자 배정 패널**: 추천 담당자/백업 리스트, confidence, 업무량 지표, “배정 확정/재추천” 버튼, 메일 발송 상태 표시.
- **케이스 라이브러리**: 필터·검색·벡터 유사 결과, 케이스 태깅/승인 UI.
- **설정 화면**: 번역 엔진 선택, 수신자 규칙, SLA 임계값, 에이전트 상태/재처리 제어.
- **보고서 뷰**: 주간/월간 Ops Insights, 담당자별 처리 속도, On Hold 사유 분포 등 다운로드 가능한 리포트 제공.

#### 화면 예시
1. **실시간 대시보드**
   - 상단 KPI 카드: “금일 생성”, “금일 해결”, “SLA 위험 티켓”, “메일 실패”.
   - 중앙 라인 차트: 최근 7일 생성/해결 추이.
   - 우측 테이블: On Hold 티켓 목록(문의 유형, 경과일, 담당자, 재시도 버튼).
   - 하단 패널: 알림 로그(시간, 대상, 상태)와 번역/요약 파이프라인 상태 표시등.
2. **티켓 상세/추천 케이스**
   - 좌측: 티켓 헤더(우선순위, 상태, SLA 타이머), 원문/번역 탭.
   - 중앙: 구조화 요약 카드(문의/배경/원인/요청 액션/현재 상태) + 첨부 다운로드.
   - 우측 상단: 추천 담당자 카드(주요 후보 2~3명, 근거 태그, 업무량, 배정 버튼)와 메일 발송 로그.
   - 우측 하단: 추천 케이스 카드 3개(유사도 %, 과거 조치 요약, 담당 팀, “플레이북 보기” 버튼).
   - 하단: 에이전트 액션 타임라인(번역→요약→메일→케이스)과 오퍼레이터 노트 입력.
3. **케이스 라이브러리**
   - 상단 필터 바: 문의 유형, 지역, 원인, 결과, 날짜 범위.
   - 리스트: 케이스 제목, 요약, 마지막 사용 횟수, 신뢰도 배지, “승인/거절/편집” 버튼.
   - 상세 슬라이드 패널: 전체 해결 히스토리, 첨부 링크, 태그 관리, 학습 피드백 입력.
4. **설정/운영 패널**
   - 탭: 템플릿 관리, 수신자 룰, SLA 설정, API 키/토큰, 에이전트 상태.
   - 각 탭에는 수정 이력과 롤백 버튼, 테스트 전송 기능이 포함.
5. **보고서 뷰**
   - 월간 리포트 카드: 생성/해결/백로그/On Hold 비율, 담당자별 처리 속도 히트맵.
   - 다운로드 버튼: CSV/PDF.
   - Insight Spotlight: “이번 달 가장 많은 원인”, “SLA 위험 구간” 자동 분석 문장.
6. **문서 질의 LLM 위젯**
   - 좌측 패널에서 현재 작업 문서/플레이북/정책을 선택 후 질문 입력.
   - RAG 파이프라인이 `JIRA_AGENT_PLAN.md`와 케이스 문서를 인덱싱하고, 답변과 참조 섹션 링크를 반환.
   - 답변 이력은 오퍼레이터 노트와 함께 저장되어 반복 질문을 줄이고, “응답 재생성/평가” 버튼 제공.

## 9. 테스트 데이터 스트림 시뮬레이션
- 스크립트: `simulate_test_stream.py`
- 입력: 기본적으로 `DATA/jira_data_gta/JIRA 2025ыЕД_4Q.csv`를 사용하며 `--csv`로 교체 가능.
- 기능:
  1. 각 행을 `jira.issue.created` 형태의 JSON 이벤트로 만들어 표준 출력 또는 지정한 `--post-url` HTTP 엔드포인트에 POST.
  2. `--interval`, `--jitter`로 이벤트 간격을 제어하여 실제 Webhook 유입처럼 시뮬레이션.
  3. `--limit`, `--start-index`로 테스트 범위를 조절하고, 전송 결과를 로깅.
- 용도: AIops 파이프라인(번역·요약·메일·케이스 추천)이 신규 티켓 유입 시 어떻게 작동하는지 자동화 테스트에 활용.

## 10. 오케스트라 에이전트 아키텍처
### 10.1 시스템 아키텍처
- **Event Ingress Layer**: Jira Webhook, 테스트 시뮬레이터, 배치 CSV 로더가 모두 Kafka/NATS 등 메시지 버퍼로 이벤트를 푸시한다.
- **Orchestrator Agent**: Temporal/Celery 기반으로 단계별 워크플로우(수집→번역→요약→케이스 매칭→알림)를 상태 머신으로 관리. 각 단계 실패 시 재시도, 일정 시간 초과 시 SLA Sentinel 호출.
- **Service Mesh**: Translator/NLP, Case Matcher, Notification, Ops Insights 등 마이크로서비스가 gRPC/REST로 연결되며, Orchestrator는 서비스 디스커버리와 Circuit Breaker(Envoy/Istio)를 사용해 안정성을 높인다.
- **Control Plane**: 설정·템플릿·룰 엔진을 제공하는 Admin API와, 모니터링/알람 스택(Prometheus+Grafana)으로 에이전트 성능을 추적한다.

### 10.2 데이터 아키텍처
- **Operational DB (PostgreSQL)**  
  - `issues`: 최신 스냅샷, 상태, SLA 타임스탬프.  
  - `summaries`: 번역/요약 결과, 슬롯 구조(JSONB).  
  - `assignments`: 주제/룰 기반 추천 담당자, confidence, 확정 여부, 핸드오프 이력.  
  - `notifications`: 메일/Slack 로그, 재시도 상태.  
  - `cases`: 플레이북 메타데이터, 승인 이력.  
  - `workflows`: 오케스트라 인스턴스 상태(진행 단계, 실패 이유, 타임라인).
- **Data Lake / Feature Store**  
  - Parquet/DuckDB로 장기 저장(모델링·리포트).  
  - Vector Store는 Issue embedding, Case embedding, Context metadata를 관리하고, Issue key로 관계를 유지한다.
- **Metadata / Taxonomy**  
  - 문의 유형·배경·원인 등 사전 정의 값을 별도 테이블로 관리하고, 슬롯 추출 시 FK로 연결한다.
- **Audit & Observability**  
  - 모든 API 호출·자동 액션을 Audit 로그 테이블에 기록.  
  - 이벤트 ID 기준으로 Trace/Span을 남겨 디버깅 가능하게 한다.

### 10.3 파이프라인 흐름
1. **Event Intake**: Jira Webhook 혹은 시뮬레이터가 `event_raw` 토픽에 이벤트를 발행.
2. **Normalization Task**: Orchestrator가 이벤트를 잡아 공통 스키마로 정제하고 DB에 저장.
3. **Translation/Slot Extraction Task**: NLP 서비스 호출 → 결과를 `summaries` 테이블에 기록.
4. **Routing Task**: Slot/Taxonomy 결과와 룰/ML 모델을 이용해 담당자 후보를 산출, `assignments`에 로그를 남기고 재배정 이벤트를 처리.
5. **Case Matching Task**: 임베딩 생성 → Vector Store 검색 → 추천 결과를 DB 및 이벤트 스트림에 저장.
6. **Notification Task**: 템플릿 렌더링 후 메일/Slack 전송(요약·SLA·추천 담당자·케이스 링크 포함), 메시지 ID와 상태를 `notifications`에 기록.
7. **SLA Monitoring**: Orchestrator가 주기적으로 `issues`와 워크플로우 상태를 확인 → 지연 시 Sentinel Alert 발행.
8. **Ops Insights ETL**: 배치 작업이 `issues`, `summaries`, `assignments`, `notifications` 데이터를 Parquet로 적재해 리포트/모델 학습에 사용.
9. **Feedback Loop**: 운영자가 프론트 UI에서 추천 결과를 승인/거절하면 그 기록이 케이스 학습/랭킹과 Routing 모델 개선에 반영된다.

> 아키텍처 전반은 모듈 간 느슨한 결합을 유지하여 신규 서비스(예: 자동 코드 배포 알림)를 추가해도 Orchestrator 워크플로우 정의만 업데이트하면 되도록 설계한다.

## 11. 인프라 구성
### 11.1 환경 계층
- **개발/스테이징/프로덕션** 3계층 운영, 각 환경은 독립된 클러스터와 Secrets Store를 사용.
- IaC(Terraform or Pulumi)로 네트워크·클러스터·데이터베이스·스토리지 리소스를 선언적 관리.

### 11.2 핵심 리소스
- **Kubernetes 클러스터**: Orchestrator, NLP, Case, Notification, Ops Insights 마이크로서비스를 컨테이너로 배포. HPA/PodDisruptionBudget으로 가용성 확보.
- **Message Broker**: Kafka/NATS로 이벤트 스트림 관리, Partition을 티켓 유형/지역 기준으로 분리해 확장.
- **Database Layer**:  
  - PostgreSQL (HA 구성: Patroni 또는 RDS/Aurora Multi-AZ)  
  - Redis(캐시·큐), MinIO/S3(파일 저장), Vector DB(PGVector Cluster 혹은 Pinecone).
- **Observability Stack**: Prometheus + Grafana + Loki + Tempo로 메트릭/로그/트레이스 수집, Alertmanager로 SLA 경보 발송.
- **CI/CD**: GitHub Actions/GitLab CI가 Docker 빌드 → 보안 스캔 → Helm 배포. ArgoCD/Flux로 GitOps 운영 가능.
- **Secrets & Key Management**: HashiCorp Vault 혹은 AWS Secrets Manager로 API 키/SMTP 자격 증명 관리, 서비스 계정은 IAM 역할로 부여.
- **Edge & 보안**: API Gateway(Envoy/Kong) + WAF, TLS 종단, OIDC 연동. 네트워크는 VPC 내 서브넷을 분리하고, Private Subnet에서 DB/브로커 운영.

### 11.3 운영 정책
- Blue/Green 혹은 Canary 배포로 Orchestrator/AI 모듈 업데이트 시 위험 최소화.
- 백업/복구: PostgreSQL PITR, Object Storage 버전 관리, Vector Store 스냅샷 자동화.
- 비용 모니터링: 주요 리소스별 태깅, 주간 코스트 리포트 대시보드화.
- 규정 준수: 감사 로그를 장기 보관(예: 1년), 접근 제어는 RBAC·Audit Trail로 관리.

## 12. 담당자 추천 및 핸드오프 시스템
1. **주요 내용 요약/판별**: NLP Service가 문의 유형·배경·원인 슬롯을 채운 뒤 Routing Service에 전달한다.
2. **담당자 추천 로직**  
   - 룰 기반: 지역/제품/이슈 타입별 고정 오너 매핑.  
   - ML 보강: 과거 처리자 히스토리, 워크로드, SLA 성과를 피처로 사용해 추천 점수 산출.  
   - 실패 시 백업 담당자 리스트와 팀 메일링 그룹을 반환.
3. **메일링 & 케이스 공유**: Notification Service가 추천 담당자에게 1차 메일을 보내며, 요약/주제/우선순위/SLA와 함께 Top-K 케이스 링크, 처리 방법 하이라이트를 포함한다.
4. **확인 및 재배정**: 프론트 담당자 패널에서 추천을 수락·거절할 수 있고, 사유가 `assignments` 테이블에 기록되어 모델 개선에 활용된다.
5. **모니터링/리포트**: Ops Insights는 배정 정확도, 재배정 비율, 메일 성공률을 추적하며, SLA Sentinel이 미확인 티켓이나 장기 On Hold 담당자를 알림으로 노출한다.
6. **지속 개선**: Feedback Loop는 담당자 피드백, 케이스 성공 여부, 처리 시간 등을 수집해 룰/모델, 추천 설명 문구, 메일 템플릿을 주기적으로 업데이트한다.

## 13. Routing 룰/모델 및 메일 템플릿
### 13.1 Routing 설계
1. **룰 엔진(1차 후보)**  
   - 키 조합: `문의 유형 × 지역 × 제품 라인 × SLA 등급`.  
   - 룰 테이블: Jira 사용자/그룹 ID, 백업 담당자, 팀 DL, 근무 시간, 휴먼 승인 여부.  
   - 장점: 테이블 수정만으로 조직 변화에 빠르게 대응.
2. **ML 보강(Top-N 추천)**  
   - 라벨: 과거 Issue의 실제 처리자/팀.  
   - 피처: 슬롯 정보(문의/배경/원인), 케이스 임베딩, 처리자 워크로드(열린 티켓 수, 평균 처리 시간, SLA 성공률), 시간대.  
   - 모델: 다중 클래스 혹은 랭킹 모델로 Top-N 후보+confidence를 생성, 룰 결과와 병합해 설명 가능한 리스트를 구성.
3. **설명/로그 관리**  
   - “근거: 지역=북미, 제품=D2C, 최근 처리 5건”과 같은 태그를 UI/메일에 표기.  
   - `assignments` 테이블에 룰/모델 점수, 선택 이유, 재배정 사유를 저장해 재학습 자료로 활용.

### 13.2 메일 템플릿 초안
```
[요약] {한 줄 요약}
[주요 내용] 문의 유형 / 배경 / 원인 / 요청 액션
[SLA] 우선순위, 응답·해결 마감, 현재 경과 시간
[추천 담당자] {Primary 담당자} (근거: 지역=, 제품=, 과거 처리 n건)
[유사 케이스]
  - {Case-123}: 해결 방식 요약, 링크
  - {Case-098}: 해결 방식 요약, 링크
[다음 조치] 권장 액션 및 Jira 링크
```
- 한국어/영어 병행 표기 옵션 제공.  
- 메일 하단에 “배정 확정/재배정 요청” 버튼과 Ops 문서/플레이북 링크 포함.  
- Notification Service는 생성된 템플릿을 금칙어/민감정보 필터로 검증한 뒤 발송하고, 결과를 `notifications`·`assignments` 로그에 남긴다.

> 주의: 실행 가능 파일을 만들지 않는다. 모든 스크립트는 문서화된 워크플로우를 따르며, 배포 전에 수동 검토를 거친다.
