'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress-simple'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator-simple'
import { 
  UserIcon,
  BrainIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  TrendingUpIcon,
  AlertCircleIcon,
  SparklesIcon,
  BarChartIcon
} from 'lucide-react'

interface DualTrackAnalysisProps {
  humanAssessment?: {
    questionsRated: number
    totalQuestions: number
    averageRating: number
    categoryRatings: Record<string, number>
    completionRate: number
  }
  aiAnalysis?: {
    overall_rating: number
    recommendation: string
    technical_skills: Record<string, number>
    soft_skills: Record<string, number>
    confidence: number
    questionsAnalyzed: number
  }
  sessionData: {
    job_position: string
    interview_type: string
    duration_minutes: number
  }
}

export function DualTrackAnalysis({ humanAssessment, aiAnalysis, sessionData }: DualTrackAnalysisProps) {
  // Calculate discrepancies
  const overallDiscrepancy = humanAssessment && aiAnalysis 
    ? Math.abs(humanAssessment.averageRating - aiAnalysis.overall_rating)
    : 0

  const hasSignificantDiscrepancy = overallDiscrepancy > 1.0

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'hire':
        return 'text-green-600 bg-green-50'
      case 'no_hire':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-amber-600 bg-amber-50'
    }
  }

  const getRecommendationText = (recommendation: string) => {
    switch (recommendation) {
      case 'hire':
        return 'Recommend Hire'
      case 'no_hire':
        return 'Do Not Hire'
      default:
        return 'Further Evaluation'
    }
  }

  const formatRating = (rating: number) => {
    return rating ? rating.toFixed(1) : 'N/A'
  }

  return (
    <div className="space-y-6">
      {/* Discrepancy Alert */}
      {hasSignificantDiscrepancy && (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangleIcon className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            <strong>Significant Discrepancy Detected:</strong> Human and AI assessments differ by {overallDiscrepancy.toFixed(1)} points.
            This warrants further review and discussion.
          </AlertDescription>
        </Alert>
      )}

      {/* Side-by-Side Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Human Assessment */}
        <Card className="border-2 border-blue-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserIcon className="h-5 w-5 text-blue-600" />
              Human Assessment
            </CardTitle>
            <CardDescription>
              Based on live interview observations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {humanAssessment ? (
              <>
                {/* Overall Rating */}
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <h4 className="text-sm font-medium text-blue-600 mb-1">Overall Rating</h4>
                  <div className="text-3xl font-bold text-blue-700">
                    {formatRating(humanAssessment.averageRating)}/5.0
                  </div>
                  <p className="text-xs text-blue-600 mt-1">
                    {humanAssessment.questionsRated} of {humanAssessment.totalQuestions} questions rated
                  </p>
                </div>

                {/* Completion Rate */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium">Interview Completion</span>
                    <span className="text-sm text-muted-foreground">
                      {Math.round(humanAssessment.completionRate)}%
                    </span>
                  </div>
                  <Progress value={humanAssessment.completionRate} className="h-2" />
                </div>

                {/* Category Ratings */}
                {Object.entries(humanAssessment.categoryRatings).length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium">Category Breakdown</h4>
                    {Object.entries(humanAssessment.categoryRatings).map(([category, rating]) => (
                      <div key={category}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm capitalize">{category.replace('_', ' ')}</span>
                          <span className="text-sm text-muted-foreground">{rating.toFixed(1)}/5.0</span>
                        </div>
                        <Progress value={rating * 20} className="h-2" />
                      </div>
                    ))}
                  </div>
                )}

                {/* Key Observations */}
                <div className="pt-2">
                  <p className="text-sm text-muted-foreground">
                    <SparklesIcon className="h-3 w-3 inline mr-1" />
                    Based on interviewer's real-time assessment
                  </p>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <UserIcon className="h-12 w-12 mx-auto mb-2 opacity-20" />
                <p>No human ratings recorded</p>
                <p className="text-xs mt-1">Rate questions during the interview</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Analysis */}
        <Card className="border-2 border-purple-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BrainIcon className="h-5 w-5 text-purple-600" />
              AI Analysis
            </CardTitle>
            <CardDescription>
              Based on transcript content analysis
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {aiAnalysis ? (
              <>
                {/* Overall Rating & Recommendation */}
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <h4 className="text-sm font-medium text-purple-600 mb-1">Overall AI Score</h4>
                  <div className="text-3xl font-bold text-purple-700">
                    {formatRating(aiAnalysis.overall_rating)}/5.0
                  </div>
                  <p className="text-xs text-purple-600 mt-1 mb-2">
                    Comprehensive transcript analysis
                  </p>
                  <div className="mt-2">
                    <Badge className={getRecommendationColor(aiAnalysis.recommendation)}>
                      {getRecommendationText(aiAnalysis.recommendation)}
                    </Badge>
                  </div>
                </div>

                {/* AI Confidence */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium">Analysis Confidence</span>
                    <span className="text-sm text-muted-foreground">
                      {Math.round((aiAnalysis.confidence || 0.85) * 100)}%
                    </span>
                  </div>
                  <Progress value={(aiAnalysis.confidence || 0.85) * 100} className="h-2" />
                  {aiAnalysis.confidence && aiAnalysis.confidence < 0.5 && (
                    <p className="text-xs text-amber-600 mt-1">
                      <AlertCircleIcon className="h-3 w-3 inline mr-1" />
                      Low confidence - results may be unreliable
                    </p>
                  )}
                </div>

                {/* Skills Assessment */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium">Skills Detected</h4>
                  
                  {/* Technical Skills */}
                  {Object.keys(aiAnalysis.technical_skills).length > 0 && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Technical</p>
                      {Object.entries(aiAnalysis.technical_skills).slice(0, 3).map(([skill, rating]) => (
                        <div key={skill} className="mb-2">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm">{skill}</span>
                            <span className="text-sm text-muted-foreground">{rating.toFixed(1)}/5.0</span>
                          </div>
                          <Progress value={rating * 20} className="h-2" />
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Soft Skills */}
                  {Object.keys(aiAnalysis.soft_skills).length > 0 && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Soft Skills</p>
                      {Object.entries(aiAnalysis.soft_skills).slice(0, 2).map(([skill, rating]) => (
                        <div key={skill} className="mb-2">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm">{skill}</span>
                            <span className="text-sm text-muted-foreground">{rating.toFixed(1)}/5.0</span>
                          </div>
                          <Progress value={rating * 20} className="h-2" />
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Analysis Note */}
                <div className="pt-2">
                  <p className="text-sm text-muted-foreground">
                    <SparklesIcon className="h-3 w-3 inline mr-1" />
                    Analyzed {aiAnalysis.questionsAnalyzed || 'all'} Q&A exchanges
                  </p>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <BrainIcon className="h-12 w-12 mx-auto mb-2 opacity-20" />
                <p>No AI analysis available</p>
                <p className="text-xs mt-1">Upload recording or add transcript</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Comparison Summary */}
      {humanAssessment && aiAnalysis && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChartIcon className="h-5 w-5" />
              Assessment Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Overall Comparison */}
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-sm text-muted-foreground">Human Rating</p>
                  <p className="text-2xl font-bold">{formatRating(humanAssessment.averageRating)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Difference</p>
                  <p className="text-2xl font-bold">
                    {overallDiscrepancy > 0.1 && (
                      <span className={overallDiscrepancy > 1.0 ? 'text-amber-600' : 'text-gray-600'}>
                        {overallDiscrepancy.toFixed(1)}
                      </span>
                    )}
                    {overallDiscrepancy <= 0.1 && (
                      <span className="text-green-600">Aligned</span>
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">AI Rating</p>
                  <p className="text-2xl font-bold">{formatRating(aiAnalysis.overall_rating)}</p>
                </div>
              </div>

              <Separator />

              {/* Insights */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Key Insights</h4>
                
                {overallDiscrepancy <= 0.5 && (
                  <div className="flex items-start gap-2">
                    <CheckCircleIcon className="h-4 w-4 text-green-600 mt-0.5" />
                    <p className="text-sm">Human and AI assessments are well-aligned, indicating consistent candidate performance</p>
                  </div>
                )}
                
                {overallDiscrepancy > 0.5 && overallDiscrepancy <= 1.0 && (
                  <div className="flex items-start gap-2">
                    <AlertCircleIcon className="h-4 w-4 text-amber-600 mt-0.5" />
                    <p className="text-sm">Moderate difference in assessments. Review specific areas of divergence</p>
                  </div>
                )}
                
                {overallDiscrepancy > 1.0 && (
                  <div className="flex items-start gap-2">
                    <AlertTriangleIcon className="h-4 w-4 text-red-600 mt-0.5" />
                    <p className="text-sm">Significant discrepancy requires further investigation. Consider a panel review</p>
                  </div>
                )}
                
                {humanAssessment.completionRate < 50 && (
                  <div className="flex items-start gap-2">
                    <AlertCircleIcon className="h-4 w-4 text-blue-600 mt-0.5" />
                    <p className="text-sm">Limited human rating data ({Math.round(humanAssessment.completionRate)}% complete). AI analysis may provide additional insights</p>
                  </div>
                )}
              </div>

              {/* Recommendation */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium mb-2">Recommended Action</h4>
                {overallDiscrepancy > 1.0 ? (
                  <p className="text-sm">Schedule a calibration discussion to understand the assessment gap. Consider additional reference checks or a panel interview.</p>
                ) : (
                  <p className="text-sm">Assessments are aligned. Proceed with the {aiAnalysis.recommendation === 'hire' ? 'hiring process' : aiAnalysis.recommendation === 'no_hire' ? 'candidate rejection' : 'next evaluation round'}.</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}