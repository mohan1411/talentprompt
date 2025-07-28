'use client';

import { useEffect, useRef, useState } from 'react';
import { Radar, Maximize2, Users } from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';

interface Candidate {
  id: string;
  name: string;
  title: string;
  score: number;
  skills: string[];
}

interface TalentRadarPreviewProps {
  candidates: Candidate[];
}

export default function TalentRadarPreview({ candidates }: TalentRadarPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [hoveredCandidate, setHoveredCandidate] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    let rotation = 0;

    const drawRadar = () => {
      const width = canvas.offsetWidth;
      const height = canvas.offsetHeight;
      const centerX = width / 2;
      const centerY = height / 2;
      const maxRadius = Math.min(width, height) / 2 - 40;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Draw radar circles
      ctx.strokeStyle = 'rgba(107, 114, 128, 0.2)';
      ctx.lineWidth = 1;
      for (let i = 1; i <= 3; i++) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, (maxRadius * i) / 3, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Draw radar lines
      for (let i = 0; i < 6; i++) {
        const angle = (i * Math.PI * 2) / 6;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(
          centerX + Math.cos(angle) * maxRadius,
          centerY + Math.sin(angle) * maxRadius
        );
        ctx.stroke();
      }

      // Draw scanning line
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + Math.cos(rotation) * maxRadius,
        centerY + Math.sin(rotation) * maxRadius
      );
      ctx.stroke();

      // Draw candidates
      candidates.slice(0, 8).forEach((candidate, index) => {
        const angle = (index / 8) * Math.PI * 2 + rotation * 0.1;
        const distance = (candidate.score * 0.8 + 0.2) * maxRadius;
        const x = centerX + Math.cos(angle) * distance;
        const y = centerY + Math.sin(angle) * distance;

        // Candidate dot
        const isHovered = hoveredCandidate === candidate.id;
        const dotSize = isHovered ? 8 : 6;
        
        ctx.fillStyle = `hsl(${candidate.score * 120}, 70%, 50%)`;
        ctx.beginPath();
        ctx.arc(x, y, dotSize, 0, Math.PI * 2);
        ctx.fill();

        // Pulse effect
        if (isHovered) {
          ctx.strokeStyle = `hsla(${candidate.score * 120}, 70%, 50%, 0.3)`;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(x, y, dotSize + 4, 0, Math.PI * 2);
          ctx.stroke();
        }
      });

      // Update rotation
      rotation += 0.01;

      animationRef.current = requestAnimationFrame(drawRadar);
    };

    drawRadar();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [candidates, hoveredCandidate]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = canvas.offsetWidth / 2;
    const centerY = canvas.offsetHeight / 2;
    const maxRadius = Math.min(canvas.offsetWidth, canvas.offsetHeight) / 2 - 40;

    // Check if mouse is near any candidate
    let foundCandidate = null;
    candidates.slice(0, 8).forEach((candidate, index) => {
      const angle = (index / 8) * Math.PI * 2;
      const distance = (candidate.score * 0.8 + 0.2) * maxRadius;
      const candidateX = centerX + Math.cos(angle) * distance;
      const candidateY = centerY + Math.sin(angle) * distance;

      const dist = Math.sqrt((x - candidateX) ** 2 + (y - candidateY) ** 2);
      if (dist < 15) {
        foundCandidate = candidate.id;
      }
    });

    setHoveredCandidate(foundCandidate);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.2 }}
      className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 relative overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Radar className="h-5 w-5 text-primary" />
          Talent Radar
        </h3>
        <Link
          href="/dashboard/search/progressive"
          className="text-sm text-primary hover:underline flex items-center gap-1"
        >
          <Maximize2 className="h-3 w-3" />
          Full View
        </Link>
      </div>

      {/* Canvas */}
      <div className="relative h-64">
        {candidates.length > 0 ? (
          <>
            <canvas
              ref={canvasRef}
              className="w-full h-full cursor-pointer"
              onMouseMove={handleMouseMove}
              onMouseLeave={() => setHoveredCandidate(null)}
            />
            
            {/* Tooltip */}
            {hoveredCandidate && (
              <div className="absolute top-4 right-4 bg-gray-900 text-white px-3 py-2 rounded-lg text-sm">
                {candidates.find(c => c.id === hoveredCandidate)?.name}
              </div>
            )}
          </>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500 dark:text-gray-400">
                No candidates to display
              </p>
              <Link
                href="/dashboard/upload"
                className="text-sm text-primary hover:underline mt-2 inline-block"
              >
                Upload resumes to see radar
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      {candidates.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {candidates.length}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Total Candidates
            </p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">
              {candidates.filter(c => c.score > 0.8).length}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              High Matches
            </p>
          </div>
          <div>
            <p className="text-2xl font-bold text-blue-600">
              {Math.round(candidates.reduce((acc, c) => acc + c.score, 0) / candidates.length * 100)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Avg. Match
            </p>
          </div>
        </div>
      )}
    </motion.div>
  );
}