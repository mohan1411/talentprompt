'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Search,
  FileText,
  User,
  Upload,
  LogOut,
  Home,
  Menu,
  X,
  Zap,
  BrainIcon,
  Sparkles,
  Mail,
  GitBranch,
  ChevronLeft,
  ChevronRight,
  Settings,
  HelpCircle,
  Bell,
  Briefcase,
  Users,
  BarChart3,
  Activity
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth/context';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface NavigationItem {
  name: string;
  href: string;
  icon: any;
  badge?: string;
  badgeType?: 'new' | 'count' | 'live';
  count?: number;
  isLive?: boolean;
}

interface NavigationGroup {
  name: string;
  items: NavigationItem[];
  icon?: any;
}

const navigationGroups: NavigationGroup[] = [
  {
    name: 'Main',
    icon: Home,
    items: [
      { name: 'Dashboard', href: '/dashboard', icon: Home },
      { name: 'Pipeline', href: '/dashboard/pipeline', icon: GitBranch, badge: 'NEW', badgeType: 'new' },
    ]
  },
  {
    name: 'Search & Discovery',
    icon: Search,
    items: [
      { name: 'Search', href: '/dashboard/search', icon: Search },
      { name: 'Mind Reader', href: '/dashboard/search/progressive', icon: Sparkles, badge: 'AI', badgeType: 'new' },
      { name: 'Talent Radar', href: '/dashboard/talent-radar', icon: Activity, isLive: true, badgeType: 'live' },
    ]
  },
  {
    name: 'Resume Management',
    icon: FileText,
    items: [
      { name: 'My Resumes', href: '/dashboard/resumes', icon: FileText, count: 42, badgeType: 'count' },
      { name: 'Upload Resume', href: '/dashboard/upload', icon: Upload },
      { name: 'Bulk Upload', href: '/dashboard/bulk-upload', icon: Zap },
    ]
  },
  {
    name: 'Engagement',
    icon: Mail,
    items: [
      { name: 'Campaigns', href: '/dashboard/campaigns', icon: Mail, badge: 'NEW', badgeType: 'new' },
      { name: 'AI Interview', href: '/dashboard/interviews', icon: BrainIcon },
      { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
    ]
  },
  {
    name: 'Settings',
    icon: Settings,
    items: [
      { name: 'Profile', href: '/dashboard/profile', icon: User },
      { name: 'Team', href: '/dashboard/team', icon: Users },
      { name: 'Preferences', href: '/dashboard/settings', icon: Settings },
      { name: 'Help', href: '/dashboard/help', icon: HelpCircle },
    ]
  }
];

export function ModernSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['Main', 'Search & Discovery']);
  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  // Load collapsed state from localStorage
  useEffect(() => {
    const savedState = localStorage.getItem('sidebar-collapsed');
    if (savedState) {
      setIsCollapsed(JSON.parse(savedState));
    }
  }, []);

  // Save collapsed state
  const toggleCollapsed = useCallback(() => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem('sidebar-collapsed', JSON.stringify(newState));
    // Dispatch custom event for immediate updates
    window.dispatchEvent(new Event('sidebar-toggle'));
  }, [isCollapsed]);

  // Toggle group expansion
  const toggleGroup = (groupName: string) => {
    setExpandedGroups(prev => 
      prev.includes(groupName) 
        ? prev.filter(g => g !== groupName)
        : [...prev, groupName]
    );
  };

  // Filter navigation based on search
  const filteredGroups = navigationGroups.map(group => ({
    ...group,
    items: group.items.filter(item => 
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(group => group.items.length > 0);

  const sidebarVariants = {
    expanded: { width: '256px' },
    collapsed: { width: '80px' }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0 }
  };

  return (
    <>
      {/* Mobile menu button */}
      <motion.div 
        className="lg:hidden fixed top-4 left-4 z-50"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-3 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200/50 dark:border-gray-700/50"
        >
          {isMobileMenuOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </motion.div>

      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={isCollapsed ? 'collapsed' : 'expanded'}
        variants={sidebarVariants}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className={cn(
          "fixed inset-y-0 left-0 z-40",
          "bg-gradient-to-b from-white/90 to-white/70 dark:from-gray-900/90 dark:to-gray-900/70",
          "backdrop-blur-xl border-r border-gray-200/50 dark:border-gray-700/50",
          "shadow-2xl transform transition-transform duration-300 ease-in-out",
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full',
          "lg:translate-x-0"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo and collapse button */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200/50 dark:border-gray-700/50">
            <motion.div 
              className="flex items-center"
              animate={{ opacity: isCollapsed ? 0 : 1 }}
              transition={{ duration: 0.2 }}
            >
              {!isCollapsed && (
                <img 
                  src="/logo-horizontal.svg" 
                  alt="Promtitude" 
                  className="h-8 w-auto"
                />
              )}
            </motion.div>
            
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={toggleCollapsed}
              className="hidden lg:flex items-center justify-center w-8 h-8 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </motion.button>
          </div>

          {/* Search bar */}
          {!isCollapsed && (
            <motion.div 
              className="px-4 py-3 border-b border-gray-200/50 dark:border-gray-700/50"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Quick search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm bg-gray-100/50 dark:bg-gray-800/50 rounded-lg border border-gray-200/50 dark:border-gray-700/50 focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
                <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">
                  ⌘K
                </kbd>
              </div>
            </motion.div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-2 overflow-y-auto scrollbar-thin">
            <AnimatePresence>
              {filteredGroups.map((group, groupIndex) => (
                <motion.div
                  key={group.name}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                  variants={itemVariants}
                  transition={{ delay: groupIndex * 0.05 }}
                  className="space-y-1"
                >
                  {/* Group header */}
                  {!isCollapsed && (
                    <button
                      onClick={() => toggleGroup(group.name)}
                      className="w-full flex items-center justify-between px-2 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
                    >
                      <span className="flex items-center gap-2">
                        {group.icon && <group.icon className="h-3 w-3" />}
                        {group.name.toUpperCase()}
                      </span>
                      <motion.div
                        animate={{ rotate: expandedGroups.includes(group.name) ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronLeft className="h-3 w-3 rotate-90" />
                      </motion.div>
                    </button>
                  )}

                  {/* Group items */}
                  <AnimatePresence>
                    {(isCollapsed || expandedGroups.includes(group.name)) && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="space-y-0.5"
                      >
                        {group.items.map((item, itemIndex) => {
                          const isActive = pathname === item.href;
                          const ItemIcon = item.icon;
                          
                          return (
                            <motion.div
                              key={item.name}
                              initial="hidden"
                              animate="visible"
                              variants={itemVariants}
                              transition={{ delay: itemIndex * 0.03 }}
                            >
                              <Link
                                href={item.href}
                                onClick={() => setIsMobileMenuOpen(false)}
                                onMouseEnter={() => setHoveredItem(item.name)}
                                onMouseLeave={() => setHoveredItem(null)}
                                className={cn(
                                  "group relative flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200",
                                  isActive
                                    ? "bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/25"
                                    : "text-gray-700 dark:text-gray-300 hover:bg-gray-100/80 dark:hover:bg-gray-800/80"
                                )}
                              >
                                {/* Hover effect */}
                                {hoveredItem === item.name && !isActive && (
                                  <motion.div
                                    layoutId="hoverBackground"
                                    className="absolute inset-0 bg-gradient-to-r from-gray-100/50 to-gray-100/30 dark:from-gray-800/50 dark:to-gray-800/30 rounded-xl"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                  />
                                )}

                                {/* Icon */}
                                <motion.div
                                  whileHover={{ scale: 1.1, rotate: 5 }}
                                  transition={{ duration: 0.2 }}
                                  className="relative z-10"
                                >
                                  <ItemIcon
                                    className={cn(
                                      "h-5 w-5",
                                      isActive
                                        ? "text-white"
                                        : "text-gray-500 group-hover:text-gray-700 dark:group-hover:text-gray-200"
                                    )}
                                  />
                                  {item.isLive && (
                                    <span className="absolute -top-1 -right-1 h-2 w-2">
                                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                    </span>
                                  )}
                                </motion.div>

                                {/* Label */}
                                {!isCollapsed && (
                                  <motion.span 
                                    className="ml-3 flex-1 relative z-10"
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.1 }}
                                  >
                                    {item.name}
                                  </motion.span>
                                )}

                                {/* Badge */}
                                {!isCollapsed && item.badge && (
                                  <motion.span
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ delay: 0.2, type: 'spring' }}
                                    className={cn(
                                      "ml-2 px-2 py-0.5 text-xs font-semibold rounded-full",
                                      item.badgeType === 'new' && "bg-gradient-to-r from-blue-500 to-purple-500 text-white",
                                      item.badgeType === 'count' && "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200",
                                      item.badgeType === 'live' && "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300"
                                    )}
                                  >
                                    {item.badge || item.count}
                                  </motion.span>
                                )}

                                {/* Tooltip for collapsed state */}
                                {isCollapsed && (
                                  <motion.div
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: hoveredItem === item.name ? 1 : 0, x: 0 }}
                                    className="absolute left-full ml-2 px-2 py-1 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-md whitespace-nowrap pointer-events-none z-50"
                                  >
                                    {item.name}
                                    {item.badge && (
                                      <span className="ml-2 px-1.5 py-0.5 bg-white/20 dark:bg-black/20 rounded text-xs">
                                        {item.badge}
                                      </span>
                                    )}
                                  </motion.div>
                                )}
                              </Link>
                            </motion.div>
                          );
                        })}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>
          </nav>

          {/* Notifications */}
          {!isCollapsed && (
            <div className="px-4 py-3 border-t border-gray-200/50 dark:border-gray-700/50">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full flex items-center justify-between px-3 py-2 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg hover:from-purple-500/20 hover:to-blue-500/20 transition-all"
              >
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  <span className="text-sm font-medium">3 new notifications</span>
                </div>
                <span className="h-2 w-2 bg-purple-500 rounded-full animate-pulse"></span>
              </motion.button>
            </div>
          )}

          {/* User section */}
          <div className="p-4 border-t border-gray-200/50 dark:border-gray-700/50">
            <div className={cn(
              "flex items-center",
              isCollapsed ? "justify-center" : "mb-3"
            )}>
              {!isCollapsed && (
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {user?.full_name || user?.username}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.email}
                  </p>
                </div>
              )}
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={logout}
              className={cn(
                "flex items-center w-full px-3 py-2 text-sm font-medium rounded-lg",
                "text-gray-700 dark:text-gray-300",
                "hover:bg-red-50 dark:hover:bg-red-900/20",
                "hover:text-red-600 dark:hover:text-red-400",
                "transition-all duration-200",
                isCollapsed && "justify-center"
              )}
            >
              <LogOut className="h-4 w-4" />
              {!isCollapsed && <span className="ml-3">Logout</span>}
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Mobile overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 lg:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Add custom scrollbar styles */}
      <style jsx global>{`
        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: transparent;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: rgba(156, 163, 175, 0.3);
          border-radius: 3px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: rgba(156, 163, 175, 0.5);
        }
      `}</style>
    </>
  );
}