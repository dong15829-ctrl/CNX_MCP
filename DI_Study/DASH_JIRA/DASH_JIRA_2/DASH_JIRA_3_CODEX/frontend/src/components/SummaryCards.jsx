const numberFormatter = new Intl.NumberFormat('en-US')

const SummaryCards = ({ summary }) => {
  if (!summary) {
    return <div className="card-grid skeleton" />
  }

  const cards = [
    {
      key: 'total_issues',
      label: '전체 티켓',
      value: summary.total_issues,
      caption: '데이터셋 누적',
    },
    {
      key: 'open_issues',
      label: '미해결',
      value: summary.open_issues,
      caption: '열린 상태',
    },
    {
      key: 'high_priority_open',
      label: '고우선 미해결',
      value: summary.high_priority_open,
      caption: 'High / Critical',
    },
    {
      key: 'avg_resolution_hours',
      label: '평균 해결 시간(h)',
      value: summary.avg_resolution_hours,
      caption: 'Resolved 티켓 기준',
      format: (value) => (value ? value.toFixed(1) : '-'),
    },
  ]

  return (
    <div className="card-grid">
      {cards.map((card) => (
        <article key={card.key} className="card">
          <p className="card-label">{card.label}</p>
          <p className="card-value">
            {card.format
              ? card.format(card.value)
              : typeof card.value === 'number'
              ? numberFormatter.format(card.value)
              : '-'}
          </p>
          <p className="card-caption">{card.caption}</p>
        </article>
      ))}
    </div>
  )
}

export default SummaryCards
