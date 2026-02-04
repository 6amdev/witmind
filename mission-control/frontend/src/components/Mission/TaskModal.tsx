import { useState, useEffect } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { X, Trash2 } from 'lucide-react'
import { tasksApi, agentsApi } from '../../services/api'
import type { Task, TaskStatus, TaskPriority, Agent } from '../../types'
import clsx from 'clsx'

interface TaskModalProps {
  task: Task
  projectId: string
  onClose: () => void
}

const statusOptions: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'planned', label: 'Planned', color: 'bg-text-muted' },
  { value: 'assigned', label: 'Assigned', color: 'bg-accent-blue' },
  { value: 'working', label: 'Working', color: 'bg-accent-yellow' },
  { value: 'testing', label: 'Testing', color: 'bg-accent-purple' },
  { value: 'review', label: 'Review', color: 'bg-accent-orange' },
  { value: 'done', label: 'Done', color: 'bg-accent-green' },
]

const priorityOptions: { value: TaskPriority; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: 'text-text-muted' },
  { value: 'normal', label: 'Normal', color: 'text-text-secondary' },
  { value: 'high', label: 'High', color: 'text-accent-orange' },
  { value: 'urgent', label: 'Urgent', color: 'text-accent-red' },
]

export default function TaskModal({ task, projectId, onClose }: TaskModalProps) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description || '')
  const [status, setStatus] = useState(task.status)
  const [priority, setPriority] = useState(task.priority)
  const [assignedTo, setAssignedTo] = useState(task.assigned_to || '')

  // Fetch agents for assignment
  const { data: agents = [] } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: () => agentsApi.list(),
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: Partial<Task>) => tasksApi.update(task.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => tasksApi.delete(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      onClose()
    },
  })

  // Auto-save on change
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (
        title !== task.title ||
        description !== (task.description || '') ||
        status !== task.status ||
        priority !== task.priority ||
        assignedTo !== (task.assigned_to || '')
      ) {
        updateMutation.mutate({
          title,
          description: description || undefined,
          status,
          priority,
          assigned_to: assignedTo || undefined,
        })
      }
    }, 500)

    return () => clearTimeout(timeout)
  }, [title, description, status, priority, assignedTo])

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const selectedAgent = agents.find((a: Agent) => a.id === assignedTo)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-bg-primary border border-border-default rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-default">
          <div className="flex items-center gap-3">
            <div className={clsx(
              'w-3 h-3 rounded-full',
              statusOptions.find(s => s.value === status)?.color
            )} />
            <span className="text-sm text-text-muted">Task Details</span>
          </div>
          <button onClick={onClose} className="btn-ghost p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-130px)]">
          {/* Title */}
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full text-xl font-semibold bg-transparent border-none outline-none focus:ring-0 mb-4"
            placeholder="Task title"
          />

          {/* Description */}
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full min-h-[100px] bg-bg-secondary rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-accent-blue mb-6"
            placeholder="Add description..."
          />

          {/* Properties */}
          <div className="grid grid-cols-2 gap-4">
            {/* Status */}
            <div>
              <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as TaskStatus)}
                className="w-full bg-bg-secondary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
              >
                {statusOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as TaskPriority)}
                className="w-full bg-bg-secondary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
              >
                {priorityOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Assigned Agent */}
            <div className="col-span-2">
              <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
                Assigned To
              </label>
              <select
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
                className="w-full bg-bg-secondary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
              >
                <option value="">Unassigned</option>
                {agents.map((agent: Agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.icon} {agent.name} ({agent.team})
                  </option>
                ))}
              </select>
              {selectedAgent && (
                <div className="mt-2 flex items-center gap-2 text-sm text-text-secondary">
                  <span className="text-lg">{selectedAgent.icon}</span>
                  <span>{selectedAgent.name}</span>
                  <span className={clsx(
                    'w-2 h-2 rounded-full',
                    selectedAgent.status === 'standby' && 'bg-accent-green',
                    selectedAgent.status === 'working' && 'bg-accent-yellow',
                    selectedAgent.status === 'blocked' && 'bg-accent-red',
                  )} />
                </div>
              )}
            </div>
          </div>

          {/* Labels */}
          <div className="mt-6">
            <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
              Labels
            </label>
            <div className="flex flex-wrap gap-2">
              {task.labels.map((label) => (
                <span
                  key={label}
                  className="px-2 py-1 bg-accent-blue/20 text-accent-blue rounded text-xs"
                >
                  {label}
                </span>
              ))}
              {task.labels.length === 0 && (
                <span className="text-sm text-text-muted">No labels</span>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-border-default bg-bg-secondary/50">
          <button
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
            className="btn-ghost text-accent-red flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </button>

          <div className="flex items-center gap-2 text-xs text-text-muted">
            {updateMutation.isPending && (
              <span className="text-accent-blue">Saving...</span>
            )}
            {updateMutation.isSuccess && (
              <span className="text-accent-green">Saved</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
