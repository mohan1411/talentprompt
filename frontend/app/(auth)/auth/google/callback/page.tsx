'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/context';
import { oauthApi } from '@/lib/api/client';
import { Loader2 } from 'lucide-react';

function GoogleCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { handleOAuthCallback } = useAuth();
  const [error, setError] = useState('');
  const [isProcessing, setIsProcessing] = useState(true);
  const [hasProcessed, setHasProcessed] = useState(false);

  useEffect(() => {
    // Prevent double execution in React strict mode
    if (hasProcessed) return;
    
    const handleCallback = async () => {
      setHasProcessed(true);
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      if (error) {
        setError('Authentication was cancelled or failed. Please try again.');
        setIsProcessing(false);
        return;
      }

      if (!code || !state) {
        setError('Invalid callback parameters. Please try logging in again.');
        setIsProcessing(false);
        return;
      }

      // Verify state token
      const storedState = sessionStorage.getItem('oauth_state');
      if (state !== storedState) {
        setError('Security verification failed. Please try logging in again.');
        setIsProcessing(false);
        return;
      }

      try {
        // Exchange code for token using the new endpoint
        console.log('Exchanging OAuth code for token...');
        const response = await oauthApi.exchangeToken(code, 'google');
        console.log('Token exchange response:', response);
        
        // Clear state token
        sessionStorage.removeItem('oauth_state');
        
        // Handle the authentication
        console.log('Handling OAuth callback with token...');
        await handleOAuthCallback(response.access_token);
        console.log('OAuth callback handled successfully');
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError('Failed to complete authentication. Please try again.');
        setIsProcessing(false);
      }
    };

    handleCallback();
  }, [searchParams, handleOAuthCallback, hasProcessed]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full p-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 mb-4">
              <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Authentication Failed
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {error}
            </p>
            <button
              onClick={() => router.push('/login')}
              className="btn-primary"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Completing Sign In
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Please wait while we complete your Google sign in...
        </p>
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Loading...
          </h2>
        </div>
      </div>
    }>
      <GoogleCallbackContent />
    </Suspense>
  );
}