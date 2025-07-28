'use client';

import React from 'react';
import { Brain, Sparkles, Target, Briefcase, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';

interface QueryAnalysis {
  primary_skills: string[];
  secondary_skills: string[];
  implied_skills: string[];
  experience_level: string;
  role_type: string;
  search_intent: string;
  corrected_query?: string;
  original_query?: string;
}

interface QueryIntelligenceProps {
  analysis?: QueryAnalysis;
  suggestions?: string[];
  isLoading?: boolean;
}

export default function QueryIntelligence({ 
  analysis, 
  suggestions,
  isLoading 
}: QueryIntelligenceProps) {
  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <Brain className="h-5 w-5 text-blue-600 animate-pulse" />
          <span className="text-sm font-medium text-gray-700">Analyzing your search...</span>
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-6 border border-blue-100"
    >
      <div className="flex items-center space-x-2 mb-3">
        <Brain className="h-5 w-5 text-blue-600" />
        <span className="text-sm font-semibold text-gray-700">Search Intelligence</span>
        <Sparkles className="h-4 w-4 text-indigo-600" />
      </div>

      {/* Show typo correction if applied */}
      {analysis.corrected_query && (
        <div className="mb-3 px-3 py-2 bg-amber-50 border border-amber-200 rounded-md">
          <p className="text-xs text-amber-800">
            <span className="font-medium">Auto-corrected:</span> Searching for "{analysis.corrected_query}" 
            {analysis.original_query && ` (from "${analysis.original_query}")`}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Primary Skills */}
        {analysis.primary_skills.length > 0 && (
          <div>
            <p className="text-xs text-gray-600 mb-1 font-medium">Looking for:</p>
            <div className="flex flex-wrap gap-1">
              {/* Deduplicate skills on frontend as safety measure */}
              {Array.from(new Map(
                analysis.primary_skills.map(skill => [skill.toLowerCase(), skill])
              ).values()).map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-blue-600 text-white text-xs rounded-md font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Secondary Skills */}
        {analysis.secondary_skills.length > 0 && (
          <div>
            <p className="text-xs text-gray-600 mb-1 font-medium">Nice to have:</p>
            <div className="flex flex-wrap gap-1">
              {Array.from(new Map(
                analysis.secondary_skills.map(skill => [skill.toLowerCase(), skill])
              ).values()).map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-blue-200 text-blue-800 text-xs rounded-md"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Implied Skills */}
        {analysis.implied_skills.length > 0 && (
          <div>
            <p className="text-xs text-gray-600 mb-1 font-medium">Also considering:</p>
            <div className="flex flex-wrap gap-1">
              {Array.from(new Map(
                analysis.implied_skills.map(skill => [skill.toLowerCase(), skill])
              ).values()).map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded-md"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Additional Context */}
      <div className="mt-3 pt-3 border-t border-blue-100 flex flex-wrap items-center gap-4 text-xs">
        {analysis.experience_level && analysis.experience_level !== 'any' && (
          <div className="flex items-center space-x-1">
            <TrendingUp className="h-3 w-3 text-gray-600" />
            <span className="text-gray-700">
              {analysis.experience_level} level
            </span>
          </div>
        )}
        
        {analysis.role_type && analysis.role_type !== 'any' && (
          <div className="flex items-center space-x-1">
            <Briefcase className="h-3 w-3 text-gray-600" />
            <span className="text-gray-700">
              {analysis.role_type} role
            </span>
          </div>
        )}
        
        {analysis.search_intent && (
          <div className="flex items-center space-x-1">
            <Target className="h-3 w-3 text-gray-600" />
            <span className="text-gray-700">
              {analysis.search_intent.replace('_', ' ')} search
            </span>
          </div>
        )}
      </div>

      {/* Search Suggestions */}
      {suggestions && suggestions.length > 0 && (
        <div className="mt-3 pt-3 border-t border-blue-100">
          <p className="text-xs text-gray-600 mb-2">Suggestions to improve results:</p>
          <div className="space-y-1">
            {/* Deduplicate suggestions */}
            {Array.from(new Set(suggestions)).map((suggestion, idx) => (
              <p key={idx} className="text-xs text-gray-700 flex items-start">
                <span className="text-blue-600 mr-1">•</span>
                {suggestion}
              </p>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}