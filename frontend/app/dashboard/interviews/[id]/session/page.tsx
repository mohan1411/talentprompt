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
  HeadphonesIcon,
  PhoneIcon,
  UsersIcon
} from 'lucide-react'
import { interviewsApi, InterviewSession, InterviewQuestion } from '@/lib/api/interviews'
import { resumeApi, Resume } from '@/lib/api/client'
import { useInterviewWebSocket } from '@/hooks/useInterviewWebSocket'
import { TranscriptionPanel } from '@/components/interview/TranscriptionPanel'
import { LiveInsightsPanel } from '@/components/interview/LiveInsightsPanel'
import { CoachingSuggestionsPanel } from '@/components/interview/CoachingSuggestionsPanel'
import { WebSocketDebug } from '@/components/interview/WebSocketDebug'
import { UploadRecordingDialog } from '@/components/interview/UploadRecordingDialog'
import { InterviewScorecard } from '@/components/interview/InterviewScorecard'
import { DualTrackAnalysis } from '@/components/interview/DualTrackAnalysis'

export default function InterviewSessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  
  const [isLive, setIsLive] = useState(false)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [notes, setNotes] = useState('')
  const [candidateResponse, setCandidateResponse] = useState('')
  const [showLiveAssist, setShowLiveAssist] = useState(false)
  const [manualTranscript, setManualTranscript] = useState('')
  const [savingManualTranscript, setSavingManualTranscript] = useState(false)
  
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
      console.log('Session data loaded:', sessionData)
      console.log('Transcript:', sessionData.transcript)
      console.log('Transcript data:', sessionData.transcript_data)
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

  // Calculate human assessment data from rated questions
  const humanAssessment = questions.length > 0 ? (() => {
    const ratedQuestions = questions.filter(q => q.response_rating !== null && q.response_rating !== undefined)
    const categoryRatings: Record<string, { total: number; count: number }> = {}
    
    // Calculate ratings by category
    ratedQuestions.forEach(q => {
      const category = q.category || 'general'
      if (!categoryRatings[category]) {
        categoryRatings[category] = { total: 0, count: 0 }
      }
      categoryRatings[category].total += q.response_rating || 0
      categoryRatings[category].count += 1
    })
    
    // Convert to averages
    const categoryAverages: Record<string, number> = {}
    Object.entries(categoryRatings).forEach(([category, data]) => {
      if (data.count > 0) {
        categoryAverages[category] = data.total / data.count
      }
    })
    
    const totalRating = ratedQuestions.reduce((sum, q) => sum + (q.response_rating || 0), 0)
    const averageRating = ratedQuestions.length > 0 ? totalRating / ratedQuestions.length : 0
    
    return {
      questionsRated: ratedQuestions.length,
      totalQuestions: questions.length,
      averageRating,
      categoryRatings: categoryAverages,
      completionRate: (ratedQuestions.length / questions.length) * 100
    }
  })() : null


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
        status: 'IN_PROGRESS'
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
        status: 'COMPLETED',
        notes: notes,
        duration_minutes: duration
      })
      
      // Refresh the page or redirect to show completion
      router.push('/dashboard/interviews')
    } catch (error) {
      console.error('Failed to update session status:', error)
    }
  }

  const handleCompleteWithoutRecording = async () => {
    if (!confirm('Complete this interview without uploading a recording? You can still upload a recording later.')) {
      return
    }

    try {
      await interviewsApi.updateSession(sessionId, {
        status: 'COMPLETED',
        notes: notes || 'Interview completed without recording.'
      })
      
      // Show success message
      alert('Interview marked as completed!')
      
      // Reload session data
      await loadSessionData()
    } catch (error) {
      console.error('Failed to complete interview:', error)
      alert('Failed to complete interview. Please try again.')
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
            {session?.status === 'COMPLETED' && (
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
            {session?.interview_type && (
              <Badge variant="secondary" className="text-xs">
                {session.interview_type === 'IN_PERSON' && <UsersIcon className="h-3 w-3 mr-1" />}
                {session.interview_type === 'VIRTUAL' && <VideoIcon className="h-3 w-3 mr-1" />}
                {session.interview_type === 'PHONE' && <PhoneIcon className="h-3 w-3 mr-1" />}
                {session.interview_type.replace('_', ' ')}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {(session?.status === 'COMPLETED' || session?.status === 'IN_PROGRESS') ? (
            <>
              <Button 
                variant="outline" 
                onClick={() => router.push('/dashboard/interviews')}
                className="flex items-center gap-2"
              >
                <ArrowLeftIcon className="h-4 w-4" />
                Back to Interviews
              </Button>
              <Button 
                variant="default" 
                onClick={() => setShowUploadDialog(true)}
                className="flex items-center gap-2"
              >
                <FileTextIcon className="h-4 w-4" />
                Upload Recording
              </Button>
              {session?.status === 'IN_PROGRESS' && (
                <Button 
                  variant="secondary" 
                  onClick={handleCompleteWithoutRecording}
                  className="flex items-center gap-2"
                >
                  <CheckCircleIcon className="h-4 w-4" />
                  Complete Without Recording
                </Button>
              )}
            </>
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

          {/* Transcript and Analysis */}
          {(session?.transcript || session?.scorecard || session?.status === 'COMPLETED') && (
            <Card>
              <CardHeader>
                <CardTitle>Interview Results</CardTitle>
                <CardDescription>Transcript and AI analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue={session?.scorecard ? "analysis" : "transcript"}>
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="transcript">Transcript</TabsTrigger>
                    <TabsTrigger value="analysis">Analysis</TabsTrigger>
                    <TabsTrigger value="manual">Manual Entry</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="transcript" className="mt-4">
                    {session?.transcript ? (
                      <ScrollArea className="h-[400px] w-full rounded-md border p-4">
                        <div className="space-y-4">
                          {session.transcript_data?.speakers ? (
                            // Show speaker-separated transcript if available
                            Object.entries(session.transcript_data.speakers).map(([speakerId, speaker]: [string, any]) => (
                              <div key={speakerId} className="space-y-2">
                                <h4 className="font-medium text-sm">
                                  Speaker {speakerId} ({speaker.likely_role})
                                </h4>
                                {speaker.utterances?.map((utterance: any, idx: number) => (
                                  <p key={idx} className="text-sm text-muted-foreground ml-4">
                                    {utterance.text}
                                  </p>
                                ))}
                              </div>
                            ))
                          ) : (
                            // Show plain transcript
                            <p className="text-sm whitespace-pre-wrap">{session.transcript}</p>
                          )}
                        </div>
                      </ScrollArea>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        No transcript available. Upload a recording to generate transcript.
                      </div>
                    )}
                  </TabsContent>
                  
                  <TabsContent value="analysis" className="mt-4">
                    {session?.scorecard ? (
                      <div className="space-y-6">
                        {/* Dual Track Analysis - Human vs AI */}
                        <DualTrackAnalysis
                          humanAssessment={humanAssessment}
                          aiAnalysis={session.scorecard ? {
                            overall_rating: session.scorecard.overall_rating,
                            recommendation: session.scorecard.recommendation,
                            technical_skills: session.scorecard.technical_skills || {},
                            soft_skills: session.scorecard.soft_skills || {},
                            confidence: session.transcript_data?.confidence || 0.95,
                            questionsAnalyzed: session.preparation_notes?.transcript_analysis?.qa_pairs?.length
                          } : undefined}
                          sessionData={{
                            job_position: session.job_position,
                            interview_type: session.interview_type,
                            duration_minutes: session.duration_minutes || 0
                          }}
                        />
                        
                        {/* Detailed AI Scorecard */}
                        <div>
                          <h3 className="text-lg font-semibold mb-4">Detailed AI Analysis</h3>
                          <InterviewScorecard 
                            scorecard={session.scorecard}
                            qaAnalysis={session.preparation_notes?.transcript_analysis}
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-muted-foreground mb-4">
                          No analysis available yet. 
                          {session?.transcript ? 'Analysis will be generated automatically after upload.' : 'Upload a recording to generate analysis.'}
                        </p>
                        {session?.transcript && (
                          <Button 
                            onClick={async () => {
                              try {
                                const response = await fetch(
                                  `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/interviews/sessions/${sessionId}/analyze-transcript`,
                                  {
                                    method: 'POST',
                                    headers: {
                                      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                                    }
                                  }
                                )
                                if (response.ok) {
                                  // Reload session data
                                  await loadSessionData()
                                } else {
                                  alert('Failed to generate analysis')
                                }
                              } catch (error) {
                                console.error('Analysis error:', error)
                                alert('Failed to generate analysis')
                              }
                            }}
                            className="flex items-center gap-2"
                          >
                            <BrainIcon className="h-4 w-4" />
                            Generate Analysis
                          </Button>
                        )}
                      </div>
                    )}
                  </TabsContent>
                  
                  <TabsContent value="manual" className="mt-4">
                    <div className="space-y-4">
                      <Alert>
                        <AlertCircleIcon className="h-4 w-4" />
                        <AlertDescription>
                          <strong>Format Guide:</strong> Enter the transcript with speaker labels like:
                          <br />
                          <code className="text-xs">[interviewer]: Question here...</code>
                          <br />
                          <code className="text-xs">[candidate]: Answer here...</code>
                        </AlertDescription>
                      </Alert>
                      
                      <Textarea
                        placeholder="Paste or type the interview transcript here...

Example:
[interviewer]: Tell me about your experience with React and component libraries.
[candidate]: I have 7 years of experience building user interfaces with React. At Web Works, I led the development of a comprehensive component library that's now used across 5 different products. I focused on creating reusable, accessible components with proper documentation and testing.
[interviewer]: Can you describe the design system you implemented?
[candidate]: The design system I implemented at Web Works was built on atomic design principles..."
                        value={manualTranscript}
                        onChange={(e) => setManualTranscript(e.target.value)}
                        className="min-h-[400px] font-mono text-sm"
                      />
                      
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            // Sample transcript for Betty Taylor
                            const sampleTranscript = `[interviewer]: Hi Betty, thank you for joining us today. Can you tell me about your experience with React and component libraries?
[candidate]: Thank you for having me! I have 7 years of experience building user interfaces, with the last 5 years focused heavily on React. At Web Works, I led the development of a comprehensive component library that's now used across 5 different products. I focused on creating reusable, accessible components with proper documentation and testing. The library included over 50 components ranging from basic UI elements to complex data visualization components.

[interviewer]: That's impressive. Can you describe the design system you implemented and the impact it had?
[candidate]: The design system I implemented at Web Works was built on atomic design principles. We started by defining our design tokens - colors, typography, spacing, and shadows. Then we built atoms like buttons and inputs, molecules like form fields with labels, and organisms like complete forms and navigation menus. The impact was significant - we reduced UI development time by 40% and achieved 100% consistency across all our products. We also saw a 30% reduction in CSS bundle size due to the systematic approach.

[interviewer]: You mentioned improving page load speed by 50%. Can you walk me through how you achieved that?
[candidate]: Absolutely. When I joined Cloud Systems, the main application had a page load time of over 8 seconds. I conducted a performance audit and identified several issues. First, I implemented code splitting and lazy loading for React components, which reduced the initial bundle size by 60%. Second, I optimized our image loading with lazy loading and WebP format, saving another 30% in bandwidth. Third, I implemented service workers for caching static assets. Finally, I reduced render-blocking resources and optimized our webpack configuration. The combination of these improvements brought our load time down to under 4 seconds.

[interviewer]: How do you approach making components accessible?
[candidate]: Accessibility is a core requirement, not an afterthought. I follow WCAG 2.1 AA standards. For every component, I ensure proper semantic HTML, ARIA labels where needed, keyboard navigation support, and screen reader compatibility. I use tools like axe-core for automated testing and conduct manual testing with screen readers. At Web Works, I also created an accessibility checklist that became part of our component review process. This helped us achieve and maintain an accessibility score of 98% across our applications.

[interviewer]: Tell me about a challenging technical problem you've solved recently.
[candidate]: Recently at Web Works, we faced a challenge with our data table component that needed to handle 10,000+ rows efficiently. The virtual scrolling solution we initially tried had issues with dynamic row heights. I researched and implemented a hybrid approach using react-window with a custom solution for dynamic heights. I created a height cache that pre-calculated and stored row heights, updating them only when content changed. This solution maintained smooth 60fps scrolling even with complex cell content and reduced memory usage by 80% compared to rendering all rows.

[interviewer]: How do you stay updated with the rapidly changing frontend ecosystem?
[candidate]: I have a structured approach to continuous learning. I follow key thought leaders and official blogs for React, Vue, and Angular. I participate in frontend communities on Discord and Reddit. I also dedicate time each week to explore new tools and techniques - recently I've been exploring React Server Components and the new React compiler. I contribute to open source projects which helps me learn from other developers' code. Additionally, I attend virtual conferences and have spoken at two local meetups about performance optimization.

[interviewer]: What interests you most about this Senior Frontend Engineer position?
[candidate]: I'm excited about the opportunity to work on products that directly impact users' daily workflows. Your focus on creating intuitive, performant applications aligns perfectly with my passion for user experience and technical excellence. I'm particularly interested in the AI-powered features you're building - I believe the intersection of AI and frontend development is where the most innovative user experiences will emerge. Also, the collaborative culture you've described, where engineers have input on product decisions, is exactly the environment where I thrive.

[interviewer]: Do you have any questions for me about the role or the company?
[candidate]: Yes, I have a few questions. First, can you tell me more about the tech stack beyond what's in the job description? Second, how does the team approach testing - do you use TDD or another methodology? Third, what are the biggest technical challenges the team is currently facing? And finally, what does the career progression look like for senior engineers at your company?`;
                            setManualTranscript(sampleTranscript);
                          }}
                        >
                          Load Sample Transcript
                        </Button>
                        
                        <Button
                          onClick={async () => {
                            if (!manualTranscript.trim()) {
                              alert('Please enter a transcript');
                              return;
                            }
                            
                            setSavingManualTranscript(true);
                            try {
                              const response = await fetch(
                                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/interviews/sessions/${sessionId}/manual-transcript`,
                                {
                                  method: 'POST',
                                  headers: {
                                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                                    'Content-Type': 'application/json'
                                  },
                                  body: JSON.stringify({ transcript: manualTranscript })
                                }
                              );
                              
                              if (response.ok) {
                                // Reload session data to show the transcript and analysis
                                await loadSessionData();
                                alert('Transcript saved and analysis generated!');
                              } else {
                                const error = await response.text();
                                alert(`Failed to save transcript: ${error}`);
                              }
                            } catch (error) {
                              console.error('Error saving transcript:', error);
                              alert('Failed to save transcript');
                            } finally {
                              setSavingManualTranscript(false);
                            }
                          }}
                          disabled={savingManualTranscript || !manualTranscript.trim()}
                          className="flex items-center gap-2"
                        >
                          {savingManualTranscript ? (
                            <>
                              <Loader2Icon className="h-4 w-4 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <CheckCircleIcon className="h-4 w-4" />
                              Save & Analyze
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
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
      
      {/* Upload Dialog */}
      {showUploadDialog && (
        <UploadRecordingDialog
          sessionId={sessionId}
          onClose={() => setShowUploadDialog(false)}
          onUploadComplete={(transcript) => {
            // Refresh the session data
            loadSessionData()
            setShowUploadDialog(false)
          }}
        />
      )}
    </div>
  )
}