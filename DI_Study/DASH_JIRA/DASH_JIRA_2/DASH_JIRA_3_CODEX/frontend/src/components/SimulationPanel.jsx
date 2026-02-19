import { useState } from 'react'
import clsx from 'clsx'

const SimulationPanel = ({ state, onRun, onReset, loading }) => {
  const [selected, setSelected] = useState(null)
  const [confirmed, setConfirmed] = useState({})
  const [activeTab, setActiveTab] = useState('detail')

  if (!state) {
    return (
      <div className="panel muted">
        <h3>시뮬레이션</h3>
        <p>상태를 불러오는 중입니다...</p>
      </div>
    )
  }

  const processedPct = state.total
    ? Math.round((state.processed / state.total) * 100)
    : 0

  return (
    <div className="panel">
      <div className="panel-header between">
        <div>
          <h3>신규 티켓 시뮬레이션</h3>
          <p>
            총 {state.total.toLocaleString()}건 중 {state.processed.toLocaleString()}건 처리 ({processedPct}%)
          </p>
        </div>
        <button type="button" className="text-button" onClick={onReset} disabled={loading}>
          초기화
        </button>
      </div>
      <div className="simulation-controls">
        <button type="button" className={clsx('chip', 'toggle')} disabled={loading} onClick={() => onRun(1)}>
          다음 1건
        </button>
        <button type="button" className={clsx('chip', 'toggle')} disabled={loading} onClick={() => onRun(5)}>
          다음 5건
        </button>
        <button type="button" className={clsx('chip', 'toggle')} disabled={loading} onClick={() => onRun(10)}>
          다음 10건
        </button>
      </div>
      <div className="ingest-log">
        <p>남은 건수: {state.remaining.toLocaleString()}건</p>
        {loading && <p>로딩 중...</p>}
        {!loading && state.last_ingested_details?.length ? (
          <div className="ingest-list">
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>티켓</th>
                    <th>요약</th>
                    <th>상태</th>
                    <th>우선</th>
                    <th>지역</th>
                    <th>액션</th>
                  </tr>
                </thead>
                <tbody>
                  {state.last_ingested_details.map((item) => (
                    <tr
                      key={item.issue_key}
                      className={clsx({ muted: confirmed[item.issue_key] })}
                      onClick={() => setSelected(item)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>
                        <strong>{item.issue_key}</strong>
                      </td>
                      <td>
                        <div className="summary-cell">
                          <p>{item.translation?.summary || item.summary || '요약 없음'}</p>
                          <div className="chips">
                            {item.priority && <span className="chip">{item.priority}</span>}
                            {confirmed[item.issue_key] && <span className="chip success">컨펌됨</span>}
                          </div>
                        </div>
                      </td>
                      <td>{item.status || '—'}</td>
                      <td>{item.priority || '—'}</td>
                      <td>{item.region || '—'}</td>
                      <td>
                        <button type="button" className="ghost-button" onClick={() => setSelected(item)}>
                          새 탭에서 보기
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {loading && <div className="table-overlay">로딩 중...</div>}
            </div>
          </div>
        ) : (
          <p>최근 처리 건이 없습니다.</p>
        )}
      </div>
      {selected && (
        <div className="modal-overlay">
          <div className="modal-body">
            <div className="modal-header">
              <h3>{selected.issue_key} 신규 티켓 상세</h3>
              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setConfirmed((prev) => ({ ...prev, [selected.issue_key]: true }))}
                >
                  최종 컨펌
                </button>
                <button type="button" className="ghost-button" onClick={() => setSelected(null)}>
                  닫기
                </button>
              </div>
            </div>

            <div className="tab-header">
              <button
                type="button"
                className={clsx('tab', { active: activeTab === 'detail' })}
                onClick={() => setActiveTab('detail')}
              >
                상세
              </button>
              <button
                type="button"
                className={clsx('tab', { active: activeTab === 'cases' })}
                onClick={() => setActiveTab('cases')}
              >
                유사 사례
              </button>
            </div>

            {activeTab === 'detail' && (
              <>
                <div className="dual-columns">
                  <div className="dual-column">
                    <span>원문</span>
                    <div className="description body-text">
                      <p className="muted">Summary</p>
                      <p>{selected.summary || '—'}</p>
                      <p className="muted">Description</p>
                      <p>{selected.translation?.description_original || selected.description_original || '—'}</p>
                    </div>
                  </div>
                  <div className="dual-column">
                    <span>번역 (KO)</span>
                    <div className="description body-text">
                      <p className="muted">Summary</p>
                      <p>{selected.translation?.summary || selected.summary || '—'}</p>
                      <p className="muted">Description</p>
                      <p>{selected.translation?.description || selected.translation?.description_original || '—'}</p>
                    </div>
                  </div>
                </div>

                {selected.summary_structured && (
                  <div className="ingest-summary">
                    <p className="muted">구조화 요약</p>
                    <p>개요: {selected.summary_structured.overview || '—'}</p>
                    <p>요구사항: {selected.summary_structured.requirements || '—'}</p>
                    <p>위험: {selected.summary_structured.risks || '—'}</p>
                    <p>SLA: {selected.summary_structured.sla || '—'}</p>
                    <p>추천 조직: {selected.summary_structured.recommended_org || '—'}</p>
                  </div>
                )}

                {selected.summary_outline && (
                  <div className="ingest-outline">
                    <p className="muted">description_summary</p>
                    <p>
                      대상: {selected.summary_outline.target || '없음'} / 작업: {selected.summary_outline.work || '없음'} / 설명:{' '}
                      {selected.summary_outline.details || '없음'} / 기타: {selected.summary_outline.etc || '없음'}
                    </p>
                  </div>
                )}

                {selected.assignment?.primary && (
                  <div className="ingest-assignment">
                    <p className="muted">담당자 추천</p>
                    <p>
                      Primary: {selected.assignment.primary.name} ({selected.assignment.primary.email}) ·{' '}
                      {selected.assignment.primary.reason}
                    </p>
                    {selected.assignment.backups?.length > 0 && (
                      <p className="muted">
                        백업: {selected.assignment.backups
                          .map((b) => `${b.name}(${Math.round((b.confidence || 0) * 100)}%)`)
                          .join(', ')}
                      </p>
                    )}
                  </div>
                )}

                {selected.notifications?.length > 0 && (
                  <div className="ingest-notifications">
                    <p className="muted">알림</p>
                    {selected.notifications.map((n, idx) => (
                      <p key={`${n.subject}-${idx}`}>
                        {n.channel?.toUpperCase() || 'MSG'} · {n.status} · {n.recipient || '수신자 미상'}
                      </p>
                    ))}
                  </div>
                )}
              </>
            )}

            {activeTab === 'cases' && (
              <div className="ingest-cases">
                <p className="muted">유사 사례</p>
                {selected.cases?.length > 0 ? (
                  selected.cases.map((c) => (
                    <div key={c.issue_key} className="case-snippet">
                      <strong>{c.issue_key}</strong> · {Math.round((c.similarity || 0) * 100)}% · {c.team || '팀 미상'}
                      <div className="dual-columns">
                        <div className="dual-column">
                          <span>원문</span>
                          <div className="description body-text">
                            <p className="muted">Summary</p>
                            <p>{c.summary || '—'}</p>
                            <p className="muted">Description</p>
                            <p>{c.details || '—'}</p>
                          </div>
                        </div>
                        <div className="dual-column">
                          <span>번역 (KO)</span>
                          <div className="description body-text">
                            <p className="muted">Summary</p>
                            <p>{c.summary_translated || c.summary || '—'}</p>
                            <p className="muted">Description</p>
                            <p>{c.details_translated || c.details || '—'}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>유사 사례가 없습니다.</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default SimulationPanel
