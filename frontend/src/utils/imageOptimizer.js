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
 * Get thumbnail-optimized URL (sharp and crisp)
 * Use this for grid views and small previews
 */
export const getThumbnailUrl = (url, width = 300) => {
  if (!url) return url;
  
  // For Cloudinary, add sharpening for crisp thumbnails
  if (url.includes('res.cloudinary.com')) {
    const transforms = [
      `w_${width}`,
      'q_75',
      'e_sharpen:100',
      'f_auto',
      'c_limit',
      'dpr_auto'
    ];
    return url.replace('/upload/', `/upload/${transforms.join(',')}/`);
  }
  
  return getOptimizedImageUrl(url, { 
    width, 
    quality: '75',
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

/**
 * Get the best available image URL from an item object
 * Handles various property names used across the codebase
 */
export const getImageUrl = (item) => {
  if (!item) return null;
  return item.url || item.image_url || item.thumbnail_url || null;
};

/**
 * Get video thumbnail URL with Cloudinary transformation fallback
 * Converts video URL to a thumbnail image URL
 */
export const getVideoThumbnailUrl = (videoUrl, options = {}) => {
  const { width = 300, height = 300, time = 0 } = options;
  
  if (!videoUrl) return null;
  
  // For Cloudinary video URLs, generate a thumbnail
  if (videoUrl.includes('cloudinary.com') && 
      (videoUrl.includes('/video/') || videoUrl.includes('.mp4') || videoUrl.includes('.webm'))) {
    // Transform video URL to image thumbnail
    // so_0 = start offset (first frame), w_300, h_300, c_fill = crop to fill
    return videoUrl
      .replace('/upload/', `/upload/so_${time},w_${width},h_${height},c_fill/`)
      .replace('.mp4', '.jpg')
      .replace('.webm', '.jpg')
      .replace('/video/', '/video/'); // Keep video folder
  }
  
  return null;
};

/**
 * Azories branded placeholder images as inline data URIs
 * Using simple, browser-compatible SVGs
 */
export const AZORIES_PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Crect fill='%237c3aed' width='200' height='200'/%3E%3Ctext x='100' y='90' fill='%23fff' font-family='Arial' font-size='16' text-anchor='middle'%3EAzories%3C/text%3E%3Crect x='70' y='105' width='60' height='50' rx='5' fill='%23ffffff33'/%3E%3C/svg%3E";

export const AZORIES_VIDEO_PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Crect fill='%237c3aed' width='200' height='200'/%3E%3Ccircle cx='100' cy='85' r='30' fill='%23ffffff33'/%3E%3Cpolygon points='90,70 90,100 115,85' fill='%23fff'/%3E%3Ctext x='100' y='150' fill='%23fff' font-family='Arial' font-size='14' text-anchor='middle'%3EAzories%3C/text%3E%3C/svg%3E";

/**
 * Handle image load error with branded fallback
 * Use this in onError handlers for img tags
 */
export const handleImageError = (event, isVideo = false) => {
  const target = event.target;
  const fallback = isVideo ? AZORIES_VIDEO_PLACEHOLDER : AZORIES_PLACEHOLDER;
  
  // Prevent infinite loop if fallback also fails
  if (target.dataset.fallbackSet === 'true') return;
  
  target.dataset.fallbackSet = 'true';
  target.src = fallback;
  target.onerror = null; // Prevent further error handling
};

export default {
  getOptimizedImageUrl,
  getThumbnailUrl,
  getFullSizeUrl,
  getPlaceholderUrl,
  preloadImages,
  supportsWebP,
  supportsAvif,
  getImageUrl,
  getVideoThumbnailUrl,
  AZORIES_PLACEHOLDER,
  AZORIES_VIDEO_PLACEHOLDER,
  handleImageError
};
