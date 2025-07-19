'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { X, Cookie } from 'lucide-react';

export function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem('cookie-consent');
    if (!consent) {
      // Show banner after a short delay for better UX
      setTimeout(() => setShowBanner(true), 1000);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookie-consent', 'accepted');
    localStorage.setItem('cookie-consent-date', new Date().toISOString());
    closeBanner();
  };

  const handleDecline = () => {
    localStorage.setItem('cookie-consent', 'declined');
    localStorage.setItem('cookie-consent-date', new Date().toISOString());
    // Remove any non-essential cookies/storage here
    closeBanner();
  };

  const closeBanner = () => {
    setIsClosing(true);
    setTimeout(() => {
      setShowBanner(false);
      setIsClosing(false);
    }, 300);
  };

  if (!showBanner) return null;

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 z-50 p-4 transition-transform duration-300 ${
        isClosing ? 'translate-y-full' : 'translate-y-0'
      }`}
    >
      <div className="container mx-auto max-w-6xl">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <Cookie className="h-6 w-6 text-gray-600 dark:text-gray-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                We use cookies
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                We use cookies and similar technologies to provide you with a better experience, 
                improve performance, analyze traffic, and personalize content. By continuing to browse 
                this website, you agree to the use of cookies.{' '}
                <Link href="/privacy" className="text-primary hover:underline">
                  Learn more in our Privacy Policy
                </Link>
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleAccept}
                  className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors text-sm font-medium"
                >
                  Accept All
                </button>
                <button
                  onClick={handleDecline}
                  className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
                >
                  Decline Non-Essential
                </button>
                <Link
                  href="/privacy#cookies"
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-sm font-medium flex items-center"
                >
                  Cookie Settings
                </Link>
              </div>
            </div>
            <button
              onClick={closeBanner}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Close cookie banner"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}