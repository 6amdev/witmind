import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Settings, Share2, Play, PanelRightClose, PanelRightOpen, Activity, ShieldCheck, Users } from 'lucide-react'
import { projectsApi, tasksApi, approvalsApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'
import { useSocket } from '../hooks/useSocket'
import KanbanBoard from '../components/Mission/KanbanBoard'
import ActivityFeed from '../components/Mission/ActivityFeed'
import ApprovalPanel from '../components/Mission/ApprovalPanel'
import AgentStatusPanel from '../components/Mission/AgentStatusPanel'
import clsx from 'clsx'

const statusLabels = {
  draft: 'Draft',
  planning: 'Planning',
  in_progress: 'In Progress',
  review: 'Review',
  completed: 'Completed',
  archived: 'Archived',
}

const teamNames = {
  dev: 'Dev Team',
  marketing: 'Marketing Team',
  creative: 'Creative Team',
}

type PanelTab = 'activity' | 'approvals' | 'agents'

export default function MissionBoardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const { setCurrentProject, setTasks } = useProjectStore()
  const [showActivityPanel, setShowActivityPanel] = useState(true)
  const [activeTab, setActiveTab] = useState<PanelTab>('activity')

  // Connect to socket for real-time updates
  useSocket(projectId)

  // Fetch pending approvals count
  const { data: approvals = [] } = useQuery({
    queryKey: ['approvals', projectId],
    queryFn: () => approvalsApi.list(projectId, true),
    refetchInterval: 5000,
  })
  const pendingApprovalsCount = approvals.filter(a => a.status === 'pending').length

  // Fetch project
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  })

  // Fetch tasks
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => tasksApi.list(projectId!),
    enabled: !!projectId,
  })

  // Memoize tasks to prevent unnecessary re-renders
  const tasks = useMemo(() => tasksData || [], [tasksData])
  const tasksKey = useMemo(() => tasks.map(t => `${t.id}:${t.status}`).join(','), [tasks])

  // Start project mutation
  const startMutation = useMutation({
    mutationFn: () => projectsApi.start(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  // Update store when data changes
  useEffect(() => {
    if (project) setCurrentProject(project)
  }, [project, setCurrentProject])

  useEffect(() => {
    setTasks(tasks)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tasksKey])

  if (projectLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-bg-tertiary rounded w-1/3 mb-4" />
        <div className="h-4 bg-bg-tertiary rounded w-1/4 mb-8" />
        <div className="grid grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-96 bg-bg-secondary rounded" />
          ))}
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-text-secondary">Project not found</p>
        <Link to="/projects" className="btn-primary mt-4">
          Back to Projects
        </Link>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-56px-48px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <Link to="/projects" className="btn-ghost p-2 -ml-2">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-semibold">{project.name}</h1>
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              {project.team_id && (
                <span>{teamNames[project.team_id as keyof typeof teamNames]}</span>
              )}
              <span>•</span>
              <span className={clsx({
                'text-text-muted': project.status === 'draft',
                'text-accent-blue': project.status === 'planning',
                'text-accent-yellow': project.status === 'in_progress',
                'text-accent-purple': project.status === 'review',
                'text-accent-green': project.status === 'completed',
              })}>
                {statusLabels[project.status]}
              </span>
              <span>•</span>
              <span>{project.progress}%</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {project.status === 'draft' && (
            <button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              {startMutation.isPending ? 'Starting...' : 'Start Project'}
            </button>
          )}
          <button className="btn-ghost p-2">
            <Share2 className="w-5 h-5" />
          </button>
          <button className="btn-ghost p-2">
            <Settings className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowActivityPanel(!showActivityPanel)}
            className={clsx(
              'btn-ghost p-2',
              showActivityPanel && 'bg-accent-blue/20 text-accent-blue'
            )}
            title={showActivityPanel ? 'Hide Activity' : 'Show Activity'}
          >
            {showActivityPanel ? (
              <PanelRightClose className="w-5 h-5" />
            ) : (
              <PanelRightOpen className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden gap-4">
        {/* Kanban Board */}
        <div className={clsx(
          'flex-1 overflow-hidden transition-all duration-300',
          showActivityPanel ? 'pr-0' : ''
        )}>
          <KanbanBoard projectId={projectId!} tasks={tasks} isLoading={tasksLoading} projectStatus={project?.status} />
        </div>

        {/* Side Panel */}
        <div className={clsx(
          'bg-bg-secondary/50 rounded-lg border border-border-default overflow-hidden transition-all duration-300 flex flex-col',
          showActivityPanel ? 'w-96 opacity-100' : 'w-0 opacity-0 border-0'
        )}>
          {showActivityPanel && (
            <>
              {/* Tabs */}
              <div className="flex border-b border-border-default">
                <button
                  onClick={() => setActiveTab('activity')}
                  className={clsx(
                    'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                    activeTab === 'activity'
                      ? 'text-accent-blue border-b-2 border-accent-blue bg-accent-blue/5'
                      : 'text-text-muted hover:text-text-primary hover:bg-bg-tertiary/50'
                  )}
                >
                  <Activity className="w-4 h-4" />
                  Activity
                </button>
                <button
                  onClick={() => setActiveTab('approvals')}
                  className={clsx(
                    'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative',
                    activeTab === 'approvals'
                      ? 'text-accent-yellow border-b-2 border-accent-yellow bg-accent-yellow/5'
                      : 'text-text-muted hover:text-text-primary hover:bg-bg-tertiary/50'
                  )}
                >
                  <ShieldCheck className="w-4 h-4" />
                  Approvals
                  {pendingApprovalsCount > 0 && (
                    <span className="absolute top-2 right-2 w-5 h-5 flex items-center justify-center bg-accent-yellow text-bg-primary rounded-full text-xs font-bold">
                      {pendingApprovalsCount}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('agents')}
                  className={clsx(
                    'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                    activeTab === 'agents'
                      ? 'text-accent-purple border-b-2 border-accent-purple bg-accent-purple/5'
                      : 'text-text-muted hover:text-text-primary hover:bg-bg-tertiary/50'
                  )}
                >
                  <Users className="w-4 h-4" />
                  Agents
                </button>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {activeTab === 'activity' && (
                  <ActivityFeed projectId={projectId} limit={30} showHeader={false} />
                )}
                {activeTab === 'approvals' && (
                  <ApprovalPanel projectId={projectId} />
                )}
                {activeTab === 'agents' && (
                  <AgentStatusPanel team={project.team_id} />
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
