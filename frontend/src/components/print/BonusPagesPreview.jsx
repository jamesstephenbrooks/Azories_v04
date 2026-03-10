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

function BonusPagesPreview(props) {
  const { isOpen, onClose, bookTitle, childName, dedicationMessage } = props;
  const [currentPage, setCurrentPage] = useState(0);
  
  const title = bookTitle || 'My Amazing Story';
  const name = childName || 'Little Reader';
  const message = dedicationMessage || '"Every story is an adventure waiting to unfold!"';
  
  const pageNames = ['Welcome', 'Dedication', 'The End', 'Thank You', 'Certificate', 'About Azories', 'Meet Azora'];
  const totalPages = 7;

  function handleNext(e) {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    setCurrentPage(function(prev) {
      return (prev + 1) % totalPages;
    });
  }

  function handlePrev(e) {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    setCurrentPage(function(prev) {
      return (prev - 1 + totalPages) % totalPages;
    });
  }

  function handleDotClick(e, idx) {
    e.stopPropagation();
    setCurrentPage(idx);
  }

  function handleClose(e) {
    e.stopPropagation();
    onClose();
  }

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
      className="fixed inset-0 z-[9999] bg-black/80 flex items-center justify-center p-4"
      onClick={function(e) { e.stopPropagation(); e.preventDefault(); }}
      onMouseDown={function(e) { e.stopPropagation(); }}
      onTouchStart={function(e) { e.stopPropagation(); }}
      style={{ zIndex: 9999 }}
    >
      <button
        onClick={handleClose}
        className="absolute top-4 right-4 text-white/80 hover:text-white p-3 z-[10001] touch-manipulation cursor-pointer"
        style={{ zIndex: 10001, touchAction: 'manipulation' }}
        aria-label="Close preview"
      >
        <FiX className="w-8 h-8" />
      </button>

      <div className="absolute top-4 left-1/2 -translate-x-1/2 text-white text-center">
        <p className="text-sm text-white/60 mb-1">Bonus Page Preview</p>
        <h3 className="text-lg font-semibold">{pageNames[currentPage]}</h3>
        <p className="text-sm text-white/60 mt-1">{currentPage + 1} of {totalPages}</p>
      </div>

      <button
        onClick={handlePrev}
        className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2 w-14 h-14 rounded-full bg-white/20 hover:bg-white/30 items-center justify-center text-white transition-colors z-[10001] touch-manipulation cursor-pointer"
        style={{ zIndex: 10001 }}
      >
        <FiChevronLeft className="w-7 h-7" />
      </button>

      <button
        onClick={handleNext}
        className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 w-14 h-14 rounded-full bg-white/20 hover:bg-white/30 items-center justify-center text-white transition-colors z-[10001] touch-manipulation cursor-pointer"
        style={{ zIndex: 10001 }}
      >
        <FiChevronRight className="w-7 h-7" />
      </button>

      <div 
        className="w-full max-w-sm bg-white rounded-lg shadow-2xl overflow-hidden"
        style={{ aspectRatio: '8/11' }}
      >
        <div className="w-full h-full overflow-hidden">
          {renderCurrentPage()}
        </div>
      </div>

      <div className="md:hidden absolute bottom-20 left-1/2 -translate-x-1/2 flex items-center gap-4 z-[10001]" style={{ zIndex: 10001 }}>
        <button
          onClick={handlePrev}
          className="flex items-center gap-2 px-6 py-4 rounded-full bg-white/30 hover:bg-white/40 active:bg-white/50 text-white font-medium transition-colors touch-manipulation cursor-pointer"
          style={{ touchAction: 'manipulation', minWidth: '100px' }}
        >
          <FiChevronLeft className="w-5 h-5" />
          Prev
        </button>
        <button
          onClick={handleNext}
          className="flex items-center gap-2 px-6 py-4 rounded-full bg-white/30 hover:bg-white/40 active:bg-white/50 text-white font-medium transition-colors touch-manipulation cursor-pointer"
          style={{ touchAction: 'manipulation', minWidth: '100px' }}
        >
          Next
          <FiChevronRight className="w-5 h-5" />
        </button>
      </div>

      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3 z-[10001]" style={{ zIndex: 10001 }}>
        <button onClick={function(e) { handleDotClick(e, 0); }} className={'w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation cursor-pointer ' + (currentPage === 0 ? 'bg-white' : 'bg-white/30 hover:bg-white/50')} />
        <button onClick={function(e) { handleDotClick(e, 1); }} className={'w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation cursor-pointer ' + (currentPage === 1 ? 'bg-white' : 'bg-white/30 hover:bg-white/50')} />
        <button onClick={function(e) { handleDotClick(e, 2); }} className={'w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation cursor-pointer ' + (currentPage === 2 ? 'bg-white' : 'bg-white/30 hover:bg-white/50')} />
        <button onClick={function(e) { handleDotClick(e, 3); }} className={'w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation cursor-pointer ' + (currentPage === 3 ? 'bg-white' : 'bg-white/30 hover:bg-white/50')} />
        <button onClick={function(e) { handleDotClick(e, 4); }} className={'w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation cursor-pointer ' + (currentPage === 4 ? 'bg-white' : 'bg-white/30 hover:bg-white/50')} />
        <button onClick={function(e) { handleDotClick(e, 5); }} className={'w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation cursor-pointer ' + (currentPage === 5 ? 'bg-white' : 'bg-white/30 hover:bg-white/50')} />
        <button onClick={function(e) { handleDotClick(e, 6); }} className={'w-4 h-4 md:w-3 md:h-3 rounded-full transition-colors touch-manipulation cursor-pointer ' + (currentPage === 6 ? 'bg-white' : 'bg-white/30 hover:bg-white/50')} />
      </div>
    </div>
  );
}

export default BonusPagesPreview;
