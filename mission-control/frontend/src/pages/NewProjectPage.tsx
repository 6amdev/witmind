import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Sparkles, Zap, Eye, Hand } from 'lucide-react'
import { projectsApi } from '../services/api'
import type { ProjectCreate, ExecutionMode } from '../types'

const EXECUTION_MODES: { value: ExecutionMode; label: string; icon: typeof Zap; description: string }[] = [
  {
    value: 'full_auto',
    label: 'Full Auto',
    icon: Zap,
    description: 'PM creates tasks and dev agents execute automatically'
  },
  {
    value: 'review_first',
    label: 'Review First',
    icon: Eye,
    description: 'PM creates tasks, you review and dispatch manually'
  },
  {
    value: 'manual',
    label: 'Manual',
    icon: Hand,
    description: 'You create tasks and dispatch agents yourself'
  }
]

export default function NewProjectPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('review_first')

  const createMutation = useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate(`/projects/${project.id}/mission`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !description.trim()) return

    createMutation.mutate({ name, description, execution_mode: executionMode })
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="btn-ghost mb-6 -ml-2 flex items-center gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <div className="card">
        <h1 className="text-2xl font-semibold mb-6">Create New Project</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Project Name <span className="text-accent-red">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="My Awesome Project"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Description <span className="text-accent-red">*</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input min-h-[150px] resize-y"
              placeholder="Describe what you want to build...&#10;&#10;Example:&#10;Build a modern e-commerce website with:&#10;- Product catalog&#10;- Shopping cart&#10;- Checkout with Stripe&#10;- Admin dashboard"
              required
            />
            <p className="text-xs text-text-muted mt-2">
              <Sparkles className="w-3 h-3 inline mr-1" />
              AI will automatically detect project type and assign the right team
            </p>
          </div>

          {/* Execution Mode */}
          <div>
            <label className="block text-sm font-medium mb-3">
              Execution Mode
            </label>
            <div className="grid grid-cols-3 gap-3">
              {EXECUTION_MODES.map((mode) => {
                const Icon = mode.icon
                const isSelected = executionMode === mode.value
                return (
                  <button
                    key={mode.value}
                    type="button"
                    onClick={() => setExecutionMode(mode.value)}
                    className={`
                      p-4 rounded-lg border-2 text-left transition-all
                      ${isSelected
                        ? 'border-accent-cyan bg-accent-cyan/10'
                        : 'border-border-subtle hover:border-border-default bg-bg-secondary'
                      }
                    `}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className={`w-5 h-5 ${isSelected ? 'text-accent-cyan' : 'text-text-muted'}`} />
                      <span className={`font-medium ${isSelected ? 'text-accent-cyan' : ''}`}>
                        {mode.label}
                      </span>
                    </div>
                    <p className="text-xs text-text-muted leading-relaxed">
                      {mode.description}
                    </p>
                  </button>
                )
              })}
            </div>
            {executionMode === 'full_auto' && (
              <p className="text-xs text-accent-yellow mt-2 flex items-center gap-1">
                <Zap className="w-3 h-3" />
                Full Auto mode will run until completion without intervention
              </p>
            )}
          </div>

          {/* Submit */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !name.trim() || !description.trim()}
              className="btn-primary flex-1"
            >
              {createMutation.isPending ? 'Creating...' : 'Create & Start →'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
