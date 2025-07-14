'use client';

import { useEffect, useState } from 'react';
import { Tag, TrendingUp, Code, Cloud, Database, Brain, Wrench } from 'lucide-react';
import { searchApi } from '@/lib/api/client';
import type { PopularTag } from '@/lib/api/client';

interface TagCloudProps {
  onTagClick: (tag: string) => void;
  selectedTags: string[];
}

export default function TagCloud({ onTagClick, selectedTags }: TagCloudProps) {
  const [tags, setTags] = useState<PopularTag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPopularTags();
  }, []);

  const fetchPopularTags = async () => {
    try {
      const popularTags = await searchApi.getPopularTags(25);
      setTags(popularTags);
    } catch (err) {
      console.error('Failed to fetch popular tags:', err);
      setError('Failed to load tags');
    } finally {
      setIsLoading(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'language':
        return <Code className="h-3 w-3" />;
      case 'cloud':
        return <Cloud className="h-3 w-3" />;
      case 'database':
        return <Database className="h-3 w-3" />;
      case 'data':
        return <Brain className="h-3 w-3" />;
      case 'devops':
      case 'tool':
        return <Wrench className="h-3 w-3" />;
      default:
        return <Tag className="h-3 w-3" />;
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      language: 'bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400',
      frontend: 'bg-purple-100 text-purple-700 hover:bg-purple-200 dark:bg-purple-900/30 dark:text-purple-400',
      framework: 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400',
      database: 'bg-orange-100 text-orange-700 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-400',
      cloud: 'bg-sky-100 text-sky-700 hover:bg-sky-200 dark:bg-sky-900/30 dark:text-sky-400',
      devops: 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400',
      data: 'bg-pink-100 text-pink-700 hover:bg-pink-200 dark:bg-pink-900/30 dark:text-pink-400',
      tool: 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300',
      methodology: 'bg-teal-100 text-teal-700 hover:bg-teal-200 dark:bg-teal-900/30 dark:text-teal-400',
      skill: 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300',
    };
    return colors[category as keyof typeof colors] || colors.skill;
  };

  if (isLoading) {
    return (
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Tag className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Popular Skills</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error || tags.length === 0) {
    return null;
  }

  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Popular Skills</h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">(Click to search)</span>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => {
          const isSelected = selectedTags.includes(tag.name);
          return (
            <button
              key={tag.name}
              onClick={() => onTagClick(tag.name)}
              className={`
                inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium
                transition-all duration-200 transform hover:scale-105
                ${getCategoryColor(tag.category)}
                ${isSelected ? 'ring-2 ring-offset-2 ring-primary' : ''}
              `}
              title={`${tag.count} candidates with ${tag.name}`}
            >
              {getCategoryIcon(tag.category)}
              <span>{tag.name}</span>
              <span className="text-xs opacity-75">({tag.count})</span>
            </button>
          );
        })}
      </div>

      {/* Category Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-1">
          <Code className="h-3 w-3" />
          <span>Languages</span>
        </div>
        <div className="flex items-center gap-1">
          <Cloud className="h-3 w-3" />
          <span>Cloud</span>
        </div>
        <div className="flex items-center gap-1">
          <Database className="h-3 w-3" />
          <span>Databases</span>
        </div>
        <div className="flex items-center gap-1">
          <Brain className="h-3 w-3" />
          <span>Data/AI</span>
        </div>
      </div>
    </div>
  );
}