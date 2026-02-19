const DistributionList = ({ title, items = [], labelKey, valueKey }) => {
  if (!items.length) {
    return (
      <div className="panel muted">
        <h3>{title}</h3>
        <p>데이터가 없습니다.</p>
      </div>
    )
  }

  const max = Math.max(...items.map((item) => Number(item[valueKey]) || 0)) || 1

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>{title}</h3>
      </div>
      <ul className="distribution-list">
        {items.map((item) => {
          const value = Number(item[valueKey]) || 0
          return (
            <li key={item[labelKey] || 'n/a'}>
              <div className="label-group">
                <span className="label">{item[labelKey] || 'Unspecified'}</span>
                <span className="value">{value.toLocaleString()}</span>
              </div>
              <div className="progress">
                <div
                  className="progress-bar"
                  style={{ width: `${(value / max) * 100}%` }}
                />
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default DistributionList
