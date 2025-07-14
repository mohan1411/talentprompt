import { useState, useEffect, useCallback, useRef } from 'react'
import { useAuth } from '@/lib/auth/context'

interface WebSocketMessage {
  type: string
  data?: any
  message?: string
  user?: any
  timestamp?: string
}

interface TranscriptionUpdate {
  session_id: string
  timestamp: string
  text: string
  duration: number
  analysis: {
    sentiment: {
      sentiment: 'positive' | 'neutral' | 'negative'
      confidence: number
      emotion: string
    }
    skills_mentioned: string[]
    quality_indicators: {
      uses_examples: boolean
      structured_response: boolean
      uses_numbers: boolean
      confidence_words: number
      hedge_words: number
    }
    word_count: number
    speaking_pace: number
  }
  is_final: boolean
}

interface LiveInsights {
  sentiment: any
  skills_mentioned: string[]
  quality_indicators: any
  speaking_metrics: {
    word_count: number
    speaking_pace: number
  }
  alerts: Array<{
    type: string
    level: 'info' | 'warning' | 'error'
    message: string
  }>
}

interface CoachingSuggestions {
  follow_up_questions: string[]
  dig_deeper_prompts: string[]
  coaching_tips: string[]
  red_flags: string[]
  positive_signals: string[]
}

export function useInterviewWebSocket(sessionId: string) {
  const { token } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [transcription, setTranscription] = useState<TranscriptionUpdate[]>([])
  const [liveInsights, setLiveInsights] = useState<LiveInsights | null>(null)
  const [coachingSuggestions, setCoachingSuggestions] = useState<CoachingSuggestions | null>(null)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  
  const ws = useRef<WebSocket | null>(null)
  const audioContext = useRef<AudioContext | null>(null)
  const mediaStream = useRef<MediaStream | null>(null)
  const audioProcessor = useRef<ScriptProcessorNode | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null)
  const isRecording = useRef(false)

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!token || !sessionId) {
      console.log('WebSocket connection aborted: missing token or sessionId', { token: !!token, sessionId })
      return
    }

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v1/ws/interview/${sessionId}?token=${token}`
      console.log('Connecting to WebSocket:', wsUrl)
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        setIsConnected(true)
        setError(null)
        console.log('WebSocket connected')
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('Connection error occurred')
      }

      ws.current.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected')
        
        // Attempt to reconnect after 3 seconds
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current)
        }
        reconnectTimeout.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 3000)
      }
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
      setError('Failed to establish connection')
    }
  }, [token, sessionId])

  // Handle incoming messages
  const handleMessage = (message: WebSocketMessage) => {
    setMessages((prev) => [...prev, message])

    switch (message.type) {
      case 'transcription_update':
        setTranscription((prev) => [...prev, message.data as TranscriptionUpdate])
        break
      
      case 'live_insights':
        setLiveInsights(message.data as LiveInsights)
        break
      
      case 'coaching_suggestions':
        setCoachingSuggestions(message.data as CoachingSuggestions)
        break
      
      case 'connection_established':
        console.log('Connection established:', message.data)
        break
      
      case 'error':
        setError(message.message || 'An error occurred')
        break
      
      default:
        console.log('Unhandled message type:', message.type)
    }
  }

  // Send message
  const sendMessage = useCallback((type: string, data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, ...data }))
    } else {
      console.error('WebSocket is not connected')
    }
  }, [])

  // Start audio recording
  const startRecording = useCallback(async () => {
    try {
      // Get user media
      mediaStream.current = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      })

      // Create audio context
      audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000
      })

      const source = audioContext.current.createMediaStreamSource(mediaStream.current)
      
      // Create processor
      audioProcessor.current = audioContext.current.createScriptProcessor(4096, 1, 1)
      
      audioProcessor.current.onaudioprocess = (e) => {
        if (!isRecording.current) return

        const inputData = e.inputBuffer.getChannelData(0)
        const audioData = convertFloat32ToInt16(inputData)
        
        // Send audio chunk to server
        sendMessage('audio_chunk', {
          audio: btoa(String.fromCharCode(...new Uint8Array(audioData.buffer))),
          is_final: false
        })
      }

      source.connect(audioProcessor.current)
      audioProcessor.current.connect(audioContext.current.destination)
      
      isRecording.current = true
      console.log('Recording started')
    } catch (err) {
      console.error('Failed to start recording:', err)
      setError('Failed to access microphone')
    }
  }, [sendMessage])

  // Stop audio recording
  const stopRecording = useCallback(() => {
    isRecording.current = false

    if (audioProcessor.current) {
      audioProcessor.current.disconnect()
      audioProcessor.current = null
    }

    if (audioContext.current) {
      audioContext.current.close()
      audioContext.current = null
    }

    if (mediaStream.current) {
      mediaStream.current.getTracks().forEach(track => track.stop())
      mediaStream.current = null
    }

    // Send final audio chunk
    sendMessage('audio_chunk', { audio: '', is_final: true })
    
    console.log('Recording stopped')
  }, [sendMessage])

  // Request coaching suggestions
  const requestSuggestions = useCallback((context: any, recentTranscript: string) => {
    sendMessage('request_suggestion', {
      context,
      recent_transcript: recentTranscript
    })
  }, [sendMessage])

  // Send chat message
  const sendChatMessage = useCallback((message: string) => {
    sendMessage('chat_message', { message })
  }, [sendMessage])

  // Sync state
  const syncState = useCallback((state: any) => {
    sendMessage('sync_state', { state })
  }, [sendMessage])

  // End transcription and get summary
  const endTranscription = useCallback(() => {
    sendMessage('end_transcription', {})
  }, [sendMessage])

  // Convert audio format
  const convertFloat32ToInt16 = (buffer: Float32Array): Int16Array => {
    const l = buffer.length
    const buf = new Int16Array(l)
    
    for (let i = 0; i < l; i++) {
      buf[i] = Math.min(1, buffer[i]) * 0x7FFF
    }
    
    return buf
  }

  // Connect on mount
  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      
      if (ws.current) {
        ws.current.close()
      }
      
      stopRecording()
    }
  }, [connect, stopRecording])

  return {
    isConnected,
    transcription,
    liveInsights,
    coachingSuggestions,
    messages,
    error,
    startRecording,
    stopRecording,
    requestSuggestions,
    sendChatMessage,
    syncState,
    endTranscription,
    sendMessage
  }
}