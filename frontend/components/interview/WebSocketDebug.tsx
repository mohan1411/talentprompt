'use client'

import { useAuth } from '@/lib/auth/context'
import { useEffect } from 'react'

export function WebSocketDebug({ sessionId }: { sessionId: string }) {
  const { token } = useAuth()
  
  useEffect(() => {
    console.log('WebSocket Debug:', {
      token: token ? `${token.substring(0, 10)}...` : null,
      sessionId,
      wsUrl: process.env.NEXT_PUBLIC_WS_URL,
      apiUrl: process.env.NEXT_PUBLIC_API_URL
    })
  }, [token, sessionId])
  
  return (
    <div className="fixed bottom-4 right-4 bg-black/80 text-white p-4 rounded-lg text-xs font-mono">
      <div>Token: {token ? '✓' : '✗'}</div>
      <div>Session: {sessionId}</div>
      <div>WS URL: {process.env.NEXT_PUBLIC_WS_URL}</div>
    </div>
  )
}