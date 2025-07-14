'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, MapPin, Briefcase, Users } from 'lucide-react';
import { searchApi } from '@/lib/api/client';
import type { SearchResult } from '@/lib/api/client';

export default function SimilarResumesPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [candidateName, setCandidateName] = useState('');

  useEffect(() => {
    const name = searchParams.get('name');
    if (name) {
      setCandidateName(name);
    }
    
    if (params.id) {
      fetchSimilarResumes(params.id as string);
    }
  }, [params.id, searchParams]);

  const fetchSimilarResumes = async (resumeId: string) => {
    setIsLoading(true);
    try {
      const similarResumes = await searchApi.getSimilarResumes(resumeId, 10);
      setResults(similarResumes);
    } catch (error) {
      console.error('Failed to fetch similar resumes:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <button
          onClick={() => router.back()}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </button>
        
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Similar Candidates
        </h1>
        {candidateName && (
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Showing candidates similar to <span className="font-medium">{candidateName}</span>
          </p>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      )}

      {/* Results */}
      {!isLoading && results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Found {results.length} similar candidates
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
                      {Math.round(result.score * 100)}% similar
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

                  {result.highlights && result.highlights.length > 0 && (
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
      {!isLoading && results.length === 0 && (
        <div className="text-center py-12">
          <Users className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            No similar candidates found
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            This candidate appears to have a unique profile
          </p>
          <Link
            href="/dashboard/search"
            className="btn-primary mt-4"
          >
            Go to Search
          </Link>
        </div>
      )}
    </div>
  );
}