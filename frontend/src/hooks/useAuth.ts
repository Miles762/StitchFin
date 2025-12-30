import { useState, useEffect } from 'react'

export function useAuth() {
  const [apiKey, setApiKey] = useState<string | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem('apiKey')
    if (stored) setApiKey(stored)
  }, [])

  const login = (key: string) => {
    localStorage.setItem('apiKey', key)
    setApiKey(key)
  }

  const logout = () => {
    localStorage.removeItem('apiKey')
    setApiKey(null)
  }

  return { apiKey, login, logout, isAuthenticated: !!apiKey }
}
