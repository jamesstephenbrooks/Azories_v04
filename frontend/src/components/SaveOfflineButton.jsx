/**
 * SaveOfflineButton - Button to save/remove books for offline reading
 */

import { useState, useCallback } from 'react';
import { FiDownload, FiCheck, FiWifiOff, FiTrash2, FiLoader } from 'react-icons/fi';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function SaveOfflineButton({ 
  book, 
  isOffline, 
  onSave, 
  onRemove, 
  variant = 'default', // 'default', 'icon', 'compact'
  compact = false, // Shortcut for compact variant
  showLabel = false, // Show full label button in card footer
  className = '' 
}) {
  const [isSaving, setIsSaving] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, message: '' });

  // Use compact variant if compact prop is true
  const effectiveVariant = compact ? 'compact' : (showLabel ? 'label' : variant);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setProgress({ current: 0, total: 1, message: 'Preparing book...' });

    try {
      // If book doesn't have pages, fetch the full book data first
      let bookToSave = book;
      
      if (!book.pages || book.pages.length === 0) {
        setProgress({ current: 0, total: 1, message: 'Fetching book data...' });
        
        try {
          // Fetch full book with pages from API (use the /full endpoint)
          const response = await axios.get(`${API}/books/${book.id}/full`);
          const fullBook = response.data;
          
          if (!fullBook.pages || fullBook.pages.length === 0) {
            toast.error('This book has no pages to save');
            setIsSaving(false);
            return;
          }
          
          bookToSave = fullBook;
        } catch (fetchError) {
          console.error('Failed to fetch book data:', fetchError);
          toast.error('Failed to load book data');
          setIsSaving(false);
          return;
        }
      }

      setProgress({ current: 0, total: bookToSave.pages.length + 1, message: 'Starting download...' });

      const result = await onSave(bookToSave, (current, total, message) => {
        setProgress({ current, total, message });
      });

      if (result.success) {
        const audioInfo = result.audioPageCount > 0 
          ? ` with ${result.audioPageCount} narrations` 
          : '';
        toast.success(`"${book.title}" saved for offline${audioInfo} (${result.sizeMB}MB)`);
      } else {
        toast.error(`Failed to save: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      toast.error('Failed to save book offline');
      console.error('Save offline error:', error);
    } finally {
      setIsSaving(false);
      setProgress({ current: 0, total: 0, message: '' });
    }
  }, [book, onSave]);

  const handleRemove = useCallback(async () => {
    try {
      const result = await onRemove(book.id);
      if (result.success) {
        toast.success(`"${book.title}" removed from offline storage`);
      } else {
        toast.error('Failed to remove from offline storage');
      }
    } catch (error) {
      toast.error('Failed to remove book');
      console.error('Remove offline error:', error);
    }
  }, [book, onRemove]);

  // Icon-only variant (for book cards)
  if (effectiveVariant === 'icon') {
    if (isSaving) {
      return (
        <div className={`flex items-center justify-center w-8 h-8 rounded-full bg-purple-500/20 ${className}`}>
          <FiLoader className="w-4 h-4 text-purple-400 animate-spin" />
        </div>
      );
    }

    if (isOffline) {
      return (
        <button
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            handleRemove();
          }}
          className={`flex items-center justify-center w-8 h-8 rounded-full bg-green-500/20 hover:bg-red-500/20 group transition-colors touch-manipulation ${className}`}
          title="Available offline - tap to remove"
        >
          <FiCheck className="w-4 h-4 text-green-400 group-hover:hidden" />
          <FiTrash2 className="w-4 h-4 text-red-400 hidden group-hover:block" />
        </button>
      );
    }

    return (
      <button
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          handleSave();
        }}
        className={`flex items-center justify-center w-8 h-8 rounded-full bg-white/10 hover:bg-purple-500/30 transition-colors touch-manipulation ${className}`}
        title="Save for offline reading"
      >
        <FiDownload className="w-4 h-4 text-white/70 hover:text-purple-400" />
      </button>
    );
  }

  // Compact variant (smaller button with text)
  if (effectiveVariant === 'compact') {
    if (isSaving) {
      return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/20 text-sm ${className}`}>
          <FiLoader className="w-4 h-4 text-purple-400 animate-spin" />
          <span className="text-purple-300">{progress.current}/{progress.total}</span>
        </div>
      );
    }

    if (isOffline) {
      return (
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleRemove();
          }}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/20 hover:bg-red-500/20 group transition-colors text-sm touch-manipulation ${className}`}
        >
          <FiWifiOff className="w-4 h-4 text-green-400" />
          <span className="text-green-400 group-hover:hidden">Offline</span>
          <span className="text-red-400 hidden group-hover:inline">Remove</span>
        </button>
      );
    }

    return (
      <button
        onClick={(e) => {
          e.stopPropagation();
          handleSave();
        }}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 hover:bg-purple-500/30 transition-colors text-sm touch-manipulation ${className}`}
      >
        <FiDownload className="w-4 h-4 text-white/70" />
        <span className="text-white/70">Save Offline</span>
      </button>
    );
  }

  // Label variant - Full width button with label for card footer
  if (effectiveVariant === 'label') {
    if (isSaving) {
      return (
        <Button 
          disabled 
          variant="outline"
          size="sm"
          className={`w-full rounded-full ${className}`}
        >
          <FiLoader className="mr-2 w-4 h-4 animate-spin" />
          Saving... {progress.current}/{progress.total}
        </Button>
      );
    }

    if (isOffline) {
      return (
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            handleRemove();
          }}
          className={`w-full rounded-full bg-green-500/10 border-green-500/30 hover:bg-red-500/10 hover:border-red-500/30 group ${className}`}
        >
          <FiWifiOff className="mr-2 w-4 h-4 text-green-500 group-hover:text-red-500" />
          <span className="text-green-600 group-hover:hidden">Available Offline</span>
          <span className="text-red-500 hidden group-hover:inline">Remove Offline</span>
        </Button>
      );
    }

    return (
      <Button
        variant="outline"
        size="sm"
        onClick={(e) => {
          e.stopPropagation();
          handleSave();
        }}
        className={`w-full rounded-full hover:bg-purple-500/10 hover:border-purple-500/30 ${className}`}
      >
        <FiDownload className="mr-2 w-4 h-4" />
        Save for Offline
      </Button>
    );
  }

  // Default full button variant
  if (isSaving) {
    return (
      <Button 
        disabled 
        className={`bg-purple-500/20 text-purple-300 ${className}`}
      >
        <FiLoader className="w-4 h-4 mr-2 animate-spin" />
        {progress.message || `Saving... ${progress.current}/${progress.total}`}
      </Button>
    );
  }

  if (isOffline) {
    return (
      <Button
        onClick={handleRemove}
        variant="outline"
        className={`border-green-500/50 text-green-400 hover:bg-red-500/20 hover:border-red-500/50 hover:text-red-400 group ${className}`}
      >
        <FiCheck className="w-4 h-4 mr-2 group-hover:hidden" />
        <FiTrash2 className="w-4 h-4 mr-2 hidden group-hover:block" />
        <span className="group-hover:hidden">Available Offline</span>
        <span className="hidden group-hover:inline">Remove Offline</span>
      </Button>
    );
  }

  return (
    <Button
      onClick={handleSave}
      variant="outline"
      className={`border-white/20 text-white/70 hover:bg-purple-500/20 hover:border-purple-500/50 hover:text-purple-300 ${className}`}
    >
      <FiDownload className="w-4 h-4 mr-2" />
      Save for Offline
    </Button>
  );
}

export default SaveOfflineButton;
