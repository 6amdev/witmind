import { useState } from 'react'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, CheckCircle, Loader2, ListChecks, X, Rocket } from 'lucide-react'
import { tasksApi, projectsApi, platformAgentsApi } from '../../services/api'
import KanbanColumn from './KanbanColumn'
import TaskCard from './TaskCard'
import TaskModal from './TaskModal'
import CreateTaskModal from './CreateTaskModal'
import type { Task, TaskStatus } from '../../types'

interface KanbanBoardProps {
  projectId: string
  tasks: Task[]
  isLoading: boolean
  projectStatus?: string
}

const columns: { id: TaskStatus; title: string; color: string }[] = [
  { id: 'planned', title: 'PLANNED', color: 'text-text-muted' },
  { id: 'assigned', title: 'ASSIGNED', color: 'text-accent-blue' },
  { id: 'working', title: 'WORKING', color: 'text-accent-yellow' },
  { id: 'testing', title: 'TESTING', color: 'text-accent-purple' },
  { id: 'review', title: 'REVIEW', color: 'text-accent-orange' },
  { id: 'done', title: 'DONE', color: 'text-accent-green' },
]

export default function KanbanBoard({ projectId, tasks, isLoading, projectStatus }: KanbanBoardProps) {
  const queryClient = useQueryClient()
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<string>>(new Set())
  const [isRunning, setIsRunning] = useState(false)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const moveMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: TaskStatus }) =>
      tasksApi.move(taskId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
    },
  })

  // Approve and start project
  const handleApproveAndRun = async () => {
    setIsApproving(true)
    try {
      await projectsApi.update(projectId, { status: 'in_progress' })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    } catch (error) {
      console.error('Failed to approve project:', error)
    } finally {
      setIsApproving(false)
    }
  }

  // Toggle task selection
  const handleTaskSelect = (taskId: string, selected: boolean) => {
    setSelectedTaskIds(prev => {
      const newSet = new Set(prev)
      if (selected) {
        newSet.add(taskId)
      } else {
        newSet.delete(taskId)
      }
      return newSet
    })
  }

  // Select all planned tasks
  const handleSelectAll = () => {
    const plannedTasks = tasks.filter(t => t.status === 'planned')
    setSelectedTaskIds(new Set(plannedTasks.map(t => t.id)))
  }

  // Clear selection
  const handleClearSelection = () => {
    setSelectedTaskIds(new Set())
    setSelectionMode(false)
  }

  // Run selected tasks
  const handleRunSelected = async () => {
    if (selectedTaskIds.size === 0) return

    setIsRunning(true)
    try {
      // Update project status to in_progress if not already
      if (projectStatus !== 'in_progress') {
        await projectsApi.update(projectId, { status: 'in_progress' })
      }

      // Dispatch tasks to Platform API for AI agent execution
      const taskIdsArray = Array.from(selectedTaskIds)

      try {
        // Send all tasks to Platform API
        await platformAgentsApi.runTasks(taskIdsArray)
        console.log(`Dispatched ${taskIdsArray.length} tasks to Platform API`)
      } catch (platformError) {
        console.warn('Platform API not available, moving tasks manually:', platformError)
        // Fallback: just move tasks to working status
        for (const taskId of taskIdsArray) {
          await tasksApi.move(taskId, { status: 'working' })
        }
      }

      // Refresh data
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })

      // Clear selection
      handleClearSelection()
    } catch (error) {
      console.error('Failed to run tasks:', error)
    } finally {
      setIsRunning(false)
    }
  }

  const handleDragStart = (event: DragStartEvent) => {
    const task = tasks.find((t) => t.id === event.active.id)
    if (task) setActiveTask(task)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    setActiveTask(null)

    if (!over) return

    const taskId = active.id as string
    const newStatus = over.id as TaskStatus

    const task = tasks.find((t) => t.id === taskId)
    if (!task || task.status === newStatus) return

    // Optimistic update
    queryClient.setQueryData(['tasks', projectId], (oldTasks: Task[]) =>
      oldTasks.map((t) =>
        t.id === taskId ? { ...t, status: newStatus } : t
      )
    )

    // API call
    moveMutation.mutate({ taskId, status: newStatus })
  }

  // Group tasks by status
  const tasksByStatus = columns.reduce((acc, col) => {
    acc[col.id] = tasks.filter((t) => t.status === col.id)
    return acc
  }, {} as Record<TaskStatus, Task[]>)

  if (isLoading) {
    return (
      <div className="flex gap-4 h-full">
        {columns.map((col) => (
          <div key={col.id} className="flex-1 bg-bg-secondary/50 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  // Show empty state when no tasks
  const hasNoTasks = tasks.length === 0
  const isPlanningOrDraft = projectStatus === 'planning' || projectStatus === 'draft'

  if (hasNoTasks && isPlanningOrDraft) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div className="w-16 h-16 mb-4 rounded-full bg-accent-blue/10 flex items-center justify-center">
          {projectStatus === 'planning' ? (
            <svg className="w-8 h-8 text-accent-blue animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-8 h-8 text-accent-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          )}
        </div>
        <h3 className="text-lg font-medium text-text-primary mb-2">
          {projectStatus === 'planning' ? 'Planning in Progress...' : 'No Tasks Yet'}
        </h3>
        <p className="text-sm text-text-muted max-w-md mb-4">
          {projectStatus === 'planning'
            ? 'The PM agent is analyzing your project and creating tasks. This may take a moment.'
            : 'Click "Start Project" to begin planning, or add tasks manually using the + button.'}
        </p>
        {projectStatus === 'planning' && (
          <div className="flex items-center gap-2 text-xs text-accent-blue">
            <span className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
            Agents are working...
          </div>
        )}
      </div>
    )
  }

  // Show review banner when project is ready for review
  const isReviewStatus = projectStatus === 'review'

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Review Banner */}
      {isReviewStatus && !selectionMode && (
        <div className="bg-accent-purple/10 border border-accent-purple/30 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-purple/20 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-accent-purple" />
            </div>
            <div>
              <h4 className="font-medium text-text-primary">Plan Ready for Review</h4>
              <p className="text-sm text-text-muted">
                PM Agent has created {tasks.length} tasks. Click task to edit, or select tasks to run.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSelectionMode(true)
                handleSelectAll()
              }}
              className="btn-ghost flex items-center gap-2 px-4"
            >
              <ListChecks className="w-4 h-4" />
              Select Tasks
            </button>
            <button
              onClick={handleApproveAndRun}
              disabled={isApproving}
              className="btn-primary flex items-center gap-2 px-6"
            >
              {isApproving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Rocket className="w-4 h-4" />
                  Run All
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Selection Mode Banner */}
      {selectionMode && (
        <div className="bg-accent-blue/10 border border-accent-blue/30 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-blue/20 flex items-center justify-center">
              <ListChecks className="w-5 h-5 text-accent-blue" />
            </div>
            <div>
              <h4 className="font-medium text-text-primary">
                {selectedTaskIds.size} tasks selected
              </h4>
              <p className="text-sm text-text-muted">
                Click tasks to select/deselect, then run selected tasks.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSelectAll}
              className="btn-ghost px-3 text-sm"
            >
              Select All
            </button>
            <button
              onClick={handleClearSelection}
              className="btn-ghost flex items-center gap-1 px-3"
            >
              <X className="w-4 h-4" />
              Cancel
            </button>
            <button
              onClick={handleRunSelected}
              disabled={selectedTaskIds.size === 0 || isRunning}
              className="btn-primary flex items-center gap-2 px-6"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Selected ({selectedTaskIds.size})
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* In Progress Banner */}
      {projectStatus === 'in_progress' && !selectionMode && (
        <div className="bg-accent-yellow/10 border border-accent-yellow/30 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-yellow/20 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-accent-yellow animate-spin" />
            </div>
            <div>
              <h4 className="font-medium text-text-primary">Project In Progress</h4>
              <p className="text-sm text-text-muted">
                Agents are working on tasks. Drag tasks to update status.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setSelectionMode(true)
            }}
            className="btn-ghost flex items-center gap-2 px-4"
          >
            <ListChecks className="w-4 h-4" />
            Run More Tasks
          </button>
        </div>
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 flex-1 overflow-x-auto pb-4">
        {columns.map((column) => (
          <KanbanColumn
            key={column.id}
            id={column.id}
            title={column.title}
            color={column.color}
            tasks={tasksByStatus[column.id] || []}
            projectId={projectId}
            onTaskClick={(task) => !selectionMode && setSelectedTask(task)}
            onAddTask={column.id === 'planned' ? () => setShowCreateModal(true) : undefined}
            selectionMode={selectionMode}
            selectedTaskIds={selectedTaskIds}
            onTaskSelect={handleTaskSelect}
          />
        ))}
      </div>

      <DragOverlay>
        {activeTask && <TaskCard task={activeTask} isDragging />}
      </DragOverlay>

      {/* Task Detail Modal */}
      {selectedTask && (
        <TaskModal
          task={selectedTask}
          projectId={projectId}
          onClose={() => setSelectedTask(null)}
        />
      )}

      {/* Create Task Modal */}
      {showCreateModal && (
        <CreateTaskModal
          projectId={projectId}
          onClose={() => setShowCreateModal(false)}
        />
      )}
      </DndContext>
    </div>
  )
}
