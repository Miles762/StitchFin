import apiClient from './client'
import { Agent } from '../types'

export const agentsApi = {
  list: () => apiClient.get<Agent[]>('/api/agents'),

  create: (data: {
    name: string
    primary_provider: 'vendorA' | 'vendorB'
    fallback_provider?: 'vendorA' | 'vendorB'
    system_prompt: string
    enabled_tools?: string[]
  }) => apiClient.post<Agent>('/api/agents', data),

  update: (id: string, data: Partial<Agent>) =>
    apiClient.put<Agent>(`/api/agents/${id}`, data),

  delete: (id: string) => apiClient.delete(`/api/agents/${id}`),
}
