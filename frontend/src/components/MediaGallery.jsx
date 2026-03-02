import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FiImage, FiVideo, FiPlay, FiTrash2, FiMaximize2, FiX, FiPlus,
  FiChevronDown, FiStar, FiFolder, FiDownload, FiCheck
} from 'react-icons/fi';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { ScrollArea } from './ui/scroll-area';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Optimize Cloudinary URLs for thumbnails
const getOptimizedThumbnail = (url, width = 200) => {
  if (!url) return url;
  if (url.includes('res.cloudinary.com')) {
    return url.replace('/upload/', `/upload/f_auto,q_auto,w_${width},c_limit/`);
  }
  return url;
};

/**
 * MediaGallery - Unified gallery component with 3 sections:
 * 1. Starter Library - Free pre-made assets
 * 2. Creator Studio - User's own creations
 * 3. Pro Studio - Premium content
 * 
 * Each section has Images and Videos tabs.
 * 
 * Props:
 * - onSelect: (imageUrl, item) => void - Called when user selects an item
 * - mode: 'picker' | 'gallery' - Picker mode for selection, gallery mode for full view
 * - bookId: string - Filter by book ID (optional)
 * - showDelete: boolean - Show delete buttons (default: true in gallery mode)
 * - showAnimateButton: boolean - Show animate button on images
 * - onAnimate: (imageUrl) => void - Called when animate button clicked
 * - onDelete: (itemId) => void - Called when delete button clicked
 * - compact: boolean - Compact view with smaller thumbnails
 */
export default function MediaGallery({ 
  onSelect, 
  mode = 'gallery',
  bookId = null,
  showDelete = null,
  showAnimateButton = false,
  onAnimate,
  onDelete,
  compact = false,
  className = ''
}) {
  const { user } = useAuth();
  
  // Gallery data state
  const [starterLibrary, setStarterLibrary] = useState([]);
  const [creatorStudio, setCreatorStudio] = useState([]);
  const [proStudio, setProStudio] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Section expand state
  const [starterExpanded, setStarterExpanded] = useState(true);
  const [creatorExpanded, setCreatorExpanded] = useState(true);
  const [proExpanded, setProExpanded] = useState(true);
  
  // Media type filter per section
  const [starterFilter, setStarterFilter] = useState('images'); // 'images' | 'videos'
  const [creatorFilter, setCreatorFilter] = useState('images');
  const [proFilter, setProFilter] = useState('images');
  
  // Category filter for starter library
  const [starterCategory, setStarterCategory] = useState('all');
  
  // Preview modal
  const [previewItem, setPreviewItem] = useState(null);
  
  // Selected item for picker mode
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Determine if delete should be shown
  const canDelete = showDelete !== null ? showDelete : mode === 'gallery';
  
  useEffect(() => {
    loadAllGalleries();
  }, [bookId, user]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('azories-token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const loadAllGalleries = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadStarterLibrary(),
        loadCreatorStudio(),
        loadProStudio()
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadStarterLibrary = async () => {
    try {
      const response = await fetch(`${API_URL}/api/starter-library`);
      if (response.ok) {
        const data = await response.json();
        setStarterLibrary(data.images || []);
      }
    } catch (error) {
      console.error('Failed to load starter library:', error);
    }
  };

  const loadCreatorStudio = async () => {
    try {
      const url = bookId 
        ? `${API_URL}/api/art-studio/gallery?book_id=${bookId}`
        : `${API_URL}/api/art-studio/gallery`;
      
      const response = await fetch(url, { headers: getAuthHeaders() });
      if (response.ok) {
        const data = await response.json();
        // Filter out pro_studio items - those go in Pro Studio section
        const creatorItems = (data.images || []).filter(item => item.source !== 'pro_studio');
        setCreatorStudio(creatorItems);
      }
    } catch (error) {
      console.error('Failed to load creator studio:', error);
    }
  };

  const loadProStudio = async () => {
    try {
      const response = await fetch(`${API_URL}/api/art-studio/gallery`, { headers: getAuthHeaders() });
      if (response.ok) {
        const data = await response.json();
        // Filter to only pro_studio items
        const proItems = (data.images || []).filter(item => item.source === 'pro_studio');
        setProStudio(proItems);
      }
    } catch (error) {
      console.error('Failed to load pro studio:', error);
    }
  };

  const handleItemClick = (item, imageUrl) => {
    if (mode === 'picker') {
      setSelectedItem(item);
      if (onSelect) {
        onSelect(imageUrl || item.url || item.image_url, item);
      }
    } else {
      setPreviewItem(item);
    }
  };

  const handleDelete = async (itemId, e) => {
    e?.stopPropagation();
    if (onDelete) {
      onDelete(itemId);
    } else {
      try {
        await fetch(`${API_URL}/api/art-studio/gallery/${itemId}`, {
          method: 'DELETE',
          headers: getAuthHeaders()
        });
        loadCreatorStudio();
        loadProStudio();
      } catch (error) {
        console.error('Failed to delete item:', error);
      }
    }
  };

  const handleAnimate = (imageUrl, e) => {
    e?.stopPropagation();
    if (onAnimate) {
      onAnimate(imageUrl);
    }
  };

  // Count helpers
  const getImageCount = (items) => items.filter(i => i.type !== 'animation' && i.type !== 'video').length;
  const getVideoCount = (items) => items.filter(i => i.type === 'animation' || i.type === 'video').length;
  
  // Filter helpers
  const filterByType = (items, filter) => {
    if (filter === 'images') {
      return items.filter(i => i.type !== 'animation' && i.type !== 'video');
    } else {
      return items.filter(i => i.type === 'animation' || i.type === 'video');
    }
  };

  // Render individual media item
  const renderMediaItem = (item, section) => {
    const imageUrl = item.url || item.image_url;
    const isVideo = item.type === 'animation' || item.type === 'video';
    const isSelected = selectedItem?._id === item._id || selectedItem?.id === item.id;
    
    return (
      <div
        key={item._id || item.id}
        className={`relative group rounded-lg overflow-hidden border-2 transition-all cursor-pointer ${
          isSelected
            ? 'border-purple-500 ring-2 ring-purple-500/30'
            : 'border-transparent hover:border-white/30'
        }`}
        onClick={() => handleItemClick(item, imageUrl)}
      >
        {isVideo ? (
          <video
            src={imageUrl}
            className={`w-full ${compact ? 'aspect-square' : 'aspect-[4/3]'} object-cover`}
            muted
            loop
            onMouseEnter={(e) => e.target.play()}
            onMouseLeave={(e) => { e.target.pause(); e.target.currentTime = 0; }}
          />
        ) : (
          <img
            src={getOptimizedThumbnail(imageUrl, compact ? 100 : 200)}
            alt={item.name || 'Gallery item'}
            className={`w-full ${compact ? 'aspect-square' : 'aspect-[4/3]'} object-cover`}
            loading="lazy"
          />
        )}
        
        {/* Overlay with info */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="absolute bottom-0 left-0 right-0 p-2">
            <p className="text-white text-xs font-medium truncate">{item.name}</p>
            <p className="text-white/50 text-[10px] flex items-center gap-1">
              {isVideo ? <FiVideo className="w-2.5 h-2.5" /> : <FiImage className="w-2.5 h-2.5" />}
              {isVideo ? 'Video' : item.style || item.category || 'Image'}
            </p>
          </div>
        </div>
        
        {/* Video badge */}
        {isVideo && (
          <div className="absolute top-1 left-1 px-1.5 py-0.5 bg-pink-500 rounded text-[10px] text-white flex items-center gap-0.5">
            <FiPlay className="w-2 h-2" />
            Video
          </div>
        )}
        
        {/* Category badge for starter library */}
        {section === 'starter' && item.category && (
          <div className="absolute top-1 right-1 bg-amber-500 text-white text-[8px] px-1 rounded">
            {item.category}
          </div>
        )}
        
        {/* Pro badge */}
        {section === 'pro' && (
          <div className="absolute top-1 right-1 px-1.5 py-0.5 bg-gradient-to-r from-yellow-500 to-orange-500 rounded text-[10px] text-white font-medium">
            PRO
          </div>
        )}
        
        {/* Selected checkmark */}
        {isSelected && mode === 'picker' && (
          <div className="absolute top-1 left-1 w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
            <FiCheck className="w-3 h-3 text-white" />
          </div>
        )}
        
        {/* Action buttons */}
        <div className="absolute bottom-1 left-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {showAnimateButton && !isVideo && (
            <button
              onClick={(e) => handleAnimate(imageUrl, e)}
              className="p-1 bg-pink-500/80 rounded-full hover:bg-pink-600"
              title="Animate this image"
            >
              <FiPlay className="w-2.5 h-2.5 text-white" />
            </button>
          )}
        </div>
        
        {/* Delete button */}
        {canDelete && section !== 'starter' && (
          <button
            onClick={(e) => handleDelete(item._id || item.id, e)}
            className="absolute top-1 right-1 p-1 bg-red-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
            title="Delete"
          >
            <FiTrash2 className="w-2.5 h-2.5 text-white" />
          </button>
        )}
      </div>
    );
  };

  // Render section with header and content
  const renderSection = (title, icon, items, filter, setFilter, expanded, setExpanded, section, gradient, iconColor) => {
    const imageCount = getImageCount(items);
    const videoCount = getVideoCount(items);
    const filteredItems = filterByType(items, filter);
    
    // Additional category filtering for starter library
    let displayItems = filteredItems;
    if (section === 'starter' && starterCategory !== 'all') {
      displayItems = filteredItems.filter(i => i.category === starterCategory);
    }
    
    if (items.length === 0) return null;
    
    return (
      <div className={`${gradient} rounded-xl border ${section === 'starter' ? 'border-amber-500/30' : section === 'pro' ? 'border-yellow-500/30' : 'border-purple-500/30'} overflow-hidden`}>
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded ${section === 'starter' ? 'bg-gradient-to-r from-amber-500 to-orange-500' : section === 'pro' ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 'bg-gradient-to-r from-purple-500 to-pink-500'} flex items-center justify-center`}>
              {icon}
            </div>
            <span className={`text-sm font-semibold ${iconColor}`}>{title}</span>
            <span className={`text-xs ${iconColor.replace('300', '400')}/60`}>
              {imageCount} images, {videoCount} videos
            </span>
          </div>
          <FiChevronDown className={`w-4 h-4 ${iconColor.replace('300', '400')} transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </button>
        
        {expanded && (
          <div className="p-4 pt-0">
            {/* Images/Videos toggle */}
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={() => setFilter('images')}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  filter === 'images'
                    ? section === 'starter' ? 'bg-amber-500 text-white' : section === 'pro' ? 'bg-yellow-500 text-white' : 'bg-purple-500 text-white'
                    : 'bg-white/10 text-white/60 hover:text-white'
                }`}
              >
                <FiImage className="w-3 h-3" />
                Images ({imageCount})
              </button>
              <button
                onClick={() => setFilter('videos')}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                  filter === 'videos'
                    ? 'bg-pink-500 text-white'
                    : 'bg-white/10 text-white/60 hover:text-white'
                }`}
              >
                <FiVideo className="w-3 h-3" />
                Videos ({videoCount})
              </button>
            </div>
            
            {/* Category filter for starter library */}
            {section === 'starter' && filter === 'images' && (
              <div className="flex flex-wrap gap-1 mb-3">
                {['all', 'character', 'scene', 'object', 'action'].map(cat => (
                  <button
                    key={cat}
                    onClick={() => setStarterCategory(cat)}
                    className={`px-2 py-0.5 text-[10px] rounded ${
                      starterCategory === cat 
                        ? 'bg-amber-500 text-white' 
                        : 'bg-white/10 text-white/60 hover:text-white'
                    }`}
                  >
                    {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1) + 's'}
                  </button>
                ))}
              </div>
            )}
            
            {/* Grid of items */}
            <div className={`grid ${compact ? 'grid-cols-4 sm:grid-cols-6 gap-2' : 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3'} ${!compact && 'max-h-80 overflow-y-auto'}`}>
              {displayItems.map(item => renderMediaItem(item, section))}
            </div>
            
            {displayItems.length === 0 && (
              <div className="text-center py-6 text-white/40">
                <FiFolder className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-xs">No {filter} in this section</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const totalItems = starterLibrary.length + creatorStudio.length + proStudio.length;
  
  if (totalItems === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <FiImage className="w-16 h-16 mx-auto text-white/20 mb-4" />
        <p className="text-white/50">No media available yet.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Starter Library Section */}
      {renderSection(
        'Starter Library',
        <span className="text-white text-xs">⭐</span>,
        starterLibrary,
        starterFilter,
        setStarterFilter,
        starterExpanded,
        setStarterExpanded,
        'starter',
        'bg-gradient-to-r from-amber-500/10 to-orange-500/10',
        'text-amber-300'
      )}
      
      {/* Creator Studio Section */}
      {renderSection(
        'Creator Studio',
        <FiImage className="w-3 h-3 text-white" />,
        creatorStudio,
        creatorFilter,
        setCreatorFilter,
        creatorExpanded,
        setCreatorExpanded,
        'creator',
        'bg-purple-500/10',
        'text-purple-300'
      )}
      
      {/* Pro Studio Section */}
      {renderSection(
        'Pro Studio',
        <FiStar className="w-3 h-3 text-white" />,
        proStudio,
        proFilter,
        setProFilter,
        proExpanded,
        setProExpanded,
        'pro',
        'bg-gradient-to-r from-yellow-500/10 to-orange-500/10',
        'text-yellow-300'
      )}
      
      {/* Preview Modal */}
      <Dialog open={!!previewItem} onOpenChange={() => setPreviewItem(null)}>
        <DialogContent className="max-w-3xl bg-slate-900 border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              {previewItem?.type === 'animation' || previewItem?.type === 'video' ? (
                <FiVideo className="text-pink-400" />
              ) : (
                <FiImage className="text-purple-400" />
              )}
              {previewItem?.name || 'Media Preview'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="relative">
            {previewItem?.type === 'animation' || previewItem?.type === 'video' ? (
              <video
                src={previewItem?.url || previewItem?.image_url}
                controls
                autoPlay
                loop
                className="w-full rounded-lg"
              />
            ) : (
              <img
                src={previewItem?.url || previewItem?.image_url}
                alt={previewItem?.name || 'Preview'}
                className="w-full rounded-lg"
              />
            )}
          </div>
          
          <div className="flex justify-between items-center mt-4">
            <div className="text-white/60 text-sm">
              {previewItem?.style && <span>Style: {previewItem.style}</span>}
              {previewItem?.category && <span>Category: {previewItem.category}</span>}
            </div>
            <div className="flex gap-2">
              {mode === 'picker' && onSelect && (
                <Button
                  onClick={() => {
                    onSelect(previewItem?.url || previewItem?.image_url, previewItem);
                    setPreviewItem(null);
                  }}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <FiPlus className="w-4 h-4 mr-2" />
                  Select
                </Button>
              )}
              <Button
                variant="outline"
                asChild
                className="border-white/20 text-white"
              >
                <a href={previewItem?.url || previewItem?.image_url} download target="_blank" rel="noopener noreferrer">
                  <FiDownload className="w-4 h-4 mr-2" />
                  Download
                </a>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * MediaGalleryPicker - Dialog wrapper for MediaGallery in picker mode
 */
export function MediaGalleryPicker({ 
  open, 
  onOpenChange, 
  onSelect,
  bookId = null,
  title = 'Select from Galleries'
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] bg-slate-900 border-white/10">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <FiImage className="text-purple-400" />
            {title}
          </DialogTitle>
        </DialogHeader>
        
        <ScrollArea className="h-[65vh]">
          <MediaGallery
            mode="picker"
            onSelect={(url, item) => {
              onSelect(url, item);
              onOpenChange(false);
            }}
            bookId={bookId}
            showDelete={false}
            compact={true}
          />
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
