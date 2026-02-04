import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  Check,
  X,
  Clock,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  FileCode,
  Rocket,
  Globe,
  Trash2,
  Package
} from 'lucide-react'
import { approvalsApi } from '../../services/api'
import type { ApprovalRequest, ApprovalType } from '../../types'
import clsx from 'clsx'

interface ApprovalPanelProps {
  projectId?: string
}

const typeConfig: Record<ApprovalType, { icon: typeof AlertTriangle; color: string; label: string }> = {
  code_change: { icon: FileCode, color: 'text-accent-blue', label: 'Code Change' },
  deploy: { icon: Rocket, color: 'text-accent-green', label: 'Deploy' },
  external_api: { icon: Globe, color: 'text-accent-purple', label: 'External API' },
  file_delete: { icon: Trash2, color: 'text-accent-red', label: 'Delete Files' },
  install_package: { icon: Package, color: 'text-accent-yellow', label: 'Install Package' },
  custom: { icon: AlertTriangle, color: 'text-accent-orange', label: 'Approval Required' },
}

function formatTimeLeft(expiresAt: string): string {
  const expires = new Date(expiresAt)
  const now = new Date()
  const diffMs = expires.getTime() - now.getTime()

  if (diffMs <= 0) return 'Expired'

  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 60) return `${diffMins}m left`

  const diffHours = Math.floor(diffMins / 60)
  return `${diffHours}h ${diffMins % 60}m left`
}

function ApprovalCard({
  approval,
  onRespond
}: {
  approval: ApprovalRequest
  onRespond: (id: string, action: 'approve' | 'reject', optionId?: string, note?: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [selectedOption, setSelectedOption] = useState<string | undefined>(
    approval.options.length > 0 ? approval.options[0].id : undefined
  )
  const [note, setNote] = useState('')
  const [isResponding, setIsResponding] = useState(false)

  const config = typeConfig[approval.type] || typeConfig.custom
  const Icon = config.icon
  const timeLeft = formatTimeLeft(approval.expires_at)
  const isExpired = timeLeft === 'Expired'

  const handleRespond = async (action: 'approve' | 'reject') => {
    setIsResponding(true)
    try {
      await onRespond(approval.id, action, selectedOption, note || undefined)
    } finally {
      setIsResponding(false)
    }
  }

  return (
    <div className={clsx(
      'border rounded-lg overflow-hidden transition-all',
      isExpired ? 'border-border-muted opacity-60' : 'border-accent-yellow/50 bg-accent-yellow/5'
    )}>
      {/* Header */}
      <div
        className="p-3 cursor-pointer hover:bg-bg-secondary/50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-3">
          <div className={clsx('p-2 rounded-lg bg-bg-tertiary', config.color)}>
            <Icon className="w-4 h-4" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{approval.agent_icon}</span>
              <span className="font-medium text-sm">{approval.agent_name}</span>
              <span className={clsx('text-xs px-1.5 py-0.5 rounded', config.color, 'bg-bg-tertiary')}>
                {config.label}
              </span>
            </div>
            <h4 className="font-semibold text-sm mb-1">{approval.title}</h4>
            <p className="text-xs text-text-secondary line-clamp-2">{approval.description}</p>
          </div>

          <div className="flex flex-col items-end gap-1">
            <div className={clsx(
              'flex items-center gap-1 text-xs',
              isExpired ? 'text-accent-red' : 'text-accent-yellow'
            )}>
              <Clock className="w-3 h-3" />
              {timeLeft}
            </div>
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-text-muted" />
            ) : (
              <ChevronDown className="w-4 h-4 text-text-muted" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && !isExpired && (
        <div className="px-3 pb-3 border-t border-border-muted">
          {/* Details (Markdown) */}
          {approval.details && (
            <div className="mt-3 p-3 bg-bg-tertiary rounded text-sm">
              <pre className="whitespace-pre-wrap font-mono text-xs">{approval.details}</pre>
            </div>
          )}

          {/* Options */}
          {approval.options.length > 0 && (
            <div className="mt-3">
              <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
                Select Option
              </label>
              <div className="space-y-2">
                {approval.options.map((opt) => (
                  <label
                    key={opt.id}
                    className={clsx(
                      'flex items-start gap-3 p-2 rounded cursor-pointer transition-colors',
                      selectedOption === opt.id
                        ? 'bg-accent-blue/20 border border-accent-blue'
                        : 'bg-bg-tertiary border border-transparent hover:border-border-default'
                    )}
                  >
                    <input
                      type="radio"
                      name={`option-${approval.id}`}
                      value={opt.id}
                      checked={selectedOption === opt.id}
                      onChange={() => setSelectedOption(opt.id)}
                      className="mt-0.5"
                    />
                    <div>
                      <div className="font-medium text-sm">{opt.label}</div>
                      {opt.description && (
                        <div className="text-xs text-text-secondary">{opt.description}</div>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Note */}
          <div className="mt-3">
            <label className="block text-xs text-text-muted mb-2 uppercase tracking-wide">
              Note (optional)
            </label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a note..."
              className="w-full bg-bg-tertiary rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 mt-4">
            <button
              onClick={() => handleRespond('approve')}
              disabled={isResponding}
              className="flex-1 btn-primary flex items-center justify-center gap-2 py-2"
            >
              <Check className="w-4 h-4" />
              {isResponding ? 'Processing...' : 'Approve'}
            </button>
            <button
              onClick={() => handleRespond('reject')}
              disabled={isResponding}
              className="flex-1 btn-ghost text-accent-red flex items-center justify-center gap-2 py-2 border border-accent-red/30"
            >
              <X className="w-4 h-4" />
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function ApprovalPanel({ projectId }: ApprovalPanelProps) {
  const queryClient = useQueryClient()

  const { data: approvals = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['approvals', projectId],
    queryFn: () => approvalsApi.list(projectId, true),
    refetchInterval: 5000,
  })

  const respondMutation = useMutation({
    mutationFn: ({
      id,
      action,
      optionId,
      note
    }: {
      id: string
      action: 'approve' | 'reject'
      optionId?: string
      note?: string
    }) => approvalsApi.respond(id, action, optionId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
    },
  })

  const handleRespond = (id: string, action: 'approve' | 'reject', optionId?: string, note?: string) => {
    respondMutation.mutate({ id, action, optionId, note })
  }

  const pendingCount = approvals.filter(a => a.status === 'pending').length

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-default">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-sm">Approvals</h3>
          {pendingCount > 0 && (
            <span className="px-2 py-0.5 bg-accent-yellow/20 text-accent-yellow rounded-full text-xs font-medium">
              {pendingCount}
            </span>
          )}
        </div>
        <button
          onClick={() => refetch()}
          className="btn-ghost p-1 text-text-muted hover:text-text-primary"
          disabled={isFetching}
        >
          <RefreshCw className={clsx('w-4 h-4', isFetching && 'animate-spin')} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="py-8 text-center text-text-muted">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
            Loading...
          </div>
        ) : approvals.length === 0 ? (
          <div className="py-8 text-center text-text-muted">
            <Check className="w-8 h-8 mx-auto mb-2 text-accent-green" />
            <div className="text-sm">No pending approvals</div>
            <div className="text-xs mt-1">All clear!</div>
          </div>
        ) : (
          approvals.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onRespond={handleRespond}
            />
          ))
        )}
      </div>
    </div>
  )
}
