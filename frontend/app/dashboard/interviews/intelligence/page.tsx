'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress-simple'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ScrollArea } from '@/components/ui/scroll-area-simple'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select-simple'
import { 
  BrainIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  UserIcon,
  ClockIcon,
  BarChart3Icon,
  PieChartIcon,
  AlertCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
  SparklesIcon,
  MessageSquareIcon,
  CalendarIcon,
  FilterIcon,
  DownloadIcon,
  RefreshCwIcon,
  ActivityIcon,
  ZapIcon,
  StarIcon,
  TargetIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from 'lucide-react'
import { interviewsApi } from '@/lib/api/interviews'
import { apiClient } from '@/lib/api/client'

interface InterviewAnalytics {
  total_interviews: number
  completed_interviews: number
  average_duration: number
  average_rating: number
  skill_coverage: { [key: string]: number }
  sentiment_distribution: {
    positive: number
    neutral: number
    negative: number
  }
  top_candidates: Array<{
    candidate_name: string
    position: string
    rating: number
    interview_date: string
  }>
  common_strengths: string[]
  common_concerns: string[]
  interview_trends: Array<{
    date: string
    count: number
    average_rating: number
  }>
  interviewer_performance: {
    questions_asked_ratio: number
    follow_up_rate: number
    time_management_score: number
  }
}

export default function InterviewIntelligencePage() {
  const [analytics, setAnalytics] = useState<InterviewAnalytics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('7d')
  const [selectedPosition, setSelectedPosition] = useState('all')

  useEffect(() => {
    loadAnalytics()
  }, [timeRange, selectedPosition])

  const loadAnalytics = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      console.log('Fetching analytics with time range:', timeRange)
      
      // Fetch real analytics data from the API
      const data = await apiClient.get('/interviews/analytics/extended', {
        params: { time_range: timeRange }
      })
      
      console.log('Analytics data received:', data)
      
      // Transform the API response to match the frontend interface
      const analytics: InterviewAnalytics = {
        total_interviews: data.total_interviews || 0,
        completed_interviews: data.completed_interviews || 0,
        average_duration: Math.round(data.average_duration || 45),
        average_rating: data.average_rating || 0,
        skill_coverage: data.skill_coverage || {},
        sentiment_distribution: data.sentiment_distribution || {
          positive: 0,
          neutral: 0,
          negative: 0
        },
        top_candidates: data.top_candidates || [],
        common_strengths: data.common_strengths || ['No data available yet'],
        common_concerns: data.common_concerns || ['No data available yet'],
        interview_trends: data.interview_trends || [],
        interviewer_performance: data.interviewer_performance || {
          questions_asked_ratio: 0,
          follow_up_rate: 0,
          time_management_score: 0
        }
      }
      
      setAnalytics(analytics)
    } catch (error: any) {
      console.error('Failed to load analytics:', error)
      
      // Better error message based on the error type
      let errorMessage = 'Failed to load interview analytics. Please try again.'
      
      if (error.status === 401) {
        errorMessage = 'Your session has expired. Please log in again.'
      } else if (error.status === 404) {
        errorMessage = 'Analytics endpoint not found. Please contact support.'
      } else if (error.detail) {
        errorMessage = error.detail
      } else if (error.message) {
        errorMessage = `Error: ${error.message}`
      }
      
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const getProgressColor = (value: number) => {
    if (value >= 80) return 'text-green-600'
    if (value >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 0.8) return <CheckCircleIcon className="h-4 w-4 text-green-500" />
    if (score >= 0.6) return <AlertCircleIcon className="h-4 w-4 text-yellow-500" />
    return <XCircleIcon className="h-4 w-4 text-red-500" />
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-7xl">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <BrainIcon className="h-12 w-12 animate-pulse mx-auto text-muted-foreground" />
            <p className="mt-4 text-lg text-muted-foreground">Loading interview intelligence...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-7xl">
        <Alert variant="destructive">
          <AlertCircleIcon className="h-4 w-4" />
          <AlertDescription>
            {error || 'Failed to load analytics. Please try again.'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BrainIcon className="h-6 w-6" />
            Interview Intelligence
          </h1>
          <p className="text-muted-foreground mt-1">
            AI-powered insights from your interview data
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="all">All time</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            size="icon"
            onClick={() => loadAnalytics()}
            disabled={isLoading}
          >
            <RefreshCwIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="outline" size="icon">
            <DownloadIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Interviews</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_interviews}</div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
              {analytics.total_interviews > 0 ? (
                <>
                  <TrendingUpIcon className="h-4 w-4 text-green-500" />
                  <span>Active interviewing</span>
                </>
              ) : (
                <span>Start interviewing to see trends</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round((analytics.completed_interviews / analytics.total_interviews) * 100)}%
            </div>
            <Progress 
              value={(analytics.completed_interviews / analytics.total_interviews) * 100} 
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Avg. Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.average_duration} min</div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
              <ClockIcon className="h-4 w-4" />
              <span>Target: 45-60 min</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Avg. Rating</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              {analytics.average_rating}
              <StarIcon className="h-5 w-5 text-yellow-500 fill-yellow-500" />
            </div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
              <span>Out of 5.0</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="candidates">Top Candidates</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Sentiment Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ActivityIcon className="h-5 w-5" />
                  Sentiment Analysis
                </CardTitle>
                <CardDescription>
                  Overall candidate sentiment during interviews
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Positive</span>
                      <span className="text-sm text-muted-foreground">{analytics.sentiment_distribution.positive}%</span>
                    </div>
                    <Progress value={analytics.sentiment_distribution.positive} className="h-3 bg-green-100">
                      <div className="h-full bg-green-500 rounded-full" style={{ width: `${analytics.sentiment_distribution.positive}%` }} />
                    </Progress>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Neutral</span>
                      <span className="text-sm text-muted-foreground">{analytics.sentiment_distribution.neutral}%</span>
                    </div>
                    <Progress value={analytics.sentiment_distribution.neutral} className="h-3 bg-gray-100">
                      <div className="h-full bg-gray-500 rounded-full" style={{ width: `${analytics.sentiment_distribution.neutral}%` }} />
                    </Progress>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Negative</span>
                      <span className="text-sm text-muted-foreground">{analytics.sentiment_distribution.negative}%</span>
                    </div>
                    <Progress value={analytics.sentiment_distribution.negative} className="h-3 bg-red-100">
                      <div className="h-full bg-red-500 rounded-full" style={{ width: `${analytics.sentiment_distribution.negative}%` }} />
                    </Progress>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Skill Coverage */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TargetIcon className="h-5 w-5" />
                  Skill Assessment Coverage
                </CardTitle>
                <CardDescription>
                  How well interviews cover key skill areas
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(analytics.skill_coverage).map(([skill, coverage]) => (
                    <div key={skill}>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium">{skill}</span>
                        <span className={`text-sm font-medium ${getProgressColor(coverage)}`}>
                          {coverage}%
                        </span>
                      </div>
                      <Progress value={coverage} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Interview Trends */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3Icon className="h-5 w-5" />
                Interview Activity Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics.interview_trends.length > 0 ? (
                <div className="h-64 flex items-end gap-2">
                  {analytics.interview_trends.map((trend, idx) => {
                    const maxCount = Math.max(...analytics.interview_trends.map(t => t.count), 1)
                    const heightPercent = (trend.count / maxCount) * 100
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                        <div className="w-full bg-primary/10 rounded-t relative" style={{ height: `${heightPercent}%` }}>
                          {trend.count > 0 && (
                            <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-medium">
                              {trend.count}
                            </div>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(trend.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center">
                  <p className="text-muted-foreground">No interview data for this period</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Top Candidates Tab */}
        <TabsContent value="candidates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>High-Performing Candidates</CardTitle>
              <CardDescription>
                Candidates with the highest interview ratings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.top_candidates.map((candidate, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 rounded-lg border">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10 text-primary font-semibold">
                        {idx + 1}
                      </div>
                      <div>
                        <p className="font-medium">{candidate.candidate_name}</p>
                        <p className="text-sm text-muted-foreground">{candidate.position}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="flex items-center gap-1">
                          <span className="font-medium">{candidate.rating}</span>
                          <StarIcon className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {new Date(candidate.interview_date).toLocaleDateString()}
                        </p>
                      </div>
                      <Button size="sm" variant="outline">View Details</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  Common Strengths
                </CardTitle>
                <CardDescription>
                  Frequently observed positive attributes
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {analytics.common_strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <ChevronUpIcon className="h-4 w-4 text-green-500 mt-0.5" />
                      <span className="text-sm">{strength}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircleIcon className="h-5 w-5 text-amber-500" />
                  Common Concerns
                </CardTitle>
                <CardDescription>
                  Areas that frequently need clarification
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {analytics.common_concerns.map((concern, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <ChevronDownIcon className="h-4 w-4 text-amber-500 mt-0.5" />
                      <span className="text-sm">{concern}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SparklesIcon className="h-5 w-5" />
                AI Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <ZapIcon className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Interview Process:</strong> Consider adding more technical depth questions for senior positions to better assess advanced skills.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <MessageSquareIcon className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Communication:</strong> Follow-up questions are being used effectively. Keep encouraging candidates to provide specific examples.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <TargetIcon className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Skill Coverage:</strong> Leadership assessment could be improved. Consider adding scenario-based questions for management roles.
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Interviewer Performance Metrics</CardTitle>
              <CardDescription>
                How effectively interviews are being conducted
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getScoreIcon(analytics.interviewer_performance.questions_asked_ratio)}
                      <span className="font-medium">Questions Coverage</span>
                    </div>
                    <span className="text-sm font-medium">
                      {Math.round(analytics.interviewer_performance.questions_asked_ratio * 100)}%
                    </span>
                  </div>
                  <Progress 
                    value={analytics.interviewer_performance.questions_asked_ratio * 100} 
                    className="h-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Percentage of prepared questions asked during interviews
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getScoreIcon(analytics.interviewer_performance.follow_up_rate)}
                      <span className="font-medium">Follow-up Rate</span>
                    </div>
                    <span className="text-sm font-medium">
                      {Math.round(analytics.interviewer_performance.follow_up_rate * 100)}%
                    </span>
                  </div>
                  <Progress 
                    value={analytics.interviewer_performance.follow_up_rate * 100} 
                    className="h-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    How often follow-up questions are used to dig deeper
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getScoreIcon(analytics.interviewer_performance.time_management_score)}
                      <span className="font-medium">Time Management</span>
                    </div>
                    <span className="text-sm font-medium">
                      {Math.round(analytics.interviewer_performance.time_management_score * 100)}%
                    </span>
                  </div>
                  <Progress 
                    value={analytics.interviewer_performance.time_management_score * 100} 
                    className="h-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Efficiency in completing interviews within target duration
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Best Practices Checklist</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  <span className="text-sm">Consistently using prepared questions</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  <span className="text-sm">Good follow-up question usage</span>
                </div>
                <div className="flex items-center gap-3">
                  <AlertCircleIcon className="h-5 w-5 text-yellow-500" />
                  <span className="text-sm">Consider more behavioral questions</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  <span className="text-sm">Effective time management</span>
                </div>
                <div className="flex items-center gap-3">
                  <AlertCircleIcon className="h-5 w-5 text-yellow-500" />
                  <span className="text-sm">Increase leadership assessment coverage</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}