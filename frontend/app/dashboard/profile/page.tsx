'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth/context';
import { User, Mail, Calendar, Shield, Key, Chrome, Copy, Check, RefreshCw, ExternalLink, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { authApi } from '@/lib/api/client';
import Link from 'next/link';

export default function ProfilePage() {
  const { user } = useAuth();
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [extensionToken, setExtensionToken] = useState<string | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<any>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);
  
  useEffect(() => {
    checkTokenStatus();
  }, []);
  
  const checkTokenStatus = async () => {
    try {
      const status = await authApi.getExtensionTokenStatus();
      setTokenStatus(status);
    } catch (err) {
      console.error('Failed to check token status:', err);
    }
  };
  
  const generateToken = async () => {
    setIsGeneratingToken(true);
    setTokenError(null);
    
    try {
      const response = await authApi.generateExtensionToken();
      setExtensionToken(response.access_token);
      await checkTokenStatus();
    } catch (err: any) {
      setTokenError(err.detail || 'Failed to generate access token');
    } finally {
      setIsGeneratingToken(false);
    }
  };
  
  const copyToClipboard = async () => {
    if (!extensionToken) return;
    
    try {
      await navigator.clipboard.writeText(extensionToken);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

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

        </div>
      </div>

      {/* Chrome Extension Settings Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mt-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Chrome className="mr-2 h-5 w-5" />
          Chrome Extension
        </h2>
        
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {tokenStatus?.is_oauth_user
              ? 'As a Google/LinkedIn user, you need an access code to log into the Chrome extension.'
              : 'You can log into the Chrome extension using your email and password.'}
          </p>
          
          {tokenStatus?.is_oauth_user && (
            <>
              {tokenError && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-400 rounded-lg text-sm">
                  {tokenError}
                </div>
              )}
              
              {extensionToken ? (
                <div className="space-y-4">
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Your access code:</p>
                    <div className="flex items-center gap-2">
                      <code className="text-xl font-mono font-bold flex-1">
                        {extensionToken}
                      </code>
                      <button
                        onClick={copyToClipboard}
                        className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                        title="Copy to clipboard"
                      >
                        {isCopied ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400 rounded-lg text-sm">
                    <strong>Instructions:</strong> Use this code as your password when logging into the Chrome extension with your email.
                  </div>
                </div>
              ) : (
                <button
                  onClick={generateToken}
                  disabled={isGeneratingToken}
                  className="btn-primary flex items-center"
                >
                  {isGeneratingToken ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Generate Access Code
                    </>
                  )}
                </button>
              )}
            </>
          )}
          
          <div className="pt-4 border-t">
            <Link
              href="/extension-auth"
              className="text-sm text-primary hover:underline inline-flex items-center"
            >
              Go to Extension Auth Page
              <ExternalLink className="ml-1 h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}