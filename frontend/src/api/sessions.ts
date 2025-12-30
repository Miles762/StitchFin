import apiClient from './client'
import { Session, Message } from '../types'

export const sessionsApi = {
  create: (data: {
    agent_id: string
    customer_id?: string
    channel?: string
  }) => apiClient.post<Session>('/api/sessions', data),

  get: (id: string) => apiClient.get<Session>(`/api/sessions/${id}`),

  sendMessage: (sessionId: string, content: string, idempotencyKey?: string) =>
    apiClient.post<Message>(
      `/api/sessions/${sessionId}/messages`,
      { content },
      idempotencyKey ? {
        headers: { 'Idempotency-Key': idempotencyKey }
      } : undefined
    ),
}
