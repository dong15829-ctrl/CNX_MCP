import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import SummaryCards from '../components/SummaryCards'
import TrendChart from '../components/TrendChart'
import DistributionList from '../components/DistributionList'
import Loader from '../components/Loader'
import { useSummaryData } from '../hooks/useSummaryData'

const TIME_TABS = [
  { id: 'day', label: '일별', subtitle: '최근 30일', config: { granularity: 'day', days: 30 } },
  { id: 'week', label: '주차별', subtitle: '최근 26주', config: { granularity: 'week', days: 180 } },
  { id: 'month', label: '월별', subtitle: '최근 24개월', config: { granularity: 'month', days: 730 } },
  { id: 'year', label: '연도별', subtitle: '최근 5년', config: { granularity: 'year', days: 1825 } },
]

const Home = () => {
  const {
    dashboardData,
    loading,
    error,
    refreshDashboard,
    timeSeries,
    timeSeriesLoading,
    updateTimeSeries,
  } = useSummaryData()
  const [activeTimeTab, setActiveTimeTab] = useState(TIME_TABS[0].id)

  const activeTimeOption =
    TIME_TABS.find((tab) => tab.id === activeTimeTab) ?? TIME_TABS[0]

  const labelMap = useMemo(() => {
    const entries = {}
    timeSeries.forEach((item) => {
      entries[item.date] = item.label || item.date
    })
    return entries
  }, [timeSeries])

  const handleTimeTabChange = async (tabId) => {
    if (tabId === activeTimeTab) return
    const tab = TIME_TABS.find((item) => item.id === tabId)
    if (!tab) return
    setActiveTimeTab(tab.id)
    await updateTimeSeries(tab.config)
  }

  const handleRefresh = async () => {
    await refreshDashboard()
    const tab = TIME_TABS.find((item) => item.id === activeTimeTab)
    if (tab && tab.id !== 'day') {
      await updateTimeSeries(tab.config)
    }
  }

  const xFormatter = (value) => labelMap[value] || value

  const chartActions = (
    <div className="time-tabs">
      {TIME_TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={clsx('chip', 'toggle', activeTimeTab === tab.id && 'active')}
          onClick={() => handleTimeTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )

  return (
    <div className="dashboard">
      <header className="page-header">
        <div>
          <h1>AI Jira Ops 메인</h1>
          <p>요약·주제 판별·SLA·케이스 지표를 한눈에 모니터링합니다.</p>
        </div>
        <div className="header-actions">
          <Link to="/issues" className="ghost-button">
            티켓 작업실 이동
          </Link>
          <button type="button" className="primary" onClick={handleRefresh}>
            새로고침
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <Loader label="요약 데이터를 불러오는 중" />
      ) : (
        <>
          <SummaryCards summary={dashboardData.summary} />
          <TrendChart
            data={timeSeries}
            title={`${activeTimeOption.label} 생성/종결 추이`}
            subtitle={activeTimeOption.subtitle}
            xFormatter={xFormatter}
            labelFormatter={xFormatter}
            actions={chartActions}
            loading={timeSeriesLoading}
          />
          <div className="grid">
            <DistributionList
              title="상태 상위"
              items={dashboardData.statusDistribution}
              labelKey="status"
              valueKey="count"
            />
            <DistributionList
              title="우선순위 구성"
              items={dashboardData.priorityDistribution}
              labelKey="priority"
              valueKey="count"
            />
            <DistributionList
              title="지역 분포"
              items={dashboardData.regionDistribution}
              labelKey="region"
              valueKey="count"
            />
            <DistributionList
              title="카테고리"
              items={dashboardData.categoryDistribution}
              labelKey="category"
              valueKey="count"
            />
          </div>

          <div className="panel highlight">
            <div>
              <h3>분석 파이프라인 상황판</h3>
              <p className="muted">
                상세 분석, taxonomy, 담당자 추천, 메일 로그는 티켓 작업실에서 단계별로 확인하세요.
              </p>
            </div>
            <Link to="/issues" className="primary">
              작업실 열기
            </Link>
          </div>
        </>
      )}
    </div>
  )
}

export default Home
