'use client';

import { Info } from 'lucide-react';

interface DataDisclaimerProps {
  hasData: boolean;
}

export default function DataDisclaimer({ hasData }: DataDisclaimerProps) {
  if (hasData) return null;

  return (
    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-start gap-3">
      <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
      <div className="text-sm text-blue-800 dark:text-blue-200">
        <p className="font-medium mb-1">Welcome to your AI-powered dashboard!</p>
        <p>
          The insights and visualizations will populate with real data as you upload resumes. 
          Start by uploading your first resume to see the magic happen.
        </p>
      </div>
    </div>
  );
}