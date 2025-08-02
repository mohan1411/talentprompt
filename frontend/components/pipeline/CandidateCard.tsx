'use client';

import { CandidateInPipeline } from '@/types/pipeline';
import { User, Clock, Tag } from 'lucide-react';

interface CandidateCardProps {
  candidate: CandidateInPipeline;
  onClick: () => void;
  stageColor: string;
}

export default function CandidateCard({ candidate, onClick, stageColor }: CandidateCardProps) {
  const formatTimeInStage = (seconds: number): string => {
    const days = Math.floor(seconds / (24 * 60 * 60));
    const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60));
    
    if (days > 0) {
      return `${days}d`;
    } else if (hours > 0) {
      return `${hours}h`;
    } else {
      const minutes = Math.floor(seconds / 60);
      return `${minutes}m`;
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded shadow-sm border border-gray-200 p-2 cursor-pointer hover:shadow-md transition-shadow"
      style={{ borderLeftWidth: '3px', borderLeftColor: stageColor }}
    >
      {/* Name and Title - Ultra compact */}
      <div className="mb-1.5">
        <h4 className="font-medium text-xs text-gray-900 truncate">
          {candidate.first_name} {candidate.last_name}
        </h4>
        {candidate.current_title && (
          <p className="text-xs text-gray-500 truncate" style={{ fontSize: '11px' }}>
            {candidate.current_title}
          </p>
        )}
      </div>

      {/* Ultra compact info section */}
      <div className="space-y-1" style={{ fontSize: '11px' }}>
        {/* Time and Assignee on same line */}
        <div className="flex items-center justify-between text-gray-500">
          <div className="flex items-center">
            <Clock className="w-3 h-3 mr-0.5" />
            <span>{formatTimeInStage(candidate.time_in_stage)}</span>
          </div>
          {candidate.assigned_to && (
            <div className="flex items-center">
              <User className="w-3 h-3 mr-0.5" />
              <span className="truncate max-w-[60px]">{candidate.assigned_to.name.split(' ')[0]}</span>
            </div>
          )}
        </div>

        {/* Tags - show only if present, very compact */}
        {candidate.tags.length > 0 && (
          <div className="flex items-center gap-0.5">
            <Tag className="w-3 h-3 text-gray-400" />
            <span className="text-gray-600 truncate">
              {candidate.tags[0]}{candidate.tags.length > 1 && ` +${candidate.tags.length - 1}`}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}