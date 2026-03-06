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

  const nextPage = () => {
    setCurrentPage((prev) => (prev + 1) % pages.length);
  };

  const prevPage = () => {
    setCurrentPage((prev) => (prev - 1 + pages.length) % pages.length);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-white/80 hover:text-white p-2"
      >
        <FiX className="w-6 h-6" />
      </button>

      {/* Page title */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 text-white text-center">
        <p className="text-sm text-white/60 mb-1">Bonus Page Preview</p>
        <h3 className="text-lg font-semibold">{pages[currentPage].name}</h3>
        <p className="text-sm text-white/60 mt-1">{currentPage + 1} of {pages.length}</p>
      </div>

      {/* Navigation arrows */}
      <button
        onClick={prevPage}
        className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
      >
        <FiChevronLeft className="w-6 h-6" />
      </button>

      <button
        onClick={nextPage}
        className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
      >
        <FiChevronRight className="w-6 h-6" />
      </button>

      {/* Page preview - 8x8 aspect ratio */}
      <div className="w-full max-w-lg aspect-square bg-white rounded-lg shadow-2xl overflow-hidden">
        {pages[currentPage].component}
      </div>

      {/* Page dots */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
        {pages.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentPage(idx)}
            className={`w-2 h-2 rounded-full transition-colors ${
              idx === currentPage ? 'bg-white' : 'bg-white/30 hover:bg-white/50'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default BonusPagesPreview;
