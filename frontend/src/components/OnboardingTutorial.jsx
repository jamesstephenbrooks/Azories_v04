import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { FiBook, FiEdit3, FiHeadphones, FiShare2, FiStar, FiArrowRight, FiX, FiCheck } from 'react-icons/fi';
import { AZORA_ASSETS, AZORIES_TAGLINE } from '@/components/AzoraMascot';

const ONBOARDING_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to Azories!',
    description: AZORIES_TAGLINE,
    icon: FiStar,
    color: 'from-purple-500 to-pink-500',
    mascotImage: AZORA_ASSETS.pointing,
    tips: [
      'Read amazing stories from young authors',
      'Create your own illustrated books',
      'Listen to audiobooks with auto-narration'
    ]
  },
  {
    id: 'browse',
    title: 'Explore the Library',
    description: 'Discover stories across all genres - Fantasy, Adventure, Mystery, and more.',
    icon: FiBook,
    color: 'from-blue-500 to-cyan-500',
    mascotImage: AZORA_ASSETS.readingCozy,
    tips: [
      'Browse featured and trending books',
      'Filter by genre or search by title',
      'Try the immersive 3D library view'
    ]
  },
  {
    id: 'read',
    title: 'Immersive Reading',
    description: 'Enjoy a beautiful reading experience with special features.',
    icon: FiHeadphones,
    color: 'from-green-500 to-emerald-500',
    mascotImage: AZORA_ASSETS.reading,
    tips: [
      'Auto-read narration with different voices',
      'Ambient sounds to set the mood',
      'Adjust speed and text size'
    ]
  },
  {
    id: 'create',
    title: 'Create Your Stories',
    description: 'Upgrade to Pro and become an author with AI-powered tools.',
    icon: FiEdit3,
    color: 'from-orange-500 to-red-500',
    mascotImage: AZORA_ASSETS.confident,
    tips: [
      'Write and illustrate your own books',
      'AI generates images for your story',
      'Auto-generate entire stories from ideas'
    ]
  }
];

export default function OnboardingTutorial({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  const handleNext = () => {
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      handleComplete();
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleComplete = () => {
    localStorage.setItem('azories-onboarding-complete', 'true');
    setIsVisible(false);
    if (onComplete) onComplete();
  };

  const step = ONBOARDING_STEPS[currentStep];
  const Icon = step.icon;
  const isLastStep = currentStep === ONBOARDING_STEPS.length - 1;

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      >
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: -20 }}
          transition={{ type: 'spring', damping: 20 }}
          className="relative bg-background rounded-3xl shadow-2xl max-w-md w-full overflow-hidden"
        >
          {/* Skip Button */}
          <button
            onClick={handleSkip}
            className="absolute top-4 right-4 p-2 text-muted-foreground hover:text-foreground transition-colors z-10"
          >
            <FiX className="w-5 h-5" />
          </button>

          {/* Gradient Header */}
          <div className={`bg-gradient-to-r ${step.color} p-8 text-white`}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mb-4 backdrop-blur"
            >
              <Icon className="w-8 h-8" />
            </motion.div>
            <h2 className="text-2xl font-bold mb-2">{step.title}</h2>
            <p className="text-white/80">{step.description}</p>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Tips */}
            <div className="space-y-3 mb-6">
              {step.tips.map((tip, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  className="flex items-center gap-3"
                >
                  <div className={`w-6 h-6 rounded-full bg-gradient-to-r ${step.color} flex items-center justify-center flex-shrink-0`}>
                    <FiCheck className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm text-muted-foreground">{tip}</span>
                </motion.div>
              ))}
            </div>

            {/* Progress Dots */}
            <div className="flex justify-center gap-2 mb-6">
              {ONBOARDING_STEPS.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentStep 
                      ? 'w-6 bg-primary' 
                      : index < currentStep
                        ? 'bg-primary/50'
                        : 'bg-muted'
                  }`}
                />
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              {currentStep > 0 && (
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(prev => prev - 1)}
                  className="flex-1 rounded-full"
                >
                  Back
                </Button>
              )}
              <Button
                onClick={handleNext}
                className={`flex-1 rounded-full bg-gradient-to-r ${step.color} hover:opacity-90 text-white border-0`}
              >
                {isLastStep ? (
                  <>Get Started</>
                ) : (
                  <>
                    Next <FiArrowRight className="ml-2" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// Hook to check if onboarding should be shown
export function useOnboarding() {
  // Initialize from localStorage synchronously to prevent flash
  const [shouldShow, setShouldShow] = useState(() => {
    // Check localStorage immediately during initial render
    if (typeof window !== 'undefined') {
      const completed = localStorage.getItem('azories-onboarding-complete');
      return !completed;
    }
    return false;
  });

  // Also verify on mount (for SSR compatibility)
  useEffect(() => {
    const completed = localStorage.getItem('azories-onboarding-complete');
    setShouldShow(!completed);
  }, []);

  const completeOnboarding = () => {
    localStorage.setItem('azories-onboarding-complete', 'true');
    setShouldShow(false);
  };

  const resetOnboarding = () => {
    localStorage.removeItem('azories-onboarding-complete');
    setShouldShow(true);
  };

  return { shouldShow, setShouldShow, completeOnboarding, resetOnboarding };
}
