import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Sparkles } from 'lucide-react'
import { projectsApi } from '../services/api'
import type { ProjectCreate } from '../types'

export default function NewProjectPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

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

    createMutation.mutate({ name, description })
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
