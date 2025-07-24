'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress-simple'
import { Separator } from '@/components/ui/separator-simple'
import { 
  CheckCircleIcon,
  XCircleIcon,
  AlertCircleIcon,
  StarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  UserCheckIcon,
  BrainIcon,
  HeartIcon,
  MessageSquareIcon,
  TargetIcon,
  AlertTriangleIcon
} from 'lucide-react'

interface InterviewScorecardProps {
  scorecard: {
    overall_rating: number
    recommendation: string
    technical_skills: Record<string, number>
    soft_skills: Record<string, number>
    culture_fit: number
    strengths: string[]
    concerns: string[]
    next_steps: string[]
    percentile_rank?: number
  }
  qaAnalysis?: {
    summary: string
    key_strengths: string[]
    areas_of_concern: string[]
    qa_pairs?: Array<{
      question: string
      rating: number
      evaluation: string
    }>
  }
}

export function InterviewScorecard({ scorecard, qaAnalysis }: InterviewScorecardProps) {
  const getRecommendationIcon = () => {
    switch (scorecard.recommendation) {
      case 'hire':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />
      case 'no_hire':
        return <XCircleIcon className="h-5 w-5 text-red-600" />
      default:
        return <AlertCircleIcon className="h-5 w-5 text-amber-600" />
    }
  }

  const getRecommendationText = () => {
    switch (scorecard.recommendation) {
      case 'hire':
        return 'Recommend Hire'
      case 'no_hire':
        return 'Do Not Hire'
      default:
        return 'Further Evaluation Needed'
    }
  }

  const getRecommendationColor = () => {
    switch (scorecard.recommendation) {
      case 'hire':
        return 'text-green-600 bg-green-50'
      case 'no_hire':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-amber-600 bg-amber-50'
    }
  }

  const renderStars = (rating: number) => {
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <StarIcon
            key={star}
            className={`h-5 w-5 ${
              star <= rating
                ? 'fill-amber-400 text-amber-400'
                : 'fill-gray-200 text-gray-200'
            }`}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Overall Assessment */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Interview Assessment</CardTitle>
              <CardDescription>
                {qaAnalysis?.summary || 'AI-powered evaluation of interview performance'}
              </CardDescription>
            </div>
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${getRecommendationColor()}`}>
              {getRecommendationIcon()}
              <span className="font-medium">{getRecommendationText()}</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Overall Rating */}
            <div className="text-center">
              <h4 className="text-sm font-medium text-muted-foreground mb-2">Overall Rating</h4>
              <div className="text-3xl font-bold mb-2">{scorecard.overall_rating.toFixed(1)}/5.0</div>
              {renderStars(Math.round(scorecard.overall_rating))}
            </div>

            {/* Culture Fit */}
            <div className="text-center">
              <h4 className="text-sm font-medium text-muted-foreground mb-2">Culture Fit</h4>
              <div className="text-3xl font-bold mb-2">{scorecard.culture_fit.toFixed(1)}/5.0</div>
              {renderStars(Math.round(scorecard.culture_fit))}
            </div>

            {/* Percentile Rank */}
            {scorecard.percentile_rank !== undefined && (
              <div className="text-center">
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Percentile Rank</h4>
                <div className="text-3xl font-bold mb-2">{scorecard.percentile_rank}%</div>
                <div className="text-sm text-muted-foreground">
                  Better than {scorecard.percentile_rank}% of candidates
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Skills Assessment */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Technical Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BrainIcon className="h-5 w-5" />
              Technical Skills
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(scorecard.technical_skills).map(([skill, rating]) => (
              <div key={skill}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium">{skill}</span>
                  <span className="text-sm text-muted-foreground">{rating.toFixed(1)}/5.0</span>
                </div>
                <Progress value={rating * 20} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Soft Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HeartIcon className="h-5 w-5" />
              Soft Skills
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(scorecard.soft_skills).map(([skill, rating]) => (
              <div key={skill}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium">{skill}</span>
                  <span className="text-sm text-muted-foreground">{rating.toFixed(1)}/5.0</span>
                </div>
                <Progress value={rating * 20} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Strengths & Concerns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-600">
              <TrendingUpIcon className="h-5 w-5" />
              Key Strengths
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {scorecard.strengths.map((strength, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{strength}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Concerns */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-600">
              <AlertTriangleIcon className="h-5 w-5" />
              Areas of Concern
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {scorecard.concerns.map((concern, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <AlertCircleIcon className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{concern}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Question Analysis */}
      {qaAnalysis?.qa_pairs && qaAnalysis.qa_pairs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquareIcon className="h-5 w-5" />
              Question-by-Question Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {qaAnalysis.qa_pairs.map((qa, idx) => (
              <div key={idx}>
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <p className="text-sm font-medium mb-1">Q{idx + 1}: {qa.question}</p>
                    <p className="text-sm text-muted-foreground">{qa.evaluation}</p>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <span className="text-sm font-medium">{qa.rating}/5</span>
                    {renderStars(qa.rating)}
                  </div>
                </div>
                {idx < (qaAnalysis.qa_pairs?.length ?? 0) - 1 && <Separator className="my-4" />}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TargetIcon className="h-5 w-5" />
            Recommended Next Steps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {scorecard.next_steps.map((step, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-primary/10 text-primary text-xs font-medium rounded-full flex items-center justify-center">
                  {idx + 1}
                </span>
                <span className="text-sm">{step}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}