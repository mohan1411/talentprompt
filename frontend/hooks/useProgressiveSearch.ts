import { useState, useCallback, useRef } from 'react';
import { apiClient } from '@/lib/api/client';
import { config } from '@/lib/config';

export interface SkillAnalysis {
  matched: string[];
  missing: string[];
  additional: string[];
  match_percentage: number;
}

export interface SearchResult {
  id: string;
  first_name: string;
  last_name: string;
  current_title?: string;
  location?: string;
  years_experience?: number;
  skills: string[];
  score: number;
  match_explanation?: string;
  skill_analysis?: SkillAnalysis;
  key_strengths?: string[];
  potential_concerns?: string[];
  interview_focus?: string[];
  overall_fit?: string;
  hiring_recommendation?: string;
}

export interface ProgressiveSearchState {
  stage: 'idle' | 'instant' | 'enhanced' | 'intelligent' | 'complete' | 'error';
  stageNumber: number;
  totalStages: number;
  results: SearchResult[];
  isLoading: boolean;
  error: string | null;
  timing: {
    instant?: number;
    enhanced?: number;
    intelligent?: number;
    total?: number;
  };
  searchId?: string;
  queryAnalysis?: {
    primary_skills: string[];
    secondary_skills: string[];
    implied_skills: string[];
    experience_level: string;
    role_type: string;
    search_intent: string;
  };
  suggestions?: string[];
}

export function useProgressiveSearch() {
  const [state, setState] = useState<ProgressiveSearchState>({
    stage: 'idle',
    stageNumber: 0,
    totalStages: 3,
    results: [],
    isLoading: false,
    error: null,
    timing: {},
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const startTimeRef = useRef<number>(0);

  const search = useCallback(async (query: string, limit: number = 10) => {
    // Clean up any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // Reset state
    setState({
      stage: 'idle',
      stageNumber: 0,
      totalStages: 3,
      results: [],
      isLoading: true,
      error: null,
      timing: {},
    });

    startTimeRef.current = Date.now();

    try {
      // First, analyze the query
      // The endpoint expects query as a query parameter, not in the body
      const analysisUrl = `/search/analyze-query?query=${encodeURIComponent(query)}`;
      const analysisResponse = await apiClient.post(analysisUrl, {});
      
      const queryAnalysis = analysisResponse.analysis;
      const suggestions = analysisResponse.suggestions || [];
      
      setState(prev => ({
        ...prev,
        queryAnalysis,
        suggestions,
      }));

      // Create EventSource for progressive search
      const token = localStorage.getItem('access_token');
      
      // For EventSource, we'll pass the token as a query parameter since headers aren't supported
      const params = new URLSearchParams({
        query,
        limit: limit.toString(),
      });
      
      // Add token to params for authentication
      if (token) {
        params.append('token', token);
      }
      
      // Note: In production, you'd want to use a more secure method
      // EventSource doesn't support headers, so we'd need to modify the backend
      // to accept tokens via query params or use a different approach
      const eventSource = new EventSource(
        `${config.apiUrl}/api/v1/search/progressive?${params.toString()}`,
        { withCredentials: true }
      );

      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.event === 'complete') {
          setState(prev => ({
            ...prev,
            stage: 'complete',
            isLoading: false,
            timing: {
              ...prev.timing,
              total: Date.now() - startTimeRef.current,
            },
          }));
          eventSource.close();
          eventSourceRef.current = null;
          return;
        }

        if (data.event === 'error') {
          setState(prev => ({
            ...prev,
            stage: 'error',
            error: data.message,
            isLoading: false,
          }));
          eventSource.close();
          eventSourceRef.current = null;
          return;
        }

        // Update state with new results
        setState(prev => ({
          ...prev,
          stage: data.stage as ProgressiveSearchState['stage'],
          stageNumber: data.stage_number,
          totalStages: data.total_stages,
          results: data.results,
          searchId: data.search_id,
          timing: {
            ...prev.timing,
            [data.stage]: data.timing_ms,
          },
        }));
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        setState(prev => ({
          ...prev,
          stage: 'error',
          error: 'Connection lost. Please try again.',
          isLoading: false,
        }));
        eventSource.close();
        eventSourceRef.current = null;
      };

    } catch (error) {
      console.error('Search error:', error);
      setState(prev => ({
        ...prev,
        stage: 'error',
        error: error instanceof Error ? error.message : 'Search failed',
        isLoading: false,
      }));
    }
  }, []);

  const cancel = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isLoading: false,
    }));
  }, []);

  return {
    ...state,
    search,
    cancel,
  };
}

// Alternative WebSocket implementation
export function useProgressiveSearchWS() {
  const [state, setState] = useState<ProgressiveSearchState>({
    stage: 'idle',
    stageNumber: 0,
    totalStages: 3,
    results: [],
    isLoading: false,
    error: null,
    timing: {},
  });

  const wsRef = useRef<WebSocket | null>(null);
  const startTimeRef = useRef<number>(0);

  const search = useCallback(async (query: string, limit: number = 10) => {
    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Reset state
    setState({
      stage: 'idle',
      stageNumber: 0,
      totalStages: 3,
      results: [],
      isLoading: true,
      error: null,
      timing: {},
    });

    startTimeRef.current = Date.now();

    try {
      const token = localStorage.getItem('access_token');
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
      const ws = new WebSocket(`${wsUrl}/api/v1/search/progressive/ws`);
      
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({
          query,
          limit,
          token,
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.event === 'complete') {
          setState(prev => ({
            ...prev,
            stage: 'complete',
            isLoading: false,
            timing: {
              ...prev.timing,
              total: Date.now() - startTimeRef.current,
            },
          }));
          ws.close();
          wsRef.current = null;
          return;
        }

        if (data.event === 'error') {
          setState(prev => ({
            ...prev,
            stage: 'error',
            error: data.message,
            isLoading: false,
          }));
          ws.close();
          wsRef.current = null;
          return;
        }

        // Update state with new results
        setState(prev => ({
          ...prev,
          stage: data.stage as ProgressiveSearchState['stage'],
          stageNumber: data.stage_number,
          totalStages: data.total_stages,
          results: data.results,
          searchId: data.search_id,
          timing: {
            ...prev.timing,
            [data.stage]: data.timing_ms,
          },
        }));
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({
          ...prev,
          stage: 'error',
          error: 'Connection failed. Please try again.',
          isLoading: false,
        }));
      };

      ws.onclose = () => {
        wsRef.current = null;
      };

    } catch (error) {
      console.error('Search error:', error);
      setState(prev => ({
        ...prev,
        stage: 'error',
        error: error instanceof Error ? error.message : 'Search failed',
        isLoading: false,
      }));
    }
  }, []);

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isLoading: false,
    }));
  }, []);

  return {
    ...state,
    search,
    cancel,
  };
}