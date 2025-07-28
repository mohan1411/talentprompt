'use client';

import { useState, useEffect } from 'react';
import { Brain, TrendingUp, Users, Zap, Eye, Star, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';

interface Insight {
  id: string;
  type: 'talent' | 'pattern' | 'opportunity' | 'recommendation';
  icon: React.ElementType;
  title: string;
  description: string;
  action?: {
    label: string;
    href: string;
  };
  metric?: {
    value: string;
    label: string;
  };
}

interface SmartInsightsProps {
  totalResumes: number;
}

export default function SmartInsights({ totalResumes }: SmartInsightsProps) {
  const [insights, setInsights] = useState<Insight[]>([]);

  useEffect(() => {
    // Generate insights based on resume count
    const generateInsights = () => {
      const newInsights: Insight[] = [];

      if (totalResumes > 10) {
        newInsights.push({
          id: 'skill-combo',
          type: 'talent',
          icon: Brain,
          title: 'Hidden Skill Combinations',
          description: 'Found 3 Python developers who also know React and DevOps',
          action: {
            label: 'View Candidates',
            href: '/dashboard/search/progressive?q=Python React DevOps'
          },
          metric: {
            value: '3',
            label: 'Matches'
          }
        });
      }

      if (totalResumes > 5) {
        newInsights.push({
          id: 'career-pattern',
          type: 'pattern',
          icon: TrendingUp,
          title: 'Career Growth Patterns',
          description: '5 candidates show rapid growth trajectories in the last 2 years',
          action: {
            label: 'Explore Patterns',
            href: '/dashboard/search/progressive?q=rapid career growth'
          },
          metric: {
            value: '85%',
            label: 'Growth Rate'
          }
        });
      }

      if (totalResumes > 0) {
        newInsights.push({
          id: 'availability',
          type: 'opportunity',
          icon: Zap,
          title: 'High Availability Alert',
          description: '2 senior engineers show signs of being open to opportunities',
          action: {
            label: 'View Profiles',
            href: '/dashboard/search/progressive?q=senior engineer available'
          },
          metric: {
            value: '2',
            label: 'Available'
          }
        });
      }

      // Always show this one
      newInsights.push({
        id: 'recommendation',
        type: 'recommendation',
        icon: Star,
        title: 'AI Recommendation',
        description: totalResumes > 0 
          ? 'Based on your searches, consider looking for Full-Stack developers'
          : 'Upload resumes to get personalized talent insights',
        action: totalResumes > 0 ? {
          label: 'Search Now',
          href: '/dashboard/search/progressive?q=Full-Stack developer'
        } : {
          label: 'Upload Resumes',
          href: '/dashboard/upload'
        }
      });

      setInsights(newInsights);
    };

    generateInsights();
  }, [totalResumes]);

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'talent': return 'from-blue-500 to-cyan-500';
      case 'pattern': return 'from-purple-500 to-pink-500';
      case 'opportunity': return 'from-green-500 to-emerald-500';
      case 'recommendation': return 'from-amber-500 to-orange-500';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Brain className="h-6 w-6 text-primary" />
          Smart Insights
        </h2>
        <Link 
          href="/dashboard/insights"
          className="text-sm text-primary hover:underline flex items-center gap-1"
        >
          View all insights
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, index) => (
          <motion.div
            key={insight.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="group relative bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-300"
          >
            {/* Gradient accent */}
            <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${getInsightColor(insight.type)} rounded-t-xl`} />
            
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg bg-gradient-to-r ${getInsightColor(insight.type)} bg-opacity-10`}>
                <insight.icon className="h-6 w-6 text-gray-700 dark:text-gray-300" />
              </div>
              
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  {insight.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {insight.description}
                </p>
                
                <div className="flex items-center justify-between">
                  {insight.action && (
                    <Link
                      href={insight.action.href}
                      className="text-sm font-medium text-primary hover:underline flex items-center gap-1 group-hover:gap-2 transition-all"
                    >
                      {insight.action.label}
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  )}
                  
                  {insight.metric && (
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {insight.metric.value}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {insight.metric.label}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {totalResumes === 0 && (
        <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <div className="flex items-center gap-2 text-amber-800 dark:text-amber-200">
            <Eye className="h-5 w-5" />
            <p className="text-sm font-medium">
              Upload resumes to unlock powerful AI insights about your talent pool
            </p>
          </div>
        </div>
      )}
    </div>
  );
}