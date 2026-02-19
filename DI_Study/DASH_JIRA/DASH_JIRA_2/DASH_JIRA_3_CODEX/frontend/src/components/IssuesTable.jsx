import { useEffect, useState } from 'react'
import dayjs from 'dayjs'
import clsx from 'clsx'

const formatDate = (value) =>
  value ? dayjs(value).format('YY.MM.DD HH:mm') : '—'

const IssuesTable = ({
  data,
  loading,
  filters,
  onFiltersChange,
  options,
  onSelectIssue,
  favorites = [],
  toggleFavorite,
  isFavorite,
  showFavoritesOnly = false,
  onToggleFavoritesOnly,
}) => {
  const [searchText, setSearchText] = useState(filters.search)

  useEffect(() => {
    setSearchText(filters.search)
  }, [filters.search])

  const handleFilterChange = (field, value) => {
    onFiltersChange({
      ...filters,
      [field]: value,
      page: 1,
    })
  }

  const handleSearchSubmit = (event) => {
    event.preventDefault()
    const sanitized =
      searchText.trim().length >= 2 ? searchText.trim() : ''
    onFiltersChange({ ...filters, search: sanitized, page: 1 })
  }

  const handlePageChange = (direction) => {
    onFiltersChange({ ...filters, page: filters.page + direction })
  }

  const resetFilters = () =>
    onFiltersChange({
      status: '',
      priority: '',
      region: '',
      category: '',
      search: '',
      page: 1,
      pageSize: filters.pageSize,
      sortBy: filters.sortBy,
      sortOrder: filters.sortOrder,
      showFavoritesOnly: false,
    })

  const favoritesSet = new Set(favorites)
  const displayItems = showFavoritesOnly
    ? data.items.filter((issue) => favoritesSet.has(issue.issue_key))
    : data.items
  const totalPages = Math.max(1, Math.ceil(data.total / filters.pageSize))
  const headerDescription = showFavoritesOnly
    ? `총 ${data.total.toLocaleString()}건 · 즐겨찾기 ${favorites.length}건 중 ${displayItems.length}건 표시`
    : `총 ${data.total.toLocaleString()}건 중 ${
        displayItems.length ? `${displayItems.length}건 표시` : '0건'
      }`

  return (
    <div className="panel">
      <div className="panel-header between">
        <div>
          <h3>티켓 목록</h3>
          <p>{headerDescription}</p>
        </div>
        <button type="button" className="text-button" onClick={resetFilters}>
          필터 초기화
        </button>
      </div>

      <form className="filters" onSubmit={handleSearchSubmit}>
        <select
          value={filters.status}
          onChange={(event) => handleFilterChange('status', event.target.value)}
        >
          <option value="">전체 상태</option>
          {options.statuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
        <select
          value={filters.priority}
          onChange={(event) => handleFilterChange('priority', event.target.value)}
        >
          <option value="">전체 우선순위</option>
          {options.priorities.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>
        <select
          value={filters.region}
          onChange={(event) => handleFilterChange('region', event.target.value)}
        >
          <option value="">전체 지역</option>
          {options.regions.map((region) => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
        <select
          value={filters.category}
          onChange={(event) => handleFilterChange('category', event.target.value)}
        >
          <option value="">전체 카테고리</option>
          {options.categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="요약/본문 검색 (2자 이상)"
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
        />
        <button type="submit" className="primary">
          검색
        </button>
      </form>

      <div className="favorites-toolbar">
        <button
          type="button"
          className={clsx('chip', 'toggle', showFavoritesOnly && 'active')}
          onClick={onToggleFavoritesOnly}
        >
          즐겨찾기만 보기 ({favorites.length})
        </button>
      </div>

      <div className={clsx('table-wrapper', loading && 'loading')}>
        <table>
          <thead>
            <tr>
              <th />
              <th>Key</th>
              <th>요약</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Region</th>
              <th>Created</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {!loading && displayItems.length === 0 && (
              <tr>
                <td colSpan={8} className="empty-state">
                  조건에 맞는 티켓이 없습니다.
                </td>
              </tr>
            )}
            {displayItems.map((issue) => (
              <tr key={issue.issue_key} onClick={() => onSelectIssue(issue)}>
                <td>
                  {toggleFavorite && (
                    <button
                      type="button"
                      className={clsx(
                        'icon-button',
                        isFavorite?.(issue.issue_key) && 'active',
                      )}
                      onClick={(event) => {
                        event.stopPropagation()
                        toggleFavorite(issue.issue_key)
                      }}
                      aria-label="즐겨찾기 전환"
                    >
                      {isFavorite?.(issue.issue_key) ? '★' : '☆'}
                    </button>
                  )}
                </td>
                <td>{issue.issue_key}</td>
                <td>
                  <div className="summary-cell">
                    <p>{issue.summary}</p>
                    <div className="chips">
                      {issue.is_high_priority && (
                        <span className="chip danger">High</span>
                      )}
                      {!issue.is_closed && (
                        <span className="chip warning">Open</span>
                      )}
                    </div>
                  </div>
                </td>
                <td>{issue.status}</td>
                <td>{issue.priority}</td>
                <td>{issue.region || '—'}</td>
                <td>{formatDate(issue.created_at)}</td>
                <td>{formatDate(issue.updated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <div className="table-overlay">로딩 중...</div>}
      </div>

      <div className="pagination">
        <button
          type="button"
          onClick={() => onFiltersChange({ ...filters, page: 1 })}
          disabled={filters.page === 1 || loading}
        >
          처음
        </button>
        <button
          type="button"
          onClick={() => handlePageChange(-1)}
          disabled={filters.page === 1 || loading}
        >
          이전
        </button>
        <span>
          페이지 {data.page} / {totalPages}
        </span>
        <button
          type="button"
          onClick={() => handlePageChange(1)}
          disabled={filters.page >= totalPages || loading}
        >
          다음
        </button>
        <button
          type="button"
          onClick={() => onFiltersChange({ ...filters, page: totalPages })}
          disabled={filters.page >= totalPages || loading}
        >
          끝
        </button>
      </div>
    </div>
  )
}

export default IssuesTable
