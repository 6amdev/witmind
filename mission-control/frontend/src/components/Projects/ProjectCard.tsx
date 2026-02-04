import { Link } from 'react-router-dom'
import clsx from 'clsx'
import type { Project } from '../../types'
import { formatRelativeTime } from '../../utils/date'

interface ProjectCardProps {
  project: Project
}

const statusColors = {
  draft: 'badge-gray',
  planning: 'badge-blue',
  in_progress: 'badge-yellow',
  review: 'badge-purple',
  completed: 'badge-green',
  archived: 'badge-gray',
}

const statusLabels = {
  draft: 'Draft',
  planning: 'Planning',
  in_progress: 'In Progress',
  review: 'Review',
  completed: 'Completed',
  archived: 'Archived',
}

const teamIcons = {
  dev: '💻',
  marketing: '📊',
  creative: '🎨',
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link
      to={`/projects/${project.id}/mission`}
      className="card hover:border-border-default/80 hover:shadow-lg transition-all duration-200 group"
    >
      {/* Progress bar */}
      <div className="h-1 bg-bg-tertiary rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-accent-blue transition-all duration-300"
          style={{ width: `${project.progress}%` }}
        />
      </div>

      {/* Title */}
      <h3 className="font-semibold text-lg mb-2 group-hover:text-accent-blue transition-colors">
        {project.name}
      </h3>

      {/* Description */}
      <p className="text-text-secondary text-sm mb-4 line-clamp-2">
        {project.description}
      </p>

      {/* Meta */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          {project.team_id && (
            <span className="text-lg">
              {teamIcons[project.team_id as keyof typeof teamIcons] || '📁'}
            </span>
          )}
          <span className={clsx('badge', statusColors[project.status])}>
            {statusLabels[project.status]}
          </span>
        </div>

        <span className="text-text-muted">
          {formatRelativeTime(project.updated_at)}
        </span>
      </div>

      {/* Progress text */}
      {project.progress > 0 && (
        <div className="mt-3 text-xs text-text-muted">
          {project.progress}% complete
        </div>
      )}
    </Link>
  )
}
