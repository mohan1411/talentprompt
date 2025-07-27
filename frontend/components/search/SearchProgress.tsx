'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Search, Brain, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchProgressProps {
  stage: 'idle' | 'instant' | 'enhanced' | 'intelligent' | 'complete' | 'error';
  stageNumber: number;
  totalStages: number;
  timing: {
    instant?: number;
    enhanced?: number;
    intelligent?: number;
  };
}

const stages = [
  {
    id: 'instant',
    name: 'Instant Results',
    icon: Zap,
    description: 'Quick matches from cache',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
  },
  {
    id: 'enhanced',
    name: 'Enhanced Search',
    icon: Search,
    description: 'Deep vector analysis',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  {
    id: 'intelligent',
    name: 'AI Insights',
    icon: Brain,
    description: 'Understanding matches',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
  },
];

export default function SearchProgress({ 
  stage, 
  stageNumber, 
  timing 
}: SearchProgressProps) {
  if (stage === 'idle' || stage === 'error') return null;

  const currentStageIndex = stages.findIndex(s => s.id === stage);
  const isComplete = stage === 'complete';

  return (
    <div className="mb-6">
      {/* Progress Bar */}
      <div className="relative">
        <div className="flex items-center justify-between mb-2">
          {stages.map((stageInfo, idx) => {
            const isActive = idx === currentStageIndex;
            const isPast = isComplete || idx < currentStageIndex;
            const Icon = stageInfo.icon;

            return (
              <motion.div
                key={stageInfo.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.1 }}
                className="flex-1 flex flex-col items-center"
              >
                <div className="relative">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300",
                      isPast ? "bg-green-600 text-white" :
                      isActive ? `${stageInfo.bgColor} ${stageInfo.color}` :
                      "bg-gray-200 text-gray-400"
                    )}
                  >
                    {isPast && !isActive ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      <Icon className={cn(
                        "h-5 w-5",
                        isActive && "animate-pulse"
                      )} />
                    )}
                  </div>
                  
                  {/* Timing Badge */}
                  {timing[stageInfo.id as keyof typeof timing] && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-600 whitespace-nowrap"
                    >
                      {timing[stageInfo.id as keyof typeof timing]}ms
                    </motion.div>
                  )}
                </div>
                
                <p className={cn(
                  "text-xs mt-2 font-medium transition-colors duration-300",
                  isPast || isActive ? "text-gray-700" : "text-gray-400"
                )}>
                  {stageInfo.name}
                </p>
                
                {isActive && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-xs text-gray-500 mt-1"
                  >
                    {stageInfo.description}
                  </motion.p>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Progress Line */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200 -z-10">
          <motion.div
            className="h-full bg-gradient-to-r from-green-600 to-blue-600"
            initial={{ width: '0%' }}
            animate={{ 
              width: isComplete ? '100%' : `${(currentStageIndex + 1) / stages.length * 100}%` 
            }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>

      {/* Stage Message */}
      {!isComplete && currentStageIndex >= 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 text-center"
        >
          <p className="text-sm text-gray-600">
            {currentStageIndex === 0 && "Finding quick matches..."}
            {currentStageIndex === 1 && "Analyzing deep connections..."}
            {currentStageIndex === 2 && "Understanding why they match..."}
          </p>
        </motion.div>
      )}

      {/* Completion Message */}
      {isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 text-center"
        >
          <p className="text-sm text-green-600 font-medium">
            Search complete in {Object.values(timing).reduce((a, b) => a + b, 0)}ms
          </p>
        </motion.div>
      )}
    </div>
  );
}