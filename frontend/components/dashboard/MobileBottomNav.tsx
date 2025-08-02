'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Search, GitBranch, FileText, User } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const mobileNavItems = [
  { name: 'Home', href: '/dashboard', icon: Home },
  { name: 'Search', href: '/dashboard/search', icon: Search },
  { name: 'Pipeline', href: '/dashboard/pipeline', icon: GitBranch },
  { name: 'Resumes', href: '/dashboard/resumes', icon: FileText },
  { name: 'Profile', href: '/dashboard/profile', icon: User },
];

export function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl border-t border-gray-200/50 dark:border-gray-700/50">
      <nav className="flex items-center justify-around h-16 px-2">
        {mobileNavItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "relative flex flex-col items-center justify-center flex-1 h-full",
                "transition-all duration-200"
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="mobileActiveTab"
                  className="absolute inset-x-2 top-0 h-0.5 bg-gradient-to-r from-primary to-primary/80"
                  initial={false}
                  transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 30
                  }}
                />
              )}
              
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="flex flex-col items-center gap-1"
              >
                <Icon
                  className={cn(
                    "h-5 w-5 transition-colors",
                    isActive
                      ? "text-primary"
                      : "text-gray-500 dark:text-gray-400"
                  )}
                />
                <span
                  className={cn(
                    "text-xs font-medium transition-colors",
                    isActive
                      ? "text-primary"
                      : "text-gray-500 dark:text-gray-400"
                  )}
                >
                  {item.name}
                </span>
              </motion.div>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}