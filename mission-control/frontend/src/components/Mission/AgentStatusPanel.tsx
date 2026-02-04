import { useQuery } from '@tanstack/react-query'
import { agentsApi } from '../../services/api'
import type { Agent, AgentStatus } from '../../types'
import clsx from 'clsx'

interface AgentStatusPanelProps {
  team?: string
  compact?: boolean
}

const statusConfig: Record<AgentStatus, { label: string; color: string; bgColor: string; pulse?: boolean }> = {
  standby: { label: 'Standby', color: 'text-text-muted', bgColor: 'bg-bg-tertiary' },
  working: { label: 'Working', color: 'text-accent-green', bgColor: 'bg-accent-green/20', pulse: true },
  blocked: { label: 'Blocked', color: 'text-accent-yellow', bgColor: 'bg-accent-yellow/20' },
  error: { label: 'Error', color: 'text-accent-red', bgColor: 'bg-accent-red/20' },
  offline: { label: 'Offline', color: 'text-text-muted', bgColor: 'bg-bg-tertiary' },
}

const teamNames: Record<string, string> = {
  dev: 'Development',
  marketing: 'Marketing',
  creative: 'Creative',
}

function AgentCard({ agent, compact }: { agent: Agent; compact?: boolean }) {
  const config = statusConfig[agent.status] || statusConfig.standby

  if (compact) {
    return (
      <div className={clsx(
        'flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors',
        config.bgColor
      )}>
        <span className="text-lg">{agent.icon}</span>
        <span className="text-sm font-medium flex-1 truncate">{agent.name}</span>
        <div className="flex items-center gap-1">
          {config.pulse && (
            <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
          )}
          <span className={clsx('text-xs', config.color)}>{config.label}</span>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx(
      'p-3 rounded-lg border transition-all',
      agent.status === 'working'
        ? 'border-accent-green/50 bg-accent-green/5'
        : 'border-border-default bg-bg-secondary/50'
    )}>
      <div className="flex items-start gap-3">
        <div className={clsx(
          'w-10 h-10 rounded-lg flex items-center justify-center text-xl',
          config.bgColor
        )}>
          {agent.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium truncate">{agent.name}</span>
            <span className={clsx(
              'px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1',
              config.bgColor, config.color
            )}>
              {config.pulse && (
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
              )}
              {config.label}
            </span>
          </div>
          <p className="text-xs text-text-muted mt-0.5">{agent.role}</p>
          {agent.current_task_id && agent.status === 'working' && (
            <p className="text-xs text-accent-green mt-1 truncate">
              Working on: {agent.current_task_id}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AgentStatusPanel({ team, compact = false }: AgentStatusPanelProps) {
  const { data: agents = [], isLoading } = useQuery({
    queryKey: ['agents', team],
    queryFn: () => agentsApi.list(team),
    refetchInterval: 3000, // Poll every 3 seconds for status updates
  })

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-bg-tertiary rounded-lg" />
        ))}
      </div>
    )
  }

  // Group agents by team
  const agentsByTeam = agents.reduce((acc, agent) => {
    const t = agent.team
    if (!acc[t]) acc[t] = []
    acc[t].push(agent)
    return acc
  }, {} as Record<string, Agent[]>)

  // Count working agents
  const workingCount = agents.filter(a => a.status === 'working').length

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center justify-between px-1">
        <span className="text-sm text-text-muted">
          {agents.length} agents
        </span>
        {workingCount > 0 && (
          <span className="flex items-center gap-1.5 text-sm text-accent-green">
            <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
            {workingCount} working
          </span>
        )}
      </div>

      {/* Agents by team */}
      {team ? (
        // Single team view
        <div className="space-y-2">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} compact={compact} />
          ))}
        </div>
      ) : (
        // All teams view
        Object.entries(agentsByTeam).map(([teamId, teamAgents]) => (
          <div key={teamId}>
            <h4 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2 px-1">
              {teamNames[teamId] || teamId}
            </h4>
            <div className="space-y-2">
              {teamAgents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} compact={compact} />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
