import { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Track analytics event
export const trackEvent = async (eventType, data = {}) => {
  try {
    const token = localStorage.getItem('azories-token');
    await axios.post(`${API}/api/analytics/track`, {
      event_type: eventType,
      page: data.page || window.location.pathname,
      book_id: data.bookId || null,
      metadata: data.metadata || {}
    }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
  } catch (error) {
    // Silently fail - analytics shouldn't break the app
    console.debug('Analytics tracking failed:', error.message);
  }
};

// Hook to automatically track page views
export const usePageTracking = () => {
  const location = useLocation();

  useEffect(() => {
    // Track page view on route change
    trackEvent('page_view', { page: location.pathname });
  }, [location.pathname]);
};

// Hook for manual event tracking
export const useAnalytics = () => {
  const trackPageView = useCallback((page) => {
    trackEvent('page_view', { page });
  }, []);

  const trackBookRead = useCallback((bookId) => {
    trackEvent('book_read', { bookId });
  }, []);

  const trackAIStoryCreate = useCallback((bookId, metadata = {}) => {
    trackEvent('ai_story_create', { bookId, metadata });
  }, []);

  const trackSignup = useCallback(() => {
    trackEvent('signup');
  }, []);

  const trackLogin = useCallback(() => {
    trackEvent('login');
  }, []);

  const trackPurchase = useCallback((amount, credits) => {
    trackEvent('credit_purchase', { metadata: { amount, credits } });
  }, []);

  const trackPrintPDF = useCallback((bookId) => {
    trackEvent('print_pdf', { bookId });
  }, []);

  return {
    trackPageView,
    trackBookRead,
    trackAIStoryCreate,
    trackSignup,
    trackLogin,
    trackPurchase,
    trackPrintPDF,
    trackEvent
  };
};

export default useAnalytics;
