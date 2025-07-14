'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
  Search,
  Upload,
  FileText,
  Users,
  TrendingUp,
  Clock,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '@/lib/auth/context';
import { resumeApi } from '@/lib/api/client';
import type { Resume } from '@/lib/api/client';
import { searchHistory } from '@/lib/search-history';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalResumes: 0,
    recentSearches: 0,
    activeResumes: 0,
    pendingParsing: 0,
  });
  const [recentResumes, setRecentResumes] = useState<Resume[]>([]);
  const [recentSearchQueries, setRecentSearchQueries] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch all resumes to get accurate counts
      const allResumes = await resumeApi.getMyResumes(0, 1000); // Fetch up to 1000 resumes
      const recentResumes = allResumes.slice(0, 5); // Get first 5 for recent list
      setRecentResumes(recentResumes);
      
      // Calculate stats from all resumes
      const activeCount = allResumes.filter((r: Resume) => r.status === 'active').length;
      const pendingCount = allResumes.filter((r: Resume) => r.parse_status === 'pending').length;
      
      // Get search history count and recent searches
      const searchCount = searchHistory.getRecentCount(30);
      const recentSearches = searchHistory.getRecentSearches(5);
      setRecentSearchQueries(recentSearches.map(s => s.query));
      
      setStats({
        totalResumes: allResumes.length,
        recentSearches: searchCount,
        activeResumes: activeCount,
        pendingParsing: pendingCount,
      });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'Search Resumes',
      description: 'Find candidates using natural language',
      icon: Search,
      href: '/dashboard/search',
      color: 'bg-blue-500',
    },
    {
      title: 'Upload Resume',
      description: 'Add new resumes to your database',
      icon: Upload,
      href: '/dashboard/upload',
      color: 'bg-green-500',
    },
    {
      title: 'My Resumes',
      description: 'View and manage your resume collection',
      icon: FileText,
      href: '/dashboard/resumes',
      color: 'bg-purple-500',
    },
  ];

  const statCards = [
    {
      title: 'Total Resumes',
      value: stats.totalResumes,
      icon: FileText,
      trend: '+12%',
      color: 'text-blue-600',
    },
    {
      title: 'Active Resumes',
      value: stats.activeResumes,
      icon: Users,
      trend: '+5%',
      color: 'text-green-600',
    },
    {
      title: 'Pending Parsing',
      value: stats.pendingParsing,
      icon: Clock,
      trend: '-',
      color: 'text-yellow-600',
    },
    {
      title: 'Recent Searches',
      value: stats.recentSearches,
      icon: TrendingUp,
      trend: '+23%',
      color: 'text-purple-600',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.full_name || user?.username}!
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Here's what's happening with your talent search today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => (
          <div key={stat.title} className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {stat.title}
                </p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {stat.value}
                </p>
                {stat.trend !== '-' && (
                  <p className="mt-1 text-sm text-green-600">
                    {stat.trend} from last month
                  </p>
                )}
              </div>
              <stat.icon className={`h-12 w-12 ${stat.color} opacity-20`} />
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => (
            <Link
              key={action.title}
              href={action.href}
              className="card p-6 hover:shadow-lg transition-shadow group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${action.color} bg-opacity-10`}>
                  <action.icon className={`h-6 w-6 ${action.color} text-white`} />
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-gray-600 transition-colors" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                {action.title}
              </h3>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {action.description}
              </p>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Searches */}
      {recentSearchQueries.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Recent Searches
          </h2>
          <div className="flex flex-wrap gap-2">
            {recentSearchQueries.map((searchQuery, index) => (
              <Link
                key={index}
                href={`/dashboard/search?q=${encodeURIComponent(searchQuery)}`}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                <Clock className="h-3 w-3 mr-1" />
                {searchQuery}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent Resumes */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Recent Resumes
          </h2>
          <Link
            href="/dashboard/resumes"
            className="text-sm text-primary hover:underline"
          >
            View all
          </Link>
        </div>

        {isLoading ? (
          <div className="card p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          </div>
        ) : recentResumes.length === 0 ? (
          <div className="card p-8 text-center">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              No resumes uploaded yet
            </p>
            <Link
              href="/dashboard/upload"
              className="mt-4 inline-flex items-center btn-primary"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload your first resume
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentResumes.map((resume) => (
              <div key={resume.id} className="card p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {resume.first_name} {resume.last_name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {resume.current_title || 'No title'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">
                      {new Date(resume.created_at).toLocaleDateString()}
                    </p>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        resume.parse_status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : resume.parse_status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {resume.parse_status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}