'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/context';
import { useEffect } from 'react';
import { ArrowLeft, Settings, User, Key, Bell, Shield, CreditCard } from 'lucide-react';

export default function SettingsPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isLoading && !user) {
      router.push('/login?redirect=/settings');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Link
            href="/dashboard"
            className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-primary mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Dashboard
          </Link>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Settings className="h-8 w-8" />
            Settings
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your account settings and preferences
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {/* Profile Settings */}
            <Link href="/settings/profile" className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <User className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Profile</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Update your personal information</p>
                  </div>
                </div>
                <ArrowLeft className="h-5 w-5 text-gray-400 rotate-180" />
              </div>
            </Link>

            {/* Security Settings */}
            <Link href="/settings/security" className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <Key className="h-6 w-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Security</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Manage passwords and security settings</p>
                  </div>
                </div>
                <ArrowLeft className="h-5 w-5 text-gray-400 rotate-180" />
              </div>
            </Link>

            {/* Notification Settings */}
            <Link href="/settings/notifications" className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <Bell className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Notifications</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Configure email and app notifications</p>
                  </div>
                </div>
                <ArrowLeft className="h-5 w-5 text-gray-400 rotate-180" />
              </div>
            </Link>

            {/* Privacy Settings */}
            <Link href="/settings/privacy" className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                    <Shield className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Privacy</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Control your data and privacy preferences</p>
                  </div>
                </div>
                <ArrowLeft className="h-5 w-5 text-gray-400 rotate-180" />
              </div>
            </Link>

            {/* Billing Settings */}
            <Link href="/settings/billing" className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-lg">
                    <CreditCard className="h-6 w-6 text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Billing</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Manage subscription and payment methods</p>
                  </div>
                </div>
                <ArrowLeft className="h-5 w-5 text-gray-400 rotate-180" />
              </div>
            </Link>
          </div>
        </div>

        {/* Chrome Extension Section */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Chrome Extension</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            You're using the Promtitude Chrome Extension. Here you can manage your extension settings.
          </p>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700 dark:text-gray-300">Extension Version</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">1.1.1</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700 dark:text-gray-300">Status</span>
              <span className="text-sm font-medium text-green-600 dark:text-green-400">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}