import { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Slider } from '../components/ui/slider';
import { toast } from 'sonner';
import { 
  FiImage, FiUser, FiVideo, FiCamera, FiGrid, FiSave, FiDownload, 
  FiTrash2, FiPlus, FiZap, FiSliders, FiRefreshCw, FiArrowLeft, 
  FiFolder, FiUpload, FiCheck, FiEye, FiMaximize2, FiSettings, 
  FiX, FiPlay, FiPause, FiFilm, FiStar, FiAperture
} from 'react-icons/fi';
import {
  CAMERA_BODIES,
  CINEMA_LENSES,
  VIDEO_MODELS,
  IMAGE_MODELS,
  CHARACTER_CONSISTENCY_MODELS,
  ASPECT_RATIOS,
  EXPRESSIONS,
  SHOT_TYPES,
  LIGHTING_PRESETS,
  buildCinemaPrompt,
  buildCharacterPrompt
} from '../config/ProStudioConfig';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ProStudio() {
  const { user, token } = useAuth();
  const isAuthenticated = !!user;
  const navigate = useNavigate();
  
  // Main state
  const [activeTab, setActiveTab] = useState('characters');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  
  // Character state
  const [characters, setCharacters] = useState([]);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [characterName, setCharacterName] = useState('');
  const [characterImages, setCharacterImages] = useState([]);
  const [isCreatingCharacter, setIsCreatingCharacter] = useState(false);
  
  // LoRA Training state
  const [isTrainingLora, setIsTrainingLora] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(null);
  const [falAvailable, setFalAvailable] = useState(false);
  
  // Consistency Generation state
  const [consistencyMethod, setConsistencyMethod] = useState('auto'); // 'auto', 'lora', 'pulid', 'openai'
  const [selectedImageModel, setSelectedImageModel] = useState('flux-dev');
  
  // Book linking state
  const [userBooks, setUserBooks] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState('general');
  
  // Gallery picker state
  const [showGalleryPicker, setShowGalleryPicker] = useState(false);
  const [galleryPickerMode, setGalleryPickerMode] = useState('character'); // 'character' or 'shots'
  
  // Generation state
  const [prompt, setPrompt] = useState('');
  const [generatedImages, setGeneratedImages] = useState([]);
  const [generatedVideos, setGeneratedVideos] = useState([]);
  const [selectedHeroFrame, setSelectedHeroFrame] = useState(null);
  
  // Cinema Studio state
  const [selectedCamera, setSelectedCamera] = useState('arri-alexa-35');
  const [selectedLens, setSelectedLens] = useState('panavision-series');
  const [selectedFocalLength, setSelectedFocalLength] = useState('35mm');
  const [selectedLighting, setSelectedLighting] = useState('natural');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  
  // Video state
  const [selectedVideoModel, setSelectedVideoModel] = useState('sora-2');
  const [videoDuration, setVideoDuration] = useState(5);
  const [videoPrompt, setVideoPrompt] = useState('');
  
  // Shots App state
  const [shotsSourceImage, setShotsSourceImage] = useState(null);
  const [shotsResults, setShotsResults] = useState([]);
  
  // Expression state
  const [selectedExpression, setSelectedExpression] = useState('neutral');
  
  // Gallery state
  const [gallery, setGallery] = useState([]);
  
  // Load user's characters on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadCharacters();
      loadGallery();
      loadUserBooks();
      checkFalAvailability();
    }
  }, [isAuthenticated]);

  // Check if fal.ai is available
  const checkFalAvailability = async () => {
    try {
      const response = await fetch(`${API_URL}/api/fal/models`);
      if (response.ok) {
        const data = await response.json();
        setFalAvailable(data.available);
      }
    } catch (error) {
      console.error('Error checking fal.ai availability:', error);
    }
  };

  const loadUserBooks = async () => {
    try {
      const tkn = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/my-books`, {
        headers: { Authorization: `Bearer ${tkn}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUserBooks(data || []);
      }
    } catch (error) {
      console.error('Error loading books:', error);
    }
  };

  const loadCharacters = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCharacters(data.characters || []);
      }
    } catch (error) {
      console.error('Error loading characters:', error);
    }
  };

  const loadGallery = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/art-studio/gallery`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setGallery(data.gallery || []);
      }
    } catch (error) {
      console.error('Error loading gallery:', error);
    }
  };

  // File upload handler
  const handleFileUpload = async (e, purpose = 'character') => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    for (const file of files) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const newImage = {
          id: Date.now() + Math.random(),
          url: event.target.result,
          name: file.name
        };
        
        if (purpose === 'character') {
          setCharacterImages(prev => [...prev, newImage]);
        } else if (purpose === 'shots') {
          setShotsSourceImage(event.target.result);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Create character from reference images
  const createCharacter = async () => {
    if (!characterName.trim()) {
      toast.error('Please enter a character name');
      return;
    }
    if (characterImages.length < 3) {
      toast.error('Please upload at least 3 reference images');
      return;
    }

    setIsCreatingCharacter(true);
    setLoadingMessage('Analyzing reference images...');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: characterName,
          reference_images: characterImages.map(img => img.url)
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Character "${characterName}" created!`);
        setCharacters(prev => [...prev, data.character]);
        setSelectedCharacter(data.character);
        setCharacterName('');
        setCharacterImages([]);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create character');
      }
    } catch (error) {
      toast.error('Error creating character');
      console.error(error);
    } finally {
      setIsCreatingCharacter(false);
      setLoadingMessage('');
    }
  };

  // Train LoRA for character consistency
  const trainCharacterLora = async (characterId) => {
    if (!falAvailable) {
      toast.error('fal.ai is not available for LoRA training');
      return;
    }

    setIsTrainingLora(true);
    setLoadingMessage('Starting LoRA training (this takes 5-15 minutes)...');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/train-consistency?character_id=${characterId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('LoRA training started! This will take 5-15 minutes.');
        
        // Start polling for training status
        pollTrainingStatus(data.job_id, characterId);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to start LoRA training');
        setIsTrainingLora(false);
      }
    } catch (error) {
      toast.error('Error starting LoRA training');
      console.error(error);
      setIsTrainingLora(false);
    }
  };

  // Poll training status
  const pollTrainingStatus = async (jobId, characterId) => {
    const token = localStorage.getItem('token');
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/fal/training-status/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setTrainingProgress(data);

          if (data.status === 'completed') {
            clearInterval(pollInterval);
            toast.success('LoRA training complete! Your character is now ready for consistent generation.');
            setIsTrainingLora(false);
            setLoadingMessage('');
            // Reload characters to get updated data
            loadCharacters();
          } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            toast.error('LoRA training failed. Please try again.');
            setIsTrainingLora(false);
            setLoadingMessage('');
          } else {
            setLoadingMessage(`Training in progress... ${data.logs?.[0] || ''}`);
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 10000); // Poll every 10 seconds

    // Timeout after 20 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (isTrainingLora) {
        setIsTrainingLora(false);
        setLoadingMessage('');
        toast.error('Training timed out. Please check later.');
      }
    }, 1200000);
  };

  // Generate consistent character image
  const generateConsistentCharacterImage = async () => {
    if (!selectedCharacter) {
      toast.error('Please select a character first');
      return;
    }
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setIsLoading(true);
    const method = selectedCharacter.lora_status === 'completed' ? 'LoRA' : 'PuLID';
    setLoadingMessage(`Generating consistent image using ${method}...`);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('prompt', prompt);
      formData.append('image_size', aspectRatio === '16:9' ? 'landscape_16_9' : aspectRatio === '9:16' ? 'portrait_16_9' : 'square_hd');

      const response = await fetch(`${API_URL}/api/pro-studio/characters/${selectedCharacter.id}/generate-consistent`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        if (data.images && data.images.length > 0) {
          const newImage = {
            id: Date.now(),
            url: data.images[0].url,
            prompt: prompt,
            method: data.method,
            character: selectedCharacter.name
          };
          setGeneratedImages(prev => [newImage, ...prev]);
          setSelectedHeroFrame(newImage);
          toast.success(`Generated using ${data.method}!`);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Generation failed');
      }
    } catch (error) {
      toast.error('Error generating image');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Generate with fal.ai FLUX
  const generateWithFal = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setIsLoading(true);
    setLoadingMessage('Generating with FLUX...');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/fal/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: prompt,
          model: selectedImageModel,
          image_size: aspectRatio === '16:9' ? 'landscape_16_9' : aspectRatio === '9:16' ? 'portrait_16_9' : 'square_hd',
          num_images: 1
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.images && data.images.length > 0) {
          const newImage = {
            id: Date.now(),
            url: data.images[0].url,
            prompt: prompt,
            model: selectedImageModel
          };
          setGeneratedImages(prev => [newImage, ...prev]);
          setSelectedHeroFrame(newImage);
          toast.success('Image generated with FLUX!');
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Generation failed');
      }
    } catch (error) {
      toast.error('Error generating image');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Generate hero frame with Cinema Studio settings
  const generateHeroFrame = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setIsLoading(true);
    setLoadingMessage('Creating your cinematic hero frame...');

    try {
      const cinemaPrompt = buildCinemaPrompt(selectedCamera, selectedLens, selectedFocalLength);
      const lightingPreset = LIGHTING_PRESETS.find(l => l.id === selectedLighting);
      const characterPrompt = selectedCharacter ? buildCharacterPrompt(selectedCharacter) : '';
      
      const fullPrompt = [
        prompt,
        characterPrompt,
        cinemaPrompt,
        lightingPreset?.prompt || ''
      ].filter(Boolean).join(', ');

      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/pro-studio/generate-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: fullPrompt,
          character_id: selectedCharacter?.id,
          camera: selectedCamera,
          lens: selectedLens,
          focal_length: selectedFocalLength,
          lighting: selectedLighting,
          aspect_ratio: aspectRatio
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newImage = {
          id: Date.now(),
          url: data.image_url,
          prompt: fullPrompt,
          settings: { selectedCamera, selectedLens, selectedFocalLength, selectedLighting }
        };
        setGeneratedImages(prev => [newImage, ...prev]);
        setSelectedHeroFrame(newImage);
        toast.success('Hero frame generated!');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Generation failed');
      }
    } catch (error) {
      toast.error('Error generating image');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Generate shots (9 angles from 1 image)
  const generateShots = async () => {
    if (!shotsSourceImage) {
      toast.error('Please upload a source image first');
      return;
    }

    setIsLoading(true);
    setLoadingMessage('Generating 9 different angles...');
    setShotsResults([]);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/pro-studio/generate-shots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          source_image: shotsSourceImage,
          character_id: selectedCharacter?.id
        })
      });

      if (response.ok) {
        const data = await response.json();
        setShotsResults(data.shots || []);
        toast.success('9 shots generated!');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to generate shots');
      }
    } catch (error) {
      toast.error('Error generating shots');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Generate expression variations
  const generateExpression = async () => {
    if (!selectedCharacter) {
      toast.error('Please select a character first');
      return;
    }

    setIsLoading(true);
    const expressionData = EXPRESSIONS.find(e => e.id === selectedExpression);
    setLoadingMessage(`Generating ${expressionData.name} expression...`);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/pro-studio/generate-expression`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          character_id: selectedCharacter.id,
          expression: selectedExpression,
          base_prompt: prompt || `portrait of ${selectedCharacter.name}`
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newImage = {
          id: Date.now(),
          url: data.image_url,
          expression: selectedExpression,
          character: selectedCharacter.name
        };
        setGeneratedImages(prev => [newImage, ...prev]);
        toast.success(`${expressionData.name} expression generated!`);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to generate expression');
      }
    } catch (error) {
      toast.error('Error generating expression');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Animate hero frame to video
  const animateToVideo = async () => {
    if (!selectedHeroFrame) {
      toast.error('Please select a hero frame to animate');
      return;
    }

    setIsLoading(true);
    const model = VIDEO_MODELS.find(m => m.id === selectedVideoModel);
    setLoadingMessage(`Animating with ${model.name} (this may take a few minutes)...`);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/pro-studio/animate-hero`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: selectedHeroFrame.url,
          motion_prompt: videoPrompt || 'subtle cinematic movement, breathing, natural motion',
          model: selectedVideoModel,
          duration: videoDuration
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.job_id) {
          // Poll for completion
          pollVideoStatus(data.job_id);
        } else if (data.video_url) {
          const newVideo = {
            id: Date.now(),
            url: data.video_url,
            sourceImage: selectedHeroFrame.url,
            model: selectedVideoModel
          };
          setGeneratedVideos(prev => [newVideo, ...prev]);
          toast.success('Video generated!');
          setIsLoading(false);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Animation failed');
        setIsLoading(false);
      }
    } catch (error) {
      toast.error('Error animating image');
      console.error(error);
      setIsLoading(false);
    }
  };

  // Poll video generation status
  const pollVideoStatus = async (jobId) => {
    const token = localStorage.getItem('token');
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/art-studio/animation-status/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.ok) {
          const data = await response.json();
          setLoadingMessage(data.message || 'Processing...');
          
          if (data.status === 'completed' && data.video_base64) {
            clearInterval(pollInterval);
            const newVideo = {
              id: Date.now(),
              url: `data:video/mp4;base64,${data.video_base64}`,
              sourceImage: selectedHeroFrame?.url
            };
            setGeneratedVideos(prev => [newVideo, ...prev]);
            toast.success('Video generated!');
            setIsLoading(false);
            setLoadingMessage('');
          } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            toast.error(data.message || 'Video generation failed');
            setIsLoading(false);
            setLoadingMessage('');
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000);

    // Timeout after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (isLoading) {
        setIsLoading(false);
        setLoadingMessage('');
        toast.error('Video generation timed out. Please try again.');
      }
    }, 600000);
  };

  // Save to gallery
  const saveToGallery = async (item, type = 'image') => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/art-studio/gallery/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: item.url,
          prompt: item.prompt || '',
          style: type,
          is_animation: type === 'video'
        })
      });

      if (response.ok) {
        toast.success('Saved to gallery!');
        loadGallery();
      }
    } catch (error) {
      toast.error('Failed to save');
    }
  };

  // Download image/video
  const downloadMedia = (url, filename) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-center text-white">
          <h1 className="text-3xl font-bold mb-4">Pro Studio</h1>
          <p className="text-gray-400 mb-6">Please sign in to access the Pro Studio</p>
          <Button onClick={() => navigate('/auth')} className="bg-purple-600 hover:bg-purple-700">
            Sign In
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-950 to-gray-900">
      {/* Header */}
      <header className="bg-black/40 backdrop-blur-md border-b border-purple-500/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/art-studio')} className="text-gray-400 hover:text-white">
              <FiArrowLeft className="mr-2" /> Back to Art Studio
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <FiFilm className="text-white" />
              </div>
              <span className="text-xl font-bold text-white">Pro Studio</span>
              <span className="px-2 py-0.5 text-xs bg-gradient-to-r from-amber-500 to-orange-500 rounded-full text-white font-medium">
                BETA
              </span>
            </div>
          </div>
          
          {/* Book selector and Character in header */}
          <div className="flex items-center gap-3">
            {/* Book selector */}
            <Select value={selectedBookId} onValueChange={setSelectedBookId}>
              <SelectTrigger className="w-40 bg-gray-800/50 border-gray-700 text-white rounded-full text-sm">
                <SelectValue placeholder="Select book" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="general" className="text-white">General (All Books)</SelectItem>
                {userBooks.map((book) => (
                  <SelectItem key={book.id} value={book.id} className="text-white">
                    {book.title?.substring(0, 25)}{book.title?.length > 25 ? '...' : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {/* Selected Character */}
            {selectedCharacter && (
              <div className="flex items-center gap-2 bg-purple-900/30 px-3 py-1.5 rounded-full">
                <img 
                  src={selectedCharacter.thumbnail || selectedCharacter.reference_images?.[0]} 
                  alt={selectedCharacter.name}
                  className="w-6 h-6 rounded-full object-cover"
                />
                <span className="text-white text-sm">{selectedCharacter.name}</span>
                <button onClick={() => setSelectedCharacter(null)} className="text-gray-400 hover:text-white">
                  <FiX size={14} />
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Loading Overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-white text-lg">{loadingMessage}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="bg-black/40 border border-purple-500/20 p-1 mb-6">
            <TabsTrigger value="characters" className="data-[state=active]:bg-purple-600">
              <FiUser className="mr-2" /> Characters
            </TabsTrigger>
            <TabsTrigger value="cinema" className="data-[state=active]:bg-purple-600">
              <FiCamera className="mr-2" /> Cinema Studio
            </TabsTrigger>
            <TabsTrigger value="shots" className="data-[state=active]:bg-purple-600">
              <FiGrid className="mr-2" /> Shots
            </TabsTrigger>
            <TabsTrigger value="video" className="data-[state=active]:bg-purple-600">
              <FiVideo className="mr-2" /> Video
            </TabsTrigger>
            <TabsTrigger value="gallery" className="data-[state=active]:bg-purple-600">
              <FiFolder className="mr-2" /> Gallery
            </TabsTrigger>
          </TabsList>

          {/* Characters Tab */}
          <TabsContent value="characters" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Create Character Panel */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiPlus className="text-purple-400" /> Create Character
                </h2>
                <p className="text-gray-400 text-sm mb-4">
                  Upload 10-20 photos of your character from different angles. The AI will learn their appearance for consistent generation.
                </p>
                
                <Input
                  placeholder="Character name (e.g., Emma)"
                  value={characterName}
                  onChange={(e) => setCharacterName(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                  data-testid="character-name-input"
                />

                <div className="border-2 border-dashed border-purple-500/30 rounded-lg p-6 text-center mb-4">
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={(e) => handleFileUpload(e, 'character')}
                    className="hidden"
                    id="character-upload"
                    data-testid="character-image-upload"
                  />
                  <label htmlFor="character-upload" className="cursor-pointer">
                    <FiUpload className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                    <p className="text-gray-400">Click to upload reference images</p>
                    <p className="text-xs text-gray-500 mt-1">Recommended: 10-20 images from different angles</p>
                  </label>
                </div>
                
                {/* Add from Gallery Button */}
                <Button
                  variant="outline"
                  onClick={() => { setGalleryPickerMode('character'); setShowGalleryPicker(true); }}
                  className="w-full mb-4 border-purple-500/30 text-purple-300 hover:bg-purple-500/20"
                >
                  <FiFolder className="mr-2" /> Add from Gallery
                </Button>

                {/* Uploaded images preview */}
                {characterImages.length > 0 && (
                  <div className="grid grid-cols-5 gap-2 mb-4">
                    {characterImages.map((img, i) => (
                      <div key={img.id} className="relative group">
                        <img src={img.url} alt={`Ref ${i+1}`} className="w-full aspect-square object-cover rounded-lg" />
                        <button
                          onClick={() => setCharacterImages(prev => prev.filter(x => x.id !== img.id))}
                          className="absolute top-1 right-1 bg-red-500 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <FiX size={12} className="text-white" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <Button 
                  onClick={createCharacter}
                  disabled={isCreatingCharacter || characterImages.length < 3}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  data-testid="create-character-btn"
                >
                  {isCreatingCharacter ? 'Creating...' : `Create Character (${characterImages.length}/3+ images)`}
                </Button>
              </div>

              {/* My Characters Panel */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiUser className="text-purple-400" /> My Characters
                  {falAvailable && (
                    <span className="ml-auto text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">
                      fal.ai Connected
                    </span>
                  )}
                </h2>
                
                {characters.length === 0 ? (
                  <div className="text-center py-12">
                    <FiUser className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">No characters yet</p>
                    <p className="text-gray-500 text-sm">Create your first character to get started</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4">
                    {characters.map((char) => (
                      <div
                        key={char.id}
                        className={`rounded-lg border-2 transition-all ${
                          selectedCharacter?.id === char.id 
                            ? 'border-purple-500 bg-purple-900/30' 
                            : 'border-gray-700 hover:border-purple-500/50'
                        } p-4`}
                        data-testid={`character-card-${char.id}`}
                      >
                        <div className="flex items-center gap-4">
                          <img 
                            src={char.thumbnail || char.reference_images?.[0]} 
                            alt={char.name}
                            className="w-16 h-16 rounded-full object-cover cursor-pointer"
                            onClick={() => setSelectedCharacter(char)}
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="text-white font-medium">{char.name}</p>
                              {char.lora_status === 'completed' && (
                                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full flex items-center gap-1">
                                  <FiCheck size={10} /> LoRA Ready
                                </span>
                              )}
                              {char.lora_status === 'training' && (
                                <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full animate-pulse">
                                  Training...
                                </span>
                              )}
                            </div>
                            <p className="text-gray-500 text-xs">{char.reference_images?.length || 0} reference images</p>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {/* Select button */}
                            <Button
                              size="sm"
                              variant={selectedCharacter?.id === char.id ? "default" : "outline"}
                              onClick={() => setSelectedCharacter(char)}
                              className={selectedCharacter?.id === char.id ? "bg-purple-600" : "border-gray-600"}
                            >
                              {selectedCharacter?.id === char.id ? <FiCheck className="mr-1" /> : null}
                              Select
                            </Button>
                            
                            {/* Train LoRA button */}
                            {falAvailable && char.lora_status !== 'completed' && char.lora_status !== 'training' && (
                              <Button
                                size="sm"
                                onClick={() => trainCharacterLora(char.id)}
                                disabled={isTrainingLora}
                                className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
                              >
                                <FiZap className="mr-1" /> Train LoRA
                              </Button>
                            )}
                          </div>
                        </div>
                        
                        {/* LoRA Info */}
                        {char.lora_status === 'completed' && (
                          <div className="mt-3 p-2 bg-green-500/10 rounded-lg text-xs text-green-300">
                            This character has a trained LoRA model for 100% consistent generation across all images.
                          </div>
                        )}
                        {!char.lora_status && falAvailable && (
                          <div className="mt-3 p-2 bg-gray-800/50 rounded-lg text-xs text-gray-400">
                            Train a LoRA model for this character to ensure 100% consistent face across all generations.
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Consistent Generation Panel */}
            {selectedCharacter && (
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiZap className="text-amber-400" /> Generate Consistent Character
                </h2>
                <p className="text-gray-400 text-sm mb-4">
                  {selectedCharacter.lora_status === 'completed' 
                    ? `Generate ${selectedCharacter.name} with 100% face consistency using trained LoRA.`
                    : `Generate ${selectedCharacter.name} using face ID preservation (PuLID).`
                  }
                </p>
                
                <Textarea
                  placeholder={`Describe the scene for ${selectedCharacter.name}... (e.g., 'sitting in a coffee shop reading a book')`}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                  rows={3}
                  data-testid="consistent-gen-prompt"
                />

                <div className="flex gap-3 mb-4">
                  <Select value={aspectRatio} onValueChange={setAspectRatio}>
                    <SelectTrigger className="w-40 bg-gray-800/50 border-gray-700 text-white">
                      <SelectValue placeholder="Aspect Ratio" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      {ASPECT_RATIOS.map((ar) => (
                        <SelectItem key={ar.id} value={ar.id} className="text-white">
                          {ar.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={generateConsistentCharacterImage}
                  disabled={isLoading || !prompt.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  data-testid="generate-consistent-btn"
                >
                  <FiZap className="mr-2" /> 
                  Generate {selectedCharacter.name} 
                  {selectedCharacter.lora_status === 'completed' ? ' (LoRA)' : ' (PuLID)'}
                </Button>
              </div>
            )}

            {/* Expression Generator */}
            {selectedCharacter && (
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiStar className="text-amber-400" /> Generate Expressions
                </h2>
                <p className="text-gray-400 text-sm mb-4">
                  Generate your character with different expressions while maintaining consistency.
                </p>
                
                <div className="grid grid-cols-4 md:grid-cols-6 gap-2 mb-4">
                  {EXPRESSIONS.map((expr) => (
                    <button
                      key={expr.id}
                      onClick={() => setSelectedExpression(expr.id)}
                      className={`p-2 rounded-lg text-center transition-all ${
                        selectedExpression === expr.id
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      <span className="text-sm">{expr.name}</span>
                    </button>
                  ))}
                </div>

                <Textarea
                  placeholder="Additional prompt (optional) - e.g., 'on a beach at sunset'"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                  rows={2}
                />

                <Button 
                  onClick={generateExpression}
                  disabled={isLoading}
                  className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
                  data-testid="generate-expression-btn"
                >
                  <FiZap className="mr-2" /> Generate {EXPRESSIONS.find(e => e.id === selectedExpression)?.name} Expression
                </Button>
              </div>
            )}
          </TabsContent>

          {/* Cinema Studio Tab */}
          <TabsContent value="cinema" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Controls Panel */}
              <div className="lg:col-span-1 space-y-4">
                {/* Camera Selection */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                    <FiCamera className="text-purple-400" /> Camera Body
                  </h3>
                  <Select value={selectedCamera} onValueChange={setSelectedCamera}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white" data-testid="camera-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      {CAMERA_BODIES.map((camera) => (
                        <SelectItem key={camera.id} value={camera.id} className="text-white hover:bg-gray-700">
                          <div className="flex items-center gap-2">
                            <span>{camera.icon}</span>
                            <span>{camera.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-2">
                    {CAMERA_BODIES.find(c => c.id === selectedCamera)?.characteristics}
                  </p>
                </div>

                {/* Lens Selection */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                    <FiAperture className="text-purple-400" /> Lens
                  </h3>
                  <Select value={selectedLens} onValueChange={setSelectedLens}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white" data-testid="lens-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      {CINEMA_LENSES.map((lens) => (
                        <SelectItem key={lens.id} value={lens.id} className="text-white hover:bg-gray-700">
                          {lens.name} ({lens.brand})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {/* Focal Length */}
                  <div className="mt-3">
                    <label className="text-xs text-gray-400 mb-1 block">Focal Length</label>
                    <div className="flex flex-wrap gap-1">
                      {CINEMA_LENSES.find(l => l.id === selectedLens)?.focalLengths.map((fl) => (
                        <button
                          key={fl}
                          onClick={() => setSelectedFocalLength(fl)}
                          className={`px-2 py-1 text-xs rounded ${
                            selectedFocalLength === fl
                              ? 'bg-purple-600 text-white'
                              : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                          }`}
                        >
                          {fl}
                        </button>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {CINEMA_LENSES.find(l => l.id === selectedLens)?.characteristics}
                  </p>
                </div>

                {/* Lighting */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3">Lighting</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {LIGHTING_PRESETS.slice(0, 6).map((light) => (
                      <button
                        key={light.id}
                        onClick={() => setSelectedLighting(light.id)}
                        className={`p-2 text-xs rounded-lg transition-all ${
                          selectedLighting === light.id
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                        }`}
                      >
                        {light.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Aspect Ratio */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3">Aspect Ratio</h3>
                  <Select value={aspectRatio} onValueChange={setAspectRatio}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      {ASPECT_RATIOS.map((ar) => (
                        <SelectItem key={ar.id} value={ar.id} className="text-white hover:bg-gray-700">
                          {ar.name} - {ar.description}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Generation Panel */}
              <div className="lg:col-span-2 space-y-4">
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                  <h2 className="text-xl font-bold text-white mb-4">Generate Hero Frame</h2>
                  
                  <Textarea
                    placeholder="Describe your scene... (e.g., 'A woman stands on a misty beach at sunrise, waves gently rolling in behind her')"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="bg-gray-800/50 border-gray-700 text-white mb-4"
                    rows={3}
                    data-testid="cinema-prompt-input"
                  />

                  <div className="flex gap-3 mb-4">
                    <Button 
                      onClick={generateHeroFrame}
                      disabled={isLoading || !prompt.trim()}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                      data-testid="generate-hero-btn"
                    >
                      <FiZap className="mr-2" /> Generate Hero Frame
                    </Button>
                  </div>

                  {/* Cinema settings preview */}
                  <div className="bg-gray-900/50 rounded-lg p-3 text-xs text-gray-400">
                    <span className="text-purple-400">Camera:</span> {CAMERA_BODIES.find(c => c.id === selectedCamera)?.name} | 
                    <span className="text-purple-400 ml-2">Lens:</span> {CINEMA_LENSES.find(l => l.id === selectedLens)?.name} {selectedFocalLength} | 
                    <span className="text-purple-400 ml-2">Light:</span> {LIGHTING_PRESETS.find(l => l.id === selectedLighting)?.name}
                  </div>
                </div>

                {/* Generated Images Grid */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                  <h3 className="text-white font-medium mb-4">Generated Hero Frames</h3>
                  {generatedImages.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <FiImage className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No images generated yet</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {generatedImages.map((img) => (
                        <div 
                          key={img.id} 
                          className={`relative group cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                            selectedHeroFrame?.id === img.id ? 'border-purple-500' : 'border-transparent hover:border-purple-500/50'
                          }`}
                          onClick={() => setSelectedHeroFrame(img)}
                        >
                          <img src={img.url} alt="Generated" className="w-full aspect-video object-cover" />
                          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                            <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); saveToGallery(img); }}>
                              <FiSave className="text-white" />
                            </Button>
                            <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); downloadMedia(img.url, `hero-${img.id}.png`); }}>
                              <FiDownload className="text-white" />
                            </Button>
                          </div>
                          {selectedHeroFrame?.id === img.id && (
                            <div className="absolute top-2 left-2 bg-purple-500 text-white text-xs px-2 py-1 rounded">
                              Selected
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Shots Tab */}
          <TabsContent value="shots" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Upload Panel */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiGrid className="text-purple-400" /> Shots App
                </h2>
                <p className="text-gray-400 text-sm mb-4">
                  Upload one image and generate 9 different angles - front, side profiles, 3/4 views, and more.
                </p>

                <div className="border-2 border-dashed border-purple-500/30 rounded-lg p-8 text-center mb-4">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileUpload(e, 'shots')}
                    className="hidden"
                    id="shots-upload"
                    data-testid="shots-image-upload"
                  />
                  <label htmlFor="shots-upload" className="cursor-pointer">
                    {shotsSourceImage ? (
                      <img src={shotsSourceImage} alt="Source" className="w-48 h-48 object-cover rounded-lg mx-auto" />
                    ) : (
                      <>
                        <FiUpload className="w-12 h-12 text-purple-400 mx-auto mb-3" />
                        <p className="text-gray-400">Click to upload source image</p>
                      </>
                    )}
                  </label>
                </div>
                
                {/* Or Select from Gallery */}
                <Button
                  variant="outline"
                  onClick={() => { setGalleryPickerMode('shots'); setShowGalleryPicker(true); }}
                  className="w-full mb-4 border-purple-500/30 text-purple-300 hover:bg-purple-500/20"
                >
                  <FiFolder className="mr-2" /> Select from Gallery
                </Button>

                <Button 
                  onClick={generateShots}
                  disabled={isLoading || !shotsSourceImage}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  data-testid="generate-shots-btn"
                >
                  <FiGrid className="mr-2" /> Generate 9 Shots
                </Button>
              </div>

              {/* Results Panel */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h3 className="text-white font-medium mb-4">Generated Shots</h3>
                {shotsResults.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FiGrid className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Upload an image to generate multiple angles</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-2">
                    {shotsResults.map((shot, i) => (
                      <div key={i} className="relative group">
                        <img src={shot.url} alt={shot.type} className="w-full aspect-square object-cover rounded-lg" />
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white text-xs p-1 text-center">
                          {SHOT_TYPES[i]?.name || `Shot ${i+1}`}
                        </div>
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                          <Button size="sm" variant="ghost" onClick={() => saveToGallery(shot)}>
                            <FiSave className="text-white" size={14} />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => downloadMedia(shot.url, `shot-${i+1}.png`)}>
                            <FiDownload className="text-white" size={14} />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Video Tab */}
          <TabsContent value="video" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Video Controls */}
              <div className="lg:col-span-1 space-y-4">
                {/* Model Selection */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                    <FiVideo className="text-purple-400" /> Video Model
                  </h3>
                  <Select value={selectedVideoModel} onValueChange={setSelectedVideoModel}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white" data-testid="video-model-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      {VIDEO_MODELS.map((model) => (
                        <SelectItem key={model.id} value={model.id} className="text-white hover:bg-gray-700">
                          <div className="flex items-center justify-between w-full">
                            <span>{model.name}</span>
                            {!model.available && (
                              <span className="text-xs text-amber-400 ml-2">(Coming Soon)</span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {/* Model info */}
                  <div className="mt-3 text-xs text-gray-400">
                    <p className="text-purple-400">{VIDEO_MODELS.find(m => m.id === selectedVideoModel)?.provider}</p>
                    <p className="mt-1">{VIDEO_MODELS.find(m => m.id === selectedVideoModel)?.description}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {VIDEO_MODELS.find(m => m.id === selectedVideoModel)?.strengths.map((s, i) => (
                        <span key={i} className="bg-purple-900/30 px-2 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Duration */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3">Duration: {videoDuration}s</h3>
                  <Slider
                    value={[videoDuration]}
                    onValueChange={(v) => setVideoDuration(v[0])}
                    min={3}
                    max={VIDEO_MODELS.find(m => m.id === selectedVideoModel)?.maxDuration || 10}
                    step={1}
                    className="w-full"
                  />
                </div>

                {/* Selected Hero Frame */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3">Source Image</h3>
                  {selectedHeroFrame ? (
                    <div className="relative">
                      <img src={selectedHeroFrame.url} alt="Hero" className="w-full rounded-lg" />
                      <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded">
                        Ready to animate
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <p>Select a hero frame from Cinema Studio</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Video Generation Panel */}
              <div className="lg:col-span-2 space-y-4">
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                  <h2 className="text-xl font-bold text-white mb-4">Animate to Video</h2>
                  
                  <Textarea
                    placeholder="Describe the motion... (e.g., 'gentle wind blowing hair, soft breathing, subtle camera dolly forward')"
                    value={videoPrompt}
                    onChange={(e) => setVideoPrompt(e.target.value)}
                    className="bg-gray-800/50 border-gray-700 text-white mb-4"
                    rows={3}
                    data-testid="video-prompt-input"
                  />

                  <Button 
                    onClick={animateToVideo}
                    disabled={isLoading || !selectedHeroFrame}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                    data-testid="animate-video-btn"
                  >
                    <FiPlay className="mr-2" /> Animate with {VIDEO_MODELS.find(m => m.id === selectedVideoModel)?.name}
                  </Button>

                  {selectedVideoModel !== 'sora-2' && (
                    <p className="text-amber-400 text-xs mt-2 text-center">
                      Note: {VIDEO_MODELS.find(m => m.id === selectedVideoModel)?.name} requires an API key. Currently using Sora 2 fallback.
                    </p>
                  )}
                </div>

                {/* Generated Videos */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                  <h3 className="text-white font-medium mb-4">Generated Videos</h3>
                  {generatedVideos.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <FiVideo className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No videos generated yet</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {generatedVideos.map((vid) => (
                        <div key={vid.id} className="relative group rounded-lg overflow-hidden">
                          <video 
                            src={vid.url} 
                            className="w-full aspect-video object-cover"
                            controls
                            muted
                            playsInline
                          />
                          <div className="absolute top-2 right-2 flex gap-1">
                            <Button size="sm" variant="ghost" className="bg-black/50" onClick={() => saveToGallery(vid, 'video')}>
                              <FiSave className="text-white" size={14} />
                            </Button>
                            <Button size="sm" variant="ghost" className="bg-black/50" onClick={() => downloadMedia(vid.url, `video-${vid.id}.mp4`)}>
                              <FiDownload className="text-white" size={14} />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Gallery Tab */}
          <TabsContent value="gallery" className="space-y-6">
            <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <FiFolder className="text-purple-400" /> My Gallery
              </h2>
              
              {gallery.length === 0 ? (
                <div className="text-center py-16 text-gray-500">
                  <FiFolder className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">Your gallery is empty</p>
                  <p className="text-sm mt-2">Start creating to fill it up!</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {gallery.map((item) => (
                    <div key={item.id} className="relative group rounded-lg overflow-hidden">
                      {item.is_animation ? (
                        <video src={item.image_url} className="w-full aspect-square object-cover" muted playsInline loop 
                          onMouseEnter={(e) => e.target.play()}
                          onMouseLeave={(e) => { e.target.pause(); e.target.currentTime = 0; }}
                        />
                      ) : (
                        <img src={item.image_url} alt={item.prompt} className="w-full aspect-square object-cover" />
                      )}
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                        <Button size="sm" variant="ghost" onClick={() => downloadMedia(item.image_url, `gallery-${item.id}.${item.is_animation ? 'mp4' : 'png'}`)}>
                          <FiDownload className="text-white" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setSelectedHeroFrame({ id: item.id, url: item.image_url })}>
                          <FiImage className="text-white" />
                        </Button>
                      </div>
                      {item.is_animation && (
                        <div className="absolute top-2 left-2 bg-purple-500 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                          <FiVideo size={10} /> Video
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </main>
      
      {/* Gallery Picker Modal */}
      <AnimatePresence>
        {showGalleryPicker && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowGalleryPicker(false)}
          >
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-xl border border-purple-500/20 w-full max-w-4xl max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">
                  {galleryPickerMode === 'character' ? 'Select Images for Character' : 'Select Source Image'}
                </h3>
                <button onClick={() => setShowGalleryPicker(false)} className="text-gray-400 hover:text-white">
                  <FiX size={20} />
                </button>
              </div>
              
              <div className="p-4 overflow-y-auto max-h-[60vh]">
                {gallery.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FiFolder className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Your gallery is empty</p>
                    <p className="text-sm mt-2">Generate some images in Art Studio first</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-4 md:grid-cols-5 gap-3">
                    {gallery.filter(item => !item.is_animation).map((item) => (
                      <div 
                        key={item.id} 
                        className="relative cursor-pointer rounded-lg overflow-hidden border-2 border-transparent hover:border-purple-500 transition-colors"
                        onClick={() => {
                          if (galleryPickerMode === 'character') {
                            // Add to character images
                            const newImage = {
                              id: Date.now() + Math.random(),
                              url: item.image_url,
                              name: item.prompt?.substring(0, 20) || 'Gallery Image'
                            };
                            setCharacterImages(prev => [...prev, newImage]);
                            toast.success('Image added to character references');
                          } else {
                            // Set as shots source
                            setShotsSourceImage(item.image_url);
                            setShowGalleryPicker(false);
                            toast.success('Source image selected');
                          }
                        }}
                      >
                        <img 
                          src={item.image_url} 
                          alt="" 
                          className="w-full aspect-square object-cover"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="p-4 border-t border-gray-800 flex justify-end gap-3">
                <Button variant="ghost" onClick={() => setShowGalleryPicker(false)}>
                  Cancel
                </Button>
                {galleryPickerMode === 'character' && (
                  <Button onClick={() => setShowGalleryPicker(false)} className="bg-purple-600 hover:bg-purple-700">
                    Done ({characterImages.length} selected)
                  </Button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
