'use client';

import { useState } from 'react';

export default function TestApiPage() {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const testEndpoint = async (endpoint: string) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(
        `https://talentprompt-production.up.railway.app${endpoint}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const data = await response.text();
      
      setResult({
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        data: data,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const testLogin = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', 'test@example.com');
      formData.append('password', 'test123');

      const response = await fetch(
        'https://talentprompt-production.up.railway.app/api/v1/auth/login',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: formData.toString(),
        }
      );

      const data = await response.text();
      
      setResult({
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        data: data,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-8">API Test Page</h1>
      
      <div className="space-y-4 mb-8">
        <button
          onClick={() => testEndpoint('/')}
          className="btn-primary mr-4"
          disabled={loading}
        >
          Test Root Endpoint
        </button>
        
        <button
          onClick={() => testEndpoint('/api/v1/health')}
          className="btn-primary mr-4"
          disabled={loading}
        >
          Test Health Endpoint
        </button>
        
        <button
          onClick={() => testEndpoint('/api/v1/debug-system/env')}
          className="btn-primary mr-4"
          disabled={loading}
        >
          Test Debug Env
        </button>
        
        <button
          onClick={() => testEndpoint('/api/v1/debug-system/database')}
          className="btn-primary mr-4"
          disabled={loading}
        >
          Test Debug Database
        </button>
        
        <button
          onClick={testLogin}
          className="btn-primary"
          disabled={loading}
        >
          Test Login
        </button>
      </div>

      {loading && <p>Loading...</p>}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      {result && (
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-bold mb-2">Response:</h2>
          <p><strong>Status:</strong> {result.status} {result.statusText}</p>
          
          <h3 className="font-bold mt-4 mb-2">Headers:</h3>
          <pre className="bg-white p-2 rounded overflow-x-auto text-sm">
            {JSON.stringify(result.headers, null, 2)}
          </pre>
          
          <h3 className="font-bold mt-4 mb-2">Data:</h3>
          <pre className="bg-white p-2 rounded overflow-x-auto text-sm">
            {result.data}
          </pre>
        </div>
      )}
    </div>
  );
}