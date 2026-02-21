import { useRef, useEffect, useCallback } from 'react';

// Hook for swipe gesture detection
export function useSwipeGestures({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  enabled = true
}) {
  const touchStartRef = useRef({ x: 0, y: 0 });
  const touchEndRef = useRef({ x: 0, y: 0 });

  const handleTouchStart = useCallback((e) => {
    touchStartRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
  }, []);

  const handleTouchMove = useCallback((e) => {
    touchEndRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (!enabled) return;

    const deltaX = touchEndRef.current.x - touchStartRef.current.x;
    const deltaY = touchEndRef.current.y - touchStartRef.current.y;
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    // Only trigger if swipe distance exceeds threshold
    if (Math.max(absDeltaX, absDeltaY) < threshold) return;

    // Determine swipe direction
    if (absDeltaX > absDeltaY) {
      // Horizontal swipe
      if (deltaX > 0) {
        onSwipeRight?.();
      } else {
        onSwipeLeft?.();
      }
    } else {
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
