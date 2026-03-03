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

  // Check if an element or its parents are scrollable
  const isInScrollableElement = useCallback((element) => {
    let current = element;
    while (current && current !== document.body) {
      const style = window.getComputedStyle(current);
      const overflowY = style.overflowY;
      const overflowX = style.overflowX;
      
      // Check if element has scrollable content
      if ((overflowY === 'auto' || overflowY === 'scroll') && current.scrollHeight > current.clientHeight) {
        return { element: current, direction: 'vertical' };
      }
      if ((overflowX === 'auto' || overflowX === 'scroll') && current.scrollWidth > current.clientWidth) {
        return { element: current, direction: 'horizontal' };
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
    isScrollingRef.current = false;
    
    // Check if touch started in a scrollable element
    if (ignoreScrollableElements) {
      const scrollable = isInScrollableElement(e.target);
      startedInScrollableRef.current = scrollable;
    } else {
      startedInScrollableRef.current = null;
    }
  }, [ignoreScrollableElements, isInScrollableElement]);

  const handleTouchMove = useCallback((e) => {
    touchEndRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
    
    // If we started in a scrollable element and are moving vertically, mark as scrolling
    if (startedInScrollableRef.current) {
      const deltaY = Math.abs(touchEndRef.current.y - touchStartRef.current.y);
      const deltaX = Math.abs(touchEndRef.current.x - touchStartRef.current.x);
      
      // If vertical movement is greater than horizontal, user is likely scrolling
      if (deltaY > deltaX && deltaY > 10) {
        isScrollingRef.current = true;
      }
    }
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (!enabled) return;

    const deltaX = touchEndRef.current.x - touchStartRef.current.x;
    const deltaY = touchEndRef.current.y - touchStartRef.current.y;
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    // Only trigger if swipe distance exceeds threshold
    if (Math.max(absDeltaX, absDeltaY) < threshold) {
      // Reset
      touchStartRef.current = { x: 0, y: 0 };
      touchEndRef.current = { x: 0, y: 0 };
      return;
    }

    // If user was scrolling in a scrollable element, don't trigger page swipes
    if (isScrollingRef.current && startedInScrollableRef.current) {
      // Reset
      touchStartRef.current = { x: 0, y: 0 };
      touchEndRef.current = { x: 0, y: 0 };
      isScrollingRef.current = false;
      startedInScrollableRef.current = null;
      return;
    }

    // For horizontal swipes (page turns), require horizontal movement to be 
    // significantly greater than vertical to avoid conflicts with scrolling
    const isHorizontalSwipe = absDeltaX > absDeltaY * 1.5; // Horizontal must be 1.5x vertical
    const isVerticalSwipe = absDeltaY > absDeltaX * 1.5;   // Vertical must be 1.5x horizontal

    // Determine swipe direction
    if (isHorizontalSwipe && absDeltaX > threshold) {
      // Horizontal swipe - only if started outside scrollable or scrollable is horizontal
      const canSwipeHorizontal = !startedInScrollableRef.current || 
                                  startedInScrollableRef.current.direction === 'horizontal';
      
      if (canSwipeHorizontal || absDeltaX > threshold * 2) { // Allow strong horizontal swipes anywhere
        if (deltaX > 0) {
          onSwipeRight?.();
        } else {
          onSwipeLeft?.();
        }
      }
    } else if (isVerticalSwipe && absDeltaY > threshold) {
      // Vertical swipe
      if (deltaY > 0) {
        onSwipeDown?.();
      } else {
        onSwipeUp?.();
      }
    }

    // Reset
    touchStartRef.current = { x: 0, y: 0 };
    touchEndRef.current = { x: 0, y: 0 };
    isScrollingRef.current = false;
    startedInScrollableRef.current = null;
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
