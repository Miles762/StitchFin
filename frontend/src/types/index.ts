export interface Agent {
  id: string
  tenant_id: string
  name: string
  primary_provider: 'vendorA' | 'vendorB'
  fallback_provider?: 'vendorA' | 'vendorB'
  system_prompt: string
  enabled_tools: string[]
  config: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Session {
  id: string
  tenant_id: string
  agent_id: string
  customer_id?: string
  channel: string
  metadata: Record<string, any>
  created_at: string
  messages?: Message[]
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  provider_used?: string
  tokens_in?: number
  tokens_out?: number
  latency_ms?: number
  tools_called: string[]
  correlation_id?: string
  cost_usd?: string
  created_at: string
}

export interface UsageAnalytics {
  total_sessions: number
  total_messages: number
  total_tokens_in: number
  total_tokens_out: number
  total_cost_usd: string
  breakdown_by_provider: Record<string, {
    sessions: number
    tokens_in: number
    tokens_out: number
    cost_usd: string
  }>
}

export interface TopAgent {
  agent_id: string
  agent_name: string
  total_sessions: number
  total_cost_usd: string
  total_tokens: number
}
