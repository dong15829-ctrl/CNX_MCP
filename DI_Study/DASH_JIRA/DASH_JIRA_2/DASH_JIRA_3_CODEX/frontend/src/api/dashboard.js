import client from './client'

export async function fetchDashboard() {
  const [summary, timeSeries, status, priority, region, category, filters] =
    await Promise.all([
      client.get('/api/summary'),
      client.get('/api/metrics/time-series'),
      client.get('/api/metrics/status'),
      client.get('/api/metrics/priority'),
      client.get('/api/metrics/region'),
      client.get('/api/metrics/category'),
      client.get('/api/filters'),
    ])

  return {
    summary: summary.data,
    timeSeries: timeSeries.data,
    statusDistribution: status.data,
    priorityDistribution: priority.data,
    regionDistribution: region.data,
    categoryDistribution: category.data,
    filters: filters.data,
  }
}

export async function fetchIssues(params = {}) {
  const {
    status,
    priority,
    region,
    category,
    search,
    page = 1,
    pageSize = 20,
    sortBy,
    sortOrder,
  } = params

  const response = await client.get('/api/issues', {
    params: {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(status ? { status: [status] } : {}),
      ...(priority ? { priority: [priority] } : {}),
      ...(region ? { region: [region] } : {}),
      ...(category ? { category: [category] } : {}),
      ...(search && search.length >= 2 ? { text: search } : {}),
    },
    paramsSerializer: {
      indexes: null,
    },
  })

  return response.data
}

export async function fetchIssueDetail(issueKey) {
  const response = await client.get(`/api/issues/${issueKey}`)
  return response.data
}

export async function fetchIssueTaxonomy(issueKey) {
  const response = await client.get(`/api/issues/${issueKey}/taxonomy`)
  return response.data
}

export async function fetchIssueAnalysis(issueKey, options = {}) {
  const { refresh = false } = options
  const response = await client.get(`/api/issues/${issueKey}/analysis`, {
    params: refresh ? { refresh: 1 } : {},
    timeout: 60000,
  })
  return response.data
}

export async function fetchTimeSeries(params = {}) {
  const response = await client.get('/api/metrics/time-series', {
    params,
  })
  return response.data
}

export async function fetchFilters() {
  const response = await client.get('/api/filters')
  return response.data
}

export async function fetchSimulationState() {
  const response = await client.get('/api/simulation/state')
  return response.data
}

export async function simulateNextBatch(batch = 1) {
  const response = await client.post('/api/simulation/next', null, {
    params: { batch },
  })
  return response.data
}

export async function resetSimulation() {
  const response = await client.post('/api/simulation/reset')
  return response.data
}
