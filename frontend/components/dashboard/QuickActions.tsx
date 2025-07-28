'use client';

import Link from 'next/link';
import { Search, Brain, Users, Upload, Sparkles, GitCompare, FileText, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';

const actions = [
  {
    id: 'smart-search',
    title: 'Smart Search',
    description: 'AI understands your needs',
    icon: Brain,
    href: '/dashboard/search/progressive',
    gradient: 'from-blue-500 to-purple-500',
    badge: 'AI Powered',
  },
  {
    id: 'find-similar',
    title: 'Find Similar',
    description: 'Match candidates by DNA',
    icon: GitCompare,
    href: '/dashboard/search',
    gradient: 'from-green-500 to-teal-500',
    badge: 'New',
  },
  {
    id: 'talent-pipeline',
    title: 'Talent Pipeline',
    description: 'Track your candidates',
    icon: Users,
    href: '/dashboard/pipeline',
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    id: 'bulk-upload',
    title: 'Bulk Upload',
    description: 'Import multiple resumes',
    icon: Upload,
    href: '/dashboard/bulk-upload',
    gradient: 'from-orange-500 to-red-500',
  },
];

export default function QuickActions() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
        <Sparkles className="h-6 w-6 text-primary" />
        Quick Actions
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((action, index) => (
          <motion.div
            key={action.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Link
              href={action.href}
              className="group relative block h-full bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-xl transition-all duration-300 overflow-hidden"
            >
              {/* Background gradient on hover */}
              <div 
                className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}
              />
              
              {/* Icon */}
              <div className={`relative inline-flex p-3 rounded-lg bg-gradient-to-br ${action.gradient} mb-4`}>
                <action.icon className="h-6 w-6 text-white" />
              </div>
              
              {/* Badge */}
              {action.badge && (
                <span className="absolute top-4 right-4 px-2 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full">
                  {action.badge}
                </span>
              )}
              
              {/* Content */}
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-primary transition-colors">
                {action.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {action.description}
              </p>
              
              {/* Hover arrow */}
              <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <TrendingUp className="h-4 w-4 text-primary" />
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}