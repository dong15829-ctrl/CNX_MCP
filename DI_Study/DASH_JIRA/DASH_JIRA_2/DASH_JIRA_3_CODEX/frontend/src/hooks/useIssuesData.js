import { useCallback, useEffect, useState } from 'react'
import { fetchFilters, fetchIssues } from '../api/dashboard'

const defaultFilters = {
  status: '',
  priority: '',
  region: '',
  category: '',
  search: '',
  page: 1,
  pageSize: 15,
  sortBy: 'created_at',
  sortOrder: 'desc',
  showFavoritesOnly: false,
}

const emptyOptions = {
  statuses: [],
  priorities: [],
  regions: [],
  categories: [],
}

export function useIssuesData() {
  const [issueFilters, setIssueFilters] = useState(defaultFilters)
  const [issuesState, setIssuesState] = useState({
    items: [],
    total: 0,
    page: 1,
    pageSize: defaultFilters.pageSize,
  })
  const [issuesLoading, setIssuesLoading] = useState(false)

  const [filterOptions, setFilterOptions] = useState(emptyOptions)
  const [filtersLoading, setFiltersLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadIssues = useCallback(async (filters) => {
    setIssuesLoading(true)
    try {
      const { showFavoritesOnly, ...apiFilters } = filters
      const data = await fetchIssues(apiFilters)
      setIssuesState({
        items: data.items,
        total: data.total,
        page: data.page,
        pageSize: data.page_size || filters.pageSize,
      })
    } catch (err) {
      setError(err.message || '이슈 목록을 불러오지 못했습니다')
    } finally {
      setIssuesLoading(false)
    }
  }, [])

  const loadFilters = useCallback(async () => {
    setFiltersLoading(true)
    try {
      const data = await fetchFilters()
      setFilterOptions(data)
    } catch (err) {
      setError(err.message || '필터 정보를 불러오지 못했습니다')
    } finally {
      setFiltersLoading(false)
    }
  }, [])

  useEffect(() => {
    loadFilters()
  }, [loadFilters])

  useEffect(() => {
    loadIssues(issueFilters)
  }, [issueFilters, loadIssues])

  const updateIssueFilters = (nextFilters) => {
    setIssueFilters((prev) => ({
      ...prev,
      ...nextFilters,
      page: nextFilters.page ?? 1,
    }))
  }

  const resetIssueFilters = () => setIssueFilters(defaultFilters)

  const refreshIssues = () => loadIssues(issueFilters)

  return {
    issuesState,
    issuesLoading,
    issueFilters,
    updateIssueFilters,
    resetIssueFilters,
    filterOptions,
    filtersLoading,
    refreshIssues,
    error,
  }
}
