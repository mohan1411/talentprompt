'use client';

import React, { useState } from 'react';
import { 
  User, 
  MapPin, 
  Briefcase, 
  ChevronDown, 
  ChevronUp,
  CheckCircle,
  XCircle,
  AlertCircle,
  Sparkles,
  Target,
  TrendingUp,
  Eye,
  Activity,
  Zap,
  GitBranch
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { SearchResult } from '@/hooks/useProgressiveSearch';
import { cn } from '@/lib/utils';
import FindSimilarButton from './FindSimilarButton';

interface EnhancedResultCardProps {
  result: SearchResult;
  rank: number;
  stage: 'instant' | 'enhanced' | 'intelligent';
  query?: string;
  onView?: (id: string) => void;
  onEnhance?: (result: SearchResult) => Promise<void>;
  onFindSimilar?: (candidateId: string) => void;
}

export default function EnhancedResultCard({ 
  result, 
  rank, 
  stage,
  query,
  onView,
  onEnhance,
  onFindSimilar
}: EnhancedResultCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  
  const hasAIInsights = !!(
    (result.key_strengths?.length && result.key_strengths.length > 0) || 
    (result.potential_concerns?.length && result.potential_concerns.length > 0) || 
    (result.interview_focus?.length && result.interview_focus.length > 0) || 
    result.hiring_recommendation
  );
  
  const hasExpandableContent = hasAIInsights || result.career_trajectory;

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50';
    if (score >= 0.6) return 'text-blue-600 bg-blue-50';
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getFitColor = (fit?: string) => {
    switch (fit) {
      case 'excellent': return 'text-green-600 bg-green-50';
      case 'strong': return 'text-blue-600 bg-blue-50';
      case 'good': return 'text-yellow-600 bg-yellow-50';
      case 'fair': return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: rank * 0.05 }}
      className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-4">
            <div className="bg-gray-100 rounded-full p-3">
              <User className="h-6 w-6 text-gray-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {result.first_name} {result.last_name}
              </h3>
              {result.current_title && (
                <p className="text-sm text-gray-600 flex items-center mt-1">
                  <Briefcase className="h-4 w-4 mr-1" />
                  {result.current_title}
                </p>
              )}
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                {result.location && (
                  <span className="flex items-center">
                    <MapPin className="h-4 w-4 mr-1" />
                    {result.location}
                  </span>
                )}
                {result.years_experience && (
                  <span>{result.years_experience} years exp.</span>
                )}
                {/* Analytics Indicators */}
                {result.availability_score !== undefined && (
                  <span className="flex items-center" title={`Availability: ${Math.round(result.availability_score * 100)}%`}>
                    <Activity className={cn(
                      "h-4 w-4 mr-1",
                      result.availability_score > 0.7 ? "text-green-600" :
                      result.availability_score > 0.4 ? "text-orange-600" : "text-red-600"
                    )} />
                    <span className={cn(
                      result.availability_score > 0.7 ? "text-green-600" :
                      result.availability_score > 0.4 ? "text-orange-600" : "text-red-600"
                    )}>
                      {result.availability_score > 0.7 ? "Available" :
                       result.availability_score > 0.4 ? "Maybe" : "Unlikely"}
                    </span>
                  </span>
                )}
                {result.learning_velocity !== undefined && result.learning_velocity > 0.7 && (
                  <span className="flex items-center text-purple-600" title="Fast learner">
                    <Zap className="h-4 w-4 mr-1" />
                    Fast learner
                  </span>
                )}
              </div>
            </div>
          </div>
          
          {/* Score Badge */}
          <div className="flex flex-col items-end space-y-2">
            <div className={cn(
              "px-3 py-1 rounded-full text-sm font-medium",
              getScoreColor(result.score)
            )}>
              {Math.round(result.score * 100)}% match
            </div>
            {result.overall_fit && stage === 'intelligent' && (
              <div className={cn(
                "px-2 py-1 rounded text-xs font-medium",
                getFitColor(result.overall_fit)
              )}>
                {result.overall_fit} fit
              </div>
            )}
            {/* AI Insights Indicator */}
            {hasAIInsights && (
              <div className="flex items-center space-x-1 px-2 py-1 text-xs font-medium bg-purple-50 text-purple-700 rounded-full">
                <Sparkles className="h-3 w-3" />
                <span>AI Enhanced</span>
              </div>
            )}
          </div>
        </div>

        {/* Skills */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {result.skills.slice(0, 6).map((skill, idx) => {
              const isMatched = result.skill_analysis?.matched.includes(skill);
              const isAdditional = result.skill_analysis?.additional.includes(skill);
              
              return (
                <span
                  key={idx}
                  className={cn(
                    "px-2 py-1 text-xs rounded-md",
                    isMatched ? "bg-green-100 text-green-700 font-medium" :
                    isAdditional ? "bg-blue-100 text-blue-700" :
                    "bg-gray-100 text-gray-700"
                  )}
                >
                  {skill}
                  {isMatched && <CheckCircle className="inline-block ml-1 h-3 w-3" />}
                </span>
              );
            })}
            {result.skills.length > 6 && (
              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded-md">
                +{result.skills.length - 6} more
              </span>
            )}
          </div>
        </div>

        {/* AI Match Explanation (Stage 3) */}
        {stage === 'intelligent' && result.match_explanation && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200"
          >
            <div className="flex items-start space-x-2">
              <Sparkles className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-900">{result.match_explanation}</p>
            </div>
          </motion.div>
        )}

        {/* Skill Analysis (Stage 2+) */}
        {stage !== 'instant' && result.skill_analysis && (
          <div className="mb-4 space-y-2">
            {result.skill_analysis.matched.length > 0 && (
              <div className="flex items-center space-x-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-green-700">
                  Has {result.skill_analysis.matched.length} required skills
                </span>
              </div>
            )}
            {result.skill_analysis.missing.length > 0 && (
              <div className="flex items-center space-x-2 text-sm">
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-red-700">
                  Missing: {result.skill_analysis.missing.join(', ')}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center space-x-2 px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 rounded-md transition-colors"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  <span>Hide Details</span>
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  <span>Show Details</span>
                </>
              )}
            </button>
            
            {/* Get AI Insights button for non-enhanced results */}
            {!hasAIInsights && (stage === 'intelligent' || rank > 5) && onEnhance && query && (
              <button
                onClick={async () => {
                  setIsLoadingInsights(true);
                  try {
                    await onEnhance(result);
                    setIsExpanded(true); // Auto-expand after loading insights
                  } catch (error) {
                    console.error('Failed to get AI insights:', error);
                  } finally {
                    setIsLoadingInsights(false);
                  }
                }}
                disabled={isLoadingInsights}
                className="flex items-center space-x-1 text-sm text-purple-600 hover:text-purple-700 disabled:opacity-50"
              >
                <Sparkles className={cn(
                  "h-4 w-4",
                  isLoadingInsights && "animate-spin"
                )} />
                <span>{isLoadingInsights ? 'Analyzing...' : 'Get AI insights'}</span>
              </button>
            )}
            
            {/* Find Similar Career DNA button */}
            {result.career_dna && onFindSimilar && (
              <FindSimilarButton
                candidate={result}
                onFindSimilar={onFindSimilar}
                isCompact={true}
              />
            )}
          </div>
          
          <button
            onClick={() => onView?.(result.id)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Eye className="h-4 w-4" />
            <span>View Profile</span>
          </button>
        </div>

        {/* Expanded Details */}
        <AnimatePresence>
          {isExpanded && hasExpandableContent && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 pt-4 border-t border-gray-200 space-y-4"
            >
              {/* Career DNA Profile */}
              {result.career_trajectory && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <GitBranch className="h-4 w-4 mr-1 text-indigo-600" />
                    Career DNA Profile
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Pattern:</span>
                      <span className="ml-2 font-medium capitalize">
                        {result.career_trajectory.pattern.replace('_', ' ')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Level:</span>
                      <span className="ml-2 font-medium capitalize">
                        {result.career_trajectory.current_level}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Progression:</span>
                      <span className="ml-2 font-medium">
                        {result.career_trajectory.years_to_current} years to current level
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Trajectory:</span>
                      <span className={cn(
                        "ml-2 font-medium",
                        result.career_trajectory.is_ascending ? "text-green-600" : "text-gray-600"
                      )}>
                        {result.career_trajectory.is_ascending ? "Ascending" : "Stable"}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              {/* Key Strengths */}
              {result.key_strengths && result.key_strengths.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <TrendingUp className="h-4 w-4 mr-1 text-green-600" />
                    Key Strengths
                  </h4>
                  <ul className="space-y-1">
                    {result.key_strengths.map((strength, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start">
                        <span className="text-green-600 mr-2">•</span>
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Potential Concerns */}
              {result.potential_concerns && result.potential_concerns.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1 text-orange-600" />
                    Areas to Explore
                  </h4>
                  <ul className="space-y-1">
                    {result.potential_concerns.map((concern, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start">
                        <span className="text-orange-600 mr-2">•</span>
                        {concern}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Interview Focus */}
              {result.interview_focus && result.interview_focus.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                    <Target className="h-4 w-4 mr-1 text-blue-600" />
                    Interview Focus Areas
                  </h4>
                  <ul className="space-y-1">
                    {result.interview_focus.map((focus, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start">
                        <span className="text-blue-600 mr-2">•</span>
                        {focus}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Hiring Recommendation */}
              {result.hiring_recommendation && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700">
                    Recommendation: {result.hiring_recommendation}
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}