import { useState } from 'react'
import { Plus, Trash2, Edit2, Check, X } from 'lucide-react'
import { useAgents, useCreateAgent, useDeleteAgent } from '../hooks/useAgents'

export default function Agents() {
  const { data: agents, isLoading } = useAgents()
  const createAgent = useCreateAgent()
  const deleteAgent = useDeleteAgent()
  const [showCreateModal, setShowCreateModal] = useState(false)

  if (isLoading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Agents</h1>
            <p className="text-gray-600 mt-1">Manage your AI agents</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agents</h1>
          <p className="text-gray-600 mt-1">Manage your AI agents</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Agent
        </button>
      </div>

      {agents?.length === 0 ? (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Plus className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No agents yet</h3>
          <p className="text-gray-600 mb-6">Create your first agent to get started</p>
          <button onClick={() => setShowCreateModal(true)} className="btn-primary">
            Create Agent
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents?.map((agent) => (
            <div key={agent.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                <button
                  onClick={() => deleteAgent.mutate(agent.id)}
                  className="text-gray-400 hover:text-red-600 transition-colors"
                  title="Delete agent"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-500">Primary:</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    {agent.primary_provider}
                  </span>
                </div>
                {agent.fallback_provider && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500">Fallback:</span>
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                      {agent.fallback_provider}
                    </span>
                  </div>
                )}
              </div>

              {agent.enabled_tools.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-3 border-t border-gray-100">
                  <span className="text-xs text-gray-500">Tools:</span>
                  {agent.enabled_tools.map((tool) => (
                    <span key={tool} className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                      {tool}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreateAgentModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={(data) => {
            createAgent.mutate(data, {
              onSuccess: () => setShowCreateModal(false)
            })
          }}
        />
      )}
    </div>
  )
}

function CreateAgentModal({ onClose, onSubmit }: any) {
  const [formData, setFormData] = useState({
    name: '',
    primary_provider: 'vendorA' as 'vendorA' | 'vendorB',
    fallback_provider: 'vendorB' as 'vendorA' | 'vendorB' | undefined,
    system_prompt: 'You are a helpful AI assistant. Be friendly and professional.',
    enabled_tools: [] as string[]
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold">Create New Agent</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Agent Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              placeholder="Customer Support Bot"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Primary Provider *
              </label>
              <select
                value={formData.primary_provider}
                onChange={(e) => setFormData({ ...formData, primary_provider: e.target.value as any })}
                className="input"
              >
                <option value="vendorA">VendorA ($0.002/1K tokens)</option>
                <option value="vendorB">VendorB ($0.003/1K tokens)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fallback Provider
              </label>
              <select
                value={formData.fallback_provider || ''}
                onChange={(e) => setFormData({ ...formData, fallback_provider: e.target.value as any || undefined })}
                className="input"
              >
                <option value="">None</option>
                <option value="vendorA">VendorA</option>
                <option value="vendorB">VendorB</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              System Prompt *
            </label>
            <textarea
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              className="input"
              rows={4}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enabled Tools
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.enabled_tools.includes('invoice_lookup')}
                onChange={(e) => {
                  setFormData({
                    ...formData,
                    enabled_tools: e.target.checked ? ['invoice_lookup'] : []
                  })
                }}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm">Invoice Lookup</span>
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn-primary flex-1">
              Create Agent
            </button>
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
