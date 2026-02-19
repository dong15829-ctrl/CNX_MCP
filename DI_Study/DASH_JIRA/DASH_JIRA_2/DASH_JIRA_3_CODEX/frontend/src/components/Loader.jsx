const Loader = ({ label = '불러오는 중...' }) => (
  <div className="loader">
    <div className="spinner" />
    <span>{label}</span>
  </div>
)

export default Loader
