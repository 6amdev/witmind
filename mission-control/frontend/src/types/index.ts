// Project types
export type ProjectType = 'web' | 'api' | 'mobile' | 'marketing' | 'creative'
export type ProjectStatus = 'draft' | 'planning' | 'in_progress' | 'review' | 'completed' | 'archived'
export type ExecutionMode = 'full_auto' | 'review_first' | 'manual'

export interface Project {
  id: string
  name: string
  description: string
  type?: ProjectType
  team_id?: string
  execution_mode: ExecutionMode
  status: ProjectStatus
  progress: number
  created_at: string
  updated_at: string
  completed_at?: string
  output_dir?: string
  preview_url?: string
  // Git integration
  git_repo_name?: string
  git_repo_url?: string
  git_clone_url?: string
}

export interface ProjectCreate {
  name: string
  description: string
  type?: ProjectType
  team_id?: string
  execution_mode?: ExecutionMode
}

// Task types
export type TaskStatus = 'planned' | 'assigned' | 'working' | 'testing' | 'review' | 'done'
export type TaskPriority = 'low' | 'normal' | 'high' | 'urgent'
export type TaskType = 'feature' | 'bug' | 'improvement' | 'docs' | 'design' | 'review'

export interface ChecklistItem {
  id: string
  text: string
  done: boolean
  done_at?: string
}

export interface Task {
  id: string
  project_id: string
  title: string
  description?: string
  type: TaskType
  status: TaskStatus
  priority: TaskPriority
  assigned_to?: string
  labels: string[]
  checklist: ChecklistItem[]
  order: number
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string
  type?: TaskType
  priority?: TaskPriority
  labels?: string[]
}

export interface TaskMove {
  status: TaskStatus
  order?: number
}

// Agent types
export type AgentStatus = 'standby' | 'working' | 'blocked' | 'error' | 'offline'
export type AgentTeam = 'dev' | 'marketing' | 'creative'

export interface Agent {
  id: string
  name: string
  team: AgentTeam
  role: string
  description: string
  icon: string
  status: AgentStatus
  current_task_id?: string
}

// Activity types
export type ActivityType =
  | 'comment'
  | 'status_change'
  | 'assignment'
  | 'attachment'
  | 'checklist'
  | 'code_change'
  | 'review'
  | 'blocker'
  | 'created'
  // Agent work types
  | 'agent_started'
  | 'agent_progress'
  | 'agent_completed'
  | 'agent_error'

export type ActorType = 'agent' | 'user' | 'system'

export interface ActivityLink {
  label: string
  url?: string
  path?: string
  type: string // file, url, commit, pr
}

export interface ActivityContent {
  text?: string
  mentions?: string[]
  from_status?: string
  to_status?: string
  files_changed?: string[]
  lines_added?: number
  lines_removed?: number
  commit_message?: string
  file_name?: string
  file_url?: string
  file_type?: string
  item_id?: string
  item_text?: string
  checked?: boolean
  // Agent work content
  message?: string
  output?: string
  links?: ActivityLink[]
  error?: string
  duration_ms?: number
}

export interface Activity {
  id: string
  project_id: string
  task_id?: string
  type: ActivityType
  actor_type: ActorType
  actor_id: string
  actor_name: string
  actor_icon: string
  content: ActivityContent
  parent_id?: string
  reactions: { emoji: string; user_id: string }[]
  created_at: string
}

// Approval types
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired'
export type ApprovalType = 'code_change' | 'deploy' | 'external_api' | 'file_delete' | 'install_package' | 'custom'

export interface ApprovalOption {
  id: string
  label: string
  description?: string
}

export interface ApprovalRequest {
  id: string
  agent_id: string
  agent_name: string
  agent_icon: string
  project_id: string
  task_id?: string
  type: ApprovalType
  title: string
  description: string
  details?: string
  options: ApprovalOption[]
  status: ApprovalStatus
  selected_option_id?: string
  response_note?: string
  responded_by?: string
  created_at: string
  responded_at?: string
  expires_at: string
}

// Agent Command types
export type AgentCommandType = 'start' | 'pause' | 'resume' | 'abort'

export interface AgentCommand {
  command: AgentCommandType
  task_id?: string
  message?: string
}
