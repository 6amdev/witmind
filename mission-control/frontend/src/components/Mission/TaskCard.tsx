import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { MessageSquare, Paperclip, CheckSquare, Square, CheckSquare2 } from 'lucide-react'
import clsx from 'clsx'
import type { Task } from '../../types'

interface TaskCardProps {
  task: Task
  isDragging?: boolean
  onClick?: () => void
  selectionMode?: boolean
  isSelected?: boolean
  onSelect?: (taskId: string, selected: boolean) => void
}

const priorityColors = {
  low: 'bg-text-muted',
  normal: 'bg-accent-blue',
  high: 'bg-accent-orange',
  urgent: 'bg-accent-red',
}

const agentIcons: Record<string, string> = {
  pm: '👔',
  business_analyst: '📋',
  tech_lead: '🏗️',
  uxui_designer: '🎨',
  frontend_dev: '💻',
  backend_dev: '⚙️',
  fullstack_dev: '🔧',
  mobile_dev: '📱',
  qa_tester: '🧪',
  security_auditor: '🔒',
  devops: '🚀',
}

export default function TaskCard({
  task,
  isDragging = false,
  onClick,
  selectionMode = false,
  isSelected = false,
  onSelect
}: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isSortableDragging,
  } = useSortable({ id: task.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const checklistDone = task.checklist.filter((c) => c.done).length
  const checklistTotal = task.checklist.length

  const handleClick = () => {
    // In selection mode, toggle selection
    if (selectionMode && onSelect) {
      onSelect(task.id, !isSelected)
      return
    }
    // Only trigger click if not dragging
    if (!isDragging && !isSortableDragging && onClick) {
      onClick()
    }
  }

  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onSelect) {
      onSelect(task.id, !isSelected)
    }
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={handleClick}
      className={clsx(
        'card p-3 cursor-pointer',
        'hover:border-border-default/80 transition-all duration-150',
        (isDragging || isSortableDragging) && 'opacity-50 shadow-lg rotate-2 cursor-grabbing',
        isSelected && 'ring-2 ring-accent-blue border-accent-blue'
      )}
    >
      {/* Priority & Title */}
      <div className="flex items-start gap-2 mb-2">
        {/* Selection checkbox */}
        {selectionMode && (
          <button
            onClick={handleCheckboxClick}
            className="flex-shrink-0 mt-0.5"
          >
            {isSelected ? (
              <CheckSquare2 className="w-4 h-4 text-accent-blue" />
            ) : (
              <Square className="w-4 h-4 text-text-muted hover:text-accent-blue" />
            )}
          </button>
        )}
        {!selectionMode && (
          <span
            className={clsx(
              'w-2 h-2 rounded-full mt-1.5 flex-shrink-0',
              priorityColors[task.priority]
            )}
          />
        )}
        <span className="font-medium text-sm leading-tight">{task.title}</span>
      </div>

      {/* Labels */}
      {task.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {task.labels.map((label) => (
            <span
              key={label}
              className="text-xs px-1.5 py-0.5 bg-bg-tertiary rounded text-text-secondary"
            >
              {label}
            </span>
          ))}
        </div>
      )}

      {/* Checklist progress */}
      {checklistTotal > 0 && (
        <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
          <CheckSquare className="w-3 h-3" />
          <span>
            {checklistDone}/{checklistTotal}
          </span>
          <div className="flex-1 h-1 bg-bg-tertiary rounded-full overflow-hidden">
            <div
              className="h-full bg-accent-green"
              style={{ width: `${(checklistDone / checklistTotal) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-border-muted">
        <div className="flex items-center gap-3 text-text-muted">
          <span className="flex items-center gap-1 text-xs">
            <Paperclip className="w-3 h-3" />0
          </span>
          <span className="flex items-center gap-1 text-xs">
            <MessageSquare className="w-3 h-3" />0
          </span>
        </div>

        {/* Assignee */}
        {task.assigned_to && (
          <span
            className="w-6 h-6 rounded-full bg-bg-tertiary flex items-center justify-center text-sm"
            title={task.assigned_to}
          >
            {agentIcons[task.assigned_to] || '🤖'}
          </span>
        )}
      </div>
    </div>
  )
}
