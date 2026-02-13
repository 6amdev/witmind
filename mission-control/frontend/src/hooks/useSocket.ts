import { useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { io, Socket } from 'socket.io-client'
import { useProjectStore } from '../stores/projectStore'
import { useQueryClient } from '@tanstack/react-query'
import type { Task, Activity } from '../types'

export function useSocket(projectId?: string, options?: { autoNavigateOnComplete?: boolean }) {
  const socketRef = useRef<Socket | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const {
    updateTask,
    setCurrentProject,
    setActiveAgent,
    appendAgentOutput,
    clearAgentOutput,
    addActivity
  } = useProjectStore()

  useEffect(() => {
    // Connect to socket
    socketRef.current = io({
      path: '/socket.io',
      transports: ['websocket', 'polling'],
    })

    const socket = socketRef.current

    socket.on('connect', () => {
      console.log('🔌 Connected to socket')

      // Join project room if we have a project ID
      if (projectId) {
        socket.emit('join_project', { project_id: projectId })
      }
    })

    socket.on('disconnect', () => {
      console.log('🔌 Disconnected from socket')
    })

    // Listen for task updates
    socket.on('task:update', (data: { task: Task }) => {
      console.log('📝 Task updated:', data.task)
      updateTask(data.task)
      // Also invalidate tasks query to ensure UI sync
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
    })

    // Listen for new activities
    socket.on('activity:new', (data: { activity: Activity }) => {
      console.log('📢 New activity:', data.activity)
      addActivity(data.activity)
      // Invalidate activities query
      queryClient.invalidateQueries({ queryKey: ['activities', projectId] })
    })

    // Listen for agent status changes
    socket.on('agent:status', (data: { agent_id: string; status: string; task_id?: string }) => {
      console.log('🤖 Agent status:', data)
      if (data.status === 'working') {
        setActiveAgent({
          agentId: data.agent_id,
          status: 'working',
          taskId: data.task_id
        })
        clearAgentOutput()
      } else if (data.status === 'standby') {
        setActiveAgent(null)
      } else if (data.status === 'error') {
        setActiveAgent({
          agentId: data.agent_id,
          status: 'error',
          taskId: data.task_id
        })
      }
    })

    // Listen for agent output (streaming)
    socket.on('agent:output', (data: { agent_id: string; task_id: string; output: string }) => {
      console.log('📤 Agent output:', data.output?.substring(0, 50))
      appendAgentOutput(data.output)
    })

    // Listen for agent action events
    socket.on('agent:action', (data: { agent_id: string; task_id: string; action: string; message: string }) => {
      console.log('🎬 Agent action:', data)
      // Create a temporary activity for real-time feedback
      addActivity({
        id: `temp-${Date.now()}`,
        task_id: data.task_id,
        project_id: projectId || '',
        type: 'agent_progress',
        actor_type: 'agent',
        actor_id: data.agent_id,
        actor_name: data.agent_id,
        actor_icon: '🤖',
        content: { message: data.message },
        reactions: [],
        created_at: new Date().toISOString()
      } as Activity)
    })

    // Listen for agent complete
    socket.on('agent:complete', (data: { agent_id: string; task_id: string; success: boolean; duration_ms: number }) => {
      console.log('✅ Agent complete:', data)
      setActiveAgent(null)
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      queryClient.invalidateQueries({ queryKey: ['activities', projectId] })
    })

    // Listen for project completion
    socket.on('project:complete', (data: { project_id: string; tasks_completed: number; previewUrl?: string }) => {
      console.log('🎉 Project completed:', data)
      // Update project status in store
      setCurrentProject({ status: 'completed', preview_url: data.previewUrl })
      // Invalidate project query
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      // Auto-navigate to completion page if enabled
      if (options?.autoNavigateOnComplete && data.project_id === projectId) {
        navigate(`/projects/${data.project_id}/complete`)
      }
    })

    return () => {
      if (projectId) {
        socket.emit('leave_project', { project_id: projectId })
      }
      socket.disconnect()
    }
  }, [projectId, updateTask, setCurrentProject, setActiveAgent, appendAgentOutput, clearAgentOutput, addActivity, navigate, queryClient, options?.autoNavigateOnComplete])

  const joinProject = useCallback((id: string) => {
    if (socketRef.current) {
      socketRef.current.emit('join_project', { project_id: id })
    }
  }, [])

  const leaveProject = useCallback((id: string) => {
    if (socketRef.current) {
      socketRef.current.emit('leave_project', { project_id: id })
    }
  }, [])

  return {
    socket: socketRef.current,
    joinProject,
    leaveProject,
  }
}
