import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Key, AlertCircle } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import apiClient from '../api/client'

export default function Login() {
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Test the API key by fetching agents
      await apiClient.get('/api/agents', {
        headers: { 'X-API-Key': apiKey }
      })

      // If successful, store and navigate
      login(apiKey)
      // Use replace to avoid login page in history
      setTimeout(() => navigate('/agents', { replace: true }), 0)
    } catch (err: any) {
      setError(
        err.response?.status === 401
          ? 'Invalid API key. Please check and try again.'
          : 'Failed to connect to backend. Is the server running?'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-full mb-4">
            <Key className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome Back</h1>
          <p className="text-gray-600 mt-2">
            Enter your API key to access the dashboard
          </p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-2">
                API Key
              </label>
              <input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk_..."
                className="input"
                required
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-2">
                Your API key should start with "sk_"
              </p>
            </div>

            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !apiKey}
              className="btn-primary w-full"
            >
              {loading ? 'Verifying...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">
              <strong>Don't have an API key?</strong> Run the seed script in your backend:
            </p>
            <code className="block mt-2 p-2 bg-gray-100 rounded text-xs">
              python scripts/seed.py
            </code>
          </div>
        </div>
      </div>
    </div>
  )
}
