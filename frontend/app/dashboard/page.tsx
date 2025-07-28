'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
  FileText,
  Users,
  Upload,
  Brain,
  Sparkles,
  Command,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '@/lib/auth/context';
import { resumeApi } from '@/lib/api/client';
import type { Resume } from '@/lib/api/client';
import { searchHistory } from '@/lib/search-history';
import AISearchCenter from '@/components/dashboard/AISearchCenter';
import SmartInsights from '@/components/dashboard/SmartInsights';
import TalentRadarPreview from '@/components/dashboard/TalentRadarPreview';
import QuickActions from '@/components/dashboard/QuickActions';
import ActivityFeed from '@/components/dashboard/ActivityFeed';
import { motion } from 'framer-motion';

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
      const allResumes = await resumeApi.getMyResumes(0, 1000);
      const recentResumes = allResumes.slice(0, 10); // Get more for various components
      setRecentResumes(recentResumes);
      
      // Calculate stats from all resumes
      const activeCount = allResumes.filter((r: Resume) => r.status === 'active').length;
      const pendingCount = allResumes.filter((r: Resume) => r.parse_status === 'pending').length;
      
      // Get search history count and recent searches
      const searchCount = searchHistory.getRecentCount(30);
      const recentSearches = searchHistory.getRecentSearches(10);
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

  // Transform resumes for radar
  const radarCandidates = recentResumes.slice(0, 10).map((resume) => ({
    id: resume.id,
    name: `${resume.first_name} ${resume.last_name}`,
    title: resume.current_title || 'Not specified',
    score: Math.random() * 0.5 + 0.5, // Mock score for now
    skills: resume.skills || []
  }));

  // Check if user has no resumes at all
  const hasNoResumes = !isLoading && stats.totalResumes === 0;

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome back, {user?.full_name || user?.username}!
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Your AI-powered recruitment command center
        </p>
      </motion.div>

      {/* AI Search Center - Hero Section */}
      <AISearchCenter />

      {/* Main Content Grid */}
      {hasNoResumes ? (
        // Empty State
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="space-y-8"
        >
          <div className="text-center py-12 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-2xl">
            <div className="max-w-2xl mx-auto px-8">
              <div className="inline-flex p-4 bg-primary/10 rounded-full mb-6">
                <Brain className="h-12 w-12 text-primary" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                Start Building Your Talent Pool
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
                Upload resumes to unlock AI-powered search, insights, and recommendations. 
                Our AI will help you find the perfect candidates instantly.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link 
                  href="/dashboard/upload" 
                  className="inline-flex items-center px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                >
                  <Upload className="h-5 w-5 mr-2" />
                  Upload Your First Resume
                </Link>
                <Link 
                  href="/dashboard/bulk-upload" 
                  className="inline-flex items-center px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                >
                  <Sparkles className="h-5 w-5 mr-2" />
                  Bulk Import
                </Link>
              </div>
            </div>
          </div>

          {/* Features Preview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Brain,
                title: 'Natural Language Search',
                description: 'Describe your ideal candidate in plain English'
              },
              {
                icon: Sparkles,
                title: 'AI Insights',
                description: 'Discover hidden patterns and opportunities'
              },
              {
                icon: Users,
                title: 'Career DNA Matching',
                description: 'Find candidates with similar trajectories'
              }
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
              >
                <feature.icon className="h-8 w-8 text-primary mb-4" />
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      ) : (
        // Dashboard with Data
        <>
          {/* Insights and Radar Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <SmartInsights totalResumes={stats.totalResumes} />
            </div>
            <div>
              <TalentRadarPreview candidates={radarCandidates} />
            </div>
          </div>

          {/* Quick Actions */}
          <QuickActions />

          {/* Activity Feed and Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <ActivityFeed 
                recentResumes={recentResumes} 
                recentSearches={recentSearchQueries} 
              />
            </div>
            
            {/* Quick Stats */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Stats
              </h3>
              {[
                { label: 'Total Resumes', value: stats.totalResumes, icon: FileText, color: 'text-blue-600' },
                { label: 'Active Candidates', value: stats.activeResumes, icon: Users, color: 'text-green-600' },
                { label: 'Recent Searches', value: stats.recentSearches, icon: Brain, color: 'text-purple-600' },
              ].map((stat) => (
                <div 
                  key={stat.label}
                  className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {stat.label}
                      </p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {stat.value}
                      </p>
                    </div>
                    <stat.icon className={`h-8 w-8 ${stat.color} opacity-20`} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Command Palette Hint */}
      <div className="text-center py-8">
        <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center justify-center gap-2">
          <Command className="h-4 w-4" />
          Press <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Cmd+K</kbd> anywhere for quick search
        </p>
      </div>
    </div>
  );
}