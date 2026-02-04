import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { Plus } from 'lucide-react'
import TaskCard from './TaskCard'
import type { Task, TaskStatus } from '../../types'
import clsx from 'clsx'

interface KanbanColumnProps {
  id: TaskStatus
  title: string
  color: string
  tasks: Task[]
  projectId: string
  onTaskClick?: (task: Task) => void
  onAddTask?: () => void
  selectionMode?: boolean
  selectedTaskIds?: Set<string>
  onTaskSelect?: (taskId: string, selected: boolean) => void
}

export default function KanbanColumn({
  id,
  title,
  color,
  tasks,
  onTaskClick,
  onAddTask,
  selectionMode = false,
  selectedTaskIds = new Set(),
  onTaskSelect,
}: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id })

  return (
    <div
      ref={setNodeRef}
      className={clsx(
        'flex-shrink-0 w-72 flex flex-col bg-bg-secondary/30 rounded-lg transition-colors',
        isOver && 'bg-accent-blue/5 ring-2 ring-accent-blue/20'
      )}
    >
      {/* Column header */}
      <div className="px-3 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={clsx('font-medium text-sm', color)}>{title}</span>
          <span className="text-xs text-text-muted bg-bg-tertiary px-1.5 py-0.5 rounded">
            {tasks.length}
          </span>
        </div>
        {onAddTask && (
          <button
            onClick={onAddTask}
            className="btn-ghost p-1 text-text-muted hover:text-text-primary"
          >
            <Plus className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Tasks */}
      <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-2">
        <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onClick={() => onTaskClick?.(task)}
              selectionMode={selectionMode}
              isSelected={selectedTaskIds.has(task.id)}
              onSelect={onTaskSelect}
            />
          ))}
        </SortableContext>

        {tasks.length === 0 && (
          <div className="text-center py-8 text-text-muted text-sm">
            No tasks
          </div>
        )}
      </div>
    </div>
  )
}
