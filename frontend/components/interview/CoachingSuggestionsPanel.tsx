'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  SparklesIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  HelpCircleIcon,
  TrendingUpIcon,
  LightbulbIcon,
  MessageSquareIcon,
  ChevronRightIcon
} from 'lucide-react'

interface CoachingSuggestions {
  follow_up_questions: string[]
  dig_deeper_prompts: string[]
  coaching_tips: string[]
  red_flags: string[]
  positive_signals: string[]
}

interface CoachingSuggestionsPanelProps {
  suggestions: CoachingSuggestions | null
  isConnected: boolean
  onUseQuestion?: (question: string) => void
}

export function CoachingSuggestionsPanel({ 
  suggestions, 
  isConnected,
  onUseQuestion 
}: CoachingSuggestionsPanelProps) {
  return (
    <div className="space-y-4">
      {/* Follow-up Questions */}
      {suggestions && suggestions.follow_up_questions.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <HelpCircleIcon className="h-4 w-4" />
              Suggested Follow-ups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {suggestions.follow_up_questions.map((question, idx) => (
                <div 
                  key={idx} 
                  className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group"
                  onClick={() => onUseQuestion?.(question)}
                >
                  <ChevronRightIcon className="h-4 w-4 mt-0.5 text-muted-foreground group-hover:text-primary transition-colors" />
                  <p className="text-sm flex-1">{question}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Coaching Tips */}
      {suggestions && suggestions.coaching_tips.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <LightbulbIcon className="h-4 w-4" />
              Interview Tips
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {suggestions.coaching_tips.map((tip, idx) => (
                <Alert key={idx} className="py-2">
                  <SparklesIcon className="h-4 w-4" />
                  <AlertDescription className="text-sm">{tip}</AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Dig Deeper Prompts */}
      {suggestions && suggestions.dig_deeper_prompts.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUpIcon className="h-4 w-4" />
              Dig Deeper
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {suggestions.dig_deeper_prompts.map((prompt, idx) => (
                <div 
                  key={idx} 
                  className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group"
                  onClick={() => onUseQuestion?.(prompt)}
                >
                  <MessageSquareIcon className="h-4 w-4 mt-0.5 text-muted-foreground group-hover:text-primary transition-colors" />
                  <p className="text-sm flex-1">{prompt}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Red Flags */}
      {suggestions && suggestions.red_flags.length > 0 && (
        <Card className="border-red-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2 text-red-600">
              <AlertTriangleIcon className="h-4 w-4" />
              Red Flags
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {suggestions.red_flags.map((flag, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <AlertTriangleIcon className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{flag}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Positive Signals */}
      {suggestions && suggestions.positive_signals.length > 0 && (
        <Card className="border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2 text-green-600">
              <CheckCircleIcon className="h-4 w-4" />
              Positive Signals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {suggestions.positive_signals.map((signal, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{signal}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* No suggestions yet */}
      {!isConnected ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            <SparklesIcon className="h-12 w-12 mx-auto mb-2 opacity-20" />
            <p className="text-sm">Connect to see AI-powered coaching suggestions</p>
          </CardContent>
        </Card>
      ) : !suggestions && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            <SparklesIcon className="h-12 w-12 mx-auto mb-2 opacity-20" />
            <p className="text-sm">Start recording to receive coaching suggestions</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}