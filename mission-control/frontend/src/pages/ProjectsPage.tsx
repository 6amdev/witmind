import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus, FolderKanban } from 'lucide-react'
import { projectsApi } from '../services/api'
import ProjectCard from '../components/Projects/ProjectCard'

export default function ProjectsPage() {
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <Link to="/projects/new" className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Project
        </Link>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-bg-tertiary rounded w-3/4 mb-4" />
              <div className="h-3 bg-bg-tertiary rounded w-full mb-2" />
              <div className="h-3 bg-bg-tertiary rounded w-2/3" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && projects.length === 0 && (
        <div className="card text-center py-12">
          <FolderKanban className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-medium mb-2">No projects yet</h3>
          <p className="text-text-secondary mb-4">
            Create your first project to get started
          </p>
          <Link to="/projects/new" className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Create Project
          </Link>
        </div>
      )}

      {/* Projects grid */}
      {!isLoading && projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  )
}
