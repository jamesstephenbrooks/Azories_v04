import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';
import { 
  FiZap, FiBook, FiLoader, FiCheck, FiX, FiArrowLeft, FiArrowRight,
  FiImage, FiFeather, FiStar, FiHeart, FiClock, FiDollarSign
} from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Azora mascot SVG
const AzoraMascot = ({ className = "", animate = false }) => (
  <motion.div
    className={className}
    animate={animate ? { y: [0, -10, 0] } : {}}
    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
  >
    <img 
      src="/azora-mascot.png" 
      alt="Azora" 
      className="w-full h-full object-contain"
      onError={(e) => {
        e.target.style.display = 'none';
      }}
    />
  </motion.div>
);

export default function StoryCreator() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const pollIntervalRef = useRef(null);
  
  // Mode toggle: 'kids' or 'studio'
  const [creatorMode, setCreatorMode] = useState('kids');
  const [showModeWarning, setShowModeWarning] = useState(false);
  
  // Pricing and options from backend
  const [pricing, setPricing] = useState(null);
  const [credits, setCredits] = useState(0);
  const [trialStatus, setTrialStatus] = useState({ has_free_stories: false, free_stories_remaining: 0 });
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    character_name: '',
    character_description: '',
    story_description: '',
    age_range: '6-8',
    num_pages: 5,
    words_per_page: 'medium',
    art_style: '3d-pixar',
    // Studio mode extras
    genre: 'Adventure',
    tone: '',
    plot_summary: '',
    chapter_structure: false
  });
  
  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  
  // Check for existing job in URL
  useEffect(() => {
    const jobId = searchParams.get('job');
    if (jobId) {
      setCurrentJobId(jobId);
      setIsGenerating(true);
      startPolling(jobId);
    }
  }, [searchParams]);
  
  // Auth check
  useEffect(() => {
    if (!authLoading && !user && !localStorage.getItem('azories-token')) {
      navigate('/auth', { state: { from: '/ai-stories' } });
    }
  }, [user, authLoading, navigate]);
  
  // Load pricing and user data
  useEffect(() => {
    if (user) {
      fetchPricing();
      fetchCredits();
      fetchTrialStatus();
      checkActiveJobs();
    }
  }, [user]);
  
  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);
  
  const fetchPricing = async () => {
    try {
      const res = await axios.get(`${API}/ai/story-pricing`);
      setPricing(res.data);
    } catch (error) {
      console.error('Failed to fetch pricing:', error);
    }
  };
  
  const fetchCredits = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCredits(res.data.credits || 0);
    } catch (error) {
      console.error('Failed to fetch credits:', error);
    }
  };
  
  const fetchTrialStatus = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/auth/ai-story-trial`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrialStatus(res.data);
    } catch (error) {
      console.error('Failed to fetch trial status:', error);
    }
  };
  
  const checkActiveJobs = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/jobs/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.data.jobs && res.data.jobs.length > 0) {
        // Resume the most recent active job
        const activeJob = res.data.jobs[0];
        setCurrentJobId(activeJob.job_id);
        setJobStatus(activeJob);
        setIsGenerating(true);
        startPolling(activeJob.job_id);
      }
    } catch (error) {
      console.error('Failed to check active jobs:', error);
    }
  };
  
  const startPolling = (jobId) => {
    // Clear any existing interval
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    
    // Poll immediately
    pollJobStatus(jobId);
    
    // Then poll every 5 seconds
    pollIntervalRef.current = setInterval(() => {
      pollJobStatus(jobId);
    }, 5000);
  };
  
  const pollJobStatus = async (jobId) => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/jobs/${jobId}/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setJobStatus(res.data);
      
      // Check if job is complete
      if (['completed', 'partial', 'failed'].includes(res.data.status)) {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        
        if (res.data.status === 'completed' || res.data.status === 'partial') {
          // Success! Show celebration then redirect
          setTimeout(() => {
            if (res.data.book_id) {
              navigate(`/read/${res.data.book_id}`);
            } else {
              navigate('/dashboard');
            }
          }, 3000);
        }
      }
    } catch (error) {
      console.error('Failed to poll job status:', error);
    }
  };
  
  const handleModeChange = (newMode) => {
    if (newMode === 'studio' && creatorMode === 'kids') {
      setShowModeWarning(true);
    }
    setCreatorMode(newMode);
    
    // Reset form data for new mode
    if (newMode === 'kids') {
      setFormData(prev => ({
        ...prev,
        age_range: '6-8',
        num_pages: 5,
        art_style: '3d-pixar'
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        age_range: '13-16',
        num_pages: 15,
        art_style: 'realistic'
      }));
    }
  };
  
  const getCreditsNeeded = () => {
    if (!pricing) return 5;
    return pricing.page_credits[formData.num_pages] || 5;
  };
  
  const canCreateFree = () => {
    return trialStatus.has_free_stories && 
           trialStatus.free_stories_remaining > 0 && 
           creatorMode === 'kids' && 
           formData.num_pages <= 5;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.story_description.trim()) {
      toast.error('Please describe your story idea');
      return;
    }
    
    const creditsNeeded = getCreditsNeeded();
    const isFree = canCreateFree();
    
    if (!isFree && credits < creditsNeeded) {
      toast.error(`You need ${creditsNeeded} credits. You have ${credits}.`);
      return;
    }
    
    try {
      setIsGenerating(true);
      const token = localStorage.getItem('azories-token');
      
      const res = await axios.post(`${API}/ai/generate-story-async`, {
        ...formData,
        creator_mode: creatorMode,
        idea: formData.story_description // backwards compatibility
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const jobId = res.data.job_id;
      setCurrentJobId(jobId);
      
      // Update URL to include job ID (so user can return)
      window.history.replaceState({}, '', `/ai-stories?job=${jobId}`);
      
      // Start polling
      startPolling(jobId);
      
      toast.success('Story generation started!');
      
      // Refresh credits
      fetchCredits();
      fetchTrialStatus();
      
    } catch (error) {
      console.error('Failed to start story generation:', error);
      toast.error(error.response?.data?.detail || 'Failed to start story generation');
      setIsGenerating(false);
    }
  };
  
  const cancelGeneration = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsGenerating(false);
    setCurrentJobId(null);
    setJobStatus(null);
    window.history.replaceState({}, '', '/ai-stories');
  };
  
  // Get current options based on mode
  const artStyles = pricing?.art_styles?.[creatorMode] || [];
  const ageRanges = pricing?.age_ranges?.[creatorMode] || [];
  const pageOptions = pricing?.page_options?.[creatorMode] || [5, 10, 15];
  
  // Story templates for Kids Mode
  const kidsTemplates = [
    { emoji: '🐉', title: 'Dragon Friend', character: 'A kind child', story: 'Finds a tiny lost dragon egg in the garden and must help it hatch and find its family' },
    { emoji: '🧙', title: 'Magic School', character: 'A curious young wizard', story: 'Discovers a hidden door that leads to a magical world full of friendly creatures' },
    { emoji: '🚀', title: 'Space Explorer', character: 'A brave young astronaut', story: 'Crash lands on a friendly alien planet and must find their way home' },
    { emoji: '🦁', title: 'Animal Friends', character: 'A small lion cub', story: 'Leo is scared of the dark and learns to be brave with help from woodland friends' },
  ];
  
  // Render progress page when generating
  if (isGenerating && jobStatus) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-950 via-purple-900 to-indigo-950">
        <Navbar />
        
        <div className="max-w-2xl mx-auto px-4 pt-20 pb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            {/* Azora Animation */}
            <div className="relative mb-8">
              <motion.div
                animate={{ 
                  scale: [1, 1.05, 1],
                  rotate: [0, 2, -2, 0]
                }}
                transition={{ duration: 3, repeat: Infinity }}
                className="w-32 h-32 mx-auto"
              >
                <div className="w-full h-full rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-6xl">
                  🐉
                </div>
              </motion.div>
              
              {/* Magic sparkles */}
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-3 h-3 rounded-full bg-yellow-400"
                  style={{
                    top: '50%',
                    left: '50%',
                  }}
                  animate={{
                    x: [0, (Math.random() - 0.5) * 150],
                    y: [0, (Math.random() - 0.5) * 150],
                    opacity: [0, 1, 0],
                    scale: [0, 1, 0]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.3
                  }}
                />
              ))}
            </div>
            
            {/* Status Title */}
            <h1 className="text-3xl font-bold text-white mb-2">
              {jobStatus.status === 'completed' ? '🎉 Your Story is Ready!' :
               jobStatus.status === 'partial' ? '📚 Story Created!' :
               jobStatus.status === 'failed' ? '😔 Generation Failed' :
               'Azora is Creating Your Story...'}
            </h1>
            
            <p className="text-purple-200 mb-8">
              {jobStatus.current_step || 'Starting...'}
            </p>
            
            {/* Progress Bar */}
            <div className="relative mb-8">
              <div className="h-4 bg-purple-900/50 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-amber-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${jobStatus.progress_percent || 0}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              <p className="text-sm text-purple-300 mt-2">
                {jobStatus.progress_percent || 0}% complete
              </p>
            </div>
            
            {/* Page Progress */}
            {jobStatus.total_pages > 0 && (
              <div className="mb-8">
                <p className="text-sm text-purple-300 mb-3">
                  {jobStatus.story_text_done ? 'Creating illustrations...' : 'Writing story...'}
                </p>
                
                <div className="flex flex-wrap justify-center gap-2">
                  {[...Array(jobStatus.total_pages)].map((_, i) => {
                    const pageNum = i + 1;
                    const status = jobStatus.images_status?.[pageNum] || 'pending';
                    
                    return (
                      <motion.div
                        key={pageNum}
                        className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-medium
                          ${status === 'done' ? 'bg-green-500 text-white' :
                            status === 'generating' ? 'bg-purple-500 text-white animate-pulse' :
                            status === 'failed' ? 'bg-red-500 text-white' :
                            'bg-purple-900/50 text-purple-300'}`}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: i * 0.1 }}
                      >
                        {status === 'done' ? <FiCheck /> :
                         status === 'generating' ? <FiLoader className="animate-spin" /> :
                         status === 'failed' ? <FiX /> :
                         pageNum}
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )}
            
            {/* Completion Actions */}
            {jobStatus.status === 'completed' && jobStatus.book_id && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-4"
              >
                <div className="text-6xl mb-4">🎊</div>
                <Button
                  onClick={() => navigate(`/read/${jobStatus.book_id}`)}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-6 text-lg rounded-full"
                >
                  <FiBook className="mr-2" /> Read Your Story
                </Button>
              </motion.div>
            )}
            
            {/* Partial completion */}
            {jobStatus.status === 'partial' && (
              <div className="space-y-4">
                <p className="text-amber-300 text-sm">
                  {jobStatus.error_message || 'Some illustrations could not be generated.'}
                </p>
                {jobStatus.book_id && (
                  <Button
                    onClick={() => navigate(`/read/${jobStatus.book_id}`)}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-full"
                  >
                    <FiBook className="mr-2" /> Read Anyway
                  </Button>
                )}
              </div>
            )}
            
            {/* Error state */}
            {jobStatus.status === 'failed' && (
              <div className="space-y-4">
                <p className="text-red-300 text-sm">
                  {jobStatus.error_message || 'Something went wrong.'}
                </p>
                <Button
                  onClick={cancelGeneration}
                  variant="outline"
                  className="border-purple-500 text-purple-300"
                >
                  Try Again
                </Button>
              </div>
            )}
            
            {/* Can navigate away message */}
            {!['completed', 'partial', 'failed'].includes(jobStatus.status) && (
              <p className="text-xs text-purple-400 mt-8">
                You can close this page and come back later — your story will keep generating!
              </p>
            )}
          </motion.div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`min-h-screen min-h-[100dvh] pb-safe ${creatorMode === 'kids' 
      ? 'bg-gradient-to-b from-purple-100 via-pink-50 to-amber-50' 
      : 'bg-gradient-to-b from-gray-950 via-gray-900 to-purple-950'}`}>
      <Navbar />
      
      <div className="max-w-4xl mx-auto px-4 pt-20 pb-24">
        {/* Mode Toggle */}
        <div className="flex justify-center mb-8">
          <div className={`inline-flex rounded-full p-1 ${creatorMode === 'kids' ? 'bg-white shadow-lg' : 'bg-gray-800'}`}>
            <button
              onClick={() => handleModeChange('kids')}
              className={`px-6 py-3 rounded-full text-sm font-medium transition-all ${
                creatorMode === 'kids'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              }`}
              data-testid="kids-mode-btn"
            >
              🐉 A Child
            </button>
            <button
              onClick={() => handleModeChange('studio')}
              className={`px-6 py-3 rounded-full text-sm font-medium transition-all ${
                creatorMode === 'studio'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg'
                  : creatorMode === 'kids' ? 'text-gray-600 hover:text-gray-800' : 'text-gray-400 hover:text-white'
              }`}
              data-testid="studio-mode-btn"
            >
              📖 Older Readers
            </button>
          </div>
        </div>
        
        {/* Mode Warning */}
        <AnimatePresence>
          {showModeWarning && creatorMode === 'studio' && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-6 p-4 rounded-xl bg-purple-900/50 border border-purple-500/30 text-center"
            >
              <p className="text-purple-200 text-sm">
                📚 <strong>Story Studio</strong> is designed for teens and adults — content will be more complex and mature
              </p>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowModeWarning(false)}
                className="mt-2 text-purple-400"
              >
                Got it
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Header */}
        <div className="text-center mb-8">
          {creatorMode === 'kids' ? (
            <>
              <div className="w-24 h-24 mx-auto mb-4 text-6xl">🐉</div>
              <h1 className="text-4xl font-bold text-purple-900 mb-2">
                AI Story Creator
              </h1>
              <p className="text-purple-600">
                Let Azora create a magical story just for you!
              </p>
            </>
          ) : (
            <>
              <h1 className="text-4xl font-bold text-white mb-2">
                Story Studio ✍️
              </h1>
              <p className="text-gray-400">
                Create sophisticated stories for teens and adults
              </p>
            </>
          )}
        </div>
        
        {/* Credits/Free Stories Banner */}
        <div className={`mb-6 p-4 rounded-xl ${
          creatorMode === 'kids' 
            ? 'bg-white shadow-lg border border-purple-100' 
            : 'bg-gray-800 border border-gray-700'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {canCreateFree() ? (
                <>
                  <span className="text-2xl">✨</span>
                  <span className={creatorMode === 'kids' ? 'text-purple-700' : 'text-purple-300'}>
                    <strong>{trialStatus.free_stories_remaining}</strong> free {trialStatus.free_stories_remaining === 1 ? 'story' : 'stories'} remaining!
                  </span>
                </>
              ) : (
                <>
                  <FiZap className={creatorMode === 'kids' ? 'text-amber-500' : 'text-amber-400'} />
                  <span className={creatorMode === 'kids' ? 'text-gray-700' : 'text-gray-300'}>
                    Cost: <strong>{getCreditsNeeded()} credits</strong> • You have <strong>{credits}</strong>
                  </span>
                </>
              )}
            </div>
            
            {!canCreateFree() && credits < getCreditsNeeded() && (
              <Button
                size="sm"
                onClick={() => navigate('/credits')}
                className="bg-amber-500 hover:bg-amber-600 text-white"
              >
                Buy Credits
              </Button>
            )}
          </div>
        </div>
        
        {/* Kids Mode Templates */}
        {creatorMode === 'kids' && (
          <div className="mb-8">
            <p className="text-sm text-purple-600 mb-3 text-center">💡 Quick start with a template:</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {kidsTemplates.map((template) => (
                <button
                  key={template.title}
                  onClick={() => {
                    setFormData(prev => ({
                      ...prev,
                      character_description: template.character,
                      story_description: template.story
                    }));
                    toast.success(`${template.emoji} ${template.title} template loaded!`);
                  }}
                  className="p-4 rounded-xl bg-white shadow-md hover:shadow-lg border-2 border-transparent hover:border-purple-300 transition-all text-center"
                  data-testid={`template-${template.title.toLowerCase().replace(' ', '-')}`}
                >
                  <div className="text-3xl mb-2">{template.emoji}</div>
                  <div className="text-sm font-medium text-purple-800">{template.title}</div>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <Card className={creatorMode === 'kids' ? 'bg-white shadow-xl' : 'bg-gray-800 border-gray-700'}>
            <CardContent className="p-6 space-y-6">
              
              {/* Character Section */}
              <div className="space-y-4">
                <h3 className={`font-semibold flex items-center gap-2 ${creatorMode === 'kids' ? 'text-purple-800' : 'text-white'}`}>
                  <FiHeart className="text-pink-500" /> Your Character
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className={creatorMode === 'kids' ? 'text-purple-700' : 'text-gray-300'}>
                      Character Name (optional)
                    </Label>
                    <Input
                      value={formData.character_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, character_name: e.target.value }))}
                      placeholder="e.g., Luna, Max, Spark"
                      className={creatorMode === 'kids' ? 'border-purple-200' : 'bg-gray-700 border-gray-600'}
                      data-testid="character-name-input"
                    />
                  </div>
                  
                  <div>
                    <Label className={creatorMode === 'kids' ? 'text-purple-700' : 'text-gray-300'}>
                      Who are they?
                    </Label>
                    <Input
                      value={formData.character_description}
                      onChange={(e) => setFormData(prev => ({ ...prev, character_description: e.target.value }))}
                      placeholder="e.g., A curious young dragon, A brave princess"
                      className={creatorMode === 'kids' ? 'border-purple-200' : 'bg-gray-700 border-gray-600'}
                      data-testid="character-desc-input"
                    />
                  </div>
                </div>
              </div>
              
              {/* Story Section */}
              <div className="space-y-4">
                <h3 className={`font-semibold flex items-center gap-2 ${creatorMode === 'kids' ? 'text-purple-800' : 'text-white'}`}>
                  <FiFeather className="text-purple-500" /> Your Story
                </h3>
                
                <div>
                  <Label className={creatorMode === 'kids' ? 'text-purple-700' : 'text-gray-300'}>
                    {creatorMode === 'kids' ? 'What happens in your story?' : 'Story Concept / Plot Summary'}
                  </Label>
                  <Textarea
                    value={formData.story_description}
                    onChange={(e) => setFormData(prev => ({ ...prev, story_description: e.target.value }))}
                    placeholder={creatorMode === 'kids' 
                      ? "e.g., They find a magical map that leads to a hidden treasure..."
                      : "Describe your story concept, plot points, and key themes..."
                    }
                    className={`min-h-[100px] ${creatorMode === 'kids' ? 'border-purple-200' : 'bg-gray-700 border-gray-600'}`}
                    data-testid="story-desc-input"
                  />
                </div>
                
                {/* Studio Mode: Extra fields */}
                {creatorMode === 'studio' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-gray-300">Genre</Label>
                      <Select
                        value={formData.genre}
                        onValueChange={(v) => setFormData(prev => ({ ...prev, genre: v }))}
                      >
                        <SelectTrigger className="bg-gray-700 border-gray-600">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {(pricing?.genres || ['Adventure', 'Fantasy', 'Mystery', 'Romance', 'Sci-Fi', 'Horror', 'Drama', 'Comedy']).map(g => (
                            <SelectItem key={g} value={g}>{g}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label className="text-gray-300">Tone (optional)</Label>
                      <Input
                        value={formData.tone}
                        onChange={(e) => setFormData(prev => ({ ...prev, tone: e.target.value }))}
                        placeholder="e.g., dark, humorous, emotional"
                        className="bg-gray-700 border-gray-600"
                      />
                    </div>
                  </div>
                )}
              </div>
              
              {/* Options Section */}
              <div className="space-y-4">
                <h3 className={`font-semibold flex items-center gap-2 ${creatorMode === 'kids' ? 'text-purple-800' : 'text-white'}`}>
                  <FiStar className="text-amber-500" /> Options
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Age Range */}
                  <div>
                    <Label className={creatorMode === 'kids' ? 'text-purple-700' : 'text-gray-300'}>
                      Age Range
                    </Label>
                    <Select
                      value={formData.age_range}
                      onValueChange={(v) => setFormData(prev => ({ ...prev, age_range: v }))}
                    >
                      <SelectTrigger className={creatorMode === 'kids' ? 'border-purple-200' : 'bg-gray-700 border-gray-600'} data-testid="age-range-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ageRanges.map(age => (
                          <SelectItem key={age.id} value={age.id}>
                            {age.emoji} {age.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Page Count */}
                  <div>
                    <Label className={creatorMode === 'kids' ? 'text-purple-700' : 'text-gray-300'}>
                      Pages
                    </Label>
                    <Select
                      value={String(formData.num_pages)}
                      onValueChange={(v) => setFormData(prev => ({ ...prev, num_pages: parseInt(v) }))}
                    >
                      <SelectTrigger className={creatorMode === 'kids' ? 'border-purple-200' : 'bg-gray-700 border-gray-600'} data-testid="pages-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {pageOptions.map(pages => (
                          <SelectItem key={pages} value={String(pages)}>
                            {pages} pages ({pricing?.page_credits?.[pages] || pages} credits)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Words per Page */}
                  <div>
                    <Label className={creatorMode === 'kids' ? 'text-purple-700' : 'text-gray-300'}>
                      Words per Page
                    </Label>
                    <Select
                      value={formData.words_per_page}
                      onValueChange={(v) => setFormData(prev => ({ ...prev, words_per_page: v }))}
                    >
                      <SelectTrigger className={creatorMode === 'kids' ? 'border-purple-200' : 'bg-gray-700 border-gray-600'} data-testid="words-per-page-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="short">
                          <span className="flex items-center gap-2">
                            Short (~50 words)
                            <span className="text-xs text-muted-foreground">Quick reads</span>
                          </span>
                        </SelectItem>
                        <SelectItem value="medium">
                          <span className="flex items-center gap-2">
                            Medium (~100 words)
                            <span className="text-xs text-muted-foreground">Recommended</span>
                          </span>
                        </SelectItem>
                        <SelectItem value="long">
                          <span className="flex items-center gap-2">
                            Long (~150 words)
                            <span className="text-xs text-muted-foreground">More detail</span>
                          </span>
                        </SelectItem>
                        {creatorMode === 'studio' && (
                          <SelectItem value="long_adult">
                            <span className="flex items-center gap-2">
                              Extended (~200 words)
                              <span className="text-xs text-muted-foreground">Novel-style</span>
                            </span>
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Art Style */}
                  <div>
                    <Label className={creatorMode === 'kids' ? 'text-purple-700' : 'text-gray-300'}>
                      Art Style
                    </Label>
                    <Select
                      value={formData.art_style}
                      onValueChange={(v) => setFormData(prev => ({ ...prev, art_style: v }))}
                    >
                      <SelectTrigger className={creatorMode === 'kids' ? 'border-purple-200' : 'bg-gray-700 border-gray-600'} data-testid="art-style-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {artStyles.map(style => (
                          <SelectItem key={style.id} value={style.id}>
                            <span className="flex items-center gap-2">
                              {style.emoji} {style.name}
                              {style.badge && (
                                <span className="text-[10px] bg-green-500 text-white px-1.5 py-0.5 rounded-full font-medium">
                                  {style.badge}
                                </span>
                              )}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {/* Chapter structure for longer books */}
                {creatorMode === 'studio' && formData.num_pages >= 20 && (
                  <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.chapter_structure}
                      onChange={(e) => setFormData(prev => ({ ...prev, chapter_structure: e.target.checked }))}
                      className="rounded"
                    />
                    Organize into chapters
                  </label>
                )}
              </div>
            </CardContent>
          </Card>
          
          {/* Submit Button */}
          <div className="flex justify-center">
            <Button
              type="submit"
              disabled={isGenerating || (!canCreateFree() && credits < getCreditsNeeded())}
              className={`px-12 py-6 text-lg rounded-full ${
                creatorMode === 'kids'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
              }`}
              data-testid="create-story-btn"
            >
              {isGenerating ? (
                <>
                  <FiLoader className="mr-2 animate-spin" /> Creating...
                </>
              ) : (
                <>
                  <FiZap className="mr-2" />
                  {canCreateFree() ? 'Create Free Story!' : `Create Story (${getCreditsNeeded()} credits)`}
                </>
              )}
            </Button>
          </div>
        </form>
        
        {/* Back to Dashboard */}
        <div className="text-center mt-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className={creatorMode === 'kids' ? 'text-purple-600' : 'text-gray-400'}
          >
            <FiArrowLeft className="mr-2" /> Back to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
