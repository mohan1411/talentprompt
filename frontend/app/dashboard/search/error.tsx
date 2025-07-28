'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function SearchError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Search error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Search Error
        </h2>
        <p className="text-gray-600 mb-8">
          We encountered an error while searching. Please try again.
        </p>
        <Button
          onClick={reset}
          className="w-full sm:w-auto"
        >
          Try again
        </Button>
      </div>
    </div>
  );
}