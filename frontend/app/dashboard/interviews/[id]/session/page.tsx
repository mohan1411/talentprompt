'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs-simple'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress-simple'
import { ScrollArea } from '@/components/ui/scroll-area-simple'
import { Separator } from '@/components/ui/separator-simple'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  PlayIcon,
  PauseIcon,
  SkipForwardIcon,
  CheckCircleIcon,
  ClockIcon,
  UserIcon,
  BrainIcon,
  AlertCircleIcon,
  SparklesIcon,
  MicIcon,
  VideoIcon,
  MessageSquareIcon,
  ThumbsUpIcon,
  ThumbsDownIcon,
  ChevronRightIcon,
  FileTextIcon,
  Loader2Icon,
  ArrowLeftIcon,
  HeadphonesIcon
} from 'lucide-react'
import { interviewsApi, InterviewSession, InterviewQuestion } from '@/lib/api/interviews'
import { resumeApi, Resume } from '@/lib/api/client'
import { useInterviewWebSocket } from '@/hooks/useInterviewWebSocket'
import { TranscriptionPanel } from '@/components/interview/TranscriptionPanel'
import { LiveInsightsPanel } from '@/components/interview/LiveInsightsPanel'
import { CoachingSuggestionsPanel } from '@/components/interview/CoachingSuggestionsPanel'
import { WebSocketDebug } from '@/components/interview/WebSocketDebug'

export default function InterviewSessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  
  const [isLive, setIsLive] = useState(false)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [notes, setNotes] = useState('')
  const [candidateResponse, setCandidateResponse] = useState('')
  const [showLiveAssist, setShowLiveAssist] = useState(false)
  
  // API data states
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [resume, setResume] = useState<Resume | null>(null)
  const [questions, setQuestions] = useState<InterviewQuestion[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // WebSocket and real-time features
  const {
    isConnected,
    transcription,
    liveInsights,
    coachingSuggestions,
    startRecording,
    stopRecording,
    requestSuggestions,
    endTranscription
  } = useInterviewWebSocket(sessionId)
  const [isRecording, setIsRecording] = useState(false)
  
  // Load interview session data
  useEffect(() => {
    loadSessionData()
  }, [sessionId])
  
  const loadSessionData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Fetch interview session
      const sessionData = await interviewsApi.getSession(sessionId)
      setSession(sessionData)
      setQuestions(sessionData.questions || [])
      
      // Fetch resume data
      if (sessionData.resume_id) {
        const resumeData = await resumeApi.getResume(sessionData.resume_id)
        setResume(resumeData)
      }
    } catch (error: any) {
      console.error('Failed to load interview session:', error)
      const errorMessage = error?.detail || error?.message || 'Failed to load interview session'
      setError(typeof errorMessage === 'string' ? errorMessage : 'Failed to load interview session')
    } finally {
      setIsLoading(false)
    }
  }
  
  // Build candidate info from API data
  const candidateInfo = resume && session ? {
    name: `${resume.first_name} ${resume.last_name}`,
    position: session.job_position,
    resumeId: resume.id,
    strengths: session.preparation_notes?.analysis?.candidate_summary?.strengths || resume.skills?.slice(0, 3) || [],
    concerns: session.preparation_notes?.analysis?.areas_to_explore || [],
    talkingPoints: session.preparation_notes?.analysis?.key_talking_points || []
  } : null


  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isLive) {
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1)
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isLive])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleStartInterview = async () => {
    setIsLive(true)
    
    // Update session status to in_progress
    try {
      await interviewsApi.updateSession(sessionId, {
        status: 'in_progress'
      })
    } catch (error) {
      console.error('Failed to update session status:', error)
    }
    
    if (questions.length > 0 && currentQuestionIndex === 0) {
      markQuestionAsAsked(0)
    }
  }

  const handleEndInterview = async () => {
    setIsLive(false)
    
    // Stop recording if active
    if (isRecording) {
      handleStopRecording()
    }
    
    // End transcription session
    endTranscription()
    
    // Calculate duration if session was started
    const duration = session?.started_at 
      ? Math.round((Date.now() - new Date(session.started_at).getTime()) / 60000)
      : Math.round(elapsedTime / 60)
    
    // Update session status to completed
    try {
      await interviewsApi.updateSession(sessionId, {
        status: 'completed',
        notes: notes,
        duration_minutes: duration
      })
      
      // Refresh the page or redirect to show completion
      router.push('/dashboard/interviews')
    } catch (error) {
      console.error('Failed to update session status:', error)
    }
  }

  const markQuestionAsAsked = async (index: number) => {
    if (index >= questions.length) return
    
    const question = questions[index]
    try {
      await interviewsApi.updateQuestionResponse(question.id, {
        asked: true
      })
      
      // Update local state
      const updatedQuestions = [...questions]
      updatedQuestions[index] = { ...updatedQuestions[index], asked: true }
      setQuestions(updatedQuestions)
    } catch (error) {
      console.error('Failed to mark question as asked:', error)
    }
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      const nextIndex = currentQuestionIndex + 1
      setCurrentQuestionIndex(nextIndex)
      markQuestionAsAsked(nextIndex)
      setCandidateResponse('')
    }
  }

  const handleRateResponse = async (rating: number) => {
    const question = questions[currentQuestionIndex]
    if (!question) return
    
    try {
      await interviewsApi.updateQuestionResponse(question.id, {
        response_rating: rating,
        response_summary: candidateResponse
      })
      
      // Update local state
      const updatedQuestions = [...questions]
      updatedQuestions[currentQuestionIndex] = { 
        ...updatedQuestions[currentQuestionIndex], 
        response_rating: rating 
      }
      setQuestions(updatedQuestions)
    } catch (error) {
      console.error('Failed to update question rating:', error)
    }
  }

  const handleStartRecording = async () => {
    try {
      await startRecording()
      setIsRecording(true)
      
      // Request initial suggestions based on current question
      if (currentQuestion) {
        const context = {
          question: currentQuestion.question_text,
          category: currentQuestion.category,
          expected_points: currentQuestion.expected_answer_points
        }
        requestSuggestions(context, '')
      }
    } catch (error) {
      console.error('Failed to start recording:', error)
    }
  }

  const handleStopRecording = () => {
    stopRecording()
    setIsRecording(false)
  }

  const handleUseQuestion = (question: string) => {
    // Add the question to candidate response notes
    setCandidateResponse(prev => {
      if (prev) {
        return `${prev}\n\nFollow-up: ${question}`
      }
      return `Follow-up: ${question}`
    })
  }

  const currentQuestion = questions[currentQuestionIndex]
  const progress = questions.length > 0 ? ((questions.filter(q => q.asked).length) / questions.length) * 100 : 0

  // Show loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-7xl">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2Icon className="h-12 w-12 animate-spin mx-auto text-muted-foreground" />
            <p className="mt-4 text-lg text-muted-foreground">Loading interview session...</p>
          </div>
        </div>
      </div>
    )
  }

  // Show error state
  if (error || !session || !candidateInfo) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-7xl">
        <Alert variant="destructive">
          <AlertCircleIcon className="h-4 w-4" />
          <AlertDescription>
            {error || 'Failed to load interview session. Please try again.'}
          </AlertDescription>
        </Alert>
        <Button 
          className="mt-4" 
          variant="outline"
          onClick={() => router.push('/dashboard/interviews')}
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Interviews
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            {candidateInfo.name} - {candidateInfo.position}
            {isLive && (
              <Badge variant="destructive" className="animate-pulse">
                <div className="w-2 h-2 bg-white rounded-full mr-2" />
                LIVE
              </Badge>
            )}
            {session?.status === 'completed' && (
              <Badge variant="outline" className="text-green-600">
                <CheckCircleIcon className="h-4 w-4 mr-1" />
                Completed
              </Badge>
            )}
          </h1>
          <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <ClockIcon className="h-4 w-4" />
              {formatTime(elapsedTime)}
            </span>
            <span>Progress: {Math.round(progress)}%</span>
          </div>
        </div>
        <div className="flex gap-2">
          {session?.status === 'completed' ? (
            <Button 
              variant="outline" 
              onClick={() => router.push('/dashboard/interviews')}
              className="flex items-center gap-2"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              Back to Interviews
            </Button>
          ) : !isLive ? (
            <Button onClick={handleStartInterview} className="flex items-center gap-2">
              <PlayIcon className="h-4 w-4" />
              Start Interview
            </Button>
          ) : (
            <>
              <Button 
                variant={showLiveAssist ? "default" : "outline"} 
                className="flex items-center gap-2"
                onClick={() => setShowLiveAssist(!showLiveAssist)}
              >
                <HeadphonesIcon className="h-4 w-4" />
                Live Assist {showLiveAssist ? "On" : "Off"}
              </Button>
              <Button variant="destructive" onClick={handleEndInterview}>
                End Interview
              </Button>
            </>
          )}
        </div>
      </div>

      <div className={`grid grid-cols-1 gap-6 ${showLiveAssist ? 'lg:grid-cols-4' : 'lg:grid-cols-3'}`}>
        {/* Main Interview Area */}
        <div className={`${showLiveAssist ? 'lg:col-span-2' : 'lg:col-span-2'} space-y-6`}>
          {/* Current Question */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Question {currentQuestionIndex + 1} of {questions.length}</CardTitle>
                  <div className="flex gap-2 mt-2">
                    <Badge variant="outline">{currentQuestion.category}</Badge>
                    <Badge variant="outline">Difficulty: {currentQuestion.difficulty_level}/5</Badge>
                  </div>
                </div>
                <Progress value={progress} className="w-24" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-lg font-medium">{currentQuestion?.question_text || 'No question available'}</div>
              
              {/* Expected Points */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <BrainIcon className="h-4 w-4" />
                  Key Points to Listen For:
                </h4>
                <ul className="space-y-1">
                  {currentQuestion?.expected_answer_points?.map((point, idx) => (
                    <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                      <ChevronRightIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      {point}
                    </li>
                  )) || (
                    <li className="text-sm text-muted-foreground">No specific points provided</li>
                  )}
                </ul>
              </div>

              {/* Response Notes */}
              <div>
                <label className="text-sm font-medium mb-2 block">Candidate Response Notes</label>
                <Textarea
                  placeholder="Type notes about the candidate's response..."
                  rows={4}
                  value={candidateResponse}
                  onChange={(e) => setCandidateResponse(e.target.value)}
                  disabled={!isLive}
                />
              </div>

              {/* Quick Rating */}
              {isLive && (
                <div>
                  <label className="text-sm font-medium mb-2 block">Quick Rating</label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <Button
                        key={rating}
                        variant={currentQuestion?.response_rating === rating ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleRateResponse(rating)}
                      >
                        {rating}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Follow-up Question */}
              {currentQuestion?.follow_up_questions && currentQuestion.follow_up_questions.length > 0 && (
                <Alert>
                  <SparklesIcon className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Suggested Follow-up:</strong> {currentQuestion.follow_up_questions[0]}
                  </AlertDescription>
                </Alert>
              )}

              {/* Navigation */}
              <div className="flex justify-between pt-4">
                <Button
                  variant="outline"
                  disabled={currentQuestionIndex === 0}
                  onClick={() => setCurrentQuestionIndex(currentQuestionIndex - 1)}
                >
                  Previous
                </Button>
                <Button
                  onClick={handleNextQuestion}
                  disabled={currentQuestionIndex === questions.length - 1 || !isLive}
                  className="flex items-center gap-2"
                >
                  Next Question
                  <SkipForwardIcon className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* General Notes */}
          <Card>
            <CardHeader>
              <CardTitle>Interview Notes</CardTitle>
              <CardDescription>General observations and comments</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Type your general notes here..."
                rows={6}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={!isLive}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* Candidate Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Candidate Insights</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-2 text-green-600">Strengths</h4>
                <ul className="space-y-1">
                  {candidateInfo.strengths.map((strength: string, idx: number) => (
                    <li key={idx} className="text-sm flex items-start gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
              
              <Separator />
              
              <div>
                <h4 className="text-sm font-medium mb-2 text-amber-600">Areas to Explore</h4>
                <ul className="space-y-1">
                  {candidateInfo.concerns.map((concern: string, idx: number) => (
                    <li key={idx} className="text-sm flex items-start gap-2">
                      <AlertCircleIcon className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      {concern}
                    </li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <h4 className="text-sm font-medium mb-2">Key Talking Points</h4>
                <ul className="space-y-1">
                  {candidateInfo.talkingPoints.map((point: string, idx: number) => (
                    <li key={idx} className="text-sm flex items-start gap-2">
                      <MessageSquareIcon className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Question Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Question Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="space-y-2">
                  {questions.map((question, idx) => (
                    <div
                      key={question.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        idx === currentQuestionIndex ? 'bg-primary/10 border-primary' : 
                        question.asked ? 'bg-muted' : 'hover:bg-muted/50'
                      }`}
                      onClick={() => isLive && setCurrentQuestionIndex(idx)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="text-sm font-medium line-clamp-2">{question.question_text}</div>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-xs">{question.category}</Badge>
                            {question.asked && (
                              <CheckCircleIcon className="h-4 w-4 text-green-600" />
                            )}
                            {question.response_rating && (
                              <span className="text-xs text-muted-foreground">
                                Rating: {question.response_rating}/5
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          {isLive && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <SparklesIcon className="h-4 w-4 mr-2" />
                  Generate Follow-up
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <FileTextIcon className="h-4 w-4 mr-2" />
                  View Resume
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <MessageSquareIcon className="h-4 w-4 mr-2" />
                  Add Custom Question
                </Button>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Live Assist Panel - Only show when active */}
        {showLiveAssist && isLive && (
          <div className="space-y-4">
            <div className="sticky top-4">
              {/* Transcription Panel */}
              <div className="mb-4">
                <TranscriptionPanel
                  transcription={transcription}
                  isRecording={isRecording}
                  onStartRecording={handleStartRecording}
                  onStopRecording={handleStopRecording}
                  isConnected={isConnected}
                />
              </div>
              
              {/* Tabs for Insights and Coaching */}
              <Tabs defaultValue="insights" className="space-y-4">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="insights">Live Insights</TabsTrigger>
                  <TabsTrigger value="coaching">AI Coaching</TabsTrigger>
                </TabsList>
                
                <TabsContent value="insights" className="space-y-4">
                  <LiveInsightsPanel
                    insights={liveInsights}
                    isConnected={isConnected}
                  />
                </TabsContent>
                
                <TabsContent value="coaching" className="space-y-4">
                  <CoachingSuggestionsPanel
                    suggestions={coachingSuggestions}
                    isConnected={isConnected}
                    onUseQuestion={handleUseQuestion}
                  />
                </TabsContent>
              </Tabs>
            </div>
          </div>
        )}
      </div>
      
      {/* Debug component - remove in production */}
      {showLiveAssist && <WebSocketDebug sessionId={sessionId} />}
    </div>
  )
}