'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Mic, Sparkles, Command, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const exampleQueries = [
  "Find me a Python developer with 5+ years experience",
  "Show senior engineers who know React and Node.js",
  "Find candidates similar to our top performers",
  "Who has experience with AWS and DevOps?",
  "Show me full-stack developers open to new opportunities",
  "Find machine learning engineers with startup experience",
];

export default function AISearchCenter() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [placeholder, setPlaceholder] = useState('');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [isFocused, setIsFocused] = useState(false);

  // Rotate through example queries
  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % exampleQueries.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Typewriter effect for placeholder
  useEffect(() => {
    const targetPlaceholder = `Try: "${exampleQueries[placeholderIndex]}"`;
    let currentIndex = 0;
    setPlaceholder('');

    const typeInterval = setInterval(() => {
      if (currentIndex < targetPlaceholder.length) {
        setPlaceholder(targetPlaceholder.slice(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(typeInterval);
      }
    }, 30);

    return () => clearInterval(typeInterval);
  }, [placeholderIndex]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/dashboard/search/progressive?q=${encodeURIComponent(query)}`);
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    router.push(`/dashboard/search/progressive?q=${encodeURIComponent(example)}`);
  };

  return (
    <div className="relative">
      {/* Background Glow */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 blur-3xl opacity-30 -z-10" />
      
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl p-8">
        <div className="text-center mb-6">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full text-sm font-medium mb-4"
          >
            <Sparkles className="h-4 w-4" />
            AI-Powered Search
            <Sparkles className="h-4 w-4" />
          </motion.div>
          
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            What kind of talent are you looking for?
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Describe your ideal candidate in natural language
          </p>
        </div>

        <form onSubmit={handleSearch} className="relative">
          <div className={`relative transition-all duration-300 ${isFocused ? 'scale-105' : ''}`}>
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-6 w-6 text-gray-400" />
            
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholder}
              className="w-full pl-14 pr-32 py-5 text-lg bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-xl focus:border-primary focus:ring-4 focus:ring-primary/20 transition-all duration-300 placeholder:text-gray-400"
            />
            
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
              <button
                type="button"
                className="p-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Voice search (coming soon)"
              >
                <Mic className="h-5 w-5" />
              </button>
              
              <button
                type="submit"
                disabled={!query.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-medium hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center gap-2"
              >
                Search
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Command hint */}
          <div className="absolute -bottom-6 left-0 text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
            <Command className="h-3 w-3" />
            <span>Press Cmd+K anywhere to search</span>
          </div>
        </form>

        {/* Quick Examples */}
        <div className="mt-10">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">Popular searches:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.slice(0, 4).map((example, index) => (
              <motion.button
                key={example}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => handleExampleClick(example)}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-sm"
              >
                {example}
              </motion.button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}