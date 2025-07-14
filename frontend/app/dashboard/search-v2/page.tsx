'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  Search, Filter, MapPin, Briefcase, Users, Save, Download,
  Grid, List, ChevronDown, ChevronUp, Check, X, History, Sparkles,
  Building, Globe, Clock, Star, Tag
} from 'lucide-react';
import { searchApi } from '@/lib/api/client';
import type { SearchResult } from '@/lib/api/client';
import { searchHistory } from '@/lib/search-history';
import SearchSuggestions from '@/components/search/SearchSuggestions';
import TagCloud from '@/components/search/TagCloud';
import ExperienceTags from '@/components/search/ExperienceTags';

// View types
type ViewType = 'grid' | 'list';

export default function SearchPageV2() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [viewType, setViewType] = useState<ViewType>('grid');
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showTagSection, setShowTagSection] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);
  
  // Filters state
  const [filters, setFilters] = useState({
    location: '',
    experience: '',
    availability: 'all',
    skills: [] as string[],
    remote: false,
  });

  // Quick filter presets
  const experienceLevels = [
    { label: 'Entry Level', value: '0-2' },
    { label: 'Mid Level', value: '3-5' },
    { label: 'Senior', value: '6-10' },
    { label: 'Lead/Principal', value: '10+' },
  ];

  // Popular skills for sidebar
  const popularSkills = [
    'JavaScript', 'Python', 'Java', 'React', 'Node.js',
    'AWS', 'Docker', 'Kubernetes', 'TypeScript', 'Go'
  ];

  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery) {
      setQuery(urlQuery);
      // Don't save to history on mount
      performSearch(urlQuery, false);
    }
  }, []);

  const performSearch = async (searchQuery: string, saveToHistory: boolean = true) => {
    if (!searchQuery.trim() && filters.skills.length === 0) return;

    setIsSearching(true);
    try {
      const searchFilters = {
        location: filters.location || undefined,
        skills: filters.skills.length > 0 ? filters.skills : undefined,
      };

      // If only skills are selected and no query, use a generic query
      const effectiveQuery = searchQuery.trim() || 
        (filters.skills.length > 0 ? `candidates with ${filters.skills.join(' ')}` : '');

      const searchResults = await searchApi.searchResumes({
        query: effectiveQuery,
        limit: 20,
        filters: Object.keys(searchFilters).some(key => searchFilters[key as keyof typeof searchFilters])
          ? searchFilters
          : undefined,
      });

      setResults(searchResults);
      
      // Save to search history only if requested
      if (saveToHistory) {
        searchHistory.saveSearch(
          searchQuery,
          searchFilters,
          searchResults.length
        );
      }
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const params = new URLSearchParams();
    params.set('q', query);
    router.push(`/dashboard/search-v2?${params.toString()}`);
    await performSearch(query);
  };

  const toggleCandidateSelection = (id: string) => {
    setSelectedCandidates(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const selectAllCandidates = () => {
    if (selectedCandidates.length === results.length) {
      setSelectedCandidates([]);
    } else {
      setSelectedCandidates(results.map(r => r.id));
    }
  };

  const toggleSkill = (skill: string) => {
    setFilters(prev => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter(s => s !== skill)
        : [...prev.skills, skill]
    }));
    // Trigger search when skills change
    setTimeout(() => {
      performSearch(query, true);
    }, 100);
  };

  const getMatchColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 0.6) return 'text-blue-600 bg-blue-50 border-blue-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const handleTagClick = (tag: string) => {
    // For skill tags, add to skills filter
    if (!tag.includes('years')) {
      toggleSkill(tag);
    } else {
      // For experience tags, update search query
      setQuery(tag);
      performSearch(tag);
    }
  };

  return (
    <div className="flex h-full">
      {/* Sidebar Filters */}
      <div className="w-64 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 overflow-y-auto">
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </h3>
          
          {/* Location Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Location
            </label>
            <div className="relative">
              <MapPin className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={filters.location}
                onChange={(e) => setFilters({...filters, location: e.target.value})}
                placeholder="City or Remote"
                className="input pl-8 text-sm"
              />
            </div>
          </div>

          {/* Experience Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Experience Level
            </label>
            <div className="space-y-1">
              {experienceLevels.map(level => (
                <button
                  key={level.value}
                  onClick={() => setFilters({...filters, experience: level.value})}
                  className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                    filters.experience === level.value
                      ? 'bg-primary text-white'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  {level.label}
                </button>
              ))}
            </div>
          </div>

          {/* Remote Filter */}
          <div className="mb-4">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.remote}
                onChange={(e) => setFilters({...filters, remote: e.target.checked})}
                className="rounded text-primary focus:ring-primary"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Remote positions only
              </span>
            </label>
          </div>

          {/* Skills Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Skills
            </label>
            <div className="space-y-1">
              {popularSkills.map(skill => (
                <label key={skill} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.skills.includes(skill)}
                    onChange={() => toggleSkill(skill)}
                    className="rounded text-primary focus:ring-primary"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{skill}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Clear Filters */}
          <button
            onClick={() => setFilters({
              location: '',
              experience: '',
              availability: 'all',
              skills: [],
              remote: false,
            })}
            className="w-full btn-secondary text-sm"
          >
            Clear All Filters
          </button>
        </div>

        {/* Saved Searches */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center">
            <History className="h-4 w-4 mr-2" />
            Recent Searches
          </h4>
          <div className="space-y-1 text-sm">
            <button className="w-full text-left px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded">
              Senior React Developer
            </button>
            <button className="w-full text-left px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded">
              Python Data Scientist
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Search Header */}
        <div className="bg-gradient-to-r from-primary/5 to-primary/10 border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 flex items-center">
              <Sparkles className="h-6 w-6 mr-2 text-primary animate-pulse" />
              Find Your Next Hire
            </h1>

            {/* Tag Browse Section */}
            <div className="mb-4">
              <button
                onClick={() => setShowTagSection(!showTagSection)}
                className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-primary transition-colors"
              >
                <Tag className="h-4 w-4" />
                <span>Browse by popular skills & experience</span>
                {showTagSection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              
              {showTagSection && (
                <div className="mt-4 space-y-1 animate-fadeIn">
                  <div className="p-4 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                    <TagCloud 
                      onTagClick={handleTagClick} 
                      selectedTags={filters.skills}
                    />
                  </div>
                  <div className="p-4 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                    <ExperienceTags 
                      onTagClick={handleTagClick} 
                      selectedTags={selectedTags}
                    />
                  </div>
                </div>
              )}
            </div>
            
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                ref={searchInputRef}
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder="Try: 'Senior Python developer with AWS experience' or 'Frontend engineer React TypeScript'"
                className="w-full pl-12 pr-32 py-4 text-lg border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary shadow-sm"
              />
              <button
                type="submit"
                disabled={isSearching || !query.trim()}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 btn-primary px-6"
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
              <SearchSuggestions
                query={query}
                onSelectSuggestion={(suggestion) => {
                  setQuery(suggestion);
                  setShowSuggestions(false);
                  performSearch(suggestion);
                }}
                isVisible={showSuggestions}
              />
            </form>

            {/* Selected Skills Display */}
            {filters.skills.length > 0 && (
              <div className="mt-4 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filtering by:</span>
                    {filters.skills.map((skill) => (
                      <span
                        key={skill}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary/10 text-primary"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => toggleSkill(skill)}
                          className="ml-2"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={() => setFilters({...filters, skills: []})}
                    className="text-sm text-primary hover:underline"
                  >
                    Clear skills
                  </button>
                </div>
              </div>
            )}

            {/* Quick Filters */}
            <div className="flex items-center gap-2 mt-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">Quick filters:</span>
              {experienceLevels.map(level => (
                <button
                  key={level.value}
                  onClick={() => setFilters({...filters, experience: level.value})}
                  className={`px-3 py-1 text-sm rounded-full transition-colors ${
                    filters.experience === level.value
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {level.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Header */}
        {results.length > 0 && (
          <div className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                  {results.length} candidates found
                </h2>
                
                {/* Select All */}
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCandidates.length === results.length}
                    onChange={selectAllCandidates}
                    className="rounded text-primary focus:ring-primary"
                  />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Select all</span>
                </label>

                {/* Bulk Actions */}
                {selectedCandidates.length > 0 && (
                  <div className="flex items-center gap-2 ml-4">
                    <button className="btn-secondary text-sm">
                      <Save className="h-4 w-4 mr-1" />
                      Save {selectedCandidates.length}
                    </button>
                    <button className="btn-secondary text-sm">
                      <Download className="h-4 w-4 mr-1" />
                      Export
                    </button>
                  </div>
                )}
              </div>

              {/* View Toggle */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setViewType('grid')}
                  className={`p-2 rounded ${viewType === 'grid' ? 'bg-primary text-white' : 'text-gray-600'}`}
                >
                  <Grid className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setViewType('list')}
                  className={`p-2 rounded ${viewType === 'list' ? 'bg-primary text-white' : 'text-gray-600'}`}
                >
                  <List className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-6">
          {results.length > 0 ? (
            <div className={viewType === 'grid' ? 'grid grid-cols-2 gap-4' : 'space-y-3'}>
              {results.map((result) => (
                <div
                  key={result.id}
                  className={`
                    bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700
                    hover:shadow-lg transition-shadow relative
                    ${viewType === 'list' ? 'p-4' : 'p-5'}
                    ${selectedCandidates.includes(result.id) ? 'ring-2 ring-primary' : ''}
                  `}
                >
                  {/* Selection Checkbox */}
                  <input
                    type="checkbox"
                    checked={selectedCandidates.includes(result.id)}
                    onChange={() => toggleCandidateSelection(result.id)}
                    className="absolute top-4 left-4 rounded text-primary focus:ring-primary"
                  />

                  <div className={viewType === 'list' ? 'ml-8 flex items-start justify-between' : 'ml-8'}>
                    <div className="flex-1">
                      {/* Name and Match Score */}
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {result.first_name} {result.last_name}
                        </h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getMatchColor(result.score)}`}>
                          {Math.round(result.score * 100)}% match
                        </span>
                      </div>

                      {/* Title and Location */}
                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {result.current_title && (
                          <span className="flex items-center gap-1">
                            <Briefcase className="h-3 w-3" />
                            {result.current_title}
                          </span>
                        )}
                        {result.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {result.location}
                          </span>
                        )}
                        {result.years_experience !== null && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {result.years_experience} years
                          </span>
                        )}
                      </div>

                      {/* Summary for Grid View */}
                      {viewType === 'grid' && result.summary_snippet && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                          {result.summary_snippet}
                        </p>
                      )}

                      {/* Skills */}
                      {result.skills && result.skills.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {result.skills.slice(0, viewType === 'list' ? 8 : 5).map((skill, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                            >
                              {skill}
                            </span>
                          ))}
                          {result.skills.length > (viewType === 'list' ? 8 : 5) && (
                            <span className="px-2 py-1 text-xs text-gray-500">
                              +{result.skills.length - (viewType === 'list' ? 8 : 5)} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className={viewType === 'list' ? 'ml-4 flex items-center gap-2' : 'mt-4 flex gap-2'}>
                      <button 
                        onClick={() => router.push(`/dashboard/search/similar/${result.id}?name=${encodeURIComponent(`${result.first_name} ${result.last_name}`)}`)}
                        className="btn-secondary text-sm"
                        title="Find similar candidates"
                      >
                        <Users className="h-4 w-4" />
                        {viewType === 'grid' && <span className="ml-1">Similar</span>}
                      </button>
                      <button 
                        onClick={() => router.push(`/dashboard/resumes/${result.id}`)}
                        className="btn-primary text-sm"
                      >
                        View Profile
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  {query ? 'No results found' : 'Start your search'}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 max-w-sm">
                  {query 
                    ? 'Try adjusting your search query or filters'
                    : 'Enter a search query above to find the perfect candidates'
                  }
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}