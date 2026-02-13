import axios from 'axios'
import type {
  Project,
  ProjectCreate,
  Task,
  TaskCreate,
  TaskMove,
  Agent,
  Activity,
  ApprovalRequest,
  AgentCommand,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Project file info
export interface ProjectFile {
  path: string
  name: string
  size: number
  extension: string
}

export interface ProjectFilesResponse {
  files: ProjectFile[]
  total_size: number
  file_count: number
  output_dir: string
}

// Projects
export const projectsApi = {
  list: () => api.get<Project[]>('/projects').then((r) => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then((r) => r.data),
  create: (data: ProjectCreate) =>
    api.post<Project>('/projects', data).then((r) => r.data),
  update: (id: string, data: Partial<Project>) =>
    api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  start: (id: string) =>
    api.post<Project>(`/projects/${id}/start`).then((r) => r.data),
  complete: (id: string, outputDir?: string, previewUrl?: string) =>
    api.post<Project>(`/projects/${id}/complete`, {
      output_dir: outputDir,
      preview_url: previewUrl,
    }).then((r) => r.data),
  getFiles: (id: string) =>
    api.get<ProjectFilesResponse>(`/projects/${id}/files`).then((r) => r.data),
  getDownloadUrl: (id: string) => `/api/projects/${id}/download`,
}

// Tasks
export const tasksApi = {
  list: (projectId: string) =>
    api.get<Task[]>(`/projects/${projectId}/tasks`).then((r) => r.data),
  get: (id: string) => api.get<Task>(`/tasks/${id}`).then((r) => r.data),
  create: (projectId: string, data: TaskCreate) =>
    api.post<Task>(`/projects/${projectId}/tasks`, data).then((r) => r.data),
  update: (id: string, data: Partial<Task>) =>
    api.patch<Task>(`/tasks/${id}`, data).then((r) => r.data),
  move: (id: string, data: TaskMove) =>
    api.patch<Task>(`/tasks/${id}/move`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/tasks/${id}`),
}

// Agents
export const agentsApi = {
  list: (team?: string) =>
    api.get<Agent[]>('/agents', { params: { team } }).then((r) => r.data),
  get: (id: string) => api.get<Agent>(`/agents/${id}`).then((r) => r.data),
  getStatus: (id: string) =>
    api.get<{ agent_id: string; status: string; current_task_id?: string }>(
      `/agents/${id}/status`
    ).then((r) => r.data),
}

// Activities
export const activitiesApi = {
  listByProject: (projectId: string) =>
    api.get<Activity[]>(`/projects/${projectId}/activities`).then((r) => r.data),
  listByTask: (taskId: string) =>
    api.get<Activity[]>(`/tasks/${taskId}/activities`).then((r) => r.data),
  listRecent: (limit = 20, agentTypesOnly = true) =>
    api.get<Activity[]>('/activities/recent', {
      params: { limit, agent_types_only: agentTypesOnly }
    }).then((r) => r.data),
  addComment: (taskId: string, text: string, parentId?: string) =>
    api
      .post<Activity>(`/tasks/${taskId}/comments`, null, {
        params: { text, parent_id: parentId },
      })
      .then((r) => r.data),
  update: (id: string, text: string) =>
    api.patch<Activity>(`/activities/${id}`, null, { params: { text } }).then((r) => r.data),
  delete: (id: string) => api.delete(`/activities/${id}`),
  addReaction: (id: string, emoji: string) =>
    api.post(`/activities/${id}/reactions`, null, { params: { emoji } }),
}

// Approvals
export const approvalsApi = {
  list: (projectId?: string, pendingOnly = true) =>
    api.get<ApprovalRequest[]>('/approvals', {
      params: { project_id: projectId, pending_only: pendingOnly }
    }).then((r) => r.data),
  get: (id: string) =>
    api.get<ApprovalRequest>(`/approvals/${id}`).then((r) => r.data),
  respond: (id: string, action: 'approve' | 'reject', selectedOptionId?: string, note?: string) =>
    api.post<ApprovalRequest>(`/approvals/${id}/respond`, {
      action,
      selected_option_id: selectedOptionId,
      note,
    }).then((r) => r.data),
}

// Agent Commands
export const commandsApi = {
  send: (agentId: string, command: AgentCommand) =>
    api.post(`/agents/${agentId}/command`, command).then((r) => r.data),
  list: (agentId: string, pendingOnly = true) =>
    api.get(`/agents/${agentId}/commands`, {
      params: { pending_only: pendingOnly }
    }).then((r) => r.data),
}

// Platform API for running tasks with AI agents
const platformApi = axios.create({
  baseURL: import.meta.env.VITE_PLATFORM_API_URL || 'http://192.168.80.203:4005',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const platformAgentsApi = {
  // Run a single task with an agent
  runTask: (taskId: string, agentId?: string) =>
    platformApi.post('/run-task', { task_id: taskId, agent_id: agentId }).then((r) => r.data),

  // Run multiple tasks
  runTasks: (taskIds: string[], agentId?: string) =>
    platformApi.post('/run-tasks', { task_ids: taskIds, agent_id: agentId }).then((r) => r.data),

  // Get queue status
  getQueueStatus: () =>
    platformApi.get('/queue-status').then((r) => r.data),

  // Health check
  health: () =>
    platformApi.get('/health').then((r) => r.data),
}

// Auth
export interface LoginResponse {
  token: string
  expires_at: string
}

export interface VerifyResponse {
  valid: boolean
  expires_at?: string
}

export const authApi = {
  login: (password: string) =>
    api.post<LoginResponse>('/auth/login', { password }).then((r) => r.data),
  verify: () =>
    api.get<VerifyResponse>('/auth/verify').then((r) => r.data),
}

export default api
