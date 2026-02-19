import { useEffect, useMemo, useState } from 'react'
import dayjs from 'dayjs'
import clsx from 'clsx'
import Loader from './Loader'

const InfoRow = ({ label, value }) => (
  <div className="info-row">
    <span>{label}</span>
    <p>{value || '—'}</p>
  </div>
)

const formatDateTime = (value) =>
  value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '—'

const ReferenceContext = ({ context }) => {
  if (!context) return null
  const siteCodes = Array.isArray(context.site_codes) ? context.site_codes : []
  const abbreviations = Array.isArray(context.abbreviations) ? context.abbreviations : []
  if (!siteCodes.length && !abbreviations.length) return null

  return (
    <div className="reference-section">
      <h4>참조 정보</h4>
      {siteCodes.length > 0 && (
        <div className="info-row">
          <span>사이트 코드</span>
          <ul className="reference-list">
            {siteCodes.map((site, idx) => (
              <li key={`${site.token}-${idx}`}>
                <p>
                  <strong>{site.token}</strong> · {site.country || '국가 정보 없음'}
                  {site.country_code ? ` (${site.country_code})` : ''}
                </p>
                <p className="muted">
                  {site.region || '지역 미지정'}
                  {site.base_url ? ` · ${site.base_url}` : ''}
                  {site.time_zone ? ` · ${site.time_zone}` : ''}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
      {abbreviations.length > 0 && (
        <div className="info-row">
          <span>약어 해석</span>
          <ul className="reference-list">
            {abbreviations.map((abbr, idx) => (
              <li key={`${abbr.token}-${idx}`}>
                <p>
                  <strong>{abbr.token}</strong> · {abbr.definition || '정의 없음'}
                </p>
                {abbr.example && <p className="muted">예시: {abbr.example}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

const STEP_FLOW = [
  { id: 'body', label: '① 본문' },
  { id: 'summary', label: '② 요약' },
  { id: 'cases', label: '③ 사례' },
  { id: 'assignment', label: '④ 담당자' },
  { id: 'notifications', label: '⑤ 알림' },
]

const StepNavigation = ({ activeStep, onChange }) => (
  <div className="step-navigation">
    {STEP_FLOW.map((step) => (
      <button
        key={step.id}
        type="button"
        className={clsx('chip', 'toggle', activeStep === step.id && 'active')}
        onClick={() => onChange(step.id)}
      >
        {step.label}
      </button>
    ))}
  </div>
)

const StepSection = ({
  step,
  title,
  subtitle,
  actions,
  children,
  stepId,
  activeStep,
}) => {
  if (activeStep !== stepId) return null
  return (
    <section className="analysis-section">
      <div className="step-header">
        <div>
          <p className="step-badge">STEP {step}</p>
          <h4>{title}</h4>
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  )
}

const BodySection = ({
  issue,
  translation,
  summaryData,
  loading,
  taxonomy,
  taxonomyLoading,
  activeStep,
}) => {
  const outline = summaryData?.description_summary || {}
  const originalSummary = translation?.summary_original || issue?.summary || '요약 정보가 없습니다.'
  const originalDescription =
    translation?.description_original || issue?.description || '본문 정보가 없습니다.'
  const translatedSummary = translation?.summary_translated || originalSummary
  const translatedDescription =
    translation?.description_translated ||
    translation?.description_original ||
    originalDescription
  const summaryLang = translation?.summary_language?.toUpperCase()
  const descriptionLang = translation?.description_language?.toUpperCase()

  const taxonomyFields = useMemo(
    () => [
      { label: 'Taxonomy', value: taxonomy?.category },
      {
        label: 'Confidence',
        value:
          typeof taxonomy?.confidence === 'number'
            ? `${Math.round(taxonomy.confidence * 100)}%`
            : null,
      },
      { label: 'Urgency', value: taxonomy?.urgency },
      { label: 'Required Action', value: taxonomy?.required_action },
      { label: 'Suggested Team', value: taxonomy?.suggested_team },
      { label: 'Processing', value: taxonomy?.processing_state },
      { label: 'Root cause', value: taxonomy?.root_cause },
    ],
    [taxonomy],
  )

  const tags = taxonomy?.tags || []

  return (
    <StepSection
      step="01"
      stepId="body"
      activeStep={activeStep}
      title="티켓 본문 요약"
      subtitle="description_summary · 원문/번역 · taxonomy 태그를 한 번에 확인합니다."
    >
      <div className="outline-card">
        <div className="outline-head">
          <h5>Step 1. 티켓 본문 요약</h5>
          <p className="muted">description_summary 필드 기준으로 한국어 요약을 제공합니다.</p>
        </div>
        <div className="outline-list">
          <p className="muted">요약 항목 (description_summary)</p>
          <ul>
            <li>
              <strong>대상 :</strong> {outline.target || '대상 정보 없음'}
            </li>
            <li>
              <strong>작업내용 :</strong> {outline.work || '작업 내용 미상'}
            </li>
            <li>
              <strong>설명 :</strong> {outline.details || '설명 정보 없음'}
            </li>
            <li>
              <strong>기타 :</strong> {outline.etc || '추가 메모 없음'}
            </li>
          </ul>
        </div>
      </div>
      {loading && !translation && !summaryData ? (
        <Loader label="본문을 불러오는 중" />
      ) : (
        <div className="dual-columns">
          <div className="dual-column">
            <span>
              원문
              {(summaryLang || descriptionLang) && ` (${summaryLang || descriptionLang})`}
            </span>
            <div className="description body-text">
              <p className="muted">Summary</p>
              <p>{originalSummary}</p>
              <p className="muted">Description</p>
              <p>{originalDescription}</p>
            </div>
          </div>
          <div className="dual-column">
            <span>번역 (KO)</span>
            <div className="description body-text">
              <p className="muted">Summary</p>
              <p>{translatedSummary}</p>
              <p className="muted">Description</p>
              <p>{translatedDescription}</p>
            </div>
          </div>
        </div>
      )}
      {taxonomyLoading && <Loader label="Taxonomy 정보를 불러오는 중" />}
      {!taxonomyLoading && taxonomy && (
        <div className="taxonomy-inline">
          <div className="taxonomy-grid">
            {taxonomyFields.map((field) => (
              <div key={field.label} className="info-row">
                <span>{field.label}</span>
                <p>{field.value || '—'}</p>
              </div>
            ))}
          </div>
          <div className="info-row">
            <span>태그</span>
            <div className="tags-row">
              {tags.length > 0 ? (
                tags.map((tag) => (
                  <span key={tag} className="chip small">
                    {tag}
                  </span>
                ))
              ) : (
                <p>태그 정보 없음</p>
              )}
            </div>
          </div>
          <div className="timeline-wrapper">
            <span>처리 타임라인</span>
            <ul className="timeline">
              {taxonomy.timeline?.map((step, index) => (
                <li key={`${step.stage}-${index}`}>
                  <div className="timeline-dot" />
                  <div>
                    <p className="timeline-stage">{step.stage}</p>
                    <p className="timeline-detail">{step.detail}</p>
                    <p className="timeline-meta">
                      {step.timestamp ? formatDateTime(step.timestamp) : '예정'} · {step.status}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </StepSection>
  )
}

const SummarySection = ({ data, activeStep }) => {
  if (!data) return null
  return (
    <StepSection
      step="02"
      stepId="summary"
      activeStep={activeStep}
      title="LLM 요약 & 주제 판별"
      subtitle="요청/위험/SLA를 구조화하여 라우팅 근거를 확보합니다."
    >
      <div className="analysis-grid">
        <InfoRow label="개요" value={data.overview} />
        <InfoRow label="요청 사항" value={data.requirements} />
        <InfoRow label="위험 요소" value={data.risks} />
        <InfoRow label="SLA" value={data.sla} />
        <InfoRow label="추천 조직" value={data.recommended_org} />
      </div>
    </StepSection>
  )
}

const CaseSection = ({ cases, activeStep, onSelectCase }) => {
  if (!cases || cases.length === 0) return null
  return (
    <StepSection
      step="03"
      stepId="cases"
      activeStep={activeStep}
      title="유사 처리 사례"
      subtitle="과거 JIRA 해결 기록을 참조해 실행 전략을 세웁니다."
    >
      <div className="case-grid">
        {cases.map((item) => (
          <div
            key={item.issue_key}
            className="case-card"
            role="button"
            tabIndex={0}
            onClick={() => onSelectCase?.(item)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSelectCase?.(item)
            }}
          >
            <p className="case-title">
              {item.issue_key} · 유사도 {Math.round(item.similarity * 100)}%
            </p>
            <p className="case-summary">
              {item.summary_translated || item.summary || '요약 정보 없음'}
            </p>
            <p className="case-meta">
              {item.team || '미지정 팀'} · {item.status}
            </p>
            {item.details && (
              <p className="case-details">
                {item.details_translated || item.details}
              </p>
            )}
          </div>
        ))}
      </div>
    </StepSection>
  )
}

const AssignmentSection = ({ assignment, activeStep }) => {
  if (!assignment) return null
  const { primary, backups, reason } = assignment
  return (
    <StepSection
      step="04"
      stepId="assignment"
      activeStep={activeStep}
      title="담당자 추천"
      subtitle="지역·카테고리 룰 기반으로 최적 담당자를 도출합니다."
    >
      {primary && (
        <div className="assignment-card">
          <p className="assignment-title">Primary</p>
          <p>
            {primary.name} · {primary.email}
          </p>
          <p className="muted">
            {primary.reason} · confidence {Math.round(primary.confidence * 100)}%
          </p>
        </div>
      )}
      {backups && backups.length > 0 && (
        <div className="assignment-backups">
          <p className="assignment-title">백업</p>
          <ul>
            {backups.map((backup) => (
              <li key={backup.email}>
                {backup.name} · {Math.round(backup.confidence * 100)}%
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="muted">{reason}</p>
    </StepSection>
  )
}

const NotificationsSection = ({ notifications, activeStep }) => {
  if (!notifications || notifications.length === 0) return null
  return (
    <StepSection
      step="05"
      stepId="notifications"
      activeStep={activeStep}
      title="알림 로그"
      subtitle="담당자에게 발송된 메일/Slack 상태를 확인합니다."
    >
      <ul className="log-list">
        {notifications.map((note, idx) => (
          <li key={`${note.timestamp}-${idx}`}>
            <p>
              {note.channel.toUpperCase()} · {note.status}
            </p>
            <p className="muted">
              {dayjs(note.timestamp).format('YYYY-MM-DD HH:mm')} · {note.recipient}
            </p>
            <p className="muted">{note.subject}</p>
          </li>
        ))}
      </ul>
    </StepSection>
  )
}

const IssueDetailPanel = ({
  issue,
  loading,
  taxonomy,
  taxonomyLoading,
  analysis,
  analysisLoading,
  onClose,
  onOpenFullscreen,
  onRefreshAnalysis,
  variant = 'sidebar',
}) => {
  const [activeStep, setActiveStep] = useState(STEP_FLOW[0].id)
  const [activeCase, setActiveCase] = useState(null)
  const WrapperTag = variant === 'full' ? 'section' : 'aside'
  const panelClass = clsx('detail-panel', variant === 'full' && 'full')
  const closeLabel = variant === 'full' ? '목록으로' : '닫기'
  const translationData = analysis?.translation

  useEffect(() => {
    setActiveStep(STEP_FLOW[0].id)
  }, [issue?.issue_key])

  return (
    <WrapperTag className={panelClass}>
      <div className="detail-header">
        <div>
          <p className="badge">{issue?.issue_type || '티켓'}</p>
          <h3>{issue?.issue_key ?? '티켓 상세'}</h3>
        </div>
        <div className="detail-actions">
          {onRefreshAnalysis && issue && (
            <button
              type="button"
              className="ghost-button"
              onClick={onRefreshAnalysis}
              disabled={analysisLoading}
            >
              {analysisLoading ? '재분석 중...' : '재분석'}
            </button>
          )}
          {onOpenFullscreen && issue && (
            <button type="button" className="ghost-button" onClick={onOpenFullscreen}>
              전체 화면
            </button>
          )}
          {onClose && (
            <button type="button" onClick={onClose}>
              {closeLabel}
            </button>
          )}
        </div>
      </div>

      {loading && <Loader label="티켓 정보를 불러오는 중" />}
      {!loading && !issue && (
        <p className="muted">행을 클릭해 티켓 상세를 확인하세요.</p>
      )}
      {!loading && issue && (
        <div className="meta-section">
          <div className="meta-grid">
            <InfoRow label="우선순위" value={issue.priority} />
            <InfoRow label="상태" value={issue.status} />
            <InfoRow label="카테고리" value={issue.category} />
            <InfoRow label="지역" value={issue.region} />
            <InfoRow label="국가" value={issue.country} />
            <InfoRow label="Root cause" value={issue.root_cause} />
            <InfoRow label="Created" value={formatDateTime(issue.created_at)} />
            <InfoRow label="Updated" value={formatDateTime(issue.updated_at)} />
            <InfoRow label="Resolved" value={formatDateTime(issue.resolved_at)} />
          </div>
          <ReferenceContext context={issue.reference_context} />
        </div>
      )}

      <StepNavigation activeStep={activeStep} onChange={setActiveStep} />

      <div className="process-stack">
        <BodySection
          issue={issue}
          translation={translationData}
          summaryData={analysis?.summary}
          loading={analysisLoading}
          taxonomy={taxonomy}
          taxonomyLoading={taxonomyLoading}
          activeStep={activeStep}
        />
        {analysisLoading && !analysis && <Loader label="번역/요약/추천 정보를 불러오는 중" />}
        {analysis && (
          <>
            <SummarySection data={analysis.summary} activeStep={activeStep} />
            <CaseSection
              cases={analysis.case_recommendations}
              activeStep={activeStep}
              onSelectCase={setActiveCase}
            />
            {activeCase && (
              <div className="modal-overlay">
                <div className="modal-body">
                  <div className="modal-header">
                    <h3>{activeCase.issue_key} 사례 상세</h3>
                    <div className="modal-actions">
                      <button type="button" className="ghost-button" onClick={() => setActiveCase(null)}>
                        닫기
                      </button>
                    </div>
                  </div>
                  <div className="dual-columns">
                    <div className="dual-column">
                      <span>원문</span>
                      <div className="description body-text">
                        <p className="muted">Summary</p>
                        <p>{activeCase.summary || '—'}</p>
                        <p className="muted">Description</p>
                        <p>{activeCase.details || '—'}</p>
                      </div>
                    </div>
                    <div className="dual-column">
                      <span>번역 (KO)</span>
                      <div className="description body-text">
                        <p className="muted">Summary</p>
                        <p>{activeCase.summary_translated || activeCase.summary || '—'}</p>
                        <p className="muted">Description</p>
                        <p>{activeCase.details_translated || activeCase.details || '—'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <AssignmentSection assignment={analysis.assignment} activeStep={activeStep} />
            <NotificationsSection notifications={analysis.notifications} activeStep={activeStep} />
          </>
        )}
      </div>
    </WrapperTag>
  )
}

export default IssueDetailPanel
