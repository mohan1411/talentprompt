'use client';

import { Briefcase } from 'lucide-react';

interface ExperienceTagsProps {
  onTagClick: (tag: string) => void;
  selectedTags: string[];
}

const experienceLevels = [
  { name: 'Entry Level', query: 'entry level 0-2 years', years: '0-2 years' },
  { name: 'Junior', query: 'junior developer 2-4 years', years: '2-4 years' },
  { name: 'Mid-level', query: 'mid level developer 4-7 years', years: '4-7 years' },
  { name: 'Senior', query: 'senior developer 7-10 years', years: '7-10 years' },
  { name: 'Lead/Principal', query: 'lead principal developer 10+ years', years: '10+ years' },
];

export default function ExperienceTags({ onTagClick, selectedTags }: ExperienceTagsProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <Briefcase className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Experience Level</h3>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {experienceLevels.map((level) => {
          const isSelected = selectedTags.includes(level.query);
          return (
            <button
              key={level.name}
              onClick={() => onTagClick(level.query)}
              className={`
                inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium
                transition-all duration-200 transform hover:scale-105
                bg-amber-100 text-amber-700 hover:bg-amber-200 
                dark:bg-amber-900/30 dark:text-amber-400 dark:hover:bg-amber-900/50
                ${isSelected ? 'ring-2 ring-offset-2 ring-primary' : ''}
              `}
              title={`Search for ${level.name} candidates`}
            >
              <Briefcase className="h-3.5 w-3.5" />
              <span>{level.name}</span>
              <span className="text-xs opacity-75">({level.years})</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}