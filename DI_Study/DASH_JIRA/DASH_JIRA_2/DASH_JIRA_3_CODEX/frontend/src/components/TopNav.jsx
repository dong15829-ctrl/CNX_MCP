import { NavLink } from 'react-router-dom'

const TopNav = () => {
  return (
    <nav className="top-nav">
      <div>
        <p className="brand-label">Jira Monitoring</p>
        <p className="brand-caption">번역·요약·케이스 추천 파이프라인 상태</p>
      </div>
      <div className="nav-links">
        <NavLink
          to="/"
          end
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          메인 대시보드
        </NavLink>
        <NavLink
          to="/issues"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          티켓 작업실
        </NavLink>
      </div>
    </nav>
  )
}

export default TopNav
