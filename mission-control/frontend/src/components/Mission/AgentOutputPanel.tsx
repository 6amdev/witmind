import { useEffect, useRef } from 'react'
import { Terminal, X, Loader2, AlertCircle } from 'lucide-react'
import { useProjectStore } from '../../stores/projectStore'
import clsx from 'clsx'

const agentNames: Record<string, string> = {
  pm: 'Project Manager',
  tech_lead: 'Tech Lead',
  frontend_dev: 'Frontend Dev',
  backend_dev: 'Backend Dev',
  fullstack_dev: 'Fullstack Dev',
  qa_tester: 'QA Tester',
  devops: 'DevOps',
}

const agentIcons: Record<string, string> = {
  pm: '👔',
  tech_lead: '🏗️',
  frontend_dev: '💻',
  backend_dev: '⚙️',
  fullstack_dev: '🔧',
  qa_tester: '🧪',
  devops: '🚀',
}

interface AgentOutputPanelProps {
  onClose?: () => void
  className?: string
}

export default function AgentOutputPanel({ onClose, className }: AgentOutputPanelProps) {
  const { activeAgent, agentOutput, clearAgentOutput } = useProjectStore()
  const outputRef = useRef<HTMLPreElement>(null)

  // Auto-scroll to bottom when output changes
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [agentOutput])

  if (!activeAgent) {
    return null
  }

  const agentName = agentNames[activeAgent.agentId] || activeAgent.agentId
  const agentIcon = agentIcons[activeAgent.agentId] || '🤖'
  const isWorking = activeAgent.status === 'working'
  const isError = activeAgent.status === 'error'

  return (
    <div className={clsx(
      'bg-bg-secondary rounded-lg border border-border-default overflow-hidden flex flex-col',
      className
    )}>
      {/* Header */}
      <div className={clsx(
        'flex items-center justify-between px-4 py-3 border-b border-border-default',
        isWorking && 'bg-accent-yellow/10',
        isError && 'bg-accent-red/10'
      )}>
        <div className="flex items-center gap-3">
          <span className="text-xl">{agentIcon}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm">{agentName}</span>
              {isWorking && (
                <span className="flex items-center gap-1 text-xs text-accent-yellow bg-accent-yellow/20 px-2 py-0.5 rounded-full animate-pulse">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Working
                </span>
              )}
              {isError && (
                <span className="flex items-center gap-1 text-xs text-accent-red bg-accent-red/20 px-2 py-0.5 rounded-full">
                  <AlertCircle className="w-3 h-3" />
                  Error
                </span>
              )}
            </div>
            {activeAgent.taskId && (
              <span className="text-xs text-text-muted">
                Task: {activeAgent.taskId.substring(0, 8)}...
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearAgentOutput}
            className="btn-ghost p-1 text-text-muted hover:text-text-primary"
            title="Clear output"
          >
            <Terminal className="w-4 h-4" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="btn-ghost p-1 text-text-muted hover:text-text-primary"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Output */}
      <pre
        ref={outputRef}
        className="flex-1 p-4 text-xs font-mono text-text-secondary overflow-y-auto bg-bg-primary/50 max-h-64 min-h-32"
      >
        {agentOutput || (
          <span className="text-text-muted animate-pulse">
            {isWorking ? 'Waiting for output...' : 'No output yet'}
          </span>
        )}
        {isWorking && agentOutput && (
          <span className="inline-block w-2 h-4 bg-accent-yellow ml-1 animate-pulse" />
        )}
      </pre>
    </div>
  )
}
