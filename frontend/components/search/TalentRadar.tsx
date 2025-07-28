'use client';

import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Radar, Info, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

interface RadarCandidate {
  id: string;
  name: string;
  title: string;
  matchScore: number; // 0-1
  skillsGap: number; // 0-1 (0 = no gap, 1 = large gap)
  availability: number; // 0-1 (1 = highly available)
  learningVelocity: number; // 0-1 (1 = fast learner)
  experience: number; // years
  skills: string[];
}

interface TalentRadarProps {
  candidates: RadarCandidate[];
  onCandidateClick: (candidate: RadarCandidate) => void;
  isLoading?: boolean;
}

export default function TalentRadar({ candidates, onCandidateClick, isLoading }: TalentRadarProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<RadarCandidate | null>(null);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const animationRef = useRef<number>();

  useEffect(() => {
    if (!canvasRef.current || isLoading) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const centerX = canvas.offsetWidth / 2;
    const centerY = canvas.offsetHeight / 2;
    const maxRadius = Math.min(centerX, centerY) - 40;

    // Animation loop
    let animationTime = 0;
    const animate = () => {
      animationTime += 0.01;
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);
      
      // Apply zoom and rotation
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.scale(zoom, zoom);
      ctx.rotate(rotation * Math.PI / 180);
      ctx.translate(-centerX, -centerY);

      // Draw radar grid
      drawRadarGrid(ctx, centerX, centerY, maxRadius);
      
      // Draw candidates
      candidates.forEach((candidate, index) => {
        drawCandidate(ctx, candidate, centerX, centerY, maxRadius, animationTime + index * 0.5);
      });

      ctx.restore();

      // Draw labels (not affected by zoom/rotation)
      drawLabels(ctx, centerX, centerY, maxRadius);

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [candidates, zoom, rotation, isLoading]);

  const drawRadarGrid = (ctx: CanvasRenderingContext2D, centerX: number, centerY: number, maxRadius: number) => {
    // Draw concentric circles
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.1)';
    ctx.lineWidth = 1;
    
    for (let i = 1; i <= 4; i++) {
      ctx.beginPath();
      ctx.arc(centerX, centerY, (maxRadius * i) / 4, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Draw axes
    const axes = [
      { angle: 0, label: 'Match Score' },
      { angle: Math.PI / 2, label: 'Experience' },
      { angle: Math.PI, label: 'Availability' },
      { angle: (3 * Math.PI) / 2, label: 'Learning Speed' }
    ];

    ctx.strokeStyle = 'rgba(59, 130, 246, 0.2)';
    axes.forEach(axis => {
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + Math.cos(axis.angle) * maxRadius,
        centerY + Math.sin(axis.angle) * maxRadius
      );
      ctx.stroke();
    });
  };

  const drawLabels = (ctx: CanvasRenderingContext2D, centerX: number, centerY: number, maxRadius: number) => {
    ctx.font = '12px sans-serif';
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Axis labels
    ctx.fillText('High Match', centerX + maxRadius + 20, centerY);
    ctx.fillText('Senior', centerX, centerY + maxRadius + 20);
    ctx.fillText('Available', centerX - maxRadius - 20, centerY);
    ctx.fillText('Fast Learner', centerX, centerY - maxRadius - 20);
  };

  const drawCandidate = (
    ctx: CanvasRenderingContext2D, 
    candidate: RadarCandidate, 
    centerX: number, 
    centerY: number, 
    maxRadius: number,
    animationTime: number
  ) => {
    // Calculate position based on multiple dimensions
    const angle = (candidate.matchScore * Math.PI * 2) + (candidate.experience / 20) * Math.PI;
    const distance = (1 - candidate.skillsGap) * maxRadius * 0.9;
    
    // Add some animation
    const wobble = Math.sin(animationTime * candidate.learningVelocity) * 2;
    
    const x = centerX + Math.cos(angle) * distance + wobble;
    const y = centerY + Math.sin(angle) * distance + wobble;

    // Draw candidate dot
    const radius = 8 + candidate.matchScore * 12; // Size based on match score
    
    // Glow effect
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius * 2);
    const alpha = candidate.availability;
    
    // Color based on availability (green = available, orange = maybe, red = unlikely)
    const hue = candidate.availability * 120; // 0 = red, 120 = green
    gradient.addColorStop(0, `hsla(${hue}, 70%, 50%, ${alpha})`);
    gradient.addColorStop(0.5, `hsla(${hue}, 70%, 50%, ${alpha * 0.5})`);
    gradient.addColorStop(1, `hsla(${hue}, 70%, 50%, 0)`);
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, radius * 2, 0, Math.PI * 2);
    ctx.fill();

    // Draw main dot
    ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Draw border
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Pulse animation for high matches
    if (candidate.matchScore > 0.8) {
      ctx.strokeStyle = `hsla(${hue}, 70%, 50%, ${0.5 * (1 + Math.sin(animationTime * 3))})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(x, y, radius + 5 + Math.sin(animationTime * 3) * 3, 0, Math.PI * 2);
      ctx.stroke();
    }
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Find clicked candidate (simplified - in production would need proper hit detection)
    const clickedCandidate = candidates.find(candidate => {
      // Simple distance check - would need to account for actual positions
      return Math.random() > 0.5; // Placeholder
    });
    
    if (clickedCandidate) {
      setSelectedCandidate(clickedCandidate);
      onCandidateClick(clickedCandidate);
    }
  };

  return (
    <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Radar className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Smart Talent Radar</h3>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <button
            onClick={() => setZoom(Math.min(2, zoom + 0.1))}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={() => setRotation((rotation + 45) % 360)}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            title="Rotate"
          >
            <RotateCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="relative" style={{ height: '400px' }}>
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-pointer"
          onClick={handleCanvasClick}
          style={{ imageRendering: 'crisp-edges' }}
        />
        
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-800/80">
            <div className="text-center">
              <div className="h-8 w-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-sm text-gray-600 dark:text-gray-400">Analyzing talent pool...</p>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-gray-600 dark:text-gray-400">High Availability</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-500"></div>
          <span className="text-gray-600 dark:text-gray-400">Medium Availability</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-gray-600 dark:text-gray-400">Low Availability</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full border-2 border-blue-500"></div>
            <div className="w-3 h-3 rounded-full border-2 border-blue-500 -ml-1"></div>
          </div>
          <span className="text-gray-600 dark:text-gray-400">Size = Match Strength</span>
        </div>
      </div>

      {/* Info tooltip */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-blue-700 dark:text-blue-300">
            Candidates are positioned based on match score and experience. 
            Dot size indicates match strength, color shows availability, 
            and animation speed reflects learning velocity.
          </p>
        </div>
      </div>
    </div>
  );
}