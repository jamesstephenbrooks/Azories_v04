import { useRef, useCallback } from 'react';

/**
 * Hook for swipe gesture detection
 * 
 * Direction locking for scroll vs swipe is handled by the component (BookReader),
 * not this hook. This hook simply detects swipe gestures based on touch movement.
 */
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
  const touchMovedRef = useRef(false);

  const handleTouchStart = useCallback((e) => {
    touchStartRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
    touchEndRef.current = { x: 0, y: 0 };
    touchMovedRef.current = false;
  }, []);

  const handleTouchMove = useCallback((e) => {
    touchMovedRef.current = true;
    touchEndRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (!enabled) return;

    // If no movement occurred, reset and exit
    if (!touchMovedRef.current) {
      touchStartRef.current = { x: 0, y: 0 };
      touchEndRef.current = { x: 0, y: 0 };
      return;
    }

    const deltaX = touchEndRef.current.x - touchStartRef.current.x;
    const deltaY = touchEndRef.current.y - touchStartRef.current.y;
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    // Only trigger if swipe distance exceeds threshold
    if (Math.max(absDeltaX, absDeltaY) < threshold) {
      touchStartRef.current = { x: 0, y: 0 };
      touchEndRef.current = { x: 0, y: 0 };
      touchMovedRef.current = false;
      return;
    }

    // Require movement to be clearly in one direction (1.5x ratio)
    const isHorizontalSwipe = absDeltaX > absDeltaY * 1.5;
    const isVerticalSwipe = absDeltaY > absDeltaX * 1.5;

    if (isHorizontalSwipe && absDeltaX > threshold) {
      if (deltaX > 0) {
        onSwipeRight?.();
      } else {
        onSwipeLeft?.();
      }
    } else if (isVerticalSwipe && absDeltaY > threshold) {
      if (deltaY > 0) {
        onSwipeDown?.();
      } else {
        onSwipeUp?.();
      }
    }

    // Reset
    touchStartRef.current = { x: 0, y: 0 };
    touchEndRef.current = { x: 0, y: 0 };
    touchMovedRef.current = false;
  }, [enabled, threshold, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd
  };
}
