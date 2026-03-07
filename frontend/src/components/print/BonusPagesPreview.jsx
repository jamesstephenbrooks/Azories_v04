/**
 * BonusPagesPreview - Preview component for bonus pages
 * Shows all bonus pages in a carousel for preview before printing
 */

import { useState } from 'react';
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

const BonusPagesPreview = ({ 
  isOpen, 
  onClose, 
  bookTitle = 'My Amazing Story',
  childName = 'Little Reader',
  dedicationMessage = '"Every story is an adventure waiting to unfold!"'
}) => {
  const [currentPage, setCurrentPage] = useState(0);

  const pages = [
    { name: 'Welcome', component: <WelcomePage bookTitle={bookTitle} childName={childName} /> },
    { name: 'Dedication', component: <DedicationPage childName={childName} dedicationMessage={dedicationMessage} /> },
    { name: 'The End', component: <TheEndPage bookTitle={bookTitle} /> },
    { name: 'Thank You', component: <ThankYouPage childName={childName} /> },
    { name: 'Certificate', component: <CertificatePage childName={childName} bookTitle={bookTitle} /> },
    { name: 'About Azories', component: <AboutAzoriesPage /> },
    { name: 'Meet Azora', component: <MeetAzoraPage /> },
  ];

  const nextPage = (e) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    setCurrentPage((prev) => (prev + 1) % pages.length);
  };

  const prevPage = (e) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    setCurrentPage((prev) => (prev - 1 + pages.length) % pages.length);
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4"
      onClick={(e) => {
        e.stopPropagation();
        e.preventDefault();
      }}
      onMouseDown={(e) => e.stopPropagation()}
      onTouchStart={(e) => e.stopPropagation()}
    >
      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        className="absolute top-4 right-4 text-white/80 hover:text-white p-2 z-10 touch-manipulation"
      >
        <FiX className="w-6 h-6" />
      </button>

      {/* Page title */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 text-white text-center">
        <p className="text-sm text-white/60 mb-1">Bonus Page Preview</p>
        <h3 className="text-lg font-semibold">{pages[currentPage].name}</h3>
        <p className="text-sm text-white/60 mt-1">{currentPage + 1} of {pages.length}</p>
      </div>

      {/* Desktop Navigation arrows - hidden on mobile */}
      <button
        onClick={prevPage}
        className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 items-center justify-center text-white transition-colors z-10 touch-manipulation"
      >
        <FiChevronLeft className="w-6 h-6" />
      </button>

      <button
        onClick={nextPage}
        className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 items-center justify-center text-white transition-colors z-10 touch-manipulation"
      >
        <FiChevronRight className="w-6 h-6" />
      </button>

      {/* Page preview - 8x11 aspect ratio (portrait book format) */}
      <div 
        className="w-full max-w-sm bg-white rounded-lg shadow-2xl overflow-hidden"
        style={{ aspectRatio: '8/11' }}
      >
        <div className="w-full h-full overflow-hidden">
          {pages[currentPage].component}
        </div>
      </div>

      {/* Mobile Navigation buttons - shown only on mobile, positioned below the preview */}
      <div className="md:hidden absolute bottom-20 left-1/2 -translate-x-1/2 flex items-center gap-4 z-10">
        <button
          onClick={prevPage}
          className="flex items-center gap-2 px-5 py-3 rounded-full bg-white/20 hover:bg-white/30 active:bg-white/40 text-white font-medium transition-colors touch-manipulation"
        >
          <FiChevronLeft className="w-5 h-5" />
          Prev
        </button>
        <button
          onClick={nextPage}
          className="flex items-center gap-2 px-5 py-3 rounded-full bg-white/20 hover:bg-white/30 active:bg-white/40 text-white font-medium transition-colors touch-manipulation"
        >
          Next
          <FiChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Page dots */}
      <div className="absolute bottom-4 md:bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
        {pages.map((_, idx) => (
          <button
            key={idx}
            onClick={(e) => {
              e.stopPropagation();
              setCurrentPage(idx);
            }}
            className={`w-3 h-3 md:w-2 md:h-2 rounded-full transition-colors touch-manipulation ${
              idx === currentPage ? 'bg-white' : 'bg-white/30 hover:bg-white/50'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default BonusPagesPreview;
