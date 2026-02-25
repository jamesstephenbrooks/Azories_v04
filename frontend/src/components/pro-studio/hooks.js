/**
 * Pro Studio shared hooks and utilities
 * Extracted from ProStudio.js for reusability
 */

import { useState, useCallback, useRef } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Hook for managing gallery state with pagination
 */
export function useGallery() {
  const [gallery, setGallery] = useState([]);
  const [galleryPage, setGalleryPage] = useState(1);
  const [galleryHasMore, setGalleryHasMore] = useState(true);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [galleryTotal, setGalleryTotal] = useState(0);
  const [galleryFilter, setGalleryFilter] = useState('all');
  const GALLERY_PAGE_SIZE = 30;

  const loadGallery = useCallback(async (page = 1, append = false) => {
    if (galleryLoading) return;
    
    try {
      setGalleryLoading(true);
      const token = localStorage.getItem('azories-token');
      
      const filterMap = {
        'all': null,
        'images': 'images',
        'videos': 'videos',
        'characters': 'characters'
      };
      const filterParam = filterMap[galleryFilter] || null;
      
      const params = new URLSearchParams({
        page: page.toString(),
        limit: GALLERY_PAGE_SIZE.toString()
      });
      if (filterParam) params.append('filter_type', filterParam);
      
      const response = await fetch(`${API_URL}/api/pro-studio/gallery/unified?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const newItems = data.items || [];
        
        if (append) {
          setGallery(prev => [...prev, ...newItems]);
        } else {
          setGallery(newItems);
        }
        
        setGalleryTotal(data.total || 0);
        setGalleryHasMore(data.has_more || false);
        setGalleryPage(page);
      }
    } catch (error) {
      console.error('Error loading gallery:', error);
    } finally {
      setGalleryLoading(false);
    }
  }, [galleryFilter, galleryLoading]);

  const loadMoreGallery = useCallback(() => {
    if (galleryHasMore && !galleryLoading) {
      loadGallery(galleryPage + 1, true);
    }
  }, [galleryPage, galleryHasMore, galleryLoading, loadGallery]);

  return {
    gallery,
    setGallery,
    galleryPage,
    galleryHasMore,
    galleryLoading,
    galleryTotal,
    galleryFilter,
    setGalleryFilter,
    loadGallery,
    loadMoreGallery,
    GALLERY_PAGE_SIZE
  };
}

/**
 * Hook for managing credit checks
 */
export function useCreditCheck() {
  const [userCredits, setUserCredits] = useState(0);
  const [isVip, setIsVip] = useState(false);

  const checkCredits = useCallback(async () => {
    try {
      const token = localStorage.getItem('azories-token');
      if (!token) return { hasCredits: false, credits: 0 };
      
      const response = await fetch(`${API_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserCredits(data.credits || 0);
        setIsVip(data.is_vip || false);
        return { 
          hasCredits: data.is_vip || data.credits > 0, 
          credits: data.credits,
          isVip: data.is_vip 
        };
      }
      return { hasCredits: false, credits: 0, isVip: false };
    } catch (error) {
      console.error('Error checking credits:', error);
      return { hasCredits: false, credits: 0, isVip: false };
    }
  }, []);

  const withCreditCheck = useCallback((callback, navigate) => {
    return async (...args) => {
      const { hasCredits } = await checkCredits();
      if (!hasCredits) {
        navigate('/credits');
        return;
      }
      return callback(...args);
    };
  }, [checkCredits]);

  return {
    userCredits,
    isVip,
    checkCredits,
    withCreditCheck
  };
}

/**
 * Hook for managing expanded media modal
 */
export function useExpandedMedia() {
  const [expandedItem, setExpandedItem] = useState(null);

  const handleExpandMedia = useCallback((item) => {
    setExpandedItem({
      url: item.image_url || item.url,
      name: item.prompt || item.name || 'Media',
      type: item.type === 'video' || item.is_animation ? 'video' : 'image'
    });
  }, []);

  const closeExpandedMedia = useCallback(() => {
    setExpandedItem(null);
  }, []);

  return {
    expandedItem,
    handleExpandMedia,
    closeExpandedMedia
  };
}

/**
 * Utility to determine if a gallery item is a video
 */
export function isVideoItem(item) {
  return item.type === 'video' || 
         item.type === 'animation' || 
         item.is_animation || 
         (item.image_url && item.image_url.includes('video/'));
}

/**
 * Credit costs for different operations
 */
export const CREDIT_COSTS = {
  CHARACTER_CREATE: 20,
  SHOTS_GENERATE: 10,
  VIDEO_GENERATE: 50,
  SCENE_CREATE: 15,
  CINEMA_STUDIO: 20
};
