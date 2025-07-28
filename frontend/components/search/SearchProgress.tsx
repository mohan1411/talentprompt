'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  const [particles, setParticles] = useState<Array<{ id: number; delay: number }>>([]);
  
  useEffect(() => {
    // Generate particles for the flow animation
    const newParticles = Array.from({ length: 3 }, (_, i) => ({
      id: Math.random(),
      delay: i * 0.8,
    }));
    setParticles(newParticles);
  }, [stage]);

  if (stage === 'idle' || stage === 'error') return null;

  const currentStageIndex = stages.findIndex(s => s.id === stage);
  const isComplete = stage === 'complete';

  return (
    <div className="mb-6">
      {/* Progress Bar */}
      <div className="relative" style={{ minHeight: '100px' }}>
        {/* Connecting lines layer */}
        <div className="absolute inset-0" style={{ top: '20px' }}>
          {/* Background guide lines */}
          <svg className="absolute inset-0 w-full h-full" style={{ height: '2px' }}>
            <line x1="16.67%" y1="1" x2="50%" y2="1" stroke="currentColor" strokeWidth="2" className="text-gray-200 dark:text-gray-700" opacity="0.3" />
            <line x1="50%" y1="1" x2="83.33%" y2="1" stroke="currentColor" strokeWidth="2" className="text-gray-200 dark:text-gray-700" opacity="0.3" />
          </svg>
          
          {/* Animated lines */}
          {currentStageIndex >= 0 && (
            <svg className="absolute inset-0 w-full h-full" style={{ height: '2px' }}>
              <motion.line 
                x1="16.67%" 
                y1="1" 
                x2="50%" 
                y2="1" 
                stroke="url(#gradient1)" 
                strokeWidth="2"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.5, ease: "easeInOut" }}
              />
              <defs>
                <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#eab308" />
                  <stop offset="50%" stopColor="#facc15" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
            </svg>
          )}
          
          {currentStageIndex >= 1 && (
            <svg className="absolute inset-0 w-full h-full" style={{ height: '2px' }}>
              <motion.line 
                x1="50%" 
                y1="1" 
                x2="83.33%" 
                y2="1" 
                stroke="url(#gradient2)" 
                strokeWidth="2"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2, ease: "easeInOut" }}
              />
              <defs>
                <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="50%" stopColor="#60a5fa" />
                  <stop offset="100%" stopColor="#a855f7" />
                </linearGradient>
              </defs>
            </svg>
          )}
          
          {/* Flowing particles */}
          {currentStageIndex === 0 && !isComplete && (
            <div className="absolute" style={{ left: '16.67%', width: '33.33%', height: '2px' }}>
              {particles.map((particle) => (
                <motion.div
                  key={particle.id}
                  className="absolute w-2 h-2 bg-gradient-to-r from-yellow-400 to-blue-400 rounded-full"
                  initial={{ left: '0%', opacity: 0 }}
                  animate={{
                    left: ['0%', '100%'],
                    opacity: [0, 1, 1, 0],
                  }}
                  transition={{
                    duration: 2,
                    delay: particle.delay,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                  style={{
                    top: '-3px',
                    boxShadow: '0 0 8px rgba(59, 130, 246, 0.6)',
                  }}
                />
              ))}
            </div>
          )}
          
          {currentStageIndex === 1 && !isComplete && (
            <div className="absolute" style={{ left: '50%', width: '33.33%', height: '2px' }}>
              {particles.map((particle) => (
                <motion.div
                  key={particle.id}
                  className="absolute w-2 h-2 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full"
                  initial={{ left: '0%', opacity: 0 }}
                  animate={{
                    left: ['0%', '100%'],
                    opacity: [0, 1, 1, 0],
                  }}
                  transition={{
                    duration: 2,
                    delay: particle.delay,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                  style={{
                    top: '-3px',
                    boxShadow: '0 0 8px rgba(168, 85, 247, 0.6)',
                  }}
                />
              ))}
            </div>
          )}
        </div>
        
        {/* Stage indicators */}
        <div className="flex items-center justify-between mb-2 relative z-10">
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
                  <AnimatePresence>
                    {isActive && !isComplete && (
                      <motion.div
                        className="absolute inset-0 rounded-full"
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        transition={{
                          duration: 1.5,
                          repeat: Infinity,
                          ease: "easeOut",
                        }}
                        style={{
                          background: `radial-gradient(circle, ${
                            idx === 0 ? 'rgba(234, 179, 8, 0.4)' :
                            idx === 1 ? 'rgba(59, 130, 246, 0.4)' :
                            'rgba(168, 85, 247, 0.4)'
                          } 0%, transparent 70%)`,
                        }}
                      />
                    )}
                  </AnimatePresence>
                  
                  <motion.div
                    className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 relative z-10",
                      isPast ? "bg-green-600 text-white" :
                      isActive ? `${stageInfo.bgColor} ${stageInfo.color}` :
                      "bg-gray-200 text-gray-400"
                    )}
                    animate={isActive ? {
                      boxShadow: [
                        '0 0 0 0 rgba(59, 130, 246, 0)',
                        '0 0 0 8px rgba(59, 130, 246, 0.2)',
                        '0 0 0 0 rgba(59, 130, 246, 0)',
                      ],
                    } : {}}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    {isPast && !isActive ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      <Icon className={cn(
                        "h-5 w-5",
                        isActive && "animate-pulse"
                      )} />
                    )}
                  </motion.div>
                  
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