'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth/context';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { handleOAuthCallback } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for error parameters
        const error = searchParams.get('error');
        if (error) {
          const errorMessage = searchParams.get('message') || 'Authentication failed';
          setStatus('error');
          setMessage(errorMessage);
          
          // Redirect to login after 3 seconds
          setTimeout(() => {
            router.push('/login');
          }, 3000);
          return;
        }

        // Get token from URL parameters
        const accessToken = searchParams.get('access_token');
        const tokenType = searchParams.get('token_type');
        const email = searchParams.get('email');
        const name = searchParams.get('name');

        if (!accessToken) {
          throw new Error('No access token received');
        }

        // Store the token using the auth context
        // The handleOAuthCallback method will store the token and fetch user data
        await handleOAuthCallback(accessToken);

        setStatus('success');
        setMessage(`Welcome back, ${name || email || 'user'}!`);

        // Redirect to dashboard after a short delay
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);

      } catch (error) {
        console.error('OAuth callback error:', error);
        setStatus('error');
        setMessage(error instanceof Error ? error.message : 'Authentication failed');
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, handleOAuthCallback, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center space-y-4">
            {status === 'processing' && (
              <>
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                <h2 className="text-xl font-semibold">Authenticating...</h2>
                <p className="text-gray-600 text-center">{message}</p>
              </>
            )}

            {status === 'success' && (
              <>
                <CheckCircle className="h-8 w-8 text-green-600" />
                <h2 className="text-xl font-semibold">Success!</h2>
                <p className="text-gray-600 text-center">{message}</p>
                <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
              </>
            )}

            {status === 'error' && (
              <>
                <AlertCircle className="h-8 w-8 text-red-600" />
                <h2 className="text-xl font-semibold">Authentication Failed</h2>
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{message}</AlertDescription>
                </Alert>
                <p className="text-sm text-gray-500">Redirecting to login...</p>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}