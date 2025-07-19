import React, { useCallback } from 'react';
import { useAuth } from '@/lib/auth/context';

// Event types matching backend
export const EventType = {
  // Authentication
  USER_LOGIN: 'user_login',
  USER_LOGOUT: 'user_logout',
  USER_REGISTER: 'user_register',
  
  // Search
  SEARCH_PERFORMED: 'search_performed',
  SEARCH_RESULT_CLICKED: 'search_result_clicked',
  
  // Resume
  RESUME_UPLOADED: 'resume_uploaded',
  RESUME_VIEWED: 'resume_viewed',
  RESUME_DOWNLOADED: 'resume_downloaded',
  
  // LinkedIn
  LINKEDIN_PROFILE_IMPORTED: 'linkedin_profile_imported',
  LINKEDIN_BULK_IMPORT: 'linkedin_bulk_import',
  
  // Outreach
  OUTREACH_MESSAGE_GENERATED: 'outreach_message_generated',
  OUTREACH_MESSAGE_COPIED: 'outreach_message_copied',
  
  // Interview
  INTERVIEW_STARTED: 'interview_started',
  INTERVIEW_COMPLETED: 'interview_completed',
  
  // Feature Usage
  FEATURE_USED: 'feature_used',
  PAGE_VIEWED: 'page_viewed',
} as const;

export type EventTypeValue = typeof EventType[keyof typeof EventType];

interface TrackEventOptions {
  eventType: EventTypeValue;
  eventData?: Record<string, any>;
  waitForResponse?: boolean;
}

export function useAnalytics() {
  const { user } = useAuth();

  const trackEvent = useCallback(
    async ({ eventType, eventData, waitForResponse = false }: TrackEventOptions) => {
      try {
        // Don't track if no user (for now - could track anonymous events later)
        if (!user && !['page_viewed', 'user_register'].includes(eventType)) {
          return;
        }

        // In development, log to console
        if (process.env.NODE_ENV === 'development') {
          console.log('Analytics Event:', {
            eventType,
            eventData,
            userId: user?.id,
            timestamp: new Date().toISOString(),
          });
        }

        // For now, we're not sending to backend to keep it simple
        // When ready, uncomment this:
        /*
        const response = await fetch('/api/v1/analytics/track', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(user ? { Authorization: `Bearer ${user.token}` } : {}),
          },
          body: JSON.stringify({
            event_type: eventType,
            event_data: eventData,
          }),
        });

        if (!response.ok && waitForResponse) {
          throw new Error('Failed to track event');
        }
        */
      } catch (error) {
        // Don't let analytics errors break the app
        console.error('Analytics error:', error);
      }
    },
    [user]
  );

  const trackPageView = useCallback(
    (pageName: string, pageData?: Record<string, any>) => {
      trackEvent({
        eventType: EventType.PAGE_VIEWED,
        eventData: {
          page: pageName,
          ...pageData,
        },
      });
    },
    [trackEvent]
  );

  const trackSearch = useCallback(
    (query: string, resultCount: number) => {
      trackEvent({
        eventType: EventType.SEARCH_PERFORMED,
        eventData: {
          query,
          results_count: resultCount,
          has_results: resultCount > 0,
        },
      });
    },
    [trackEvent]
  );

  const trackFeature = useCallback(
    (featureName: string, featureData?: Record<string, any>) => {
      trackEvent({
        eventType: EventType.FEATURE_USED,
        eventData: {
          feature: featureName,
          ...featureData,
        },
      });
    },
    [trackEvent]
  );

  return {
    trackEvent,
    trackPageView,
    trackSearch,
    trackFeature,
  };
}

// HOC for tracking page views
export function withPageTracking<P extends object>(
  Component: React.ComponentType<P>,
  pageName: string
) {
  return function TrackedComponent(props: P) {
    const { trackPageView } = useAnalytics();

    React.useEffect(() => {
      trackPageView(pageName);
    }, [trackPageView]);

    return <Component {...props} />;
  };
}