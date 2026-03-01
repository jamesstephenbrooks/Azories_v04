import { useEffect, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Analytics queue management - prevents too many pending calls
const analyticsQueue = {
  pending: 0,
  maxPending: 10, // Max concurrent analytics calls
  
  canEnqueue() {
    return this.pending < this.maxPending;
  },
  
  increment() {
    this.pending++;
  },
  
  decrement() {
    this.pending = Math.max(0, this.pending - 1);
  }
};

// Fire-and-forget analytics tracking - NEVER blocks UI
export const trackEvent = (eventType, data = {}) => {
  // Drop if queue is full - don't block or slow down the app
  if (!analyticsQueue.canEnqueue()) {
    console.debug('[Analytics] Queue full, dropping event:', eventType);
    return;
  }
  
  // Use requestIdleCallback or setTimeout to avoid competing with book loading
  const scheduleTracking = window.requestIdleCallback || ((cb) => setTimeout(cb, 100));
  
  scheduleTracking(() => {
    // Double-check queue limit
    if (!analyticsQueue.canEnqueue()) return;
    
    analyticsQueue.increment();
    
    const token = localStorage.getItem('azories-token');
    
    // Create abort controller with 5s timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    // Fire and forget - no await, no blocking
    axios.post(`${API}/api/analytics/track`, {
      event_type: eventType,
      page: data.page || window.location.pathname,
      book_id: data.bookId || null,
      metadata: data.metadata || {}
    }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: controller.signal
    })
    .catch(() => {
      // Silently ignore ALL errors - analytics should never affect UX
    })
    .finally(() => {
      clearTimeout(timeoutId);
      analyticsQueue.decrement();
    });
  }, { timeout: 2000 }); // Max 2s delay before tracking fires
};

// Hook to automatically track page views
export const usePageTracking = () => {
  const location = useLocation();
  const lastTrackedPath = useRef(null);

  useEffect(() => {
    // Debounce - don't track the same path twice in quick succession
    if (lastTrackedPath.current === location.pathname) return;
    lastTrackedPath.current = location.pathname;
    
    // Track page view on route change - fire and forget
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
