import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import ProjectsPage from './pages/ProjectsPage'
import NewProjectPage from './pages/NewProjectPage'
import MissionBoardPage from './pages/MissionBoardPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/projects" replace />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<NewProjectPage />} />
        <Route path="projects/:projectId/mission" element={<MissionBoardPage />} />
      </Route>
    </Routes>
  )
}

export default App
