import { useRef, useCallback } from 'react';

/**
 * Hook for swipe gesture detection
 * 
 * Direction locking for scroll vs swipe is handled by the component (BookReader),
 * not this hook. This hook simply detects swipe gestures based on touch movement.
 * 
 * UPDATED: Improved iPad support - detects if touch started in scrollable area
 */
export function useSwipeGestures({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  enabled = true
}) {
  const touchStartRef = useRef({ x: 0, y: 0, target: null });
  const touchEndRef = useRef({ x: 0, y: 0 });
  const touchMovedRef = useRef(false);
  const isScrollableAreaRef = useRef(false);

  const handleTouchStart = useCallback((e) => {
    // Check if touch started in a scrollable element
    const target = e.target;
    const scrollableParent = target.closest('[data-scrollable="true"]');
    isScrollableAreaRef.current = !!scrollableParent;
    
    touchStartRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
      target: target
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
      touchStartRef.current = { x: 0, y: 0, target: null };
      touchEndRef.current = { x: 0, y: 0 };
      isScrollableAreaRef.current = false;
      return;
    }

    const deltaX = touchEndRef.current.x - touchStartRef.current.x;
    const deltaY = touchEndRef.current.y - touchStartRef.current.y;
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    // IPAD FIX: If started in scrollable area AND movement is more vertical than horizontal
    // then DO NOT trigger swipe - user is scrolling text
    if (isScrollableAreaRef.current && absDeltaY > absDeltaX) {
      console.log('[SwipeGestures] Blocked - vertical scroll in scrollable area');
      touchStartRef.current = { x: 0, y: 0, target: null };
      touchEndRef.current = { x: 0, y: 0 };
      touchMovedRef.current = false;
      isScrollableAreaRef.current = false;
      return;
    }

    // Only trigger if swipe distance exceeds threshold
    if (Math.max(absDeltaX, absDeltaY) < threshold) {
      touchStartRef.current = { x: 0, y: 0, target: null };
      touchEndRef.current = { x: 0, y: 0 };
      touchMovedRef.current = false;
      isScrollableAreaRef.current = false;
      return;
    }

    // Require movement to be clearly horizontal for page turns (2x ratio for iPad)
    const isHorizontalSwipe = absDeltaX > absDeltaY * 2;
    const isVerticalSwipe = absDeltaY > absDeltaX * 2;

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
    touchStartRef.current = { x: 0, y: 0, target: null };
    touchEndRef.current = { x: 0, y: 0 };
    touchMovedRef.current = false;
    isScrollableAreaRef.current = false;
  }, [enabled, threshold, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd
  };
}
