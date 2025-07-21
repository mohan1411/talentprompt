'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth/context';
import { User, Mail, Calendar, Shield, Key } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function ProfilePage() {
  const { user } = useAuth();
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Profile Settings</h1>

      {/* Profile Information Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <User className="mr-2 h-5 w-5" />
          Profile Information
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Full Name</label>
            <p className="mt-1 text-gray-900 dark:text-white">{user?.full_name || 'Not provided'}</p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Username</label>
            <p className="mt-1 text-gray-900 dark:text-white">{user?.username}</p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center">
              <Mail className="mr-1 h-4 w-4" />
              Email Address
            </label>
            <p className="mt-1 text-gray-900 dark:text-white">{user?.email}</p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center">
              <Calendar className="mr-1 h-4 w-4" />
              Member Since
            </label>
            <p className="mt-1 text-gray-900 dark:text-white">
              {user?.created_at ? formatDistanceToNow(new Date(user.created_at), { addSuffix: true }) : 'Recently'}
            </p>
          </div>
        </div>
      </div>

      {/* Account Status Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Shield className="mr-2 h-5 w-5" />
          Account Status
        </h2>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Account Type</span>
            <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
              {user?.is_superuser ? 'Admin' : 'Standard User'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Account Status</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              user?.is_active 
                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' 
                : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
            }`}>
              {user?.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Email Verified</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              user?.is_verified 
                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' 
                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
            }`}>
              {user?.is_verified ? 'Verified' : 'Unverified'}
            </span>
          </div>
        </div>
      </div>

      {/* Security Settings Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Key className="mr-2 h-5 w-5" />
          Security Settings
        </h2>
        
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Keep your account secure by using a strong password and enabling additional security features.
            </p>
            
            {!isChangingPassword ? (
              <button
                onClick={() => setIsChangingPassword(true)}
                className="btn-secondary"
              >
                Change Password
              </button>
            ) : (
              <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Password change functionality coming soon...
                </p>
                <button
                  onClick={() => setIsChangingPassword(false)}
                  className="text-sm text-primary hover:underline"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          {/* OAuth Connections */}
          {user?.oauth_provider && (
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Connected Accounts</p>
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm capitalize">
                  {user.oauth_provider}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">connected</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}