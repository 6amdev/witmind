import { useEffect, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'
import { useProjectStore } from '../stores/projectStore'
import type { Task, Activity } from '../types'

export function useSocket(projectId?: string) {
  const socketRef = useRef<Socket | null>(null)
  const { updateTask } = useProjectStore()

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
    })

    // Listen for new activities
    socket.on('activity:new', (data: { activity: Activity }) => {
      console.log('📢 New activity:', data.activity)
      // TODO: Handle new activities
    })

    // Listen for agent status changes
    socket.on('agent:status', (data: { agent_id: string; status: string; task_id?: string }) => {
      console.log('🤖 Agent status:', data)
      // TODO: Update agent status in store
    })

    // Listen for agent output
    socket.on('agent:output', (data: { agent_id: string; task_id: string; output: string }) => {
      console.log('📤 Agent output:', data)
      // TODO: Handle streaming output
    })

    return () => {
      if (projectId) {
        socket.emit('leave_project', { project_id: projectId })
      }
      socket.disconnect()
    }
  }, [projectId, updateTask])

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
