import { create } from 'zustand'
import type { Project, Task } from '../types'

interface ProjectState {
  // Current project
  currentProject: Project | null
  setCurrentProject: (project: Project | null) => void

  // Tasks grouped by status
  tasks: Task[]
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTask: (task: Task) => void
  removeTask: (taskId: string) => void

  // UI state
  selectedTaskId: string | null
  setSelectedTaskId: (id: string | null) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  // Current project
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),

  // Tasks
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) =>
    set((state) => ({
      tasks: [...state.tasks, task],
    })),
  updateTask: (task) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
    })),
  removeTask: (taskId) =>
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== taskId),
    })),

  // UI state
  selectedTaskId: null,
  setSelectedTaskId: (id) => set({ selectedTaskId: id }),
}))
