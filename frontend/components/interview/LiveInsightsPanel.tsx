'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress-simple'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  BrainIcon,
  TrendingUpIcon,
  AlertCircleIcon,
  ZapIcon,
  SmileIcon,
  FrownIcon,
  MehIcon,
  ActivityIcon,
  CheckCircleIcon
} from 'lucide-react'

interface LiveInsights {
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

interface LiveInsightsPanelProps {
  insights: LiveInsights | null
  isConnected: boolean
}

export function LiveInsightsPanel({ insights, isConnected }: LiveInsightsPanelProps) {
  const getSentimentIcon = () => {
    if (!insights) return <MehIcon className="h-8 w-8 text-gray-400" />
    
    switch (insights.sentiment.sentiment) {
      case 'positive':
        return <SmileIcon className="h-8 w-8 text-green-500" />
      case 'negative':
        return <FrownIcon className="h-8 w-8 text-red-500" />
      default:
        return <MehIcon className="h-8 w-8 text-yellow-500" />
    }
  }
  
  const getSentimentColor = () => {
    if (!insights) return 'text-gray-500'
    
    switch (insights.sentiment.sentiment) {
      case 'positive':
        return 'text-green-600'
      case 'negative':
        return 'text-red-600'
      default:
        return 'text-yellow-600'
    }
  }
  
  const getSpeakingPaceLabel = (pace: number) => {
    if (pace < 100) return 'Slow'
    if (pace < 140) return 'Moderate'
    if (pace < 180) return 'Fast'
    return 'Very Fast'
  }
  
  const getSpeakingPaceColor = (pace: number) => {
    if (pace < 100 || pace > 180) return 'text-amber-600'
    return 'text-green-600'
  }
  
  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircleIcon className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertCircleIcon className="h-4 w-4 text-amber-500" />
      default:
        return <AlertCircleIcon className="h-4 w-4 text-blue-500" />
    }
  }
  
  return (
    <div className="space-y-4">
      {/* Sentiment Analysis */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ActivityIcon className="h-4 w-4" />
            Real-time Sentiment
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!isConnected ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              Connect to see live insights
            </p>
          ) : !insights ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              Waiting for audio input...
            </p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getSentimentIcon()}
                  <div>
                    <p className={`font-medium capitalize ${getSentimentColor()}`}>
                      {insights.sentiment.sentiment}
                    </p>
                    <p className="text-sm text-muted-foreground capitalize">
                      {insights.sentiment.emotion}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Confidence</p>
                  <p className="font-medium">
                    {Math.round(insights.sentiment.confidence * 100)}%
                  </p>
                </div>
              </div>
              
              <Progress 
                value={insights.sentiment.confidence * 100} 
                className="h-2"
              />
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Speaking Metrics */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ZapIcon className="h-4 w-4" />
            Speaking Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          {insights ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Speaking Pace</span>
                <span className={`text-sm font-medium ${getSpeakingPaceColor(insights.speaking_metrics.speaking_pace)}`}>
                  {Math.round(insights.speaking_metrics.speaking_pace)} wpm
                  <span className="text-xs text-muted-foreground ml-1">
                    ({getSpeakingPaceLabel(insights.speaking_metrics.speaking_pace)})
                  </span>
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Word Count</span>
                <span className="text-sm font-medium">
                  {insights.speaking_metrics.word_count}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-2">
              No data yet
            </p>
          )}
        </CardContent>
      </Card>
      
      {/* Quality Indicators */}
      {insights && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <BrainIcon className="h-4 w-4" />
              Response Quality
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {insights.quality_indicators.uses_examples && (
                <div className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Uses specific examples</span>
                </div>
              )}
              
              {insights.quality_indicators.structured_response && (
                <div className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Well-structured response</span>
                </div>
              )}
              
              {insights.quality_indicators.uses_numbers && (
                <div className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Includes metrics/numbers</span>
                </div>
              )}
              
              <div className="flex items-center justify-between pt-2 border-t">
                <span className="text-sm text-muted-foreground">Confidence words</span>
                <Badge variant="secondary">{insights.quality_indicators.confidence_words}</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Hedge words</span>
                <Badge variant="secondary">{insights.quality_indicators.hedge_words}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Skills Mentioned */}
      {insights && insights.skills_mentioned.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUpIcon className="h-4 w-4" />
              Skills Mentioned
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {insights.skills_mentioned.map((skill, idx) => (
                <Badge key={idx} variant="outline">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Alerts */}
      {insights && insights.alerts.length > 0 && (
        <div className="space-y-2">
          {insights.alerts.map((alert, idx) => (
            <Alert key={idx} variant={alert.level === 'error' ? 'destructive' : 'default'}>
              {getAlertIcon(alert.level)}
              <AlertDescription>
                {alert.message}
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}
    </div>
  )
}