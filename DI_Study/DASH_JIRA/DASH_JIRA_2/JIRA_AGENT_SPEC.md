# JIRA 에이전트 상세 명세서

## 1. 데이터 스키마 및 분류 체계

### 1.1 데이터베이스 스키마 (PostgreSQL)

구조화된 이슈 데이터는 관계형 데이터베이스(PostgreSQL)에 저장하며, 유연한 커스텀 필드와 LLM 출력 결과는 `JSONB` 컬럼을 사용합니다.

#### `issues` 테이블
Jira 티켓의 핵심 정보와 현재 상태를 저장합니다.

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| `issue_key` | VARCHAR(20) | PK, 예: "GTA-10013" |
| `issue_id` | BIGINT | Jira 내부 ID |
| `summary` | TEXT | 티켓 제목 |
| `description` | TEXT | 티켓 본문 (원본) |
| `status` | VARCHAR(50) | 현재 Jira 상태 (예: "Closed", "In Progress") |
| `issue_type` | VARCHAR(50) | 예: "3rd party Tag Request", "Bug" |
| `priority` | VARCHAR(20) | 예: "Critical", "Major" |
| `created_at` | TIMESTAMP | 생성 일시 |
| `updated_at` | TIMESTAMP | 수정 일시 |
| `assignee_id` | VARCHAR(100) | 현재 담당자 이메일/ID |
| `reporter_id` | VARCHAR(100) | 보고자 이메일/ID |
| `custom_fields` | JSONB | 매핑된 모든 커스텀 필드 저장 (지역, 국가 등) |
| `analysis_result` | JSONB | LLM 분석 결과 (요약, 원인 등) |

#### `comments` 테이블
문맥 파악을 위한 대화 이력을 저장합니다.

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| `id` | SERIAL | PK |
| `issue_key` | VARCHAR(20) | `issues` 테이블 FK |
| `author_id` | VARCHAR(100) | 작성자 ID |
| `body` | TEXT | 댓글 내용 |
| `created_at` | TIMESTAMP | 작성 일시 |
| `is_internal` | BOOLEAN | 내부 메모 여부 |

#### `embeddings` 테이블 (pgvector)
의미 기반 검색(Semantic Search)을 위한 벡터 임베딩을 저장합니다.

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| `issue_key` | VARCHAR(20) | `issues` 테이블 FK |
| `embedding_type` | VARCHAR(20) | 'summary', 'full_context', 'resolution' |
| `vector` | VECTOR(1536) | OpenAI text-embedding-3-small 차원 |
| `model_version` | VARCHAR(50) | 예: "v1.0" |

### 1.2 분류 체계 (Taxonomy)

데이터셋을 기반으로 다음과 같은 표준 분류 값을 정의합니다.

**지역 / 국가 (Region / Country)**
- `Region`: NA (북미), EU (유럽), CIS (독립국가연합), SEA (동남아), MENA (중동/아프리카) 등
- `Country`: US, UK, DE, FR, KR 등

**이슈 카테고리 (추론됨)**
- `Tagging Request`: 서드파티 태그 구현 요청
- `Data Discrepancy`: GA와 백엔드 데이터 불일치
- `Access Request`: 툴(Adobe, GTA) 접근 권한 요청
- `Bug Report`: 기능 오류 보고
- `Feature Request`: 새로운 대시보드/리포트 기능 요청

**원인 (Root Cause - LLM 도출)**
- `Configuration Error`: 설정 오류
- `Code Defect`: 코드 결함
- `External Dependency`: 외부 벤더 이슈
- `User Error`: 사용자 실수
- `Data Delay`: 데이터 지연

### 1.3 LLM 분석 결과 JSON 스키마

LLM(요약 에이전트)은 반드시 아래 스키마를 따르는 JSON을 출력해야 합니다.

```json
{
  "summary": "이슈에 대한 한 줄 요약",
  "category": "Tagging Request | Data Discrepancy | ...",
  "urgency": "High | Medium | Low",
  "root_cause_hypothesis": "잠재적 원인에 대한 간략한 설명",
  "required_action": "Code Fix | Configuration Change | Investigation",
  "suggested_assignee_team": "Dev Team A | Ops Team B",
  "confidence_score": 0.95
}
```

## 2. API 인터페이스 명세

### 2.1 내부 서비스 (gRPC)

**Ingestion Service (수집)**
- `PushEvent(EventRaw) returns (Ack)`: Webhook 또는 CSV 이벤트를 수신합니다.

**NLP Service (자연어 처리)**
- `AnalyzeIssue(IssueData) returns (AnalysisResult)`: 번역, 요약, 슬롯 채우기(Slot Filling)를 수행합니다.

**Routing Service (라우팅)**
- `RecommendAssignee(IssueData, AnalysisResult) returns (RoutingSuggestion)`: 신뢰도 점수와 함께 담당자 후보를 반환합니다.

**Case Matcher Service (케이스 매칭)**
- `FindSimilarCases(IssueData, Limit) returns (CaseList)`: 유사한 과거 해결 케이스 Top-K개를 반환합니다.

### 2.2 Jira Webhook 페이로드 매핑

Jira Webhook JSON 경로를 내부 스키마로 다음과 같이 매핑합니다.

- `issue.key` -> `issues.issue_key`
- `issue.fields.summary` -> `issues.summary`
- `issue.fields.description` -> `issues.description`
- `issue.fields.customfield_10013` -> `custom_fields.region` (ID 확인 필요)
- `issue.fields.customfield_10014` -> `custom_fields.country`

## 3. 라우팅 로직 및 충돌 해결

### 3.1 하이브리드 라우팅 전략

1.  **Hard Rules (우선순위 1)**:
    - IF `Region` == 'EU' AND `Category` == 'GDPR' THEN `Legal-EU-Team`에 배정.
    - IF `Priority` == 'Critical' THEN `On-Call-Manager`에게 알림.

2.  **ML Recommendation (우선순위 2)**:
    - Hard Rule에 매칭되지 않는 경우 사용.
    - 입력: `Summary`, `Description`, `Component`.
    - 출력: 신뢰도 점수가 포함된 상위 3명 담당자.

3.  **충돌 해결 (Conflict Resolution)**:
    - Rule과 ML이 충돌할 경우, **Rule이 우선**합니다.
    - ML 신뢰도가 0.6 미만인 경우, **Triage Manager(인간 검토)**에게 배정합니다.

## 4. 임베딩 전략

- **모델**: OpenAI `text-embedding-3-small` (비용 효율성 및 고성능).
- **청킹 (Chunking)**:
    - **Chunk A**: Summary + Description (문제 상황 문맥).
    - **Chunk B**: Resolution + Comments (해결 방법 문맥).
- **인덱싱**: `pgvector`의 `HNSW` 인덱스를 사용하여 빠른 근사 최근접 이웃(ANN) 검색을 지원합니다.

## 5. 에러 처리

- **재시도 정책 (Retry Policy)**:
    - LLM API 호출: 지수 백오프(Exponential Backoff) 적용 (1초, 2초, 4초), 최대 3회 재시도.
    - Webhook 처리: 5회 실패 후 Dead Letter Queue (DLQ)로 이동.
- **폴백 (Fallback)**:
    - NLP 서비스 장애 시, Routing 서비스는 "General Support Queue"로 기본 배정합니다.

## 6. 개인정보 보호 및 보안 (Privacy & Security)

### 6.1 PII 마스킹 전략
LLM으로 데이터를 전송하기 전, 민감 정보(PII)를 제거하거나 마스킹합니다.

- **대상 필드**: `Description`, `Summary`, `Comments`
- **마스킹 규칙**:
    - **이메일**: 정규식 `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` -> `<EMAIL>`
    - **전화번호**: 정규식 기반 패턴 매칭 -> `<PHONE>`
    - **IP 주소**: IPv4/IPv6 패턴 -> `<IP>`
- **구현**: NLP Service의 전처리 파이프라인에서 `Presidio` 또는 정규식 필터를 적용합니다.

### 6.2 접근 제어 (RBAC)
어드민 패널 및 API 접근 권한을 역할별로 분리합니다.

- **Admin**: 모든 설정(룰, 프롬프트, 사용자) 변경 가능.
- **Operator**: 티켓 처리, 추천 승인/거절, 케이스 라이브러리 조회 가능.
- **Viewer**: 대시보드 및 리포트 조회만 가능 (설정 변경 불가).

## 7. 성능 평가 지표 (Evaluation Metrics)

### 7.1 요약 품질 평가
- **정량적 평가**: LLM-as-a-Judge 방식을 사용하여 원문 대비 요약문의 정확성(Accuracy)과 일관성(Consistency)을 1~5점으로 채점.
- **정성적 평가**: 운영자가 무작위 샘플링된 요약을 검토하고 "좋아요/싫어요" 피드백 제공.

### 7.2 라우팅 정확도
- **Top-N Recall**: 모델이 추천한 상위 3명(Top-3) 안에 실제 최종 담당자가 포함될 확률.
- **목표치**: 초기 80% 이상, 지속적 학습을 통해 90% 이상 달성 목표.

## 8. 운영 모니터링 (Operational Monitoring)

### 8.1 비용 및 리소스 추적
- **LLM 토큰 사용량**: 요청별 Input/Output 토큰 수를 로깅하여 일별/월별 비용 대시보드 시각화.
- **API 지연 시간 (Latency)**: 각 마이크로서비스(NLP, Routing)의 p95, p99 응답 속도 모니터링.

### 8.2 SLA 및 알림
- **SLA 위반 경보**: 티켓 생성 후 1시간 내에 "담당자 배정"이 완료되지 않으면 Slack 알림 발송.
- **에러율 모니터링**: 번역/요약 실패율이 5%를 초과하면 개발팀에 긴급 알림 (PagerDuty 연동).
