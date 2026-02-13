import { create } from 'zustand'
import type { Project, Task, Activity } from '../types'

interface AgentStatus {
  agentId: string
  status: 'standby' | 'working' | 'error'
  taskId?: string
  output?: string
}

interface ProjectState {
  // Current project
  currentProject: Project | null
  setCurrentProject: (project: Project | Partial<Project> | null) => void

  // Tasks grouped by status
  tasks: Task[]
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTask: (task: Task) => void
  removeTask: (taskId: string) => void

  // UI state
  selectedTaskId: string | null
  setSelectedTaskId: (id: string | null) => void

  // Real-time agent state
  activeAgent: AgentStatus | null
  setActiveAgent: (agent: AgentStatus | null) => void
  agentOutput: string
  appendAgentOutput: (output: string) => void
  clearAgentOutput: () => void

  // Recent activities (for live updates)
  recentActivities: Activity[]
  addActivity: (activity: Activity) => void
  setActivities: (activities: Activity[]) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  // Current project
  currentProject: null,
  setCurrentProject: (project) => set((state) => ({
    currentProject: project ? { ...state.currentProject, ...project } as Project : null
  })),

  // Tasks
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) =>
    set((state) => ({
      tasks: [...state.tasks, task],
    })),
  updateTask: (task) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === task.id ? { ...t, ...task } : t)),
    })),
  removeTask: (taskId) =>
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== taskId),
    })),

  // UI state
  selectedTaskId: null,
  setSelectedTaskId: (id) => set({ selectedTaskId: id }),

  // Real-time agent state
  activeAgent: null,
  setActiveAgent: (agent) => set({ activeAgent: agent }),
  agentOutput: '',
  appendAgentOutput: (output) => set((state) => ({
    agentOutput: state.agentOutput + output
  })),
  clearAgentOutput: () => set({ agentOutput: '' }),

  // Recent activities
  recentActivities: [],
  addActivity: (activity) => set((state) => ({
    recentActivities: [activity, ...state.recentActivities].slice(0, 50)
  })),
  setActivities: (activities) => set({ recentActivities: activities }),
}))
