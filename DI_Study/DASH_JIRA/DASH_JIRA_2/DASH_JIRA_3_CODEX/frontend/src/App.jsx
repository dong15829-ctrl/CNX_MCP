import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import IssueWorkspace from './pages/IssueWorkspace'
import TopNav from './components/TopNav'
import './App.css'

const App = () => {
  return (
    <BrowserRouter>
      <main className="app-shell">
        <TopNav />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/issues" element={<IssueWorkspace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App
