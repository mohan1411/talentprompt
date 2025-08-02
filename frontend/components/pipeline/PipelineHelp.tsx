'use client';

import { InfoIcon } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function PipelineHelp() {
  return (
    <Alert className="mb-4 border-blue-200 bg-blue-50">
      <InfoIcon className="h-4 w-4 text-blue-600" />
      <AlertDescription>
        <div className="space-y-2">
          <p className="font-medium text-blue-900">Pipeline Stage Movement Guide</p>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 border-2 border-green-400 border-dashed rounded"></div>
              <span>Normal progression</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-100 border-2 border-yellow-400 border-dashed rounded"></div>
              <span>Unusual move (requires confirmation)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-100 border-2 border-red-400 border-dashed rounded"></div>
              <span>Extreme skip (strongly discouraged)</span>
            </div>
          </div>
          <p className="text-xs text-gray-600 mt-2">
            The system automatically moves candidates through stages based on interview outcomes. 
            Manual moves that skip stages or involve rejected/withdrawn candidates will show warnings.
            Red indicates critical actions like rejecting hired candidates or re-engaging rejected ones.
          </p>
        </div>
      </AlertDescription>
    </Alert>
  );
}