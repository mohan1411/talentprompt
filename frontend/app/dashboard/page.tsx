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
  ChevronRight,
  FolderOpen,
  HardDrive,
  Cloud,
  Info,
  Target,
  Zap,
  Brain
} from 'lucide-react';
import { useAuth } from '@/lib/auth/context';
import { resumeApi } from '@/lib/api/client';
import type { Resume } from '@/lib/api/client';
import { searchHistory } from '@/lib/search-history';
import { ResumeStatisticsChart } from '@/components/dashboard/resume-statistics-chart';

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

  // Check if user has no resumes at all
  const hasNoResumes = !isLoading && stats.totalResumes === 0;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.full_name || user?.username}!
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          {hasNoResumes 
            ? "Let's get started with your AI-powered recruitment journey."
            : "Here's what's happening with your talent search today."}
        </p>
      </div>

      {/* Welcome Section - Show when user is new or has no resumes */}
      {(hasNoResumes || stats.totalResumes < 5) && (
        <div className="mb-8 bg-gradient-to-r from-primary/10 to-primary/5 rounded-lg p-6 border border-primary/20">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <Brain className="h-8 w-8 text-primary" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Find the Right Candidate with Natural Language Search
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Promtitude uses advanced AI to help you search through resumes using everyday language. 
                Simply describe your ideal candidate, and our AI will find the best matches from your resume database.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-start space-x-2">
                  <Target className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Precise Matching</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Find candidates that match your exact requirements</p>
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <Zap className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Lightning Fast</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Search through thousands of resumes in seconds</p>
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <Brain className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">AI-Powered</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Understands context and finds hidden gems</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State - When user has no resumes */}
      {hasNoResumes ? (
        <div className="space-y-8">
          {/* No Resumes Message */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border-2 border-dashed border-yellow-300 dark:border-yellow-700 rounded-lg p-8 text-center">
            <FileText className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
              No resumes available to screen
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
              Start building your resume database by uploading resumes from various sources. 
              Once you have resumes, you can use our powerful AI search to find the perfect candidates.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/dashboard/upload" className="btn-primary">
                <Upload className="h-4 w-4 mr-2" />
                Upload Resume
              </Link>
              <Link href="/dashboard/bulk-upload" className="btn-secondary">
                <Zap className="h-4 w-4 mr-2" />
                Bulk Upload
              </Link>
            </div>
          </div>

          {/* Resume Sources Hint */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
            <div className="flex items-start space-x-3">
              <Info className="h-6 w-6 text-blue-500 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                  Resume Sources You Can Use
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-start space-x-3">
                    <FolderOpen className="h-5 w-5 text-gray-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Local Folder</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Upload resumes from your computer in PDF, DOCX, or TXT format
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <Cloud className="h-5 w-5 text-gray-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Google Drive</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Import resumes directly from your Google Drive (coming soon)
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3 opacity-60">
                    <HardDrive className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        ATS Systems 
                        <span className="ml-2 text-xs bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded-full">Coming Soon</span>
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-500">
                        Integration with Greenhouse, Lever, and other ATS platforms
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
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

          {/* Resume Statistics Chart */}
          <div className="mb-8">
            <ResumeStatisticsChart />
          </div>
        </>
      )}

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

      {/* Recent Resumes - Only show when user has resumes */}
      {!hasNoResumes && (
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
      )}
    </div>
  );
}