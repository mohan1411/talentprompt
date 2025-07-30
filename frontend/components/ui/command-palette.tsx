'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Upload,
  FileText,
  Users,
  Mail,
  Settings,
  User,
  LogOut,
  Command,
  ChevronRight,
  Home,
  Brain,
  Sparkles
} from 'lucide-react';

interface CommandItem {
  id: string;
  title: string;
  description?: string;
  icon: React.ReactNode;
  action: () => void;
  keywords?: string[];
}

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  // Define all available commands
  const commands: CommandItem[] = [
    {
      id: 'search',
      title: 'Search Resumes',
      description: 'Find candidates with natural language',
      icon: <Search className="h-4 w-4" />,
      action: () => router.push('/dashboard/search'),
      keywords: ['find', 'candidates', 'search']
    },
    {
      id: 'mind-reader',
      title: 'Mind Reader Search',
      description: 'AI-powered candidate discovery',
      icon: <Sparkles className="h-4 w-4" />,
      action: () => router.push('/dashboard/search/progressive'),
      keywords: ['ai', 'smart', 'intelligent']
    },
    {
      id: 'upload',
      title: 'Upload Resume',
      description: 'Add a new resume to your pipeline',
      icon: <Upload className="h-4 w-4" />,
      action: () => router.push('/dashboard/upload'),
      keywords: ['add', 'new', 'import']
    },
    {
      id: 'resumes',
      title: 'My Resumes',
      description: 'View and manage all resumes',
      icon: <FileText className="h-4 w-4" />,
      action: () => router.push('/dashboard/resumes'),
      keywords: ['view', 'list', 'manage']
    },
    {
      id: 'campaigns',
      title: 'Campaigns',
      description: 'Manage outreach campaigns',
      icon: <Mail className="h-4 w-4" />,
      action: () => router.push('/dashboard/campaigns'),
      keywords: ['outreach', 'email', 'invite']
    },
    {
      id: 'interview',
      title: 'AI Interview Copilot',
      description: 'Start or schedule an interview',
      icon: <Brain className="h-4 w-4" />,
      action: () => router.push('/dashboard/interviews'),
      keywords: ['interview', 'copilot', 'ai']
    },
    {
      id: 'profile',
      title: 'My Profile',
      description: 'Update your profile settings',
      icon: <User className="h-4 w-4" />,
      action: () => router.push('/dashboard/profile'),
      keywords: ['settings', 'account', 'profile']
    },
    {
      id: 'dashboard',
      title: 'Dashboard',
      description: 'Go to dashboard home',
      icon: <Home className="h-4 w-4" />,
      action: () => router.push('/dashboard'),
      keywords: ['home', 'overview', 'stats']
    }
  ];

  // Filter commands based on search
  const filteredCommands = commands.filter(command => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      command.title.toLowerCase().includes(searchLower) ||
      command.description?.toLowerCase().includes(searchLower) ||
      command.keywords?.some(keyword => keyword.includes(searchLower))
    );
  });

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Open command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }

      // Close on Escape
      if (e.key === 'Escape') {
        setIsOpen(false);
        setSearch('');
        setSelectedIndex(0);
      }

      // Navigate with arrow keys
      if (isOpen) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < filteredCommands.length - 1 ? prev + 1 : 0
          );
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : filteredCommands.length - 1
          );
        } else if (e.key === 'Enter') {
          e.preventDefault();
          const selectedCommand = filteredCommands[selectedIndex];
          if (selectedCommand) {
            selectedCommand.action();
            setIsOpen(false);
            setSearch('');
            setSelectedIndex(0);
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex]);

  // Reset selected index when search changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  const handleCommandClick = useCallback((command: CommandItem) => {
    command.action();
    setIsOpen(false);
    setSearch('');
    setSelectedIndex(0);
  }, []);

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
              onClick={() => setIsOpen(false)}
            />

            {/* Command Palette */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.15 }}
              className="fixed top-[20%] left-1/2 transform -translate-x-1/2 w-full max-w-2xl bg-white dark:bg-gray-800 rounded-xl shadow-2xl z-50 overflow-hidden"
            >
              {/* Search Header */}
              <div className="border-b border-gray-200 dark:border-gray-700 p-4">
                <div className="flex items-center gap-3">
                  <Search className="h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Type a command or search..."
                    className="flex-1 bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-500"
                    autoFocus
                  />
                  <kbd className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded">
                    ESC
                  </kbd>
                </div>
              </div>

              {/* Commands List */}
              <div className="max-h-96 overflow-y-auto p-2">
                {filteredCommands.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No commands found
                  </div>
                ) : (
                  <div className="space-y-1">
                    {filteredCommands.map((command, index) => (
                      <motion.button
                        key={command.id}
                        onClick={() => handleCommandClick(command)}
                        onMouseEnter={() => setSelectedIndex(index)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                          index === selectedIndex
                            ? 'bg-primary/10 text-primary dark:bg-primary/20'
                            : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                      >
                        <div className={`p-2 rounded-lg ${
                          index === selectedIndex
                            ? 'bg-primary/20'
                            : 'bg-gray-100 dark:bg-gray-700'
                        }`}>
                          {command.icon}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900 dark:text-white">
                            {command.title}
                          </div>
                          {command.description && (
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {command.description}
                            </div>
                          )}
                        </div>
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-2">
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">↑</kbd>
                      <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">↓</kbd>
                      Navigate
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">↵</kbd>
                      Select
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Command className="h-3 w-3" />
                    <span>Command Palette</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}