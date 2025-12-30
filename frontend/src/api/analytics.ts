import apiClient from './client'
import { UsageAnalytics, TopAgent } from '../types'

export const analyticsApi = {
  getUsage: (startDate?: string, endDate?: string) => {
    const params: any = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return apiClient.get<UsageAnalytics>('/api/analytics/usage', { params })
  },

  getTopAgents: (limit = 10) =>
    apiClient.get<{ agents: TopAgent[] }>('/api/analytics/top-agents', {
      params: { limit }
    }),
}
