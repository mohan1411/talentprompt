'use client';

import React, { useState } from 'react';
import { GitBranch, Search, Loader } from 'lucide-react';
import { motion } from 'framer-motion';
import { SearchResult } from '@/hooks/useProgressiveSearch';

interface FindSimilarButtonProps {
  candidate: SearchResult;
  onFindSimilar: (candidateId: string) => void;
  isCompact?: boolean;
}

export default function FindSimilarButton({ 
  candidate, 
  onFindSimilar,
  isCompact = false 
}: FindSimilarButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    try {
      await onFindSimilar(candidate.id);
    } finally {
      setIsLoading(false);
    }
  };

  if (isCompact) {
    return (
      <button
        onClick={handleClick}
        disabled={isLoading}
        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors group relative"
        title="Find candidates with similar career DNA"
      >
        {isLoading ? (
          <Loader className="h-4 w-4 animate-spin text-gray-500" />
        ) : (
          <GitBranch className="h-4 w-4 text-gray-500 group-hover:text-indigo-600" />
        )}
        
        {/* Tooltip */}
        <span className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          Find similar careers
        </span>
      </button>
    );
  }

  return (
    <motion.button
      onClick={handleClick}
      disabled={isLoading}
      className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-md hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {isLoading ? (
        <>
          <Loader className="h-4 w-4 animate-spin" />
          <span>Finding similar...</span>
        </>
      ) : (
        <>
          <GitBranch className="h-4 w-4" />
          <span>Find Similar Career DNA</span>
        </>
      )}
    </motion.button>
  );
}