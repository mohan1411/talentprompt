/**
 * Authentication context for Promtitude
 */

'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authApi, oauthApi, User } from '@/lib/api/client';

interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  company?: string;
  job_title?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  loginWithOAuth: (provider: 'google' | 'linkedin') => Promise<void>;
  handleOAuthCallback: (token: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const router = useRouter();

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      setToken(storedToken);
      refreshUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      console.log('refreshUser: Fetching user data...');
      const userData = await authApi.getMe();
      console.log('refreshUser: User data received:', userData);
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login(username, password);
      const { access_token } = response;
      
      // Store token
      localStorage.setItem('access_token', access_token);
      setToken(access_token);
      
      // Fetch user data
      await refreshUser();
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      await authApi.register(data);
      // Auto-login after registration
      await login(data.username, data.password);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
    router.push('/');
  };

  const loginWithOAuth = async (provider: 'google' | 'linkedin') => {
    try {
      // Store current URL to redirect back after OAuth
      const currentUrl = window.location.pathname;
      sessionStorage.setItem('oauth_redirect', currentUrl);
      
      // Get OAuth URL based on provider
      const data = provider === 'google' 
        ? await oauthApi.initiateGoogleLogin()
        : await oauthApi.initiateLinkedInLogin();
      
      // Store state token for security
      sessionStorage.setItem('oauth_state', data.state);
      
      // Redirect to OAuth provider
      window.location.href = data.auth_url;
    } catch (error) {
      console.error('OAuth login failed:', error);
      throw error;
    }
  };
  
  const handleOAuthCallback = async (token: string) => {
    try {
      console.log('handleOAuthCallback: Storing token...');
      // Store token
      localStorage.setItem('access_token', token);
      setToken(token);
      
      console.log('handleOAuthCallback: Fetching user data...');
      // Fetch user data
      await refreshUser();
      
      // Get redirect URL from session storage
      const redirectUrl = sessionStorage.getItem('oauth_redirect') || '/dashboard';
      sessionStorage.removeItem('oauth_redirect');
      
      console.log('handleOAuthCallback: Redirecting to:', redirectUrl);
      // Small delay to ensure state is updated
      setTimeout(() => {
        router.push(redirectUrl);
      }, 100);
    } catch (error) {
      console.error('OAuth callback failed:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, refreshUser, loginWithOAuth, handleOAuthCallback }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}