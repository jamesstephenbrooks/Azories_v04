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
  enabled = true,
  onDebug = null // Visual debug callback for iPad testing
}) {
  const touchStartRef = useRef({ x: 0, y: 0, target: null });
  const touchEndRef = useRef({ x: 0, y: 0 });
  const touchMovedRef = useRef(false);
  const isScrollableAreaRef = useRef(false);
  
  // Helper to log both to console and visual debug
  const debug = useCallback((msg) => {
    console.log(msg);
    onDebug?.(msg);
  }, [onDebug]);

  const handleTouchStart = useCallback((e) => {
    // Check if touch started in a scrollable element
    const target = e.target;
    
    // DEFENSIVE CHECK: Multiple ways to detect scrollable area
    const hasDataScrollable = target.closest('[data-scrollable="true"]');
    const hasTextScrollClass = target.closest('.text-scroll-container');
    const isInScrollableArea = !!(hasDataScrollable || hasTextScrollClass);
    
    isScrollableAreaRef.current = isInScrollableArea;
    
    // Visual debug for iPad
    debug(`👆 Touch: ${isInScrollableArea ? 'TEXT (blocked)' : 'IMAGE (allowed)'}`);
    
    // If touch started in scrollable area, DON'T even record touch start
    // This prevents any chance of triggering a swipe
    if (isInScrollableArea) {
      debug('🚫 BLOCKED - in text area');
      touchStartRef.current = { x: 0, y: 0, target: null };
      touchEndRef.current = { x: 0, y: 0 };
      touchMovedRef.current = false;
      return;
    }
    
    touchStartRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
      target: target
    };
    touchEndRef.current = { x: 0, y: 0 };
    touchMovedRef.current = false;
  }, [debug]);

  const handleTouchMove = useCallback((e) => {
    // If we determined touch started in scrollable area, don't track movement
    if (isScrollableAreaRef.current) {
      return;
    }
    
    touchMovedRef.current = true;
    touchEndRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY
    };
  }, []);

  const handleTouchEnd = useCallback(() => {
    console.log('[SwipeGestures] touchend - enabled:', enabled, 'moved:', touchMovedRef.current);
    
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
    
    console.log('[SwipeGestures] touchend - deltaX:', deltaX, 'deltaY:', deltaY, 'scrollable:', isScrollableAreaRef.current);

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
