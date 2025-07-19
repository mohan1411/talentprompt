'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Users, Search, Zap } from 'lucide-react';
import { useAuth } from '@/lib/auth/context';
import { Loader2 } from 'lucide-react';

interface AnalyticsStats {
  daily_active_users: Array<{ date: string; active_users: number }>;
  feature_usage: Record<string, number>;
  popular_searches: Array<{ query: string; count: number }>;
  api_performance: {
    total_requests: number;
    avg_response_time_ms: number;
    requests_per_hour: number;
    top_endpoints: Array<[string, number]>;
  };
  total_users: number;
  total_resumes: number;
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/v1/analytics/stats?days=30', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch analytics (${response.status})`);
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Analytics Dashboard</h1>
        <Card>
          <CardContent className="pt-6">
            <p className="text-red-500">Error loading analytics: {error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Prepare feature usage data for chart
  const featureData = Object.entries(stats.feature_usage).map(([feature, count]) => ({
    feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    count,
  }));

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">Monitor your platform usage and performance</p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_users}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Resumes</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_resumes}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Requests (24h)</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.api_performance.total_requests}</div>
            <p className="text-xs text-muted-foreground">
              Avg: {stats.api_performance.avg_response_time_ms}ms
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Requests/Hour</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.api_performance.requests_per_hour.toFixed(1)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Daily Active Users Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Active Users</CardTitle>
          <CardDescription>User activity over the last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.daily_active_users}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(date) => new Date(date).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(date) => new Date(date).toLocaleDateString()}
                formatter={(value) => [`${value} users`, 'Active Users']}
              />
              <Line 
                type="monotone" 
                dataKey="active_users" 
                stroke="#2563eb" 
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Feature Usage */}
        <Card>
          <CardHeader>
            <CardTitle>Feature Usage</CardTitle>
            <CardDescription>Most used features in the last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={featureData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="feature" type="category" width={150} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Popular Searches */}
        <Card>
          <CardHeader>
            <CardTitle>Popular Searches</CardTitle>
            <CardDescription>Top search queries in the last 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.popular_searches.map((search, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{search.query}</span>
                  </div>
                  <span className="text-sm font-medium">{search.count}</span>
                </div>
              ))}
              {stats.popular_searches.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No search data available yet
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top API Endpoints */}
      <Card>
        <CardHeader>
          <CardTitle>Top API Endpoints</CardTitle>
          <CardDescription>Most frequently accessed endpoints in the last 24 hours</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {stats.api_performance.top_endpoints.map(([endpoint, count], index) => (
              <div key={index} className="flex items-center justify-between">
                <code className="text-sm bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                  {endpoint}
                </code>
                <span className="text-sm font-medium">{count} requests</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}