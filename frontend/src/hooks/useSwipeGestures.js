import { useRef, useEffect, useCallback } from 'react';

// Hook for swipe gesture detection
export function useSwipeGestures({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  enabled = true,
  ignoreScrollableElements = true  // New option to ignore swipes that start in scrollable areas
}) {
  const touchStartRef = useRef({ x: 0, y: 0 });
  const touchEndRef = useRef({ x: 0, y: 0 });
  const isScrollingRef = useRef(false);
  const startedInScrollableRef = useRef(false);
  const touchMovedRef = useRef(false); // Track if any movement occurred

  // Check if an element or its parents are scrollable
  const isInScrollableElement = useCallback((element) => {
    let current = element;
    while (current && current !== document.body) {
      const style = window.getComputedStyle(current);
      const overflowY = style.overflowY;
      const overflowX = style.overflowX;
      
      // Check if element has scrollable content
      if ((overflowY === 'auto' || overflowY === 'scroll') && current.scrollHeight > current.clientHeight) {
        return { element: current, direction: 'vertical', canScroll: true };
      }
      if ((overflowX === 'auto' || overflowX === 'scroll') && current.scrollWidth > current.clientWidth) {
        return { element: current, direction: 'horizontal', canScroll: true };
      }
      
      // Also check for explicit scroll classes or data attributes (for text containers)
      if (current.dataset?.scrollable === 'true' || 
          current.classList?.contains('overflow-y-auto') ||
          current.classList?.contains('overflow-y-scroll') ||
          current.classList?.contains('text-scroll-container')) {
        return { element: current, direction: 'vertical', canScroll: current.scrollHeight > current.clientHeight };
      }
      
      current = current.parentElement;
    }
    return null;
  }, []);

  const handleTouchStart = useCallback((e) => {
    touchStartRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
    touchEndRef.current = { x: 0, y: 0 };
    isScrollingRef.current = false;
    touchMovedRef.current = false;
    
    // Check if touch started in a scrollable element
    if (ignoreScrollableElements) {
      const scrollable = isInScrollableElement(e.target);
      startedInScrollableRef.current = scrollable;
      
      // If started in a scrollable vertical container, immediately mark as potential scroll
      // This is crucial for iPad where scroll detection needs to be more aggressive
      if (scrollable && scrollable.direction === 'vertical' && scrollable.canScroll) {
        isScrollingRef.current = true; // Assume scrolling until proven otherwise
      }
    } else {
      startedInScrollableRef.current = null;
    }
  }, [ignoreScrollableElements, isInScrollableElement]);

  const handleTouchMove = useCallback((e) => {
    touchMovedRef.current = true;
    touchEndRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
    
    // If we started in a scrollable element, check movement direction
    if (startedInScrollableRef.current) {
      const deltaY = Math.abs(touchEndRef.current.y - touchStartRef.current.y);
      const deltaX = Math.abs(touchEndRef.current.x - touchStartRef.current.x);
      
      // CRITICAL FIX FOR IPAD: If ANY vertical movement is detected in a vertical 
      // scrollable area, block horizontal swipe gestures completely
      // This prevents page turns when trying to scroll text
      if (startedInScrollableRef.current.direction === 'vertical') {
        // If vertical movement is non-trivial, mark as scrolling
        if (deltaY > 5) {
          isScrollingRef.current = true;
        }
        // Only allow horizontal swipe if it's VERY dominant (3x more than vertical)
        // and started with clear horizontal intent
        if (deltaY > 0 && deltaX < deltaY * 3) {
          isScrollingRef.current = true;
        }
      }
    }
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (!enabled) return;

    // If no movement occurred, reset and exit
    if (!touchMovedRef.current) {
      touchStartRef.current = { x: 0, y: 0 };
      touchEndRef.current = { x: 0, y: 0 };
      isScrollingRef.current = false;
      startedInScrollableRef.current = null;
      return;
    }

    const deltaX = touchEndRef.current.x - touchStartRef.current.x;
    const deltaY = touchEndRef.current.y - touchStartRef.current.y;
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    // Only trigger if swipe distance exceeds threshold
    if (Math.max(absDeltaX, absDeltaY) < threshold) {
      // Reset
      touchStartRef.current = { x: 0, y: 0 };
      touchEndRef.current = { x: 0, y: 0 };
      isScrollingRef.current = false;
      startedInScrollableRef.current = null;
      touchMovedRef.current = false;
      return;
    }

    // CRITICAL: If user was scrolling in a scrollable element, NEVER trigger page swipes
    if (isScrollingRef.current && startedInScrollableRef.current) {
      // Reset
      touchStartRef.current = { x: 0, y: 0 };
      touchEndRef.current = { x: 0, y: 0 };
      isScrollingRef.current = false;
      startedInScrollableRef.current = null;
      touchMovedRef.current = false;
      return;
    }

    // For horizontal swipes (page turns), require horizontal movement to be 
    // SIGNIFICANTLY greater than vertical to avoid conflicts with scrolling
    // iPad requires stricter ratio (2x instead of 1.5x)
    const isHorizontalSwipe = absDeltaX > absDeltaY * 2; // Horizontal must be 2x vertical
    const isVerticalSwipe = absDeltaY > absDeltaX * 2;   // Vertical must be 2x horizontal

    // Additional check: if started in vertical scrollable, require even stronger horizontal intent
    const inVerticalScrollable = startedInScrollableRef.current?.direction === 'vertical';
    const canTriggerHorizontalSwipe = !inVerticalScrollable || (absDeltaX > absDeltaY * 3 && absDeltaX > threshold * 1.5);

    // Determine swipe direction
    if (isHorizontalSwipe && absDeltaX > threshold && canTriggerHorizontalSwipe) {
      // Horizontal swipe - only if started outside scrollable or meets strict criteria
      if (deltaX > 0) {
        onSwipeRight?.();
      } else {
        onSwipeLeft?.();
      }
    } else if (isVerticalSwipe && absDeltaY > threshold) {
      // Vertical swipe - only outside scrollable vertical areas
      if (!inVerticalScrollable) {
        if (deltaY > 0) {
          onSwipeDown?.();
        } else {
          onSwipeUp?.();
        }
      }
    }

    // Reset
    touchStartRef.current = { x: 0, y: 0 };
    touchEndRef.current = { x: 0, y: 0 };
    isScrollingRef.current = false;
    startedInScrollableRef.current = null;
    touchMovedRef.current = false;
  }, [enabled, threshold, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd
  };
}

// Swipeable container component
export function SwipeableContainer({
  children,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  className = ''
}) {
  const swipeHandlers = useSwipeGestures({
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    threshold
  });

  return (
    <div className={className} {...swipeHandlers}>
      {children}
    </div>
  );
}

// Swipe indicator component (visual feedback)
export function SwipeIndicator({ direction = 'horizontal', show = false }) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {direction === 'horizontal' ? (
        <>
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl opacity-30">
            ← Previous
          </div>
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-2xl opacity-30">
            Next →
          </div>
        </>
      ) : (
        <>
          <div className="absolute top-4 left-1/2 -translate-x-1/2 text-2xl opacity-30">
            ↑ Menu
          </div>
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-2xl opacity-30">
            ↓ Hide
          </div>
        </>
      )}
    </div>
  );
}

// Double tap detector
export function useDoubleTap(callback, delay = 300) {
  const lastTapRef = useRef(0);

  const handleTap = useCallback((e) => {
    const currentTime = new Date().getTime();
    const tapLength = currentTime - lastTapRef.current;
    
    if (tapLength < delay && tapLength > 0) {
      callback?.(e);
    }
    
    lastTapRef.current = currentTime;
  }, [callback, delay]);

  return handleTap;
}

// Long press detector
export function useLongPress(callback, delay = 500) {
  const timerRef = useRef(null);
  const isLongPressRef = useRef(false);

  const start = useCallback((e) => {
    isLongPressRef.current = false;
    timerRef.current = setTimeout(() => {
      isLongPressRef.current = true;
      callback?.(e);
    }, delay);
  }, [callback, delay]);

  const stop = useCallback(() => {
    clearTimeout(timerRef.current);
  }, []);

  return {
    onTouchStart: start,
    onTouchEnd: stop,
    onTouchCancel: stop,
    onMouseDown: start,
    onMouseUp: stop,
    onMouseLeave: stop,
    isLongPress: () => isLongPressRef.current
  };
}

// Pull to refresh hook
export function usePullToRefresh(onRefresh, threshold = 80) {
  const startYRef = useRef(0);
  const currentYRef = useRef(0);

  const handleTouchStart = useCallback((e) => {
    // Only enable at top of page
    if (window.scrollY === 0) {
      startYRef.current = e.touches[0].clientY;
    }
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (startYRef.current === 0) return;
    currentYRef.current = e.touches[0].clientY;
  }, []);

  const handleTouchEnd = useCallback(() => {
    const pullDistance = currentYRef.current - startYRef.current;
    
    if (pullDistance > threshold && window.scrollY === 0) {
      onRefresh?.();
    }
    
    startYRef.current = 0;
    currentYRef.current = 0;
  }, [threshold, onRefresh]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd
  };
}
