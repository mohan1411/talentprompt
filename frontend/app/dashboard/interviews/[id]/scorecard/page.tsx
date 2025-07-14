'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress-simple'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  UserIcon,
  BriefcaseIcon,
  CalendarIcon,
  ClockIcon,
  StarIcon,
  CheckCircleIcon,
  XCircleIcon,
  AlertCircleIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  BrainIcon,
  FileTextIcon,
  ShareIcon,
  DownloadIcon,
  SparklesIcon,
  Loader2Icon,
  ArrowLeftIcon
} from 'lucide-react'
import { interviewsApi, InterviewSession } from '@/lib/api/interviews'
import { resumeApi, Resume } from '@/lib/api/client'

export default function InterviewScorecardPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [resume, setResume] = useState<Resume | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scorecard, setScorecard] = useState<any>(null)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  
  useEffect(() => {
    if (sessionId) {
      loadScorecardData()
    }
  }, [sessionId])
  
  const loadScorecardData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Load session data
      const sessionData = await interviewsApi.getSession(sessionId)
      setSession(sessionData)
      
      // Load resume data
      const resumeData = await resumeApi.getResume(sessionData.resume_id)
      setResume(resumeData)
      
      // Try to generate scorecard if available
      if (sessionData.status === 'completed') {
        try {
          const scorecardData = await interviewsApi.generateScorecard(sessionId)
          
          // Transform API response to match frontend format
          const transformedScorecard = {
            ...scorecardData,
            candidateName: scorecardData.candidate_name,
            position: scorecardData.position,
            interviewDate: scorecardData.interview_date,
            duration: sessionData.duration_minutes || 0,
            overallRating: scorecardData.overall_rating,
            recommendation: scorecardData.recommendation,
            percentileRank: scorecardData.percentile_rank,
            ratings: {
              technical: {
                score: scorecardData.technical_skills ? 
                  parseFloat((Object.values(scorecardData.technical_skills).reduce((sum: number, val: any) => sum + val, 0) / Object.keys(scorecardData.technical_skills).length).toFixed(1)) : 0,
                breakdown: scorecardData.technical_skills || {}
              },
              behavioral: {
                score: scorecardData.soft_skills ? 
                  parseFloat((Object.values(scorecardData.soft_skills).reduce((sum: number, val: any) => sum + val, 0) / Object.keys(scorecardData.soft_skills).length).toFixed(1)) : 0,
                breakdown: scorecardData.soft_skills || {}
              },
              cultureFit: scorecardData.culture_fit || 0
            },
            strengths: scorecardData.strengths || [],
            concerns: scorecardData.concerns || [],
            keyTakeaways: scorecardData.key_takeaways || [],
            nextSteps: scorecardData.next_steps || [],
            questionPerformance: sessionData.questions?.filter(q => q.response_rating).map(q => ({
              question: q.question_text,
              rating: q.response_rating || 0,
              category: q.category
            })) || []
          }
          
          console.log('Transformed scorecard:', transformedScorecard)
          setScorecard(transformedScorecard)
        } catch (err) {
          console.error('Failed to generate scorecard:', err)
          // Use session data to create basic scorecard
          setScorecard(generateBasicScorecard(sessionData, resumeData))
        }
      } else {
        // Create basic scorecard from session data
        setScorecard(generateBasicScorecard(sessionData, resumeData))
      }
    } catch (error: any) {
      console.error('Failed to load scorecard data:', error)
      
      if (error.status === 404) {
        setError('Interview session not found. Please check the URL.')
      } else if (error.status === 401 || error.status === 403) {
        setError('Your session has expired. Please log in again.')
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      } else {
        setError('Failed to load scorecard data. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }
  
  const generateBasicScorecard = (session: InterviewSession, resume: Resume) => {
    // Calculate ratings from questions
    const questions = session.questions || []
    console.log('Session questions:', questions)
    const answeredQuestions = questions.filter(q => q.response_rating)
    console.log('Answered questions:', answeredQuestions)
    const avgRating = answeredQuestions.length > 0
      ? answeredQuestions.reduce((sum, q) => sum + (q.response_rating || 0), 0) / answeredQuestions.length
      : 0
      
    const technicalQuestions = answeredQuestions.filter(q => q.category.toLowerCase() === 'technical')
    const behavioralQuestions = answeredQuestions.filter(q => q.category.toLowerCase() === 'behavioral')
    
    const technicalAvg = technicalQuestions.length > 0
      ? technicalQuestions.reduce((sum, q) => sum + (q.response_rating || 0), 0) / technicalQuestions.length
      : 0
      
    const behavioralAvg = behavioralQuestions.length > 0
      ? behavioralQuestions.reduce((sum, q) => sum + (q.response_rating || 0), 0) / behavioralQuestions.length
      : 0
    
    // Extract skills from questions and calculate skill-specific ratings
    const extractSkillsFromQuestions = (questions: any[]) => {
      const skillRatings: Record<string, { total: number; count: number }> = {}
      
      // Technical skill keywords
      const technicalKeywords = [
        'Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'Kubernetes',
        'Java', 'TypeScript', 'SQL', 'API', 'Database', 'System Design', 'Architecture',
        'Testing', 'CI/CD', 'Git', 'Agile', 'Frontend', 'Backend', 'Full Stack'
      ]
      
      // Behavioral skill keywords
      const behavioralKeywords = [
        'Leadership', 'Communication', 'Teamwork', 'Problem Solving', 'Time Management',
        'Conflict Resolution', 'Adaptability', 'Initiative', 'Collaboration', 'Mentoring'
      ]
      
      questions.forEach(q => {
        if (!q.response_rating) return
        
        const questionLower = q.question_text.toLowerCase()
        const keywords = q.category.toLowerCase() === 'technical' ? technicalKeywords : behavioralKeywords
        
        keywords.forEach(skill => {
          if (questionLower.includes(skill.toLowerCase())) {
            if (!skillRatings[skill]) {
              skillRatings[skill] = { total: 0, count: 0 }
            }
            skillRatings[skill].total += q.response_rating
            skillRatings[skill].count += 1
          }
        })
        
        // If no specific skill found, use general category
        if (Object.keys(skillRatings).length === 0) {
          const generalSkill = q.category.toLowerCase() === 'technical' ? 'Technical Skills' : 'Soft Skills'
          if (!skillRatings[generalSkill]) {
            skillRatings[generalSkill] = { total: 0, count: 0 }
          }
          skillRatings[generalSkill].total += q.response_rating
          skillRatings[generalSkill].count += 1
        }
      })
      
      // Calculate averages
      const breakdown: Record<string, number> = {}
      Object.entries(skillRatings).forEach(([skill, data]) => {
        breakdown[skill] = parseFloat((data.total / data.count).toFixed(1))
      })
      
      return breakdown
    }
    
    const technicalBreakdown = extractSkillsFromQuestions(technicalQuestions)
    const behavioralBreakdown = extractSkillsFromQuestions(behavioralQuestions)
    
    // Generate contextual strengths and concerns based on ratings
    const generateStrengths = () => {
      const strengths = []
      
      // Check technical strengths
      Object.entries(technicalBreakdown).forEach(([skill, rating]) => {
        if (rating >= 4) {
          strengths.push(`Strong ${skill} skills demonstrated`)
        }
      })
      
      // Check behavioral strengths
      Object.entries(behavioralBreakdown).forEach(([skill, rating]) => {
        if (rating >= 4) {
          strengths.push(`Excellent ${skill} abilities`)
        }
      })
      
      // Add from candidate's resume skills if highly rated
      if (avgRating >= 4 && resume.skills && resume.skills.length > 0) {
        strengths.push(`Proven expertise in ${resume.skills.slice(0, 3).join(', ')}`)
      }
      
      // Add experience-based strength
      if (resume.years_experience && resume.years_experience >= 5) {
        strengths.push(`${resume.years_experience} years of relevant industry experience`)
      }
      
      return strengths.length > 0 ? strengths : ['Good overall performance', 'Professional demeanor']
    }
    
    const generateConcerns = () => {
      const concerns = []
      
      // Check technical concerns
      Object.entries(technicalBreakdown).forEach(([skill, rating]) => {
        if (rating < 3) {
          concerns.push(`${skill} skills need improvement`)
        }
      })
      
      // Check behavioral concerns
      Object.entries(behavioralBreakdown).forEach(([skill, rating]) => {
        if (rating < 3) {
          concerns.push(`${skill} could be stronger`)
        }
      })
      
      // Add general concerns if low ratings
      if (avgRating < 3) {
        concerns.push('Overall performance below expectations')
      }
      
      // Check for missing skills from job requirements
      if (session.job_requirements && session.job_requirements.skills) {
        const requiredSkills = session.job_requirements.skills as string[]
        const candidateSkills = resume.skills || []
        const missingSkills = requiredSkills.filter(skill => 
          !candidateSkills.some(cs => cs.toLowerCase().includes(skill.toLowerCase()))
        )
        if (missingSkills.length > 0) {
          concerns.push(`May lack experience with ${missingSkills.slice(0, 2).join(', ')}`)
        }
      }
      
      return concerns.length > 0 ? concerns : ['Further technical assessment recommended']
    }
    
    return {
      candidateName: `${resume.first_name} ${resume.last_name}`,
      position: session.job_position,
      interviewDate: session.ended_at ? new Date(session.ended_at).toLocaleDateString() : new Date(session.created_at).toLocaleDateString(),
      duration: session.duration_minutes || 0,
      overallRating: avgRating.toFixed(1),
      recommendation: session.recommendation || (avgRating >= 4 ? 'hire' : avgRating >= 3 ? 'maybe' : 'no_hire'),
      percentileRank: avgRating >= 4.5 ? 95 : avgRating >= 4 ? 85 : avgRating >= 3.5 ? 70 : avgRating >= 3 ? 50 : 25,
      
      ratings: {
        technical: {
          score: parseFloat(technicalAvg.toFixed(1)),
          breakdown: technicalBreakdown
        },
        behavioral: {
          score: parseFloat(behavioralAvg.toFixed(1)),
          breakdown: behavioralBreakdown
        },
        cultureFit: session.overall_rating || avgRating || 0
      },
      
      strengths: session.strengths && session.strengths.length > 0 ? session.strengths : generateStrengths(),
      
      concerns: session.concerns && session.concerns.length > 0 ? session.concerns : generateConcerns(),
      
      keyTakeaways: (session.preparation_notes?.analysis?.key_talking_points && 
                     Array.isArray(session.preparation_notes.analysis.key_talking_points)) 
                     ? session.preparation_notes.analysis.key_talking_points 
                     : [
                       `${resume.first_name} has ${resume.years_experience || 0} years of experience`,
                       `Current role: ${resume.current_title || 'Not specified'}`,
                       `Key skills include ${resume.skills?.slice(0, 3).join(', ') || 'various technologies'}`
                     ],
      
      nextSteps: avgRating >= 4 
        ? ['Schedule final round interview', 'Check references', 'Prepare offer package']
        : avgRating >= 3
        ? ['Schedule technical assessment', 'Gather additional feedback', 'Compare with other candidates']
        : ['Send polite rejection', 'Keep on file for future opportunities', 'Provide constructive feedback'],
      
      questionPerformance: questions && questions.length > 0 ? questions.map(q => ({
        question: q.question_text,
        rating: q.response_rating || 0,
        category: q.category
      })) : []
    }
  }

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'hire': return 'text-green-600 bg-green-100'
      case 'no_hire': return 'text-red-600 bg-red-100'
      default: return 'text-yellow-600 bg-yellow-100'
    }
  }

  const getRecommendationText = (recommendation: string) => {
    switch (recommendation) {
      case 'hire': return 'Recommended for Hire'
      case 'no_hire': return 'Not Recommended'
      default: return 'Requires Further Discussion'
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-6xl">
        <div className="flex items-center justify-center min-h-[600px]">
          <div className="text-center">
            <Loader2Icon className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
            <p className="text-sm text-muted-foreground mt-2">Loading scorecard...</p>
          </div>
        </div>
      </div>
    )
  }
  
  if (error || !scorecard) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-6xl">
        <Alert variant="destructive">
          <AlertCircleIcon className="h-4 w-4" />
          <AlertDescription>
            {error || 'Failed to load scorecard. Please try again.'}
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
    <>
      <style jsx global>{`
        @media print {
          body * {
            visibility: hidden;
          }
          .print-area, .print-area * {
            visibility: visible;
          }
          .print-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
          .no-print {
            display: none !important;
          }
          .print-content {
            display: block !important;
          }
          .tabs-navigation {
            display: none !important;
          }
          @page {
            margin: 1cm;
            size: A4;
          }
          .page-break {
            page-break-after: always;
          }
        }
        @media screen {
          .print-content {
            display: none;
          }
        }
      `}</style>
      <div className="container mx-auto py-6 px-4 max-w-6xl print-area">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">Interview Scorecard</h1>
            <div className="flex items-center gap-4 mt-2 text-muted-foreground">
              <span className="flex items-center gap-1">
                <UserIcon className="h-4 w-4" />
                {scorecard.candidateName}
              </span>
              <span className="flex items-center gap-1">
                <BriefcaseIcon className="h-4 w-4" />
                {scorecard.position}
              </span>
              <span className="flex items-center gap-1">
                <CalendarIcon className="h-4 w-4" />
                {scorecard.interviewDate}
              </span>
              <span className="flex items-center gap-1">
                <ClockIcon className="h-4 w-4" />
                {scorecard.duration || session?.duration_minutes || 'N/A'} minutes
              </span>
            </div>
          </div>
          <div className="flex gap-2 no-print">
            <Button 
              variant="outline" 
              size="sm"
              onClick={async () => {
                try {
                  // For now, create a shareable summary
                  const shareableText = `
Interview Scorecard - ${scorecard?.candidateName}
Position: ${scorecard?.position}
Date: ${scorecard?.interviewDate}
Overall Rating: ${scorecard?.overallRating}/5
Recommendation: ${scorecard?.recommendation === 'hire' ? 'Recommended for Hire' : 
                   scorecard?.recommendation === 'no_hire' ? 'Not Recommended' : 'Requires Further Discussion'}

Technical Skills: ${scorecard?.ratings?.technical?.score || 0}/5
Behavioral Skills: ${scorecard?.ratings?.behavioral?.score || 0}/5

Key Strengths:
${scorecard?.strengths?.map((s: string) => `• ${s}`).join('\n') || 'None listed'}

Areas of Concern:
${scorecard?.concerns?.map((c: string) => `• ${c}`).join('\n') || 'None listed'}

Next Steps:
${scorecard?.nextSteps?.map((s: string) => `• ${s}`).join('\n') || 'None listed'}

Note: This is a summary. Full scorecard requires system access.
                  `.trim()
                  
                  // Try to use Web Share API first (mobile)
                  if (navigator.share && /mobile|android|iphone/i.test(navigator.userAgent)) {
                    await navigator.share({
                      title: `Interview Scorecard - ${scorecard?.candidateName}`,
                      text: shareableText
                    })
                  } else {
                    // Fallback to clipboard
                    await navigator.clipboard.writeText(shareableText)
                    alert('Scorecard summary copied to clipboard! You can paste it in an email or message.')
                  }
                } catch (err) {
                  console.error('Failed to share:', err)
                  alert('Failed to share scorecard. Please try exporting as PDF instead.')
                }
              }}
            >
              <ShareIcon className="h-4 w-4 mr-2" />
              Share
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                // Generate and download PDF
                window.print()
              }}
            >
              <DownloadIcon className="h-4 w-4 mr-2" />
              Export PDF
            </Button>
          </div>
        </div>
      </div>

      {/* Overall Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-4xl font-bold mb-2">{scorecard.overallRating}/5</div>
              <div className="flex justify-center mb-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <StarIcon
                    key={star}
                    className={`h-5 w-5 ${
                      star <= Math.floor(scorecard.overallRating)
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
              <p className="text-sm text-muted-foreground">Overall Rating</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <Badge 
                className={`text-lg px-4 py-2 mb-2 ${getRecommendationColor(scorecard.recommendation)}`}
              >
                {getRecommendationText(scorecard.recommendation)}
              </Badge>
              <p className="text-sm text-muted-foreground mt-2">Interview Decision</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-4xl font-bold mb-2">{scorecard.percentileRank}%</div>
              <Progress value={scorecard.percentileRank} className="mb-2" />
              <p className="text-sm text-muted-foreground">Percentile Ranking</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Print-only content - shows all tabs content */}
      <div className="print-content space-y-6">
        {/* All Ratings */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold">Detailed Ratings</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Technical Skills */}
            <Card>
              <CardHeader>
                <CardTitle>Technical Skills</CardTitle>
                <div className="text-2xl font-bold">
                  {scorecard?.ratings?.technical?.score || '0'}/5
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {scorecard?.ratings?.technical?.breakdown ? (
                    Object.entries(scorecard.ratings.technical.breakdown).map(([skill, rating]: [string, any]) => (
                      <div key={skill}>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">{skill}</span>
                          <span className="text-sm font-medium">{rating}/5</span>
                        </div>
                        <Progress value={rating * 20} />
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No technical skills rated</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Behavioral Skills */}
            <Card>
              <CardHeader>
                <CardTitle>Behavioral Skills</CardTitle>
                <div className="text-2xl font-bold">
                  {scorecard?.ratings?.behavioral?.score || '0'}/5
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {scorecard?.ratings?.behavioral?.breakdown ? (
                    Object.entries(scorecard.ratings.behavioral.breakdown).map(([skill, rating]: [string, any]) => (
                      <div key={skill}>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">{skill}</span>
                          <span className="text-sm font-medium">{rating}/5</span>
                        </div>
                        <Progress value={rating * 20} />
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No behavioral skills rated</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Strengths & Concerns */}
        <div className="page-break"></div>
        <div className="space-y-6">
          <h2 className="text-xl font-bold">Assessment Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUpIcon className="h-5 w-5 text-green-600" />
                  Key Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {scorecard?.strengths && scorecard.strengths.length > 0 ? (
                    scorecard.strengths.map((strength: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <span>{strength}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-muted-foreground">No strengths identified</li>
                  )}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircleIcon className="h-5 w-5 text-amber-600" />
                  Areas of Concern
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {scorecard?.concerns && scorecard.concerns.length > 0 ? (
                    scorecard.concerns.map((concern: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <AlertCircleIcon className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                        <span>{concern}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-muted-foreground">No concerns identified</li>
                  )}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Key Takeaways and Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle>Recommended Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-2">
                {scorecard?.nextSteps && scorecard.nextSteps.length > 0 ? (
                  scorecard.nextSteps.map((step: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center mt-0.5">
                        {idx + 1}
                      </span>
                      <span>{step}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-sm text-muted-foreground">No next steps defined</li>
                )}
              </ol>
            </CardContent>
          </Card>
        </div>

        {/* Question Performance */}
        {scorecard?.questionPerformance && scorecard.questionPerformance.length > 0 && (
          <>
            <div className="page-break"></div>
            <div className="space-y-6">
              <h2 className="text-xl font-bold">Question-by-Question Performance</h2>
              <Card>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {scorecard.questionPerformance.map((q: any, idx: number) => (
                      <div key={idx} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <h4 className="font-medium">{q.question}</h4>
                            <Badge variant="outline" className="mt-1">{q.category}</Badge>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold">{q.rating}/5</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>

      {/* Detailed Assessment */}
      <Tabs defaultValue="ratings" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 tabs-navigation">
          <TabsTrigger value="ratings">Ratings</TabsTrigger>
          <TabsTrigger value="strengths">Strengths & Concerns</TabsTrigger>
          <TabsTrigger value="performance">Question Performance</TabsTrigger>
          <TabsTrigger value="ai-insights">AI Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="ratings" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Technical Skills */}
            <Card>
              <CardHeader>
                <CardTitle>Technical Skills</CardTitle>
                <div className="text-2xl font-bold">
                  {scorecard.ratings?.technical?.score || '0'}/5
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {scorecard.ratings?.technical?.breakdown ? (
                    Object.entries(scorecard.ratings.technical.breakdown).map(([skill, rating]: [string, any]) => (
                      <div key={skill}>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">{skill}</span>
                          <span className="text-sm font-medium">{rating}/5</span>
                        </div>
                        <Progress value={rating * 20} />
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Technical skills will be evaluated during the interview
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Behavioral Skills */}
            <Card>
              <CardHeader>
                <CardTitle>Behavioral Skills</CardTitle>
                <div className="text-2xl font-bold">
                  {scorecard.ratings?.behavioral?.score || '0'}/5
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {scorecard.ratings?.behavioral?.breakdown ? (
                    Object.entries(scorecard.ratings.behavioral.breakdown).map(([skill, rating]: [string, any]) => (
                      <div key={skill}>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">{skill}</span>
                          <span className="text-sm font-medium">{rating}/5</span>
                        </div>
                        <Progress value={rating * 20} />
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Behavioral skills will be evaluated during the interview
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Culture Fit */}
          <Card>
            <CardHeader>
              <CardTitle>Culture Fit Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Progress value={(scorecard.ratings?.cultureFit || 0) * 20} className="h-3" />
                </div>
                <div className="ml-4 text-2xl font-bold">{scorecard.ratings?.cultureFit || 0}/5</div>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Based on alignment with company values and team dynamics
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="strengths" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUpIcon className="h-5 w-5 text-green-600" />
                  Key Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {scorecard.strengths && scorecard.strengths.length > 0 ? (
                    scorecard.strengths.map((strength: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <span>{strength}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-muted-foreground">No strengths identified yet</li>
                  )}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircleIcon className="h-5 w-5 text-amber-600" />
                  Areas of Concern
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {scorecard.concerns && scorecard.concerns.length > 0 ? (
                    scorecard.concerns.map((concern: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <AlertCircleIcon className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                        <span>{concern}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-muted-foreground">No concerns identified yet</li>
                  )}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Key Takeaways */}
          <Card>
            <CardHeader>
              <CardTitle>Key Takeaways</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {scorecard.keyTakeaways && scorecard.keyTakeaways.length > 0 ? (
                  scorecard.keyTakeaways.map((takeaway, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <BrainIcon className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                      <span>{takeaway}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-sm text-muted-foreground">Key takeaways will be available after interview completion</li>
                )}
              </ul>
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle>Recommended Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-2">
                {scorecard.nextSteps && scorecard.nextSteps.length > 0 ? (
                  scorecard.nextSteps.map((step: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center mt-0.5">
                        {idx + 1}
                      </span>
                      <span>{step}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-sm text-muted-foreground">Next steps will be determined after interview completion</li>
                )}
              </ol>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Question-by-Question Performance</CardTitle>
              <CardDescription>
                How the candidate performed on each interview question
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {scorecard.questionPerformance && scorecard.questionPerformance.length > 0 ? (
                  scorecard.questionPerformance.map((q: any, idx: number) => (
                    <div key={idx} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium line-clamp-2">{q.question}</h4>
                          <Badge variant="outline" className="mt-1">{q.category}</Badge>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold">
                            {q.rating > 0 ? `${q.rating}/5` : 'Not rated'}
                          </div>
                          {q.rating > 0 && (
                            <div className="flex justify-end mt-1">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <StarIcon
                                  key={star}
                                  className={`h-4 w-4 ${
                                    star <= q.rating
                                      ? 'fill-yellow-400 text-yellow-400'
                                      : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No questions have been rated yet
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai-insights" className="space-y-6">
          <Alert>
            <SparklesIcon className="h-4 w-4" />
            <AlertDescription>
              AI-generated insights based on interview performance and candidate profile
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>AI Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {session?.preparation_notes?.analysis ? (
                <>
                  <div>
                    <h4 className="font-medium mb-2">Candidate Summary</h4>
                    <p className="text-sm text-muted-foreground">
                      {session.preparation_notes.analysis.candidate_summary?.brief || 
                       'AI analysis will be available after interview completion.'}
                    </p>
                  </div>
                  
                  {session.preparation_notes.analysis.fit_assessment && (
                    <div>
                      <h4 className="font-medium mb-2">Fit Assessment</h4>
                      <p className="text-sm text-muted-foreground">
                        Score: {session.preparation_notes.analysis.fit_assessment.score}/10
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {session.preparation_notes.analysis.fit_assessment.reasoning}
                      </p>
                    </div>
                  )}
                  
                  {session.preparation_notes.analysis.red_flags && session.preparation_notes.analysis.red_flags.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Red Flags to Consider</h4>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {session.preparation_notes.analysis.red_flags.map((flag, idx) => (
                          <li key={idx}>• {flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <div>
                  <p className="text-sm text-muted-foreground">
                    AI insights will be generated based on the completed interview performance. 
                    Complete all interview questions and ratings to get comprehensive AI analysis.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {session?.status === 'completed' && (
            <Card>
              <CardHeader>
                <CardTitle>Generate Full AI Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <SparklesIcon className="h-12 w-12 mx-auto mb-4 text-primary" />
                  <p className="mb-4">Get comprehensive AI analysis of this interview</p>
                  <Button 
                    onClick={async () => {
                      try {
                        setIsLoading(true)
                        const scorecardData = await interviewsApi.generateScorecard(sessionId)
                        
                        // Transform API response to match frontend format
                        const transformedScorecard = {
                          ...scorecardData,
                          candidateName: scorecardData.candidate_name,
                          position: scorecardData.position,
                          interviewDate: scorecardData.interview_date,
                          duration: session?.duration_minutes || 0,
                          overallRating: scorecardData.overall_rating,
                          recommendation: scorecardData.recommendation,
                          percentileRank: scorecardData.percentile_rank,
                          ratings: {
                            technical: {
                              score: scorecardData.technical_skills ? 
                                parseFloat((Object.values(scorecardData.technical_skills).reduce((sum: number, val: any) => sum + val, 0) / Object.keys(scorecardData.technical_skills).length).toFixed(1)) : 0,
                              breakdown: scorecardData.technical_skills || {}
                            },
                            behavioral: {
                              score: scorecardData.soft_skills ? 
                                parseFloat((Object.values(scorecardData.soft_skills).reduce((sum: number, val: any) => sum + val, 0) / Object.keys(scorecardData.soft_skills).length).toFixed(1)) : 0,
                              breakdown: scorecardData.soft_skills || {}
                            },
                            cultureFit: scorecardData.culture_fit || 0
                          },
                          strengths: scorecardData.strengths || [],
                          concerns: scorecardData.concerns || [],
                          keyTakeaways: scorecardData.key_takeaways || [],
                          nextSteps: scorecardData.next_steps || [],
                          questionPerformance: session?.questions?.filter(q => q.response_rating).map(q => ({
                            question: q.question_text,
                            rating: q.response_rating || 0,
                            category: q.category
                          })) || []
                        }
                        
                        setScorecard(transformedScorecard)
                        setIsLoading(false)
                        
                        // Show success message
                        alert('AI Report generated successfully!')
                      } catch (err) {
                        console.error('Failed to generate report:', err)
                        setIsLoading(false)
                        alert('Failed to generate AI report. Please try again.')
                      }
                    }}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="h-4 w-4 mr-2" />
                        Generate AI Report
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex justify-center gap-4 mt-8 no-print">
        <Button variant="outline" onClick={() => router.push('/dashboard/interviews')}>
          Back to Interviews
        </Button>
        <Button
          onClick={async () => {
            if (!resume || !session) {
              alert('Unable to schedule next round. Missing information.')
              return
            }
            
            try {
              setIsGeneratingReport(true)
              setError(null)
              
              // Call the new API endpoint to schedule next round
              const response = await interviewsApi.scheduleNextRound(session.id)
              
              if (response && response.session_id) {
                // Navigate directly to the new interview session
                router.push(`/dashboard/interviews/${response.session_id}/session`)
              } else {
                throw new Error('Failed to schedule next round')
              }
            } catch (error: any) {
              console.error('Failed to schedule next round:', error)
              const errorMessage = error?.detail || error?.message || 'Failed to schedule next round'
              alert(typeof errorMessage === 'string' ? errorMessage : 'Failed to schedule next round')
            } finally {
              setIsGeneratingReport(false)
            }
          }}
          disabled={!resume || scorecard?.recommendation === 'no_hire' || isGeneratingReport}
        >
          {isGeneratingReport ? (
            <>
              <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
              Scheduling...
            </>
          ) : (
            'Schedule Next Round'
          )}
        </Button>
      </div>
    </div>
    </>
  )
}