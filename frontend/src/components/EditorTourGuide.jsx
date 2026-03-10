import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { FiEdit3, FiImage, FiZap, FiPlus, FiArrowRight, FiArrowLeft, FiX, FiCheck, FiBookOpen } from 'react-icons/fi';
import { AZORA_ASSETS } from '@/components/AzoraMascot';

const EDITOR_TOUR_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to the Book Editor!',
    description: "Let's take a quick tour of the tools you'll use to create your story.",
    icon: FiBookOpen,
    target: null, // No specific target, centered modal
    position: 'center',
    mascot: true
  },
  {
    id: 'text-editor',
    title: 'Write Your Story',
    description: 'Click on any page and type your story here. Your text auto-saves as you write.',
    icon: FiEdit3,
    target: '[data-tour="text-editor"]',
    position: 'right',
    highlight: true
  },
  {
    id: 'ai-polish',
    title: 'AI Author Polish',
    description: 'Click the magic wand to let AI improve your writing — fix grammar, enhance descriptions, and make it sparkle!',
    icon: FiZap,
    target: '[data-tour="ai-polish"]',
    position: 'bottom',
    highlight: true
  },
  {
    id: 'generate-image',
    title: 'Generate Illustrations',
    description: 'Click here to create AI-generated images for your page. Describe the scene and watch the magic happen!',
    icon: FiImage,
    target: '[data-tour="generate-image"]',
    position: 'left',
    highlight: true
  },
  {
    id: 'add-page',
    title: 'Add New Pages',
    description: 'Click the + button to add more pages to your story. You can have as many as you need!',
    icon: FiPlus,
    target: '[data-tour="add-page"]',
    position: 'top',
    highlight: true
  },
  {
    id: 'complete',
    title: "You're Ready!",
    description: "That's it! Start writing your story and let your imagination run wild. Happy creating!",
    icon: FiCheck,
    target: null,
    position: 'center',
    mascot: true
  }
];

const STORAGE_KEY = 'azories-editor-tour-complete';

export function useEditorTour() {
  const [hasSeenTour, setHasSeenTour] = useState(true); // Default to true to prevent flash

  useEffect(() => {
    const seen = localStorage.getItem(STORAGE_KEY);
    setHasSeenTour(seen === 'true');
  }, []);

  const completeTour = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setHasSeenTour(true);
  }, []);

  const resetTour = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setHasSeenTour(false);
  }, []);

  return { hasSeenTour, completeTour, resetTour, shouldShowTour: !hasSeenTour };
}

export default function EditorTourGuide({ onComplete, isOpen = true }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState(null);
  const [, forceUpdate] = useState(0); // For re-rendering on orientation change

  const step = EDITOR_TOUR_STEPS[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === EDITOR_TOUR_STEPS.length - 1;
  const Icon = step.icon;

  // Force re-render on orientation change for proper centering
  useEffect(() => {
    const handleOrientationChange = () => {
      // Small delay to let browser finish rotation
      setTimeout(() => forceUpdate(n => n + 1), 150);
    };

    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('resize', handleOrientationChange);
    
    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
      window.removeEventListener('resize', handleOrientationChange);
    };
  }, []);

  // Find and highlight the target element
  useEffect(() => {
    if (!step.target) {
      setTargetRect(null);
      return;
    }

    const findTarget = () => {
      const element = document.querySelector(step.target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect({
          top: rect.top,
          left: rect.left,
          width: rect.width,
          height: rect.height
        });
        
        // Scroll element into view if needed
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        setTargetRect(null);
      }
    };

    // Small delay to let DOM render
    const timer = setTimeout(findTarget, 300);
    
    // Also listen for resize
    window.addEventListener('resize', findTarget);
    
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', findTarget);
    };
  }, [step.target, currentStep]);

  const handleNext = () => {
    if (isLastStep) {
      handleComplete();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirstStep) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleComplete = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    if (onComplete) onComplete();
  };

  // Calculate tooltip position based on target and preferred position
  const getTooltipStyle = () => {
    if (!targetRect || step.position === 'center') {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)'
      };
    }

    const padding = 16;
    const tooltipWidth = 320;
    const tooltipHeight = 200;
    
    // On mobile (small screens), always center the tooltip
    const isMobile = window.innerWidth < 640;
    if (isMobile) {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        maxWidth: 'calc(100vw - 32px)'
      };
    }

    switch (step.position) {
      case 'right':
        return {
          position: 'fixed',
          top: Math.max(padding, Math.min(targetRect.top, window.innerHeight - tooltipHeight - padding)),
          left: Math.min(targetRect.left + targetRect.width + padding, window.innerWidth - tooltipWidth - padding)
        };
      case 'left':
        return {
          position: 'fixed',
          top: Math.max(padding, Math.min(targetRect.top, window.innerHeight - tooltipHeight - padding)),
          left: Math.max(padding, targetRect.left - tooltipWidth - padding)
        };
      case 'bottom':
        return {
          position: 'fixed',
          top: Math.min(targetRect.top + targetRect.height + padding, window.innerHeight - tooltipHeight - padding),
          left: Math.max(padding, Math.min(targetRect.left, window.innerWidth - tooltipWidth - padding))
        };
      case 'top':
        return {
          position: 'fixed',
          top: Math.max(padding, targetRect.top - tooltipHeight - padding),
          left: Math.max(padding, Math.min(targetRect.left, window.innerWidth - tooltipWidth - padding))
        };
      default:
        return {
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)'
        };
    }
  };

  if (!isOpen) return null;

  // Don't show tour on mobile devices - user requested removal due to alignment issues
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  if (isMobile) {
    // Auto-complete the tour for mobile users
    onComplete?.();
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[9999]"
        style={{ zIndex: 9999 }}
      >
        {/* Dark overlay/backdrop */}
        <div 
          className="fixed inset-0 bg-black/80" 
          style={{ zIndex: 9999 }}
          onClick={handleSkip} 
        />

        {/* Tooltip card - ALWAYS centered with inline styles for all mobile orientations */}
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.3 }}
          className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl border border-purple-500/30 overflow-hidden"
          style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 'min(90vw, 340px)',
            maxWidth: '340px',
            maxHeight: '90vh',
            overflowY: 'auto',
            zIndex: 10000,
            // Ensure it stays centered in both portrait and landscape
            margin: '0 auto'
          }}
        >
          {/* Header with mascot or icon */}
          <div className="p-4 bg-gradient-to-r from-purple-600 to-pink-600">
            <div className="flex items-center gap-3">
              {step.mascot ? (
                <img 
                  src={AZORA_ASSETS.pointing} 
                  alt="Azora" 
                  className="w-12 h-14 object-contain"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                  <Icon className="w-5 h-5 text-white" />
                </div>
              )}
              <div>
                <h3 className="font-bold text-white text-lg">{step.title}</h3>
                <p className="text-white/70 text-xs">
                  Step {currentStep + 1} of {EDITOR_TOUR_STEPS.length}
                </p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-4">
            <p className="text-slate-300 text-sm leading-relaxed">
              {step.description}
            </p>
          </div>

          {/* Navigation */}
          <div className="px-4 pb-4 flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              className="text-slate-400 hover:text-white"
            >
              <FiX className="w-4 h-4 mr-1" />
              Skip Tour
            </Button>

            <div className="flex gap-2">
              {!isFirstStep && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrev}
                  className="border-slate-600"
                >
                  <FiArrowLeft className="w-4 h-4" />
                </Button>
              )}
              <Button
                size="sm"
                onClick={handleNext}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {isLastStep ? (
                  <>
                    <FiCheck className="w-4 h-4 mr-1" />
                    Got it!
                  </>
                ) : (
                  <>
                    Next
                    <FiArrowRight className="w-4 h-4 ml-1" />
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Progress dots */}
          <div className="px-4 pb-3 flex justify-center gap-1.5">
            {EDITOR_TOUR_STEPS.map((_, idx) => (
              <div
                key={idx}
                className={`w-2 h-2 rounded-full transition-colors ${
                  idx === currentStep ? 'bg-purple-500' : 'bg-slate-600'
                }`}
              />
            ))}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
