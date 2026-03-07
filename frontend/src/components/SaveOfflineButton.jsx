/**
 * SaveOfflineButton - Button to save/remove books for offline reading
 */

import { useState, useCallback } from 'react';
import { FiDownload, FiCheck, FiWifiOff, FiTrash2, FiLoader } from 'react-icons/fi';
import { Button } from './ui/button';
import { toast } from 'sonner';

function SaveOfflineButton({ 
  book, 
  isOffline, 
  onSave, 
  onRemove, 
  variant = 'default', // 'default', 'icon', 'compact'
  className = '' 
}) {
  const [isSaving, setIsSaving] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, message: '' });

  const handleSave = useCallback(async () => {
    if (!book || !book.pages || book.pages.length === 0) {
      toast.error('This book has no pages to save');
      return;
    }

    setIsSaving(true);
    setProgress({ current: 0, total: book.pages.length + 1, message: 'Starting...' });

    try {
      const result = await onSave(book, (current, total, message) => {
        setProgress({ current, total, message });
      });

      if (result.success) {
        toast.success(`"${book.title}" saved for offline reading (${result.sizeMB}MB)`);
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
  if (variant === 'icon') {
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
  if (variant === 'compact') {
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
