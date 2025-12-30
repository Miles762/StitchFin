import { useState } from 'react'
import { DollarSign, MessageSquare, Hash, TrendingUp } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analytics'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function Analytics() {
  const [dateRange, setDateRange] = useState({ start: '', end: '' })

  const { data: usage } = useQuery({
    queryKey: ['analytics', 'usage', dateRange],
    queryFn: async () => {
      const { data } = await analyticsApi.getUsage(dateRange.start, dateRange.end)
      return data
    }
  })

  const { data: topAgents } = useQuery({
    queryKey: ['analytics', 'top-agents'],
    queryFn: async () => {
      const { data } = await analyticsApi.getTopAgents(5)
      return data
    }
  })

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600 mt-1">Monitor usage and costs</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          icon={<MessageSquare className="w-6 h-6" />}
          label="Total Sessions"
          value={usage?.total_sessions || 0}
          color="blue"
        />
        <StatsCard
          icon={<Hash className="w-6 h-6" />}
          label="Total Messages"
          value={usage?.total_messages || 0}
          color="green"
        />
        <StatsCard
          icon={<TrendingUp className="w-6 h-6" />}
          label="Total Tokens"
          value={(usage?.total_tokens_in || 0) + (usage?.total_tokens_out || 0)}
          color="purple"
        />
        <StatsCard
          icon={<DollarSign className="w-6 h-6" />}
          label="Total Cost"
          value={`$${parseFloat(usage?.total_cost_usd || '0').toFixed(4)}`}
          color="yellow"
        />
      </div>

      {/* Provider Breakdown */}
      {usage && (
        <div className="card mb-8">
          <h2 className="text-lg font-semibold mb-4">Provider Breakdown</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(usage.breakdown_by_provider).map(([provider, stats]) => ({
              provider,
              cost: parseFloat(stats.cost_usd),
              sessions: stats.sessions
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="provider" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="cost" fill="#3b82f6" name="Cost ($)" />
              <Bar dataKey="sessions" fill="#10b981" name="Sessions" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Agents */}
      {topAgents && topAgents.agents.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Top Agents by Cost</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200">
                <tr className="text-left text-sm text-gray-600">
                  <th className="pb-3">Agent</th>
                  <th className="pb-3">Sessions</th>
                  <th className="pb-3">Tokens</th>
                  <th className="pb-3 text-right">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {topAgents.agents.map((agent) => (
                  <tr key={agent.agent_id} className="text-sm">
                    <td className="py-3 font-medium">{agent.agent_name}</td>
                    <td className="py-3 text-gray-600">{agent.total_sessions}</td>
                    <td className="py-3 text-gray-600">{agent.total_tokens.toLocaleString()}</td>
                    <td className="py-3 text-right font-medium">
                      ${parseFloat(agent.total_cost_usd).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function StatsCard({ icon, label, value, color }: any) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    yellow: 'bg-yellow-50 text-yellow-600',
  }

  return (
    <div className="card">
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colors[color]}`}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-600">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}
