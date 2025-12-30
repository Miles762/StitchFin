import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi } from '../api/sessions'
import { Session, Message } from '../types'

export function useChat(agentId: string, existingSessionId?: string) {
  const [session, setSession] = useState<Session | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!agentId) return

    setLoading(true)

    // If we have an existing session ID, try to restore it
    if (existingSessionId) {
      Promise.all([
        sessionsApi.get(existingSessionId),
        sessionsApi.getMessages(existingSessionId)
      ])
        .then(([sessionRes, messagesRes]) => {
          // Verify the session belongs to the selected agent
          if (sessionRes.data.agent_id === agentId) {
            setSession(sessionRes.data)
            setMessages(messagesRes.data)
            setError('')
          } else {
            // Agent mismatch - create new session
            createNewSession()
          }
        })
        .catch(() => {
          // Session not found or error - create new session
          createNewSession()
        })
        .finally(() => setLoading(false))
    } else {
      // No existing session - create new one
      createNewSession()
    }

    function createNewSession() {
      sessionsApi.create({
        agent_id: agentId,
        customer_id: 'dashboard-user',
        channel: 'voice'
      })
        .then(({ data }) => {
          setSession(data)
          setMessages([])
          setError('')
        })
        .catch(err => {
          setError('Failed to create session')
        })
        .finally(() => setLoading(false))
    }
  }, [agentId, existingSessionId])

  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!session) throw new Error('No session')
      const { data } = await sessionsApi.sendMessage(
        session.id,
        content,
        `msg-${Date.now()}`
      )
      return { content, assistantMessage: data }
    },
    onMutate: async (content) => {
      // Optimistic update - add user message
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        session_id: session!.id,
        role: 'user',
        content,
        tools_called: [],
        created_at: new Date().toISOString()
      }
      setMessages((prev) => [...prev, userMessage])
    },
    onSuccess: (data) => {
      // Replace temp message with real user message + add assistant message
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        session_id: session!.id,
        role: 'user',
        content: data.content,
        tools_called: [],
        created_at: new Date().toISOString()
      }
      setMessages((prev) => [
        ...prev.filter(m => !m.id.startsWith('temp-')),
        userMessage,
        data.assistantMessage
      ])
      setError('')
    },
    onError: (err: any) => {
      setMessages((prev) => prev.filter(m => !m.id.startsWith('temp-')))
      setError(err.response?.data?.error || 'Failed to send message')
    }
  })

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message])
  }

  return {
    session,
    messages,
    sendMessage: sendMessageMutation.mutate,
    addMessage,
    isLoading: sendMessageMutation.isPending || loading,
    error,
    setSession
  }
}
