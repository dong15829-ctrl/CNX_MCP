import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import dayjs from 'dayjs'
import Loader from './Loader'

const TrendChart = ({
  data,
  title = '일자별 생성/종결 추이',
  subtitle,
  xFormatter,
  labelFormatter,
  actions,
  loading = false,
}) => {
  const defaultTickFormatter = (value) => dayjs(value).format('MM/DD')
  const defaultLabelFormatter = (value) => dayjs(value).format('YYYY-MM-DD')

  const header = (
    <div className="panel-header between">
      <div>
        <h3>{title}</h3>
        <p>{subtitle || `최근 ${data?.length ?? 0} 구간`}</p>
      </div>
      {actions}
    </div>
  )

  if (loading) {
    return (
      <div className="panel">
        {header}
        <Loader label="시간대별 데이터를 불러오는 중" />
      </div>
    )
  }

  if (!data?.length) {
    return (
      <div className="panel">
        {header}
        <div className="muted">시간대별 데이터가 없습니다.</div>
      </div>
    )
  }

  const tickFormatter = xFormatter || defaultTickFormatter
  const tooltipLabelFormatter = labelFormatter || defaultLabelFormatter

  return (
    <div className="panel">
      {header}
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ left: 12, right: 12, top: 12 }}>
          <defs>
            <linearGradient id="trendOpen" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tickFormatter={tickFormatter} style={{ fontSize: 12 }} />
          <YAxis width={50} style={{ fontSize: 12 }} allowDecimals={false} />
          <Tooltip
            formatter={(value, name) => [value, name]}
            labelFormatter={tooltipLabelFormatter}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="open"
            name="열린 티켓"
            stroke="#60a5fa"
            fill="url(#trendOpen)"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="closed"
            name="종결"
            stroke="#34d399"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="high_priority"
            name="고우선"
            stroke="#f472b6"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default TrendChart
