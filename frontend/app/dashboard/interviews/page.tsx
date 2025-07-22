'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  CalendarIcon, 
  ClockIcon, 
  UserIcon, 
  BriefcaseIcon,
  PlayIcon,
  FileTextIcon,
  BarChartIcon,
  PlusIcon,
  AlertCircleIcon,
  Loader2Icon,
  CheckCircleIcon,
  BrainIcon,
  UsersIcon,
  VideoIcon,
  PhoneIcon
} from 'lucide-react'
import { interviewsApi, InterviewSession } from '@/lib/api/interviews'
import { resumeApi } from '@/lib/api/client'

export default function InterviewsPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [interviews, setInterviews] = useState<InterviewSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resumeMap, setResumeMap] = useState<Record<string, any>>({})

  useEffect(() => {
    loadInterviews()
  }, [])

  const loadInterviews = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Load interviews
      const sessionsData = await interviewsApi.getSessions()
      setInterviews(sessionsData || [])
      
      // Load resume data for each interview to get candidate names
      const resumeIds = Array.from(new Set(sessionsData.map(s => s.resume_id)))
      const resumeData: Record<string, any> = {}
      
      for (const resumeId of resumeIds) {
        try {
          const resume = await resumeApi.getResume(resumeId)
          resumeData[resumeId] = resume
        } catch (err) {
          console.error(`Failed to load resume ${resumeId}:`, err)
        }
      }
      
      setResumeMap(resumeData)
    } catch (error: any) {
      console.error('Failed to load interviews:', error)
      
      // Check if it's an authentication error
      if (error.status === 401 || error.status === 403) {
        setError('Your session has expired. Please log in again.')
        // Redirect to login after a short delay
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      } else if (error.status === 404) {
        // This might be okay - just no interviews yet
        setInterviews([])
        setError(null)
      } else {
        setError('Failed to load interviews. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Filter interviews by status
  const upcomingInterviews = interviews.filter(i => 
    i.status === 'SCHEDULED' || i.status === 'IN_PROGRESS'
  )
  const pastInterviews = interviews.filter(i => 
    i.status === 'COMPLETED' || i.status === 'CANCELLED'
  )
  
  // Calculate stats
  const totalInterviews = interviews.length
  const completedInterviews = interviews.filter(i => i.status === 'COMPLETED')
  const avgDuration = completedInterviews.length > 0
    ? Math.round(completedInterviews.reduce((sum, i) => sum + (i.duration_minutes || 0), 0) / completedInterviews.length)
    : 0
  const hireCount = completedInterviews.filter(i => i.recommendation === 'hire').length
  const hireRate = completedInterviews.length > 0 
    ? Math.round((hireCount / completedInterviews.length) * 100)
    : 0
  const avgRating = completedInterviews.length > 0
    ? (completedInterviews.reduce((sum, i) => sum + (i.overall_rating || 0), 0) / completedInterviews.length).toFixed(1)
    : '0.0'

  return (
    <div className="container mx-auto py-6 px-4 max-w-7xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">AI Interview Copilot</h1>
          <p className="text-muted-foreground mt-1">
            Prepare, conduct, and analyze interviews with AI assistance
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={loadInterviews}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2Icon className="h-4 w-4 animate-spin" />
            ) : (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            Refresh
          </Button>
          <Button 
            variant="outline" 
            onClick={() => router.push('/dashboard/interviews/intelligence')} 
            className="flex items-center gap-2"
          >
            <BrainIcon className="h-4 w-4" />
            Intelligence
          </Button>
          <Button 
            onClick={() => router.push('/dashboard/interviews/prepare')}
            className="flex items-center gap-2"
          >
            <PlusIcon className="h-4 w-4" />
            Prepare New Interview
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Interviews</p>
                <p className="text-2xl font-bold">{totalInterviews}</p>
              </div>
              <BriefcaseIcon className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Duration</p>
                <p className="text-2xl font-bold">{avgDuration}m</p>
              </div>
              <ClockIcon className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Hire Rate</p>
                <p className="text-2xl font-bold">{hireRate}%</p>
              </div>
              <BarChartIcon className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Rating</p>
                <p className="text-2xl font-bold">{avgRating}/5</p>
              </div>
              <UserIcon className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Interview Tabs */}
      <Tabs defaultValue="upcoming" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="past">Past Interviews</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming" className="mt-4">
          {isLoading ? (
            <div className="text-center py-8">
              <Loader2Icon className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground mt-2">Loading interviews...</p>
            </div>
          ) : error ? (
            <Alert variant="destructive">
              <AlertCircleIcon className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : upcomingInterviews.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground mb-4">No upcoming interviews scheduled</p>
                <Button onClick={() => router.push('/dashboard/interviews/prepare')}>
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Prepare New Interview
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {upcomingInterviews.map((interview) => {
                const resume = resumeMap[interview.resume_id]
                const candidateName = resume 
                  ? `${resume.first_name} ${resume.last_name}`
                  : 'Unknown Candidate'
                  
                return (
                  <Card key={interview.id}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold">{candidateName}</h3>
                          <p className="text-sm text-muted-foreground">{interview.job_position}</p>
                          <div className="flex items-center gap-4 mt-2">
                            {interview.status === 'IN_PROGRESS' && (
                              <Badge variant="destructive" className="animate-pulse">
                                <div className="w-2 h-2 bg-white rounded-full mr-2" />
                                In Progress
                              </Badge>
                            )}
                            {interview.scheduled_at && (
                              <>
                                <span className="text-sm text-muted-foreground flex items-center gap-1">
                                  <CalendarIcon className="h-4 w-4" />
                                  {new Date(interview.scheduled_at).toLocaleDateString()}
                                </span>
                                <span className="text-sm text-muted-foreground flex items-center gap-1">
                                  <ClockIcon className="h-4 w-4" />
                                  {new Date(interview.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                              </>
                            )}
                            <span className="text-sm text-muted-foreground">
                              {interview.duration_minutes || 60} minutes
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => router.push(`/dashboard/interviews/${interview.id}/session`)}
                            className="flex items-center gap-2"
                          >
                            <PlayIcon className="h-4 w-4" />
                            {interview.status === 'IN_PROGRESS' ? 'Continue' : 'Start'} Interview
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="past" className="mt-4">
          {isLoading ? (
            <div className="text-center py-8">
              <Loader2Icon className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground mt-2">Loading interviews...</p>
            </div>
          ) : error ? (
            <Alert variant="destructive">
              <AlertCircleIcon className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : pastInterviews.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">No completed interviews yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {pastInterviews.map((interview) => {
                const resume = resumeMap[interview.resume_id]
                const candidateName = resume 
                  ? `${resume.first_name} ${resume.last_name}`
                  : 'Unknown Candidate'
                  
                return (
                  <Card key={interview.id}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold">{candidateName}</h3>
                          <p className="text-sm text-muted-foreground">{interview.job_position}</p>
                          <div className="flex items-center gap-4 mt-2">
                            <span className="text-sm text-muted-foreground">
                              {interview.ended_at 
                                ? new Date(interview.ended_at).toLocaleDateString()
                                : new Date(interview.created_at).toLocaleDateString()
                              }
                            </span>
                            {interview.status === 'COMPLETED' ? (
                              <Badge variant="outline" className="text-green-600">
                                <CheckCircleIcon className="h-3 w-3 mr-1" />
                                Completed
                              </Badge>
                            ) : interview.status === 'CANCELLED' ? (
                              <Badge variant="outline" className="text-gray-600">
                                Cancelled
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-blue-600">
                                {interview.status}
                              </Badge>
                            )}
                            {interview.interview_type && (
                              <Badge variant="secondary" className="text-xs">
                                {interview.interview_type === 'IN_PERSON' && <UsersIcon className="h-3 w-3 mr-1" />}
                                {interview.interview_type === 'VIRTUAL' && <VideoIcon className="h-3 w-3 mr-1" />}
                                {interview.interview_type === 'PHONE' && <PhoneIcon className="h-3 w-3 mr-1" />}
                                {interview.interview_type.replace('_', ' ')}
                              </Badge>
                            )}
                            {interview.recommendation && (
                              <span className={`px-2 py-1 rounded-full text-xs ${
                                interview.recommendation === 'hire' 
                                  ? 'bg-green-100 text-green-800' 
                                  : interview.recommendation === 'no_hire'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {interview.recommendation === 'hire' ? 'Recommended' : 
                                 interview.recommendation === 'no_hire' ? 'Not Recommended' : 'Maybe'}
                              </span>
                            )}
                            {interview.overall_rating && (
                              <span className="text-sm">Rating: {interview.overall_rating}/5</span>
                            )}
                            {interview.duration_minutes && (
                              <span className="text-sm text-muted-foreground">
                                Duration: {interview.duration_minutes}m
                              </span>
                            )}
                          </div>
                          {interview.notes && (
                            <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                              Notes: {interview.notes}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push(`/dashboard/interviews/${interview.id}/session`)}
                          >
                            View Details
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push(`/dashboard/interviews/${interview.id}/scorecard`)}
                            className="flex items-center gap-2"
                          >
                            <FileTextIcon className="h-4 w-4" />
                            Scorecard
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="templates" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Interview Templates</CardTitle>
              <CardDescription>
                Create and manage reusable interview templates for different roles
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">Software Engineer Template</h4>
                        <p className="text-sm text-muted-foreground">
                          Technical assessment with coding challenges
                        </p>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          // Navigate to prepare page with template parameters
                          const params = new URLSearchParams({
                            template: 'software-engineer',
                            position: 'Software Engineer',
                            type: 'technical',
                            focusAreas: JSON.stringify(['Coding Skills', 'System Design', 'Problem Solving', 'Technical Knowledge'])
                          })
                          router.push(`/dashboard/interviews/prepare?${params.toString()}`)
                        }}
                      >
                        Use Template
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">Product Manager Template</h4>
                        <p className="text-sm text-muted-foreground">
                          Focus on strategy and leadership skills
                        </p>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          // Navigate to prepare page with template parameters
                          const params = new URLSearchParams({
                            template: 'product-manager',
                            position: 'Product Manager',
                            type: 'behavioral',
                            focusAreas: JSON.stringify(['Product Strategy', 'Leadership', 'Data Analysis', 'Customer Focus', 'Stakeholder Management'])
                          })
                          router.push(`/dashboard/interviews/prepare?${params.toString()}`)
                        }}
                      >
                        Use Template
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">Sales Representative Template</h4>
                        <p className="text-sm text-muted-foreground">
                          Evaluate communication and sales skills
                        </p>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          // Navigate to prepare page with template parameters
                          const params = new URLSearchParams({
                            template: 'sales-representative',
                            position: 'Sales Representative',
                            type: 'behavioral',
                            focusAreas: JSON.stringify(['Communication', 'Negotiation', 'Customer Relations', 'Sales Process', 'Target Achievement'])
                          })
                          router.push(`/dashboard/interviews/prepare?${params.toString()}`)
                        }}
                      >
                        Use Template
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">Data Scientist Template</h4>
                        <p className="text-sm text-muted-foreground">
                          Technical and analytical skills assessment
                        </p>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          // Navigate to prepare page with template parameters
                          const params = new URLSearchParams({
                            template: 'data-scientist',
                            position: 'Data Scientist',
                            type: 'technical',
                            focusAreas: JSON.stringify(['Statistical Analysis', 'Machine Learning', 'Data Visualization', 'Python/R', 'SQL'])
                          })
                          router.push(`/dashboard/interviews/prepare?${params.toString()}`)
                        }}
                      >
                        Use Template
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
              <div className="mt-6 text-center">
                <Button 
                  variant="outline"
                  onClick={() => router.push('/dashboard/interviews/prepare')}
                  className="w-full"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Create Custom Interview
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}