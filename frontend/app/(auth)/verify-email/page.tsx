'use client';

import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useSearchParams, useRouter } from 'next/navigation';
import { CheckCircle, XCircle, Loader, ArrowRight } from 'lucide-react';
import { authApi } from '@/lib/api/client';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  
  const [isVerifying, setIsVerifying] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setError('No verification token provided');
      setIsVerifying(false);
      return;
    }

    const verifyEmail = async () => {
      try {
        await authApi.verifyEmail(token);
        setIsSuccess(true);
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push('/login?verified=true');
        }, 3000);
      } catch (error) {
        setError('Invalid or expired verification token');
      } finally {
        setIsVerifying(false);
      }
    };

    verifyEmail();
  }, [token, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full text-center">
        <Link href="/" className="inline-block mb-8">
          <Image 
            src="/logo-promtitude.svg" 
            alt="Promtitude" 
            width={180} 
            height={40}
            className="h-10 w-auto mx-auto"
            priority
          />
        </Link>

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          {isVerifying ? (
            <>
              <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-6">
                <Loader className="h-10 w-10 text-blue-600 dark:text-blue-400 animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Verifying your email...
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Please wait while we verify your email address.
              </p>
            </>
          ) : isSuccess ? (
            <>
              <div className="w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="h-10 w-10 text-green-600 dark:text-green-400" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Email verified successfully!
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Your email has been verified. You'll be redirected to login in a few seconds...
              </p>
              <Link 
                href="/login"
                className="inline-flex items-center gap-2 text-primary hover:underline"
              >
                Go to login now
                <ArrowRight className="h-4 w-4" />
              </Link>
            </>
          ) : (
            <>
              <div className="w-20 h-20 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mx-auto mb-6">
                <XCircle className="h-10 w-10 text-red-600 dark:text-red-400" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Verification failed
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {error || 'Something went wrong during verification.'}
              </p>
              <div className="space-y-3">
                <Link 
                  href="/register"
                  className="w-full btn-primary py-3 flex items-center justify-center gap-2"
                >
                  Back to registration
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link 
                  href="/contact"
                  className="w-full btn-secondary py-3"
                >
                  Contact support
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}