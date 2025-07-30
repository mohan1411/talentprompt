'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth/context';
import { User, Mail, Calendar, Shield, Key, Chrome, Copy, Check, RefreshCw, ExternalLink, Loader2, Building2, Briefcase, Phone, Save } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { authApi } from '@/lib/api/client';
import Link from 'next/link';
import { useToast } from '@/components/ui/use-toast';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const { toast } = useToast();
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [extensionToken, setExtensionToken] = useState<string | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<any>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    company: '',
    job_title: '',
    phone: ''
  });
  
  useEffect(() => {
    checkTokenStatus();
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        company: user.company || '',
        job_title: user.job_title || '',
        phone: user.phone || ''
      });
    }
  }, [user]);
  
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

  const handleSaveProfile = async () => {
    setIsSaving(true);
    console.log('Saving profile with data:', formData);
    
    try {
      // Check if we have a token
      const token = localStorage.getItem('access_token');
      console.log('Token exists:', !!token);
      
      // Use authApi to update user profile
      const response = await authApi.updateMe(formData);
      console.log('Update response:', response);

      await refreshUser();
      setIsEditing(false);
      toast({
        title: 'Success',
        description: 'Your profile has been updated successfully'
      });
    } catch (error: any) {
      console.error('Error updating profile:', error);
      console.error('Error details:', {
        status: error.status,
        detail: error.detail,
        message: error.message
      });
      
      let errorMessage = 'Failed to update profile';
      
      if (error.status === 401) {
        errorMessage = 'Authentication error. Please log in again.';
      } else if (error.detail) {
        errorMessage = error.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive'
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Profile Settings</h1>

      {/* Profile Information Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold flex items-center">
            <User className="mr-2 h-5 w-5" />
            Profile Information
          </h2>
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm text-primary hover:underline"
            >
              Edit Profile
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setIsEditing(false);
                  setFormData({
                    full_name: user?.full_name || '',
                    company: user?.company || '',
                    job_title: user?.job_title || '',
                    phone: user?.phone || ''
                  });
                }}
                className="text-sm text-gray-600 hover:underline"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveProfile}
                disabled={isSaving}
                className="text-sm bg-primary text-white px-3 py-1 rounded hover:bg-primary/90 flex items-center"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                    Saving
                  </>
                ) : (
                  <>
                    <Save className="mr-1 h-3 w-3" />
                    Save
                  </>
                )}
              </button>
            </div>
          )}
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Full Name</label>
            {isEditing ? (
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-700"
                placeholder="John Doe"
              />
            ) : (
              <p className="mt-1 text-gray-900 dark:text-white">{user?.full_name || 'Not provided'}</p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center">
              <Building2 className="mr-1 h-4 w-4" />
              Company
            </label>
            {isEditing ? (
              <>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-700"
                  placeholder="Acme Inc."
                />
                <p className="mt-1 text-xs text-gray-500">
                  This will show as "from [Company Name]" in invitation emails
                </p>
              </>
            ) : (
              <p className="mt-1 text-gray-900 dark:text-white">{user?.company || 'Not provided'}</p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center">
              <Briefcase className="mr-1 h-4 w-4" />
              Job Title
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.job_title}
                onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-700"
                placeholder="Senior Recruiter"
              />
            ) : (
              <p className="mt-1 text-gray-900 dark:text-white">{user?.job_title || 'Not provided'}</p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center">
              <Phone className="mr-1 h-4 w-4" />
              Phone Number
            </label>
            {isEditing ? (
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-700"
                placeholder="+1 (555) 123-4567"
              />
            ) : (
              <p className="mt-1 text-gray-900 dark:text-white">{user?.phone || 'Not provided'}</p>
            )}
          </div>

          <div className="pt-4 border-t space-y-4">
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