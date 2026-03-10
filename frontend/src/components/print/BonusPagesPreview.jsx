import { useState, useCallback } from 'react';
import { FiChevronLeft, FiChevronRight, FiX } from 'react-icons/fi';
import {
  WelcomePage,
  DedicationPage,
  TheEndPage,
  ThankYouPage,
  AboutAzoriesPage,
  CertificatePage,
  MeetAzoraPage,
} from './BonusPages';

function BonusPagesPreview(props) {
  const { isOpen, onClose, bookTitle, childName, dedicationMessage } = props;
  const [currentPage, setCurrentPage] = useState(0);
  
  const title = bookTitle || 'My Amazing Story';
  const name = childName || 'Little Reader';
  const message = dedicationMessage || '"Every story is an adventure waiting to unfold!"';
  
  const pageNames = ['Welcome', 'Dedication', 'The End', 'Thank You', 'Certificate', 'About Azories', 'Meet Azora'];
  const totalPages = 7;

  const handleNext = useCallback((e) => {
    if (e) { e.stopPropagation(); e.preventDefault(); }
    setCurrentPage((prev) => (prev + 1) % totalPages);
  }, []);

  const handlePrev = useCallback((e) => {
    if (e) { e.stopPropagation(); e.preventDefault(); }
    setCurrentPage((prev) => (prev - 1 + totalPages) % totalPages);
  }, []);

  const handleClose = useCallback((e) => {
    if (e) { e.stopPropagation(); e.preventDefault(); }
    onClose();
  }, [onClose]);

  const handleDotClick = useCallback((e, idx) => {
    if (e) { e.stopPropagation(); e.preventDefault(); }
    setCurrentPage(idx);
  }, []);

  function renderCurrentPage() {
    if (currentPage === 0) return <WelcomePage bookTitle={title} childName={name} />;
    if (currentPage === 1) return <DedicationPage childName={name} dedicationMessage={message} />;
    if (currentPage === 2) return <TheEndPage bookTitle={title} />;
    if (currentPage === 3) return <ThankYouPage childName={name} />;
    if (currentPage === 4) return <CertificatePage childName={name} bookTitle={title} />;
    if (currentPage === 5) return <AboutAzoriesPage />;
    if (currentPage === 6) return <MeetAzoraPage />;
    return <WelcomePage bookTitle={title} childName={name} />;
  }

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/80 flex items-center justify-center p-4"
      style={{ zIndex: 99999, pointerEvents: 'auto' }}
      onClick={handleClose}
      data-testid="bonus-preview-overlay"
    >
      {/* Close button */}
      <button
        onClick={handleClose}
        onTouchEnd={handleClose}
        className="absolute top-4 right-4 text-white/80 hover:text-white p-3 touch-manipulation"
        style={{ zIndex: 100001, pointerEvents: 'auto' }}
        aria-label="Close preview"
        data-testid="bonus-preview-close"
      >
        <FiX className="w-8 h-8" />
      </button>

      {/* Title area */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 text-white text-center" style={{ pointerEvents: 'none' }}>
        <p className="text-sm text-white/60 mb-1">Bonus Page Preview</p>
        <h3 className="text-lg font-semibold">{pageNames[currentPage]}</h3>
        <p className="text-sm text-white/60 mt-1">{currentPage + 1} of {totalPages}</p>
      </div>

      {/* Desktop prev/next - left/right sides */}
      <button
        onClick={handlePrev}
        onTouchEnd={handlePrev}
        className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2 w-14 h-14 rounded-full bg-white/20 hover:bg-white/30 active:bg-white/50 items-center justify-center text-white transition-colors touch-manipulation"
        style={{ zIndex: 100001, pointerEvents: 'auto' }}
        data-testid="bonus-preview-prev-desktop"
      >
        <FiChevronLeft className="w-7 h-7" />
      </button>

      <button
        onClick={handleNext}
        onTouchEnd={handleNext}
        className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 w-14 h-14 rounded-full bg-white/20 hover:bg-white/30 active:bg-white/50 items-center justify-center text-white transition-colors touch-manipulation"
        style={{ zIndex: 100001, pointerEvents: 'auto' }}
        data-testid="bonus-preview-next-desktop"
      >
        <FiChevronRight className="w-7 h-7" />
      </button>

      {/* Page content card - stops click from closing */}
      <div 
        className="w-full max-w-sm bg-white rounded-lg shadow-2xl overflow-hidden"
        style={{ aspectRatio: '8/11', pointerEvents: 'auto' }}
        onClick={(e) => e.stopPropagation()}
        onTouchEnd={(e) => e.stopPropagation()}
      >
        <div className="w-full h-full overflow-hidden">
          {renderCurrentPage()}
        </div>
      </div>

      {/* Mobile prev/next - bottom bar */}
      <div className="md:hidden absolute bottom-20 left-1/2 -translate-x-1/2 flex items-center gap-4" style={{ zIndex: 100001, pointerEvents: 'auto' }}>
        <button
          onClick={handlePrev}
          onTouchEnd={handlePrev}
          className="flex items-center gap-2 px-6 py-4 rounded-full bg-white/30 hover:bg-white/40 active:bg-white/50 text-white font-medium transition-colors touch-manipulation"
          style={{ pointerEvents: 'auto', minWidth: '100px' }}
          data-testid="bonus-preview-prev-mobile"
        >
          <FiChevronLeft className="w-5 h-5" />
          Prev
        </button>
        <button
          onClick={handleNext}
          onTouchEnd={handleNext}
          className="flex items-center gap-2 px-6 py-4 rounded-full bg-white/30 hover:bg-white/40 active:bg-white/50 text-white font-medium transition-colors touch-manipulation"
          style={{ pointerEvents: 'auto', minWidth: '100px' }}
          data-testid="bonus-preview-next-mobile"
        >
          Next
          <FiChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Page indicator dots */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3" style={{ zIndex: 100001, pointerEvents: 'auto' }}>
        {pageNames.map((_, idx) => (
          <button
            key={idx}
            onClick={(e) => handleDotClick(e, idx)}
            onTouchEnd={(e) => handleDotClick(e, idx)}
            className={`w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation ${currentPage === idx ? 'bg-white' : 'bg-white/30 hover:bg-white/50'}`}
            style={{ pointerEvents: 'auto' }}
            data-testid={`bonus-preview-dot-${idx}`}
          />
        ))}
      </div>
    </div>
  );
}

export default BonusPagesPreview;
