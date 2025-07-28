'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Search, Filter, X, Users, Mail, Sparkles, Zap, Radar, List } from 'lucide-react';
import { useProgressiveSearch, SearchResult } from '@/hooks/useProgressiveSearch';
import EnhancedResultCard from '@/components/search/EnhancedResultCard';
import QueryIntelligence from '@/components/search/QueryIntelligence';
import SearchProgress from '@/components/search/SearchProgress';
import { OutreachModal } from '@/components/outreach/OutreachModal';
import TagCloud from '@/components/search/TagCloud';
import TalentRadar from '@/components/search/TalentRadar';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '@/lib/api/client';

export default function ProgressiveSearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    location: '',
    min_experience: '',
    max_experience: '',
    skills: [] as string[],
  });
  const [newSkill, setNewSkill] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [showOutreachModal, setShowOutreachModal] = useState(false);
  const [outreachCandidate, setOutreachCandidate] = useState<any>(null);
  const [enhancedResults, setEnhancedResults] = useState<Record<string, SearchResult>>({});
  const [viewMode, setViewMode] = useState<'list' | 'radar'>('list');

  const { 
    stage, 
    stageNumber, 
    totalStages, 
    results, 
    isLoading, 
    error, 
    timing, 
    queryAnalysis,
    suggestions,
    search,
    cancel 
  } = useProgressiveSearch();

  // Load search from URL params on mount
  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery) {
      setQuery(urlQuery);
      search(urlQuery);
    }
  }, [searchParams, search]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Update URL with search query
    const params = new URLSearchParams();
    params.set('q', query);
    router.push(`/dashboard/search/progressive?${params.toString()}`);

    // Perform progressive search (suggestions will come from the hook)
    await search(query);
  };

  const handleTagClick = (tag: string) => {
    // Toggle tag selection
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
    
    // Set query to combined tags
    const newTags = selectedTags.includes(tag) 
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    
    const newQuery = newTags.join(' ');
    setQuery(newQuery);
    
    // Perform search if tags selected
    if (newTags.length > 0) {
      search(newQuery);
    }
  };

  const clearSelectedTags = () => {
    setSelectedTags([]);
    setQuery('');
    cancel();
  };

  const addSkill = () => {
    if (newSkill.trim() && !filters.skills.includes(newSkill.trim())) {
      setFilters({
        ...filters,
        skills: [...filters.skills, newSkill.trim()],
      });
      setNewSkill('');
    }
  };

  const removeSkill = (skill: string) => {
    setFilters({
      ...filters,
      skills: filters.skills.filter((s) => s !== skill),
    });
  };

  const handleGenerateOutreach = (candidate: any) => {
    setOutreachCandidate({
      id: candidate.id,
      name: `${candidate.first_name} ${candidate.last_name}`,
      title: candidate.current_title || '',
      skills: candidate.skills,
      experience: candidate.years_experience || undefined
    });
    setShowOutreachModal(true);
  };

  const handleEnhanceResult = async (result: SearchResult) => {
    try {
      const url = `/search/enhance-result?resume_id=${result.id}&query=${encodeURIComponent(query)}&score=${result.score}`;
      const response = await apiClient.post(url, {});
      
      if (response.enhancement) {
        // Update the result with the AI insights
        const enhancedResult = {
          ...result,
          ...response.enhancement
        };
        
        // Store in enhanced results map
        setEnhancedResults(prev => ({
          ...prev,
          [result.id]: enhancedResult
        }));
        
        // Update the results array to trigger re-render
        const updatedResults = results.map(r => 
          r.id === result.id ? enhancedResult : r
        );
        
        // Force a re-render by updating a dummy state
        // (since we can't directly update the hook's results)
      }
    } catch (error) {
      console.error('Failed to enhance result:', error);
      throw error;
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              Mind Reader Search
              <Sparkles className="h-7 w-7 text-blue-600" />
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              AI-powered search that understands what you really want
            </p>
          </div>
          <button
            onClick={() => router.push('/dashboard/search')}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Switch to Classic Search
          </button>
        </div>
      </div>

      {/* Tags Section */}
      <TagCloud onTagClick={handleTagClick} selectedTags={selectedTags} />
      
      {/* Selected Tags Display */}
      {selectedTags.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Selected:</span>
              <div className="flex flex-wrap gap-2">
                {selectedTags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary/10 text-primary"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleTagClick(tag)}
                      className="ml-2"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
            <button
              type="button"
              onClick={clearSelectedTags}
              className="text-sm text-primary hover:underline"
            >
              Clear all
            </button>
          </div>
        </div>
      )}

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                ref={searchInputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Find me a unicorn developer who can mentor juniors..."
                className="input pl-10 pr-4 py-3 text-base"
                disabled={isLoading}
              />
              {isLoading && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <Zap className="h-5 w-5 text-yellow-500 animate-pulse" />
                </div>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary px-4"
          >
            <Filter className="h-5 w-5" />
          </button>
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <span>Searching</span>
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              </>
            ) : (
              <>
                <span>Search</span>
                <Sparkles className="h-4 w-4" />
              </>
            )}
          </button>
        </div>

        {/* Filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 card p-6 overflow-hidden"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={filters.location}
                    onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                    placeholder="e.g., Remote, NYC"
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Min Experience
                  </label>
                  <input
                    type="number"
                    value={filters.min_experience}
                    onChange={(e) => setFilters({ ...filters, min_experience: e.target.value })}
                    placeholder="0"
                    min="0"
                    max="50"
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Max Experience
                  </label>
                  <input
                    type="number"
                    value={filters.max_experience}
                    onChange={(e) => setFilters({ ...filters, max_experience: e.target.value })}
                    placeholder="50"
                    min="0"
                    max="50"
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Required Skills
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                      placeholder="Add skill"
                      className="input"
                    />
                    <button type="button" onClick={addSkill} className="btn-secondary px-3">
                      Add
                    </button>
                  </div>
                </div>
              </div>

              {filters.skills.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {filters.skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary/10 text-primary"
                    >
                      {skill}
                      <button type="button" onClick={() => removeSkill(skill)} className="ml-2">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </form>

      {/* Query Intelligence */}
      <QueryIntelligence
        analysis={queryAnalysis}
        suggestions={suggestions}
        isLoading={isLoading && stage === 'instant'}
      />

      {/* Search Progress */}
      {isLoading && (
        <SearchProgress
          stage={stage}
          stageNumber={stageNumber}
          totalStages={totalStages}
          timing={timing}
        />
      )}

      {/* Results */}
      <AnimatePresence mode="popLayout">
        {results.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Found {results.length} candidates
              </h2>
              <div className="flex items-center gap-4">
                {stage === 'complete' && (
                  <span className="text-sm text-gray-600">
                    Search completed in {timing.total || 0}ms
                  </span>
                )}
                <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('list')}
                    className={`px-3 py-1 rounded flex items-center gap-2 transition-colors ${
                      viewMode === 'list' 
                        ? 'bg-white dark:bg-gray-700 text-primary shadow-sm' 
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    <List className="h-4 w-4" />
                    <span className="text-sm">List</span>
                  </button>
                  <button
                    onClick={() => setViewMode('radar')}
                    className={`px-3 py-1 rounded flex items-center gap-2 transition-colors ${
                      viewMode === 'radar' 
                        ? 'bg-white dark:bg-gray-700 text-primary shadow-sm' 
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    <Radar className="h-4 w-4" />
                    <span className="text-sm">Radar</span>
                  </button>
                </div>
              </div>
            </div>

            {viewMode === 'list' ? (
              results.map((result, index) => {
                // Use enhanced result if available, otherwise use original
                const displayResult = enhancedResults[result.id] || result;
                return (
                  <EnhancedResultCard
                    key={result.id}
                    result={displayResult}
                    rank={index + 1}
                    stage={stage as any}
                    query={query}
                    onView={(id) => router.push(`/dashboard/resumes/${id}`)}
                    onEnhance={handleEnhanceResult}
                  />
                );
              })
            ) : (
              <TalentRadar
                candidates={results.map((result: any, index) => ({
                  id: result.id,
                  name: `${result.first_name} ${result.last_name}`,
                  title: result.current_title || 'Not specified',
                  matchScore: result.score,
                  skillsGap: result.skill_analysis ? 
                    (1 - (result.skill_analysis.match_percentage / 100)) : 0.5,
                  availability: result.availability_score || 0.5,
                  learningVelocity: result.learning_velocity || 0.5,
                  experience: result.years_experience || 0,
                  skills: result.skills || []
                }))}
                onCandidateClick={(candidate) => router.push(`/dashboard/resumes/${candidate.id}`)}
                isLoading={isLoading && stage !== 'complete'}
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error State */}
      {error && (
        <div className="text-center py-12">
          <div className="bg-red-50 text-red-700 p-4 rounded-lg inline-block">
            <p className="font-medium">Search failed</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && query && results.length === 0 && stage === 'complete' && (
        <div className="text-center py-12">
          <Search className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            No results found
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Try adjusting your search query or filters
          </p>
        </div>
      )}

      {/* Initial State */}
      {!query && results.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <div className="max-w-2xl mx-auto">
            <Sparkles className="mx-auto h-16 w-16 text-blue-600 mb-4" />
            <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Experience the Magic of AI Search
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-8">
              Our Mind Reader search understands natural language, finds hidden gems, 
              and explains why each candidate matches your needs.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
              <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-lg">
                <Zap className="h-8 w-8 text-yellow-600 mb-2" />
                <h4 className="font-semibold text-gray-900 mb-1">Instant Results</h4>
                <p className="text-sm text-gray-600">
                  See matches immediately while AI enhances them in real-time
                </p>
              </div>
              
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg">
                <Search className="h-8 w-8 text-blue-600 mb-2" />
                <h4 className="font-semibold text-gray-900 mb-1">Deep Understanding</h4>
                <p className="text-sm text-gray-600">
                  Understands "unicorn developer" means full-stack + leadership
                </p>
              </div>
              
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg">
                <Sparkles className="h-8 w-8 text-purple-600 mb-2" />
                <h4 className="font-semibold text-gray-900 mb-1">Smart Insights</h4>
                <p className="text-sm text-gray-600">
                  AI explains why each candidate is a good match
                </p>
              </div>
            </div>

            <div className="mt-8 space-y-2">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Try these example searches:
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {[
                  "Full-stack engineer who can mentor juniors",
                  "React developer with TypeScript and testing",
                  "DevOps ninja comfortable with chaos",
                  "Find me a unicorn developer"
                ].map((example) => (
                  <button
                    key={example}
                    onClick={() => {
                      setQuery(example);
                      search(example);
                    }}
                    className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Outreach Modal */}
      {showOutreachModal && outreachCandidate && (
        <OutreachModal
          isOpen={showOutreachModal}
          onClose={() => {
            setShowOutreachModal(false);
            setOutreachCandidate(null);
          }}
          candidate={outreachCandidate}
        />
      )}
    </div>
  );
}