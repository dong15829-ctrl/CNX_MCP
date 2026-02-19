import { useState } from 'react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import IssuesTable from '../components/IssuesTable'
import IssueDetailPanel from '../components/IssueDetailPanel'
import SimulationPanel from '../components/SimulationPanel'
import Loader from '../components/Loader'
import { useIssuesData } from '../hooks/useIssuesData'
import { useSimulation } from '../hooks/useSimulation'
import { useFavorites } from '../hooks/useFavorites'
import {
  fetchIssueAnalysis,
  fetchIssueDetail,
  fetchIssueTaxonomy,
} from '../api/dashboard'

const IssueWorkspace = () => {
  const {
    issuesState,
    issuesLoading,
    issueFilters,
    updateIssueFilters,
    filterOptions,
    filtersLoading,
    refreshIssues,
    error,
  } = useIssuesData()

  const [detailIssue, setDetailIssue] = useState(null)
  const [detailTaxonomy, setDetailTaxonomy] = useState(null)
  const [detailAnalysis, setDetailAnalysis] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [taxonomyLoading, setTaxonomyLoading] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('list')
  const [showDetailModal, setShowDetailModal] = useState(false)

  const { favorites, toggleFavorite, isFavorite } = useFavorites()
  const simulation = useSimulation(refreshIssues)

  const handleSelectIssue = async (issue) => {
    setDetailLoading(true)
    setTaxonomyLoading(true)
    setAnalysisLoading(true)
    setShowDetailModal(true)
    setDetailIssue(null)
    setDetailTaxonomy(null)
    setDetailAnalysis(null)
    try {
      const [detail, taxonomy, analysis] = await Promise.all([
        fetchIssueDetail(issue.issue_key),
        fetchIssueTaxonomy(issue.issue_key),
        fetchIssueAnalysis(issue.issue_key, { refresh: true }),
      ])
      setDetailIssue(detail)
      setDetailTaxonomy(taxonomy)
      setDetailAnalysis(analysis)
    } catch (err) {
      console.error(err)
    } finally {
      setDetailLoading(false)
      setTaxonomyLoading(false)
      setAnalysisLoading(false)
    }
  }

  const handleRefreshAnalysis = async () => {
    if (!detailIssue) return
    setAnalysisLoading(true)
    try {
      const analysis = await fetchIssueAnalysis(detailIssue.issue_key, {
        refresh: true,
      })
      setDetailAnalysis(analysis)
    } catch (err) {
      console.error(err)
    } finally {
      setAnalysisLoading(false)
    }
  }

  const handleClearDetail = () => {
    setDetailIssue(null)
    setDetailTaxonomy(null)
    setDetailAnalysis(null)
    setShowDetailModal(false)
  }

  return (
    <div className="dashboard">
      <header className="page-header">
        <div>
          <h1>티켓 작업실</h1>
        </div>
        <div className="header-actions">
          <Link to="/" className="ghost-button">
            메인으로 돌아가기
          </Link>
          <button type="button" className="primary" onClick={refreshIssues}>
            목록 새로고침
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {filtersLoading ? (
        <Loader label="필터 정보를 불러오는 중" />
      ) : (
        <>
          <div className="workspace-tabs">
            <button
              type="button"
              className={clsx('chip', 'toggle', activeTab === 'list' && 'active')}
              onClick={() => setActiveTab('list')}
            >
              티켓 목록
            </button>
            <button
              type="button"
              className={clsx('chip', 'toggle', activeTab === 'simulation' && 'active')}
              onClick={() => setActiveTab('simulation')}
            >
              신규 티켓
            </button>
          </div>

          {activeTab === 'list' && (
            <>
              <IssuesTable
                data={issuesState}
                loading={issuesLoading}
                filters={issueFilters}
                onFiltersChange={updateIssueFilters}
                options={filterOptions}
                onSelectIssue={handleSelectIssue}
                favorites={favorites}
                toggleFavorite={toggleFavorite}
                isFavorite={isFavorite}
                showFavoritesOnly={issueFilters.showFavoritesOnly}
              onToggleFavoritesOnly={() =>
                updateIssueFilters({
                  showFavoritesOnly: !issueFilters.showFavoritesOnly,
                  page: issueFilters.page,
                })
              }
            />
              {showDetailModal && (
                <div className="modal-overlay">
                  <div className="modal-body">
                    <div className="modal-header">
                      <h3>{detailIssue?.issue_key || '티켓 상세'} 전체보기</h3>
                      <div className="modal-actions">
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={handleRefreshAnalysis}
                          disabled={analysisLoading}
                        >
                          {analysisLoading ? '재분석 중...' : '재분석'}
                        </button>
                        <button type="button" className="ghost-button" onClick={() => setShowDetailModal(false)}>
                          닫기
                        </button>
                      </div>
                    </div>
                    {detailLoading || taxonomyLoading || (analysisLoading && !detailAnalysis) ? (
                      <Loader label="티켓 상세를 불러오는 중" />
                    ) : (
                      <IssueDetailPanel
                        variant="full"
                        issue={detailIssue}
                        loading={detailLoading}
                        taxonomy={detailTaxonomy}
                        taxonomyLoading={taxonomyLoading}
                        analysis={detailAnalysis}
                        analysisLoading={analysisLoading}
                        onRefreshAnalysis={handleRefreshAnalysis}
                        onClose={() => setShowDetailModal(false)}
                      />
                    )}
                  </div>
                </div>
              )}
            </>
          )}
          {activeTab === 'simulation' && (
            <section className="simulation-stack">
              <div className="panel highlight">
                <h3>신규 티켓 시뮬레이션</h3>
                <p className="muted">
                  /processed/dataset_test.csv 스트림을 재생하며 LLM 번역→요약→케이스 추천→담당자 알림 흐름을 검증합니다.
                  초기화 후 원하는 배치 크기를 선택해 다음 티켓 묶음을 처리하세요.
                </p>
              </div>
              <SimulationPanel
                state={simulation.state}
                loading={simulation.loading}
                onRun={simulation.runBatch}
                onReset={simulation.reset}
              />
            </section>
          )}
        </>
      )}
    </div>
  )
}

export default IssueWorkspace
