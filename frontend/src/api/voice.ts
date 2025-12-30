import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

export interface VoiceMessageResponse {
  session_id: string
  correlation_id: string
  user_message: {
    content: string
    language?: string
    duration_seconds?: number
  }
  assistant_message: {
    id: string
    content: string
    provider_used: string
    tokens_in: number
    tokens_out: number
    latency_ms: number
    correlation_id: string
  }
  audio_download_url: string
  stt_latency_ms: number
  tts_latency_ms: number
  total_latency_ms: number
}

export const sendVoiceMessage = async (
  sessionId: string,
  audioFile: File,
  apiKey: string
): Promise<VoiceMessageResponse> => {
  const formData = new FormData()
  formData.append('audio_file', audioFile)

  const { data } = await axios.post(
    `${API_URL}/sessions/${sessionId}/voice/message`,
    formData,
    {
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'multipart/form-data'
      }
    }
  )

  return data
}

export const downloadVoiceAudio = async (
  sessionId: string,
  messageId: string,
  apiKey: string
): Promise<Blob> => {
  const { data } = await axios.get(
    `${API_URL}/sessions/${sessionId}/voice/audio/${messageId}`,
    {
      headers: {
        'X-API-Key': apiKey
      },
      responseType: 'blob'
    }
  )

  return data
}
