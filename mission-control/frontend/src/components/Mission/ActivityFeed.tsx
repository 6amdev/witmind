import { useQuery } from '@tanstack/react-query'
import {
  Play,
  CheckCircle2,
  AlertCircle,
  FileCode,
  ExternalLink,
  RefreshCw,
  Clock
} from 'lucide-react'
import { activitiesApi } from '../../services/api'
import type { Activity } from '../../types'
import clsx from 'clsx'
import { parseUTCDate } from '../../utils/date'

interface ActivityFeedProps {
  projectId?: string  // If provided, filter by project
  limit?: number
  showHeader?: boolean
}

const activityConfig: Record<string, {
  icon: typeof Play
  color: string
  bgColor: string
  label: string
}> = {
  agent_started: {
    icon: Play,
    color: 'text-accent-blue',
    bgColor: 'bg-accent-blue/20',
    label: 'Started',
  },
  agent_progress: {
    icon: FileCode,
    color: 'text-accent-yellow',
    bgColor: 'bg-accent-yellow/20',
    label: 'Progress',
  },
  agent_completed: {
    icon: CheckCircle2,
    color: 'text-accent-green',
    bgColor: 'bg-accent-green/20',
    label: 'Completed',
  },
  agent_error: {
    icon: AlertCircle,
    color: 'text-accent-red',
    bgColor: 'bg-accent-red/20',
    label: 'Error',
  },
}

function formatTime(dateStr: string): string {
  const date = parseUTCDate(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)

  if (diffMins < 1) return 'เมื่อสักครู่'
  if (diffMins < 60) return `${diffMins} นาทีที่แล้ว`
  if (diffHours < 24) return `${diffHours} ชม.ที่แล้ว`
  return date.toLocaleDateString('th-TH')
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

function ActivityItem({ activity }: { activity: Activity }) {
  const config = activityConfig[activity.type] || activityConfig.agent_progress
  const Icon = config.icon

  return (
    <div className="flex gap-3 py-3 border-b border-border-muted last:border-0">
      {/* Icon */}
      <div className={clsx(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        config.bgColor
      )}>
        <Icon className={clsx('w-4 h-4', config.color)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-lg">{activity.actor_icon}</span>
          <span className="font-medium text-sm">{activity.actor_name}</span>
          <span className={clsx('text-xs px-1.5 py-0.5 rounded', config.bgColor, config.color)}>
            {config.label}
          </span>
          <span className="text-xs text-text-muted ml-auto">
            {formatTime(activity.created_at)}
          </span>
        </div>

        {/* Message */}
        <p className="text-sm text-text-secondary mb-2">
          {activity.content.message || activity.content.text}
        </p>

        {/* Duration */}
        {activity.content.duration_ms && (
          <div className="flex items-center gap-1 text-xs text-text-muted mb-2">
            <Clock className="w-3 h-3" />
            <span>{formatDuration(activity.content.duration_ms)}</span>
          </div>
        )}

        {/* Links */}
        {activity.content.links && activity.content.links.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {activity.content.links.map((link, i) => (
              <a
                key={i}
                href={link.url || `#${link.path}`}
                className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-bg-tertiary rounded hover:bg-bg-secondary transition-colors"
                target={link.url ? '_blank' : undefined}
                rel={link.url ? 'noopener noreferrer' : undefined}
              >
                <FileCode className="w-3 h-3" />
                {link.label}
                {link.url && <ExternalLink className="w-3 h-3" />}
              </a>
            ))}
          </div>
        )}

        {/* Error */}
        {activity.content.error && (
          <div className="text-xs bg-accent-red/10 text-accent-red p-2 rounded">
            {activity.content.error}
          </div>
        )}

        {/* Output (collapsed) */}
        {activity.content.output && (
          <details className="text-xs">
            <summary className="cursor-pointer text-text-muted hover:text-text-secondary">
              Show output
            </summary>
            <pre className="mt-2 p-2 bg-bg-tertiary rounded overflow-x-auto max-h-40 overflow-y-auto">
              {activity.content.output}
            </pre>
          </details>
        )}
      </div>
    </div>
  )
}

export default function ActivityFeed({
  projectId,
  limit = 20,
  showHeader = true
}: ActivityFeedProps) {
  const { data: activities = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['activities', projectId, limit],
    queryFn: () => projectId
      ? activitiesApi.listByProject(projectId)
      : activitiesApi.listRecent(limit),
    refetchInterval: 5000,  // Poll every 5 seconds
  })

  // Filter to only agent activities if showing all
  const agentActivities = activities.filter(a =>
    a.type.startsWith('agent_')
  )

  return (
    <div className="flex flex-col h-full">
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border-default">
          <h3 className="font-semibold text-sm">Agent Activity</h3>
          <button
            onClick={() => refetch()}
            className="btn-ghost p-1 text-text-muted hover:text-text-primary"
            disabled={isFetching}
          >
            <RefreshCw className={clsx('w-4 h-4', isFetching && 'animate-spin')} />
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-4">
        {isLoading ? (
          <div className="py-8 text-center text-text-muted">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
            Loading...
          </div>
        ) : agentActivities.length === 0 ? (
          <div className="py-8 text-center text-text-muted">
            <div className="text-2xl mb-2">🤖</div>
            <div className="text-sm">No agent activity yet</div>
            <div className="text-xs mt-1">Activities will appear here when agents work</div>
          </div>
        ) : (
          agentActivities.map((activity) => (
            <ActivityItem key={activity.id} activity={activity} />
          ))
        )}
      </div>
    </div>
  )
}
