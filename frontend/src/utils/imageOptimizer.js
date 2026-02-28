/**
 * Centralized Image Optimization Utility
 * Handles Cloudinary, Unsplash, and other image sources with aggressive optimization
 */

/**
 * Get optimized image URL with transformations for faster loading
 * Supports: Cloudinary, Unsplash, and generic URLs
 * 
 * @param {string} url - Original image URL
 * @param {object} options - Transformation options
 * @param {number} options.width - Target width (default: 400)
 * @param {string} options.quality - Quality setting (default: 'auto')
 * @param {string} options.format - Output format (default: 'auto' for WebP/AVIF)
 * @returns {string} - Optimized URL
 */
export const getOptimizedImageUrl = (url, { 
  width = 400, 
  quality = 'auto', 
  format = 'auto',
  blur = null 
} = {}) => {
  if (!url) return url;
  
  // Cloudinary URLs - use their transformation API
  if (url.includes('res.cloudinary.com')) {
    // Build transformation string
    // w_ = width, q_auto = automatic quality, f_auto = automatic format (webp/avif)
    // c_limit = don't upscale, dpr_auto = device pixel ratio
    const transforms = [
      `w_${width}`,
      `q_${quality}`,
      `f_${format}`,
      'c_limit',
      'dpr_auto'
    ];
    
    if (blur) {
      transforms.push(`e_blur:${blur}`);
    }
    
    const transformString = transforms.join(',');
    return url.replace('/upload/', `/upload/${transformString}/`);
  }
  
  // Unsplash URLs - use their built-in optimization
  if (url.includes('unsplash.com')) {
    // Remove existing parameters
    const baseUrl = url.split('?')[0];
    // Add optimization parameters
    // fm=webp for modern format, q=80 for quality, w for width
    return `${baseUrl}?w=${width}&q=80&fm=webp&fit=crop`;
  }
  
  // For other URLs, return as-is (can't optimize external sources)
  return url;
};

/**
 * Get thumbnail-optimized URL (more aggressive compression)
 * Use this for grid views and small previews
 */
export const getThumbnailUrl = (url, width = 300) => {
  return getOptimizedImageUrl(url, { 
    width, 
    quality: '60',  // More aggressive quality reduction for thumbnails
    format: 'auto' 
  });
};

/**
 * Get full-size optimized URL (less compression)
 * Use this for detail views and lightboxes
 */
export const getFullSizeUrl = (url, width = 800) => {
  return getOptimizedImageUrl(url, { 
    width, 
    quality: 'auto',
    format: 'auto' 
  });
};

/**
 * Get placeholder/blur URL for progressive loading
 */
export const getPlaceholderUrl = (url) => {
  return getOptimizedImageUrl(url, { 
    width: 20,  // Tiny width
    quality: '30',
    blur: 1000
  });
};

/**
 * Preload images for faster display
 * Call this with visible book covers to preload them
 */
export const preloadImages = (urls, priority = 'low') => {
  if (typeof window === 'undefined') return;
  
  urls.forEach(url => {
    if (!url) return;
    
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = getThumbnailUrl(url);
    link.fetchPriority = priority;
    
    // Don't add duplicates
    if (!document.querySelector(`link[href="${link.href}"]`)) {
      document.head.appendChild(link);
    }
  });
};

/**
 * Check if browser supports modern image formats
 */
export const supportsWebP = () => {
  if (typeof document === 'undefined') return false;
  const canvas = document.createElement('canvas');
  return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
};

export const supportsAvif = () => {
  // AVIF support detection is async, so we just check for modern browsers
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent;
  // Chrome 85+, Firefox 93+, Safari 16+ support AVIF
  return /Chrome\/(\d+)/.test(ua) && parseInt(RegExp.$1) >= 85;
};

export default {
  getOptimizedImageUrl,
  getThumbnailUrl,
  getFullSizeUrl,
  getPlaceholderUrl,
  preloadImages,
  supportsWebP,
  supportsAvif
};
