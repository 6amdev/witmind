import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  ExternalLink,
  FileCode,
  FileText,
  FolderOpen,
  Clock,
  Package,
} from 'lucide-react'
import { projectsApi, tasksApi } from '../services/api'
import type { ProjectFile } from '../services/api'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getFileIcon(extension: string) {
  const codeExtensions = ['.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs', '.java', '.cpp', '.c', '.h']
  if (codeExtensions.includes(extension)) {
    return <FileCode className="w-4 h-4 text-accent-cyan" />
  }
  return <FileText className="w-4 h-4 text-text-muted" />
}

export default function ProjectCompletePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  })

  const { data: tasks } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => tasksApi.list(projectId!),
    enabled: !!projectId,
  })

  const { data: filesData, isLoading: filesLoading } = useQuery({
    queryKey: ['project-files', projectId],
    queryFn: () => projectsApi.getFiles(projectId!),
    enabled: !!projectId,
  })

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent-cyan"></div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">Project not found</p>
      </div>
    )
  }

  const completedTasks = tasks?.filter((t) => t.status === 'done').length || 0
  const totalTasks = tasks?.length || 0
  const files = filesData?.files || []

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="btn-ghost mb-6 -ml-2 flex items-center gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      {/* Completion Header */}
      <div className="card mb-6 text-center">
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-full bg-accent-green/20 flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8 text-accent-green" />
          </div>
        </div>
        <h1 className="text-2xl font-semibold mb-2">Project Completed!</h1>
        <p className="text-text-muted mb-4">{project.name}</p>

        {project.completed_at && (
          <p className="text-sm text-text-muted flex items-center justify-center gap-1">
            <Clock className="w-4 h-4" />
            Completed on {formatDate(project.completed_at)}
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card text-center">
          <div className="text-3xl font-bold text-accent-cyan mb-1">{completedTasks}/{totalTasks}</div>
          <div className="text-sm text-text-muted">Tasks Completed</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-accent-purple mb-1">{files.length}</div>
          <div className="text-sm text-text-muted">Files Generated</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-accent-yellow mb-1">
            {formatBytes(filesData?.total_size || 0)}
          </div>
          <div className="text-sm text-text-muted">Total Size</div>
        </div>
      </div>

      {/* Actions */}
      <div className="card mb-6">
        <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
          <Package className="w-5 h-5" />
          Project Deliverables
        </h2>

        <div className="flex flex-wrap gap-3">
          {/* Download Button */}
          <a
            href={projectsApi.getDownloadUrl(projectId!)}
            download
            className="btn-primary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download Project (.zip)
          </a>

          {/* Preview Link */}
          {project.preview_url && (
            <a
              href={project.preview_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Preview Live
            </a>
          )}

          {/* Back to Mission Board */}
          <Link
            to={`/projects/${projectId}/mission`}
            className="btn-secondary flex items-center gap-2"
          >
            <FolderOpen className="w-4 h-4" />
            View Mission Board
          </Link>
        </div>

        {filesData?.output_dir && (
          <p className="text-xs text-text-muted mt-4">
            Output directory: <code className="bg-bg-tertiary px-1 py-0.5 rounded">{filesData.output_dir}</code>
          </p>
        )}
      </div>

      {/* Files List */}
      <div className="card">
        <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
          <FileCode className="w-5 h-5" />
          Generated Files ({files.length})
        </h2>

        {filesLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-accent-cyan mx-auto"></div>
          </div>
        ) : files.length === 0 ? (
          <p className="text-text-muted text-center py-8">No files generated yet</p>
        ) : (
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {files.map((file: ProjectFile) => (
              <div
                key={file.path}
                className="flex items-center gap-3 p-2 rounded hover:bg-bg-secondary transition-colors"
              >
                {getFileIcon(file.extension)}
                <span className="flex-1 font-mono text-sm truncate">{file.path}</span>
                <span className="text-xs text-text-muted">{formatBytes(file.size)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
