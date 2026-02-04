import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { tasksApi } from '../../services/api'
import type { TaskPriority, TaskType } from '../../types'

interface CreateTaskModalProps {
  projectId: string
  onClose: () => void
}

const typeOptions: { value: TaskType; label: string }[] = [
  { value: 'feature', label: 'Feature' },
  { value: 'bug', label: 'Bug' },
  { value: 'improvement', label: 'Improvement' },
  { value: 'docs', label: 'Documentation' },
  { value: 'design', label: 'Design' },
  { value: 'review', label: 'Review' },
]

const priorityOptions: { value: TaskPriority; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'normal', label: 'Normal' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
]

export default function CreateTaskModal({ projectId, onClose }: CreateTaskModalProps) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState<TaskType>('feature')
  const [priority, setPriority] = useState<TaskPriority>('normal')

  // Create mutation
  const createMutation = useMutation({
    mutationFn: () => tasksApi.create(projectId, {
      title,
      description: description || undefined,
      type,
      priority,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      onClose()
    },
  })

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (title.trim()) {
      createMutation.mutate()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-bg-primary border border-border-default rounded-lg shadow-2xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-default">
          <h2 className="text-lg font-semibold">Create Task</h2>
          <button onClick={onClose} className="btn-ghost p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-bg-secondary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
              placeholder="What needs to be done?"
              autoFocus
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full min-h-[80px] bg-bg-secondary rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-accent-blue"
              placeholder="Add more details..."
            />
          </div>

          {/* Type & Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
                Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as TaskType)}
                className="w-full bg-bg-secondary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
              >
                {typeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

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
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-ghost">
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || createMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
