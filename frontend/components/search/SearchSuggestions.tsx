'use client';

import { useEffect, useState, useRef } from 'react';
import { Search, TrendingUp, Briefcase, Users, Sparkles, Database, Brain } from 'lucide-react';
import { searchApi } from '@/lib/api/client';
import type { SearchSuggestion } from '@/lib/api/client';

interface SearchSuggestionsProps {
  query: string;
  onSelectSuggestion: (suggestion: string) => void;
  isVisible: boolean;
}

export default function SearchSuggestions({ 
  query, 
  onSelectSuggestion, 
  isVisible 
}: SearchSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Clear suggestions if query is too short
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    // Debounce the API call
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    setIsLoading(true);
    setError(null);

    timeoutRef.current = setTimeout(async () => {
      try {
        const results = await searchApi.getSearchSuggestions(query);
        setSuggestions(results);
      } catch (err) {
        console.error('Failed to fetch suggestions:', err);
        setError('Failed to load suggestions');
      } finally {
        setIsLoading(false);
      }
    }, 300); // 300ms debounce

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [query]);

  if (!isVisible || query.length < 2) {
    return null;
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'role':
        return <Briefcase className="h-4 w-4" />;
      case 'skill':
        return <TrendingUp className="h-4 w-4" />;
      case 'experience':
        return <Users className="h-4 w-4" />;
      default:
        return <Search className="h-4 w-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'role':
        return 'text-blue-600 bg-blue-50';
      case 'skill':
        return 'text-green-600 bg-green-50';
      case 'experience':
        return 'text-purple-600 bg-purple-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800">
        <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
          <Brain className="h-4 w-4 text-primary animate-pulse" />
          <span className="font-medium">AI-Powered Smart Suggestions</span>
          {isLoading && (
            <div className="ml-auto flex items-center gap-2">
              <span className="text-xs">Analyzing...</span>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            </div>
          )}
        </div>
      </div>

      {/* Suggestions List */}
      <div className="max-h-96 overflow-y-auto">
        {error ? (
          <div className="px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        ) : suggestions.length === 0 && !isLoading ? (
          <div className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
            No suggestions found. Keep typing...
          </div>
        ) : (
          <div className="py-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSelectSuggestion(suggestion.query)}
                className="w-full px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors group"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${getCategoryColor(suggestion.category)}`}>
                    {getCategoryIcon(suggestion.category)}
                  </div>
                  
                  <div className="flex-1 text-left">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary">
                        {suggestion.query}
                      </p>
                      <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                        {suggestion.count}+ candidates
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-3 text-xs">
                      <span className="capitalize text-gray-600 dark:text-gray-400">{suggestion.category}</span>
                      <span className="text-gray-400">•</span>
                      <div className="flex items-center gap-1">
                        {suggestion.confidence >= 0.9 ? (
                          <div className="flex">
                            <div className="h-1.5 w-1.5 rounded-full bg-green-500"></div>
                            <div className="h-1.5 w-1.5 rounded-full bg-green-500 ml-0.5"></div>
                            <div className="h-1.5 w-1.5 rounded-full bg-green-500 ml-0.5"></div>
                          </div>
                        ) : suggestion.confidence >= 0.8 ? (
                          <div className="flex">
                            <div className="h-1.5 w-1.5 rounded-full bg-yellow-500"></div>
                            <div className="h-1.5 w-1.5 rounded-full bg-yellow-500 ml-0.5"></div>
                            <div className="h-1.5 w-1.5 rounded-full bg-gray-300 ml-0.5"></div>
                          </div>
                        ) : (
                          <div className="flex">
                            <div className="h-1.5 w-1.5 rounded-full bg-gray-400"></div>
                            <div className="h-1.5 w-1.5 rounded-full bg-gray-300 ml-0.5"></div>
                            <div className="h-1.5 w-1.5 rounded-full bg-gray-300 ml-0.5"></div>
                          </div>
                        )}
                        <span className="text-gray-500 dark:text-gray-400 ml-1">
                          {suggestion.confidence >= 0.9 ? 'High' : suggestion.confidence >= 0.8 ? 'Good' : 'Fair'} match
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer with search tips */}
      {suggestions.length > 0 && (
        <div className="px-4 py-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
              <Database className="h-3 w-3" />
              <span>Real-time suggestions from {suggestions.length > 5 ? '1000+' : '500+'} candidates</span>
            </div>
            <div className="flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-yellow-500" />
              <span className="text-xs text-gray-500">AI Enhanced</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}