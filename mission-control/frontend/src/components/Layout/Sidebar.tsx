import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FolderKanban, Bot, Plus } from 'lucide-react'
import { agentsApi } from '../../services/api'
import clsx from 'clsx'

const navItems = [
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  // { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
]

export default function Sidebar() {
  // Fetch agents
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
  })

  // Group agents by team
  const devAgents = agents.filter((a) => a.team === 'dev')
  const marketingAgents = agents.filter((a) => a.team === 'marketing')
  const creativeAgents = agents.filter((a) => a.team === 'creative')

  return (
    <aside className="w-60 h-[calc(100vh-56px)] bg-bg-secondary border-r border-border-default fixed left-0 top-14 overflow-y-auto">
      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-bg-tertiary text-text-primary'
                  : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
              )
            }
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </NavLink>
        ))}

        <NavLink
          to="/projects/new"
          className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-accent-blue hover:bg-accent-blue/10 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Project
        </NavLink>
      </nav>

      {/* Agents */}
      <div className="p-4 border-t border-border-default">
        <div className="flex items-center gap-2 mb-3">
          <Bot className="w-4 h-4 text-text-muted" />
          <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
            Agents
          </span>
        </div>

        {/* Dev Team */}
        <AgentGroup title="Dev Team" agents={devAgents} />

        {/* Marketing Team */}
        <AgentGroup title="Marketing" agents={marketingAgents} />

        {/* Creative Team */}
        <AgentGroup title="Creative" agents={creativeAgents} />
      </div>
    </aside>
  )
}

function AgentGroup({
  title,
  agents,
}: {
  title: string
  agents: { id: string; name: string; icon: string; status: string }[]
}) {
  if (agents.length === 0) return null

  return (
    <div className="mb-4">
      <div className="text-xs text-text-muted mb-2">{title}</div>
      <div className="space-y-1">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="flex items-center gap-2 px-2 py-1 rounded text-sm"
          >
            <span>{agent.icon}</span>
            <span className="flex-1 truncate text-text-secondary">
              {agent.name}
            </span>
            <span
              className={clsx('w-2 h-2 rounded-full', {
                'bg-accent-green': agent.status === 'standby',
                'bg-accent-yellow animate-pulse': agent.status === 'working',
                'bg-accent-red': agent.status === 'blocked' || agent.status === 'error',
                'bg-text-muted': agent.status === 'offline',
              })}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
