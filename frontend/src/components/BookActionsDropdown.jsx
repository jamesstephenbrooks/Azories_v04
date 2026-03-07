import { useState, useRef, useEffect } from 'react';
import { FiMoreHorizontal, FiBarChart2, FiLink, FiPackage, FiEye, FiEyeOff, FiTrash2 } from 'react-icons/fi';
import { Button } from '@/components/ui/button';

/**
 * BookActionsDropdown - Clean dropdown menu for book card actions
 * Appears above the button (for cards at bottom of screen)
 * Only one dropdown open at a time
 */

// Global state to track which dropdown is open
let globalCloseCallback = null;

export default function BookActionsDropdown({ 
  book, 
  onAnalytics, 
  onCopyLink, 
  onOrderPrint, 
  onTogglePublish, 
  onDelete,
  className = ''
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) &&
          buttonRef.current && !buttonRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  // Close other dropdowns when this one opens
  useEffect(() => {
    if (isOpen) {
      // Close any other open dropdown
      if (globalCloseCallback && globalCloseCallback !== closeDropdown) {
        globalCloseCallback();
      }
      globalCloseCallback = closeDropdown;
    }
    
    return () => {
      if (globalCloseCallback === closeDropdown) {
        globalCloseCallback = null;
      }
    };
  }, [isOpen]);

  const closeDropdown = () => setIsOpen(false);

  const handleToggle = (e) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const handleAction = (e, action) => {
    e.stopPropagation();
    setIsOpen(false);
    action();
  };

  const isPublished = book.is_published || book.publish_status === 'published';

  return (
    <div className={`relative ${className}`}>
      {/* Three dot button */}
      <Button
        ref={buttonRef}
        variant="outline"
        size="icon"
        className="rounded-full w-9 h-9 border-gray-200 hover:bg-gray-100"
        onClick={handleToggle}
        data-testid={`book-actions-${book.id}`}
      >
        <FiMoreHorizontal className="w-4 h-4 text-gray-600" />
      </Button>

      {/* Dropdown menu - appears ABOVE the button */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute bottom-full mb-2 right-0 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-50 animate-in fade-in slide-in-from-bottom-2 duration-150"
          style={{ 
            boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.12)',
          }}
        >
          {/* Analytics */}
          <button
            className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-gray-50 transition-colors text-sm text-gray-700"
            onClick={(e) => handleAction(e, onAnalytics)}
            data-testid={`action-analytics-${book.id}`}
          >
            <FiBarChart2 className="w-4 h-4 text-blue-500" />
            <span>Analytics</span>
          </button>

          {/* Copy Link */}
          <button
            className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-gray-50 transition-colors text-sm text-gray-700"
            onClick={(e) => handleAction(e, onCopyLink)}
            data-testid={`action-copy-link-${book.id}`}
          >
            <FiLink className="w-4 h-4 text-green-500" />
            <span>Copy Link</span>
          </button>

          {/* Order Printed Copy */}
          <button
            className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-gray-50 transition-colors text-sm text-gray-700"
            onClick={(e) => handleAction(e, onOrderPrint)}
            data-testid={`action-print-${book.id}`}
          >
            <FiPackage className="w-4 h-4 text-purple-500" />
            <span>Order Printed Copy</span>
          </button>

          {/* Publish / Unpublish toggle */}
          <button
            className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-gray-50 transition-colors text-sm text-gray-700"
            onClick={(e) => handleAction(e, onTogglePublish)}
            data-testid={`action-publish-${book.id}`}
          >
            {isPublished ? (
              <>
                <FiEyeOff className="w-4 h-4 text-amber-500" />
                <span>Unpublish</span>
              </>
            ) : (
              <>
                <FiEye className="w-4 h-4 text-green-500" />
                <span>Publish</span>
              </>
            )}
          </button>

          {/* Divider */}
          <div className="h-px bg-gray-100 my-1" />

          {/* Delete - Red */}
          <button
            className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-red-50 transition-colors text-sm text-red-600"
            onClick={(e) => handleAction(e, onDelete)}
            data-testid={`action-delete-${book.id}`}
          >
            <FiTrash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
        </div>
      )}
    </div>
  );
}
