import { useCallback, useEffect, useState } from 'react'
import { fetchDashboard, fetchTimeSeries } from '../api/dashboard'

const defaultDashboardData = {
  summary: null,
  timeSeries: [],
  statusDistribution: [],
  priorityDistribution: [],
  regionDistribution: [],
  categoryDistribution: [],
  filters: {
    statuses: [],
    priorities: [],
    regions: [],
    categories: [],
  },
}

const defaultTimeConfig = {
  granularity: 'day',
  days: 30,
}

export function useSummaryData() {
  const [dashboardData, setDashboardData] = useState(defaultDashboardData)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [timeSeries, setTimeSeries] = useState([])
  const [timeSeriesLoading, setTimeSeriesLoading] = useState(false)
  const [timeSeriesConfig, setTimeSeriesConfig] = useState(defaultTimeConfig)

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDashboard()
      setDashboardData(data)
      setTimeSeries(data.timeSeries || [])
      setTimeSeriesConfig(defaultTimeConfig)
    } catch (err) {
      setError(err.message || '데이터를 불러오지 못했습니다')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadTimeSeries = useCallback(async (config = defaultTimeConfig) => {
    setTimeSeriesLoading(true)
    setError(null)
    try {
      const data = await fetchTimeSeries(config)
      setTimeSeries(data)
      setTimeSeriesConfig(config)
    } catch (err) {
      setError(err.message || '시간대별 데이터를 불러오지 못했습니다')
    } finally {
      setTimeSeriesLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  return {
    dashboardData,
    loading,
    error,
    refreshDashboard: loadDashboard,
    timeSeries,
    timeSeriesLoading,
    timeSeriesConfig,
    updateTimeSeries: loadTimeSeries,
  }
}
