'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area-simple'
import { Button } from '@/components/ui/button'
import { 
  MicIcon, 
  MicOffIcon, 
  CopyIcon, 
  CheckIcon,
  MessageSquareIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  MinusIcon
} from 'lucide-react'

interface TranscriptionUpdate {
  session_id?: string
  timestamp: string
  text: string
  duration?: number
  analysis: {
    sentiment: {
      sentiment: 'positive' | 'neutral' | 'negative'
      confidence: number
      emotion?: string
    }
    skills_mentioned?: string[]
    quality_indicators?: any
    word_count: number
    speaking_pace: number
  }
  is_final?: boolean
}

interface TranscriptionPanelProps {
  transcription: TranscriptionUpdate[]
  isRecording: boolean
  onStartRecording: () => void
  onStopRecording: () => void
  isConnected: boolean
}

export function TranscriptionPanel({
  transcription,
  isRecording,
  onStartRecording,
  onStopRecording,
  isConnected
}: TranscriptionPanelProps) {
  const [copied, setCopied] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  
  // Auto-scroll to bottom when new transcription arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [transcription])
  
  const copyTranscript = () => {
    const fullTranscript = transcription.map(t => t.text).join(' ')
    navigator.clipboard.writeText(fullTranscript)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <TrendingUpIcon className="h-4 w-4 text-green-500" />
      case 'negative':
        return <TrendingDownIcon className="h-4 w-4 text-red-500" />
      default:
        return <MinusIcon className="h-4 w-4 text-gray-500" />
    }
  }
  
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'border-green-200 bg-green-50'
      case 'negative':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }
  
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquareIcon className="h-5 w-5" />
            Live Transcription
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={isConnected ? 'default' : 'secondary'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
            <Button
              size="sm"
              variant="ghost"
              onClick={copyTranscript}
              disabled={transcription.length === 0}
            >
              {copied ? (
                <CheckIcon className="h-4 w-4" />
              ) : (
                <CopyIcon className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea className="flex-1 px-4" ref={scrollRef}>
          <div className="space-y-3 py-4">
            {transcription.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquareIcon className="h-12 w-12 mx-auto mb-2 opacity-20" />
                <p className="text-sm">No transcription yet</p>
                <p className="text-xs mt-1">Click the microphone to start recording</p>
              </div>
            ) : (
              transcription.map((update, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border transition-all ${getSentimentColor(
                    update.analysis.sentiment.sentiment
                  )}`}
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 mt-0.5">
                      {getSentimentIcon(update.analysis.sentiment.sentiment)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 break-words">{update.text}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-muted-foreground">
                          {new Date(update.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {update.analysis.word_count} words
                        </span>
                        {update.analysis.speaking_pace > 0 && (
                          <span className="text-xs text-muted-foreground">
                            {Math.round(update.analysis.speaking_pace)} wpm
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
        
        <div className="p-4 border-t">
          <Button
            className="w-full"
            variant={isRecording ? 'destructive' : 'default'}
            onClick={isRecording ? onStopRecording : onStartRecording}
            disabled={!isConnected}
          >
            {isRecording ? (
              <>
                <MicOffIcon className="h-4 w-4 mr-2" />
                Stop Recording
              </>
            ) : (
              <>
                <MicIcon className="h-4 w-4 mr-2" />
                Start Recording
              </>
            )}
          </Button>
          {isRecording && (
            <div className="flex items-center justify-center mt-2">
              <span className="flex h-3 w-3 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
              <span className="ml-2 text-sm text-red-600">Recording...</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}