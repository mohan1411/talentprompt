'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Mail, CheckCircle, ArrowRight, RefreshCw } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { authApi } from '@/lib/api/client';

function VerifyEmailPendingContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendError, setResendError] = useState('');

  const handleResendEmail = async () => {
    setIsResending(true);
    setResendError('');
    setResendSuccess(false);

    try {
      await authApi.resendVerification(email);
      setResendSuccess(true);
    } catch (error) {
      setResendError('Failed to resend verification email. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

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
          <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="h-10 w-10 text-blue-600 dark:text-blue-400" />
          </div>

          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Check your email
          </h1>

          <p className="text-gray-600 dark:text-gray-400 mb-6">
            We've sent a verification email to:
          </p>

          <p className="font-medium text-gray-900 dark:text-white mb-6 break-all">
            {email || 'your email address'}
          </p>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              Next steps:
            </h3>
            <ol className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li className="flex items-start gap-2">
                <span className="text-blue-600 dark:text-blue-400 font-medium">1.</span>
                Check your inbox for an email from Promtitude
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 dark:text-blue-400 font-medium">2.</span>
                Click the verification link in the email
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 dark:text-blue-400 font-medium">3.</span>
                You'll be ready to start using Promtitude!
              </li>
            </ol>
          </div>

          {resendSuccess ? (
            <div className="mb-6 p-3 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              <span className="text-sm">Verification email resent successfully!</span>
            </div>
          ) : resendError ? (
            <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm">
              {resendError}
            </div>
          ) : null}

          <div className="space-y-3">
            <button
              onClick={handleResendEmail}
              disabled={isResending || resendSuccess}
              className="w-full btn-secondary py-3 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isResending ? (
                <>
                  <RefreshCw className="h-5 w-5 animate-spin" />
                  Resending...
                </>
              ) : (
                <>
                  <Mail className="h-5 w-5" />
                  Resend verification email
                </>
              )}
            </button>

            <Link 
              href="/login"
              className="w-full btn-primary py-3 flex items-center justify-center gap-2"
            >
              Go to login
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Didn't receive the email? Check your spam folder or{' '}
              <Link href="/contact" className="text-primary hover:underline">
                contact support
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPendingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    }>
      <VerifyEmailPendingContent />
    </Suspense>
  );
}