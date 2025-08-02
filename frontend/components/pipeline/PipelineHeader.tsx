'use client';

import { Pipeline } from '@/types/pipeline';
import { Settings, RefreshCw, Users, BarChart3, ChevronDown } from 'lucide-react';
import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';

interface PipelineHeaderProps {
  pipeline: Pipeline;
  pipelines: Pipeline[];
  candidateCount: number;
  onRefresh: () => void;
  onPipelineChange: (pipelineId: string) => void;
}

export default function PipelineHeader({ pipeline, pipelines, candidateCount, onRefresh, onPipelineChange }: PipelineHeaderProps) {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="bg-white border-b px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 text-2xl font-bold text-gray-900 hover:text-gray-700 transition-colors"
            >
              {pipeline.name}
              <ChevronDown className="w-5 h-5" />
            </button>
            
            {showDropdown && pipelines.length > 1 && (
              <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                {pipelines.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      onPipelineChange(p.id);
                      setShowDropdown(false);
                    }}
                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center justify-between ${
                      p.id === pipeline.id ? 'bg-blue-50 text-blue-600' : ''
                    }`}
                  >
                    <span>{p.name}</span>
                    {p.is_default && (
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">Default</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <p className="text-sm text-gray-600">
            {candidateCount} candidate{candidateCount !== 1 ? 's' : ''} in pipeline
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-5 h-5" />
          </button>

          <Link
            href={`/dashboard/pipeline/${pipeline.id}/analytics`}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Analytics"
          >
            <BarChart3 className="w-5 h-5" />
          </Link>

          <Link
            href="/dashboard/resumes"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Users className="w-4 h-4 mr-2" />
            Add Candidates
          </Link>

          <Link
            href="/dashboard/settings/pipelines"
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Pipeline Settings"
          >
            <Settings className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
}