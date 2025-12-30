import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, DollarSign, Clock, Volume2, FileAudio } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAgents } from '../hooks/useAgents'
import { useChat } from '../hooks/useChat'
import { Message } from '../types'
import VoiceRecorder from '../components/VoiceRecorder'
import { sendVoiceMessage, downloadVoiceAudio } from '../api/voice'

export default function Chat() {
  const { data: agents } = useAgents()
  const [selectedAgentId, setSelectedAgentId] = useState('')
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [voiceLoading, setVoiceLoading] = useState(false)
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const navigate = useNavigate()
  const location = useLocation()

  const { session, messages, sendMessage, isLoading, error, addMessage } = useChat(selectedAgentId)

  // Clean URL query parameters on mount
  useEffect(() => {
    if (location.search) {
      navigate('/chat', { replace: true })
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || !session) return
    sendMessage(input)
    setInput('')
  }

  const handleVoiceMessage = async (audioFile: File) => {
    if (!session) return

    setVoiceLoading(true)
    setVoiceError(null)

    try {
      const apiKey = localStorage.getItem('apiKey')
      if (!apiKey) throw new Error('No API key found')

      // Add user message placeholder
      addMessage({
        id: `voice-${Date.now()}`,
        role: 'user',
        content: '🎤 Voice message (transcribing...)',
        session_id: session.id,
        created_at: new Date().toISOString()
      })

      const response = await sendVoiceMessage(session.id, audioFile, apiKey)

      // Update user message with transcription
      addMessage({
        id: `user-voice-${Date.now()}`,
        role: 'user',
        content: `🎤 ${response.user_message.content}`,
        session_id: session.id,
        created_at: new Date().toISOString()
      })

      // Add assistant message with audio
      addMessage({
        id: response.assistant_message.id,
        role: 'assistant',
        content: response.assistant_message.content,
        provider_used: response.assistant_message.provider_used,
        tokens_in: response.assistant_message.tokens_in,
        tokens_out: response.assistant_message.tokens_out,
        latency_ms: response.assistant_message.latency_ms,
        cost_usd: '0.000000', // Will be calculated
        session_id: session.id,
        created_at: new Date().toISOString(),
        voice_audio_url: response.audio_download_url,
        voice_message_id: response.assistant_message.id
      })

    } catch (err: any) {
      console.error('Voice message error:', err)
      setVoiceError(err.response?.data?.detail || err.message || 'Failed to send voice message')
    } finally {
      setVoiceLoading(false)
    }
  }

  const playVoiceResponse = async (messageId: string) => {
    if (!session) return

    try {
      const apiKey = localStorage.getItem('apiKey')
      if (!apiKey) throw new Error('No API key found')

      const audioBlob = await downloadVoiceAudio(session.id, messageId, apiKey)
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      audio.play()
    } catch (err) {
      console.error('Error playing audio:', err)
      alert('Failed to play voice response')
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Chat</h1>
        <p className="text-gray-600 mt-1">Test your agents with text or voice</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="font-semibold mb-4">Select Agent</h2>
            <div className="space-y-2">
              {agents?.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    selectedAgentId === agent.id
                      ? 'bg-primary-50 text-primary-700 border border-primary-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="font-medium text-sm">{agent.name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {agent.primary_provider}
                  </div>
                </button>
              ))}
            </div>

            {/* Voice Instructions */}
            {selectedAgentId && session && (
              <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="text-sm font-semibold text-blue-900 mb-2">
                  🎤 Voice Mode
                </h3>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>• Click mic to record</li>
                  <li>• Click upload for files</li>
                  <li>• Click speaker to play AI voice</li>
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="lg:col-span-3">
          {!selectedAgentId ? (
            <div className="card text-center py-12">
              <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select an agent to start chatting
              </h3>
              <p className="text-gray-600">Choose an agent from the sidebar</p>
            </div>
          ) : (
            <div className="card h-[calc(100vh-16rem)] flex flex-col">
              {/* Session Info */}
              {session && (
                <div className="mb-4 pb-3 border-b border-gray-200">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-4">
                      <div>
                        <span className="text-gray-500">Session ID:</span>
                        <code className="ml-2 px-2 py-1 bg-gray-100 rounded text-gray-800 font-mono">
                          {session.id}
                        </code>
                      </div>
                      <div>
                        <span className="text-gray-500">Agent:</span>
                        <span className="ml-2 px-2 py-1 bg-primary-100 text-primary-700 rounded font-medium">
                          {agents?.find(a => a.id === selectedAgentId)?.name}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(session.id)
                        alert('Session ID copied to clipboard!')
                      }}
                      className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
                    >
                      Copy Session ID
                    </button>
                  </div>
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    onPlayVoice={message.voice_message_id ? () => playVoiceResponse(message.voice_message_id!) : undefined}
                  />
                ))}
                {(isLoading || voiceLoading) && (
                  <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
                    <span>{voiceLoading ? 'Processing voice...' : 'Thinking...'}</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-gray-200 pt-4">
                {(error || voiceError) && (
                  <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                    {error || voiceError}
                  </div>
                )}
                <div className="flex gap-2 items-center">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type a message or use voice..."
                    className="input flex-1"
                    disabled={isLoading || voiceLoading}
                  />
                  <button
                    onClick={handleSend}
                    disabled={isLoading || voiceLoading || !input.trim()}
                    className="btn-primary px-6"
                    title="Send text message"
                  >
                    <Send className="w-4 h-4" />
                  </button>

                  <VoiceRecorder
                    onSendVoice={handleVoiceMessage}
                    isLoading={voiceLoading}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message, onPlayVoice }: { message: Message & { voice_message_id?: string, voice_audio_url?: string }, onPlayVoice?: () => void }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div className="flex items-start gap-2">
          {!isUser && (
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-primary-600" />
            </div>
          )}
          <div>
            <div
              className={`px-4 py-3 rounded-2xl ${
                isUser
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.content}
            </div>

            {!isUser && (
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                {onPlayVoice && (
                  <button
                    onClick={onPlayVoice}
                    className="flex items-center gap-1 px-2 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded transition-colors"
                    title="Play AI voice response"
                  >
                    <Volume2 className="w-3 h-3" />
                    <span>Play Voice</span>
                  </button>
                )}
                {message.cost_usd && (
                  <div className="flex items-center gap-1">
                    <DollarSign className="w-3 h-3" />
                    <span>${parseFloat(message.cost_usd).toFixed(6)}</span>
                  </div>
                )}
                {message.latency_ms && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{message.latency_ms}ms</span>
                  </div>
                )}
                {message.tokens_in && message.tokens_out && (
                  <span>
                    {message.tokens_in + message.tokens_out} tokens
                  </span>
                )}
                {message.provider_used && (
                  <span className="px-2 py-0.5 bg-gray-200 rounded">
                    {message.provider_used}
                  </span>
                )}
              </div>
            )}
          </div>
          {isUser && (
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-gray-600" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
