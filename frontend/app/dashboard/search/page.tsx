'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Search, Filter, MapPin, Briefcase, X, Users, Linkedin } from 'lucide-react';
import { searchApi } from '@/lib/api/client';
import type { SearchResult } from '@/lib/api/client';
import { searchHistory } from '@/lib/search-history';
import SearchSuggestions from '@/components/search/SearchSuggestions';
import TagCloud from '@/components/search/TagCloud';
import ExperienceTags from '@/components/search/ExperienceTags';

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    location: '',
    min_experience: '',
    max_experience: '',
    skills: [] as string[],
  });
  const [newSkill, setNewSkill] = useState('');
  const [lastSearchLimit, setLastSearchLimit] = useState<number | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Load search from URL params on mount
  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery) {
      setQuery(urlQuery);
      // Trigger search with URL query (don't save to history on mount)
      performSearch(urlQuery, false);
    }
  }, []); // Only run on mount

  // Extract limit from natural language query
  const extractLimitFromQuery = (searchQuery: string): { cleanQuery: string; limit: number } => {
    const patterns = [
      /\btop (\d+)\b/i,
      /\bfirst (\d+)\b/i,
      /\bshow (?:me )?(\d+)\b/i,
      /\b(\d+) (?:best |top )?(?:candidates?|developers?|engineers?|scientists?|managers?)\b/i,
    ];
    
    for (const pattern of patterns) {
      const match = searchQuery.match(pattern);
      if (match) {
        const limit = parseInt(match[1]);
        // Remove the limit phrase from the query
        const cleanQuery = searchQuery.replace(match[0], '').replace(/\s+/g, ' ').trim();
        // Cap limit between 1 and 50
        return { 
          cleanQuery: cleanQuery || searchQuery, // Fallback to original if empty
          limit: Math.max(1, Math.min(limit, 50))
        };
      }
    }
    
    // No limit found, return original query with default limit
    return { cleanQuery: searchQuery, limit: 10 };
  };

  const performSearch = async (searchQuery: string, saveToHistory: boolean = true) => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      // Extract limit from the query
      const { cleanQuery, limit } = extractLimitFromQuery(searchQuery);
      
      const searchFilters = {
        location: filters.location || undefined,
        min_experience: filters.min_experience ? parseInt(filters.min_experience) : undefined,
        max_experience: filters.max_experience ? parseInt(filters.max_experience) : undefined,
        skills: filters.skills.length > 0 ? filters.skills : undefined,
      };

      const searchResults = await searchApi.searchResumes({
        query: cleanQuery,
        limit: limit,
        filters: Object.keys(searchFilters).some(key => searchFilters[key as keyof typeof searchFilters] !== undefined)
          ? searchFilters
          : undefined,
      });

      setResults(searchResults);
      setLastSearchLimit(limit);
      
      // Save to search history only if requested
      if (saveToHistory) {
        searchHistory.saveSearch(
          cleanQuery,
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

  const performSearchWithSkillsFilter = async (searchQuery: string, skills: string[]) => {
    setIsSearching(true);
    try {
      // Use a generic query with skill filters to ensure exact matching
      const searchFilters = {
        location: filters.location || undefined,
        min_experience: filters.min_experience ? parseInt(filters.min_experience) : undefined,
        max_experience: filters.max_experience ? parseInt(filters.max_experience) : undefined,
        skills: skills, // Use the exact tags as skill filters
      };

      // Use a generic search query that will trigger skill-based filtering
      const searchResults = await searchApi.searchResumes({
        query: `candidates with ${skills.join(' ')}`, // Generic query
        limit: 20,
        filters: searchFilters,
      });

      setResults(searchResults);
      setLastSearchLimit(20);
      
      // Save to search history
      searchHistory.saveSearch(
        `candidates with ${skills.join(' ')}`,
        searchFilters,
        searchResults.length
      );
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

    // Update URL with search query
    const params = new URLSearchParams();
    params.set('q', query);
    router.push(`/dashboard/search?${params.toString()}`);

    // Perform search and save to history
    await performSearch(query, true);
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

  const handleSelectSuggestion = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    searchInputRef.current?.focus();
    // Trigger search with the selected suggestion
    performSearch(suggestion);
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
    
    // Perform search with tags as skills filter
    if (newTags.length > 0) {
      performSearchWithSkillsFilter(newQuery, newTags);
    } else {
      // Clear results if no tags selected
      setResults([]);
    }
  };

  const clearSelectedTags = () => {
    setSelectedTags([]);
    setQuery('');
    setResults([]);
  };

  const clearFilters = () => {
    setFilters({
      location: '',
      min_experience: '',
      max_experience: '',
      skills: [],
    });
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Search Resumes
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Find the perfect candidates using natural language search
        </p>
      </div>

      {/* Tags Section */}
      <TagCloud onTagClick={handleTagClick} selectedTags={selectedTags} />
      <ExperienceTags onTagClick={handleTagClick} selectedTags={selectedTags} />
      
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
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
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
                placeholder="e.g., Senior Python developer with AWS experience..."
                className="input pl-10 pr-4 py-3 text-base"
              />
              <SearchSuggestions
                query={query}
                onSelectSuggestion={handleSelectSuggestion}
                isVisible={showSuggestions}
              />
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
            disabled={isSearching || !query.trim()}
            className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Filters
              </h3>
              <button
                type="button"
                onClick={clearFilters}
                className="text-sm text-primary hover:underline"
              >
                Clear all
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={filters.location}
                  onChange={(e) =>
                    setFilters({ ...filters, location: e.target.value })
                  }
                  placeholder="e.g., New York"
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Min Experience (years)
                </label>
                <input
                  type="number"
                  value={filters.min_experience}
                  onChange={(e) =>
                    setFilters({ ...filters, min_experience: e.target.value })
                  }
                  placeholder="0"
                  min="0"
                  max="50"
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Max Experience (years)
                </label>
                <input
                  type="number"
                  value={filters.max_experience}
                  onChange={(e) =>
                    setFilters({ ...filters, max_experience: e.target.value })
                  }
                  placeholder="50"
                  min="0"
                  max="50"
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Skills
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
                  <button
                    type="button"
                    onClick={addSkill}
                    className="btn-secondary px-3"
                  >
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
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      className="ml-2"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </form>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Found {results.length} candidates
            {lastSearchLimit && lastSearchLimit !== 10 && (
              <span className="text-sm font-normal text-gray-600 dark:text-gray-400 ml-2">
                (showing top {lastSearchLimit} as requested)
              </span>
            )}
          </h2>

          {results.map((result) => (
            <div key={result.id} className="card p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-2">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      {result.first_name} {result.last_name}
                    </h3>
                    <span className="badge bg-green-100 text-green-800">
                      {Math.round(result.score * 100)}% match
                    </span>
                  </div>

                  {result.current_title && (
                    <p className="text-gray-700 dark:text-gray-300 mb-2">
                      {result.current_title}
                    </p>
                  )}

                  <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {result.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {result.location}
                      </span>
                    )}
                    {result.years_experience !== null && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-4 w-4" />
                        {result.years_experience} years
                      </span>
                    )}
                  </div>

                  {result.summary_snippet && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {result.summary_snippet}
                    </p>
                  )}

                  {result.skills && result.skills.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {result.skills.slice(0, 5).map((skill, index) => (
                        <span
                          key={index}
                          className="badge bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                        >
                          {skill}
                        </span>
                      ))}
                      {result.skills.length > 5 && (
                        <span className="badge bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                          +{result.skills.length - 5} more
                        </span>
                      )}
                    </div>
                  )}

                  {result.highlights.length > 0 && (
                    <div className="mt-3 space-y-1">
                      {result.highlights.map((highlight, index) => (
                        <p
                          key={index}
                          className="text-sm text-gray-600 dark:text-gray-400 italic"
                        >
                          "...{highlight}"
                        </p>
                      ))}
                    </div>
                  )}
                  
                  {result.linkedin_url && (
                    <div className="mt-3 flex items-center gap-1 text-xs text-gray-500">
                      <Linkedin className="h-3 w-3" />
                      <span>LinkedIn Import</span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 ml-4">
                  <button 
                    onClick={() => router.push(`/dashboard/search/similar/${result.id}?name=${encodeURIComponent(`${result.first_name} ${result.last_name}`)}`)}
                    className="btn-secondary"
                    title="Find similar candidates"
                  >
                    <Users className="h-4 w-4" />
                  </button>
                  <button 
                    onClick={() => router.push(`/dashboard/resumes/${result.id}`)}
                    className="btn-secondary"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isSearching && query && results.length === 0 && (
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
      {!query && results.length === 0 && (
        <div className="text-center py-12">
          <Search className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            Start searching
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Enter a search query to find candidates
          </p>
          <div className="mt-6 text-left max-w-2xl mx-auto">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Example searches:
            </p>
            <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <li>• Senior Python developer with Django and AWS experience</li>
              <li>• Frontend engineer skilled in React and TypeScript</li>
              <li>• Data scientist with machine learning and PhD</li>
              <li>• DevOps engineer with Kubernetes certification</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}