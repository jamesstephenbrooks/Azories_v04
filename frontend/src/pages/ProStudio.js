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
import Cropper from 'react-easy-crop';
import { 
  FiImage, FiUser, FiVideo, FiCamera, FiGrid, FiSave, FiDownload, 
  FiTrash2, FiPlus, FiZap, FiSliders, FiRefreshCw, FiArrowLeft, 
  FiFolder, FiUpload, FiCheck, FiEye, FiMaximize2, FiSettings, 
  FiX, FiPlay, FiPause, FiFilm, FiStar, FiAperture, FiEdit3, FiLayers,
  FiSun, FiCloud, FiMoon, FiCrop
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
  const [loadingProgress, setLoadingProgress] = useState(0);
  
  // Character state
  const [characters, setCharacters] = useState([]);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [characterName, setCharacterName] = useState('');
  const [characterImages, setCharacterImages] = useState([]);
  const [isCreatingCharacter, setIsCreatingCharacter] = useState(false);
  
  // New character creation options
  const [characterDescription, setCharacterDescription] = useState('');
  const [characterStyle, setCharacterStyle] = useState('illustration');
  const [characterGenre, setCharacterGenre] = useState('fantasy');
  const [characterStyles, setCharacterStyles] = useState([]);
  const [characterGenres, setCharacterGenres] = useState([]);
  const [physicalTraits, setPhysicalTraits] = useState({
    age: '',
    gender: '',
    hairColor: '',
    hairStyle: '',
    eyeColor: '',
    skinTone: '',
    bodyType: ''
  });
  const [specialFeatures, setSpecialFeatures] = useState('');
  const [personality, setPersonality] = useState('');
  const [creationMode, setCreationMode] = useState('description'); // 'description' or 'images'
  
  // LoRA Training state
  const [isTrainingLora, setIsTrainingLora] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(null);
  const [falAvailable, setFalAvailable] = useState(false);
  
  // Credits state
  const [credits, setCredits] = useState(0);
  const [creditCosts, setCreditCosts] = useState({});
  
  // Consistency Generation state
  const [consistencyMethod, setConsistencyMethod] = useState('auto'); // 'auto', 'lora', 'pulid', 'openai'
  const [selectedImageModel, setSelectedImageModel] = useState('flux-dev');
  const [selectedSceneForGeneration, setSelectedSceneForGeneration] = useState(null); // Scene to place character in
  const [faceSimilarity, setFaceSimilarity] = useState('high'); // 'high', 'medium', 'low'
  
  // Character folder/gallery state
  const [characterGallery, setCharacterGallery] = useState([]);
  const [viewingCharacter, setViewingCharacter] = useState(null);
  
  // Image preview modal state
  const [previewImage, setPreviewImage] = useState(null);
  
  // Scene Consistency state
  const [scenes, setScenes] = useState([]);
  const [selectedScene, setSelectedScene] = useState(null);
  const [sceneName, setSceneName] = useState('');
  const [sceneDescription, setSceneDescription] = useState('');
  const [sceneStyle, setSceneStyle] = useState('illustration');
  const [sceneGenre, setSceneGenre] = useState('fantasy');
  const [sceneLocationType, setSceneLocationType] = useState('outdoor');
  const [sceneLighting, setSceneLighting] = useState('natural');
  const [sceneMood, setSceneMood] = useState('peaceful');
  const [sceneTimeOfDay, setSceneTimeOfDay] = useState('');
  const [sceneWeather, setSceneWeather] = useState('');
  const [sceneOptions, setSceneOptions] = useState({ location_types: [], lighting: [], moods: [] });
  const [isCreatingScene, setIsCreatingScene] = useState(false);
  const [viewingScene, setViewingScene] = useState(null);
  const [sceneGallery, setSceneGallery] = useState([]);
  
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
  
  // Expand/fullscreen state for gallery items
  const [expandedItem, setExpandedItem] = useState(null); // {type: 'image'|'video', url: string, name: string}
  
  // Cinema Studio state
  const [selectedCamera, setSelectedCamera] = useState('arri-alexa-35');
  const [selectedLens, setSelectedLens] = useState('panavision-series');
  const [selectedFocalLength, setSelectedFocalLength] = useState('35mm');
  const [selectedLighting, setSelectedLighting] = useState('natural');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [cinemaArtStyle, setCinemaArtStyle] = useState('cinematic'); // Art style for Cinema Studio
  
  // Video state
  const [selectedVideoModel, setSelectedVideoModel] = useState('sora-2');
  const [videoDuration, setVideoDuration] = useState(5);
  const [videoPrompt, setVideoPrompt] = useState('');
  const [videoSourceType, setVideoSourceType] = useState('hero'); // 'hero', 'character', 'upload'
  const [videoSourceCharacter, setVideoSourceCharacter] = useState(null);
  const [videoUploadedImage, setVideoUploadedImage] = useState(null);
  const [videoCharacterGallery, setVideoCharacterGallery] = useState([]); // Gallery images for selected character
  const [videoSelectedImage, setVideoSelectedImage] = useState(null); // Selected image from gallery (with description)
  const [videoArtStyle, setVideoArtStyle] = useState('cinematic'); // Style option for consistency
  
  // Shots App state
  const [shotsSourceImage, setShotsSourceImage] = useState(null);
  const [shotsResults, setShotsResults] = useState([]);
  const [showShotsReview, setShowShotsReview] = useState(false); // Modal to review generated shots
  const [shotsSelectedCharacter, setShotsSelectedCharacter] = useState(null); // Selected character for shots
  const [shotsCharacterGallery, setShotsCharacterGallery] = useState([]); // Gallery images for selected character
  const [shotsStyle, setShotsStyle] = useState('realistic'); // Art style for shots generation
  
  // Generation Preview Modal state - shows newly generated images with save options
  const [showGenerationPreview, setShowGenerationPreview] = useState(false);
  const [generationPreviewData, setGenerationPreviewData] = useState(null); // { image, type, characterId, sceneId, prompt }
  
  // Cinema Studio source image - for creating variants
  const [cinemaSourceImage, setCinemaSourceImage] = useState(null); // { url, name, type: 'character'|'scene'|'gallery' }
  const [showCinemaSourcePicker, setShowCinemaSourcePicker] = useState(false);
  
  // Crop state
  const [showCropModal, setShowCropModal] = useState(false);
  const [cropImage, setCropImage] = useState(null); // { url, type: 'scene'|'character', parentId }
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);
  const [cropAspect, setCropAspect] = useState(16 / 9);
  
  // Expression state
  const [selectedExpression, setSelectedExpression] = useState('neutral');
  
  // Unified Gallery state - contains ALL Pro Studio content
  const [gallery, setGallery] = useState([]);
  const [galleryFilter, setGalleryFilter] = useState('all'); // 'all', 'images', 'videos', 'characters'
  const [galleryPickerCallback, setGalleryPickerCallback] = useState(null); // Function to call when image selected
  
  // Load user's characters on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadCharacters();
      loadGallery();
      loadUserBooks();
      checkFalAvailability();
      loadCredits();
      loadCharacterOptions();
      loadSceneOptions();
      loadScenes();
    }
  }, [isAuthenticated]);

  // Load character styles and genres
  const loadCharacterOptions = async () => {
    try {
      const [stylesRes, genresRes] = await Promise.all([
        fetch(`${API_URL}/api/pro-studio/character-styles`),
        fetch(`${API_URL}/api/pro-studio/character-genres`)
      ]);
      
      if (stylesRes.ok) {
        const data = await stylesRes.json();
        setCharacterStyles(data.styles || []);
      }
      if (genresRes.ok) {
        const data = await genresRes.json();
        setCharacterGenres(data.genres || []);
      }
    } catch (error) {
      console.error('Error loading character options:', error);
    }
  };

  // Load scene options
  const loadSceneOptions = async () => {
    try {
      const response = await fetch(`${API_URL}/api/pro-studio/scene-options`);
      if (response.ok) {
        const data = await response.json();
        setSceneOptions(data);
      }
    } catch (error) {
      console.error('Error loading scene options:', error);
    }
  };

  // Load user's scenes
  const loadScenes = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/scenes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setScenes(data.scenes || []);
      }
    } catch (error) {
      console.error('Error loading scenes:', error);
    }
  };

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

  // Load user's credits
  const loadCredits = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCredits(data.credits || 0);
        setCreditCosts(data.costs || {});
      }
    } catch (error) {
      console.error('Error loading credits:', error);
    }
  };

  // Navigate to Credits page for purchasing
  const goToPurchaseCredits = () => {
    navigate('/credits');
  };

  // Check if user has enough credits, redirect to credits page if not
  const checkCreditsOrRedirect = (requiredCredits = 1, actionName = 'This feature') => {
    if (credits < requiredCredits) {
      toast.error(
        <div className="flex flex-col gap-2">
          <span className="font-medium">{actionName} requires {requiredCredits} credit{requiredCredits > 1 ? 's' : ''}</span>
          <span className="text-sm opacity-80">You have {credits} credits remaining</span>
          <button 
            onClick={() => navigate('/credits')}
            className="mt-1 px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded text-sm font-medium hover:from-purple-600 hover:to-pink-600"
          >
            Get Credits →
          </button>
        </div>,
        { duration: 6000 }
      );
      return false;
    }
    return true;
  };

  // Handle insufficient credits error with toast and buy button
  const handleCreditError = (errorDetail) => {
    toast.error(
      <div className="flex flex-col gap-2">
        <span className="font-medium">Insufficient credits!</span>
        <span className="text-sm opacity-80">{errorDetail || 'Please purchase more credits'}</span>
        <button 
          onClick={() => navigate('/credits')}
          className="mt-1 px-3 py-1 bg-amber-500 text-black rounded text-sm font-medium hover:bg-amber-400"
        >
          Buy Credits
        </button>
      </div>,
      { duration: 8000 }
    );
  };

  const loadUserBooks = async () => {
    try {
      const tkn = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/books/my`, {
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
      const token = localStorage.getItem('azories-token');
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

  // Load a specific character's gallery images for Shots panel
  const loadShotsCharacterGallery = async (characterId) => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}/gallery`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        return data.images || [];
      }
    } catch (error) {
      console.error('Error loading character gallery:', error);
    }
    return [];
  };

  // When a character is selected in Shots, load their gallery
  const handleShotsCharacterSelect = async (char) => {
    setShotsSelectedCharacter(char);
    setShotsCharacterGallery([]); // Clear while loading
    
    // Get all images for this character
    const galleryImages = await loadShotsCharacterGallery(char.id);
    
    // Add master thumbnail and reference images
    const allImages = [];
    if (char.thumbnail) {
      allImages.push({ 
        url: char.thumbnail, 
        type: 'master',
        label: 'Master Image'
      });
    }
    if (char.reference_images?.length > 0) {
      char.reference_images.forEach((img, i) => {
        if (img !== char.thumbnail) {
          allImages.push({ 
            url: img, 
            type: 'reference',
            label: `Reference ${i + 1}`
          });
        }
      });
    }
    // Add gallery images
    galleryImages.forEach((img) => {
      allImages.push({
        url: img.image_url || img.url,
        type: 'generated',
        label: img.prompt?.slice(0, 30) || 'Generated'
      });
    });
    
    setShotsCharacterGallery(allImages);
    
    // Auto-select master image as source
    if (char.thumbnail) {
      setShotsSourceImage(char.thumbnail);
      toast.success(`Selected ${char.name} - choose an image from the gallery`);
    }
  };

  // Pagination state for gallery
  const [galleryPage, setGalleryPage] = useState(1);
  const [galleryHasMore, setGalleryHasMore] = useState(true);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [galleryTotal, setGalleryTotal] = useState(0);
  const galleryObserverRef = useRef(null);
  const GALLERY_PAGE_SIZE = 30;

  // Load unified gallery - optimized single API call with pagination
  const loadGallery = async (page = 1, append = false) => {
    if (galleryLoading) return;
    
    try {
      setGalleryLoading(true);
      const token = localStorage.getItem('azories-token');
      
      // Map filter to API filter type
      const filterMap = {
        'all': null,
        'images': 'images',
        'videos': 'videos',
        'characters': 'characters'
      };
      const filterParam = filterMap[galleryFilter] || null;
      
      // Use optimized unified endpoint with pagination
      const params = new URLSearchParams({
        page: page.toString(),
        limit: GALLERY_PAGE_SIZE.toString()
      });
      if (filterParam) params.append('filter_type', filterParam);
      
      const response = await fetch(`${API_URL}/api/pro-studio/gallery/unified?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const newItems = data.items || [];
        
        if (append) {
          setGallery(prev => [...prev, ...newItems]);
        } else {
          setGallery(newItems);
        }
        
        setGalleryTotal(data.total || 0);
        setGalleryHasMore(data.has_more || false);
        setGalleryPage(page);
      }
    } catch (error) {
      console.error('Error loading gallery:', error);
    } finally {
      setGalleryLoading(false);
    }
  };
  
  // Load more items when scrolling (infinite scroll)
  const loadMoreGallery = useCallback(() => {
    if (galleryHasMore && !galleryLoading) {
      loadGallery(galleryPage + 1, true);
    }
  }, [galleryPage, galleryHasMore, galleryLoading]);
  
  // Reset and reload gallery when filter changes
  useEffect(() => {
    if (isAuthenticated && activeTab === 'gallery') {
      setGalleryPage(1);
      setGalleryHasMore(true);
      loadGallery(1, false);
    }
  }, [galleryFilter, isAuthenticated, activeTab]);
  
  // Gallery items are now pre-filtered from API, just use directly
  const filteredGallery = gallery;
  
  // Open gallery picker with a callback for selection
  const openGalleryPicker = (mode, callback) => {
    setGalleryPickerMode(mode);
    setGalleryPickerCallback(() => callback);
    setShowGalleryPicker(true);
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

  // Create character - from description AND/OR reference images
  const createCharacter = async () => {
    if (!characterName.trim()) {
      toast.error('Please enter a character name');
      return;
    }
    
    // Now we allow BOTH images AND description together
    const hasImages = characterImages.length > 0;
    const hasDescription = characterDescription.trim().length > 0;
    
    if (!hasImages && !hasDescription) {
      toast.error('Please provide a description or upload reference images (or both!)');
      return;
    }

    setIsCreatingCharacter(true);
    setLoadingMessage(hasImages && hasDescription 
      ? 'Creating character from images and description...' 
      : hasImages 
        ? 'Analyzing reference images...' 
        : 'Creating character from description...');

    try {
      const token = localStorage.getItem('azories-token');
      
      // Build request body - can have BOTH images AND description
      const requestBody = {
        name: characterName,
        style: characterStyle,
        genre: characterGenre,
        personality: personality || undefined,
        special_features: specialFeatures || undefined,
      };
      
      // Add description if provided
      if (hasDescription) {
        requestBody.description_prompt = characterDescription;
      }
      
      // Add images if provided
      if (hasImages) {
        requestBody.reference_images = characterImages.map(img => img.url);
      }
      
      // Include physical traits if any are filled
      const filledTraits = Object.fromEntries(
        Object.entries(physicalTraits).filter(([_, v]) => v)
      );
      if (Object.keys(filledTraits).length > 0) {
        requestBody.physical_traits = filledTraits;
      }
      
      const response = await fetch(`${API_URL}/api/pro-studio/characters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Character "${characterName}" created!`);
        setCharacters(prev => [...prev, data.character]);
        // Reset form
        setCharacterName('');
        setCharacterDescription('');
        setCharacterImages([]);
        setPhysicalTraits({ age: '', gender: '', hairColor: '', hairStyle: '', eyeColor: '', skinTone: '', bodyType: '' });
        setSpecialFeatures('');
        setPersonality('');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Error creating character');
      }
    } catch (error) {
      toast.error('Error creating character');
      console.error(error);
    } finally {
      setIsCreatingCharacter(false);
      setLoadingMessage('');
    }
  };

  // Add more images to existing character
  const addImagesToCharacter = async (characterId, newImages) => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          add_reference_images: newImages
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Images added to character!');
        loadCharacters();
        return data.character;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Error adding images');
      }
    } catch (error) {
      toast.error('Error adding images');
      console.error(error);
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
      const token = localStorage.getItem('azories-token');
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
    const token = localStorage.getItem('azories-token');
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
      toast.error('Please enter a prompt describing what the character is doing (e.g., "running through a forest", "standing on a cliff")');
      return;
    }

    setIsLoading(true);
    const method = selectedCharacter.lora_status === 'completed' ? 'LoRA' : 'PuLID';
    const sceneInfo = selectedSceneForGeneration ? ` in scene "${selectedSceneForGeneration.name}"` : '';
    setLoadingMessage(`Generating ${selectedCharacter.name}${sceneInfo} using ${method}...`);

    try {
      const token = localStorage.getItem('azories-token');
      const formData = new FormData();
      formData.append('prompt', prompt);
      formData.append('image_size', aspectRatio === '16:9' ? 'landscape_16_9' : aspectRatio === '9:16' ? 'portrait_16_9' : 'square_hd');
      formData.append('id_strength', faceSimilarity);
      
      // Add scene if selected
      if (selectedSceneForGeneration) {
        formData.append('scene_id', selectedSceneForGeneration.id);
      }

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
          const imageUrl = data.images[0].url;
          const newImage = {
            id: Date.now(),
            url: imageUrl,
            prompt: prompt,
            method: data.method,
            character: selectedCharacter.name
          };
          
          // Show preview modal instead of auto-saving
          setGenerationPreviewData({
            image: newImage,
            type: 'character',
            characterId: selectedCharacter.id,
            characterName: selectedCharacter.name,
            sceneId: selectedSceneForGeneration?.id,
            sceneName: selectedSceneForGeneration?.name,
            prompt: prompt,
            method: data.method
          });
          setShowGenerationPreview(true);
          
          // Still add to generated images for the session
          setGeneratedImages(prev => [newImage, ...prev]);
          setSelectedHeroFrame(newImage);
          loadCredits();
        }
      } else {
        const error = await response.json();
        if (response.status === 402) {
          handleCreditError(error.detail);
        } else {
          toast.error(error.detail || 'Generation failed');
        }
      }
    } catch (error) {
      toast.error('Error generating image');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
      loadCredits(); // Always refresh credits
    }
  };

  // Delete a character
  const deleteCharacter = async (characterId) => {
    if (!window.confirm('Are you sure you want to delete this character? This will also delete all generated images in the character folder.')) {
      return;
    }

    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Character deleted');
        setCharacters(prev => prev.filter(c => c.id !== characterId));
        if (selectedCharacter?.id === characterId) {
          setSelectedCharacter(null);
        }
        if (viewingCharacter?.id === characterId) {
          closeCharacterView();
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete character');
      }
    } catch (error) {
      toast.error('Error deleting character');
      console.error(error);
    }
  };

  // Edit character details
  const [editingCharacter, setEditingCharacter] = useState(null);
  const [editForm, setEditForm] = useState({});

  const openEditModal = (character) => {
    setEditingCharacter(character);
    setEditForm({
      name: character.name || '',
      description_prompt: character.description_prompt || '',
      style: character.style || 'illustration',
      genre: character.genre || 'fantasy',
      personality: character.personality || '',
      special_features: character.special_features || ''
    });
  };

  const saveCharacterEdits = async () => {
    if (!editingCharacter) return;

    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${editingCharacter.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(editForm)
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Character updated');
        setCharacters(prev => prev.map(c => c.id === editingCharacter.id ? data.character : c));
        setEditingCharacter(null);
        // Update viewing character if open
        if (viewingCharacter?.id === editingCharacter.id) {
          setViewingCharacter(data.character);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update character');
      }
    } catch (error) {
      toast.error('Error updating character');
      console.error(error);
    }
  };

  // Regenerate thumbnail for better consistency
  const regenerateThumbnail = async (characterId) => {
    setIsLoading(true);
    setLoadingMessage('Regenerating character thumbnail...');

    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}/generate-thumbnail`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Thumbnail regenerated!');
        // Update character in list
        setCharacters(prev => prev.map(c => 
          c.id === characterId ? { ...c, thumbnail: data.thumbnail } : c
        ));
        if (viewingCharacter?.id === characterId) {
          setViewingCharacter(prev => ({ ...prev, thumbnail: data.thumbnail }));
        }
        if (editingCharacter?.id === characterId) {
          setEditingCharacter(prev => ({ ...prev, thumbnail: data.thumbnail }));
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to regenerate thumbnail');
      }
    } catch (error) {
      toast.error('Error regenerating thumbnail');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Create a new scene
  const createScene = async () => {
    if (!sceneName.trim()) {
      toast.error('Please enter a scene name');
      return;
    }
    if (!sceneDescription.trim()) {
      toast.error('Please describe the scene');
      return;
    }

    setIsCreatingScene(true);
    setLoadingMessage('Creating scene...');

    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/scenes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: sceneName,
          description: sceneDescription,
          style: sceneStyle,
          genre: sceneGenre,
          location_type: sceneLocationType,
          lighting: sceneLighting,
          mood: sceneMood,
          time_of_day: sceneTimeOfDay,
          weather: sceneWeather
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Scene "${sceneName}" created!`);
        setScenes(prev => [data.scene, ...prev]);
        // Reset form
        setSceneName('');
        setSceneDescription('');
        setSceneTimeOfDay('');
        setSceneWeather('');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Error creating scene');
      }
    } catch (error) {
      toast.error('Error creating scene');
      console.error(error);
    } finally {
      setIsCreatingScene(false);
      setLoadingMessage('');
    }
  };

  // Delete a scene
  const deleteScene = async (sceneId) => {
    if (!window.confirm('Delete this scene?')) return;

    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/scenes/${sceneId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Scene deleted');
        setScenes(prev => prev.filter(s => s.id !== sceneId));
        if (selectedScene?.id === sceneId) setSelectedScene(null);
      }
    } catch (error) {
      toast.error('Error deleting scene');
    }
  };

  // Generate image with scene
  const generateWithScene = async () => {
    if (!selectedScene) {
      toast.error('Please select a scene');
      return;
    }

    setIsLoading(true);
    setLoadingMessage('Generating with scene settings...');

    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/scenes/${selectedScene.id}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: prompt,
          character_id: selectedCharacter?.id,
          image_size: aspectRatio === '16:9' ? 'landscape_16_9' : aspectRatio === '9:16' ? 'portrait_16_9' : 'square_hd'
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newImage = {
          id: Date.now(),
          url: data.image_url,
          prompt: data.prompt,
          scene: selectedScene.name,
          character: selectedCharacter?.name
        };
        
        // Show preview modal instead of auto-saving
        setGenerationPreviewData({
          image: newImage,
          type: 'scene',
          sceneId: selectedScene.id,
          sceneName: selectedScene.name,
          characterId: selectedCharacter?.id,
          characterName: selectedCharacter?.name,
          prompt: data.prompt
        });
        setShowGenerationPreview(true);
        
        // Still add to generated images for the session
        setGeneratedImages(prev => [newImage, ...prev]);
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
      const token = localStorage.getItem('azories-token');
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
      
      // Build art style prompt
      const artStylePrompts = {
        'realistic': 'photorealistic, professional photography, natural lighting, high detail',
        'cinematic': 'cinematic, movie still, dramatic lighting, film grain, professional color grading',
        'cartoon': 'cartoon style, animated, bold colors, clean lines, expressive',
        'anime': 'anime style, manga, Japanese animation, vibrant colors, detailed eyes',
        'pixar': 'Pixar style, 3D animated, smooth render, family-friendly, expressive features',
        'watercolor': 'watercolor painting, soft edges, artistic, painterly style, delicate colors',
        'comic': 'comic book style, bold outlines, dynamic shading, graphic novel',
        'fantasy': 'fantasy art style, magical, ethereal, detailed, imaginative',
        'storybook': 'children\'s book illustration, soft colors, whimsical, gentle, friendly'
      };
      const artStylePrompt = artStylePrompts[cinemaArtStyle] || artStylePrompts['cinematic'];
      
      const fullPrompt = [
        prompt,
        characterPrompt,
        cinemaPrompt,
        lightingPreset?.prompt || '',
        artStylePrompt
      ].filter(Boolean).join(', ');

      const token = localStorage.getItem('azories-token');
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
          aspect_ratio: aspectRatio,
          art_style: cinemaArtStyle
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newImage = {
          id: Date.now(),
          url: data.image_url,
          prompt: fullPrompt,
          settings: { selectedCamera, selectedLens, selectedFocalLength, selectedLighting, cinemaArtStyle }
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

  // Generate variant from source image with Cinema Studio settings
  const generateCinemaVariant = async () => {
    if (!cinemaSourceImage) {
      toast.error('Please select a source image first');
      return;
    }

    setIsLoading(true);
    setLoadingMessage(`Creating cinema variant of ${cinemaSourceImage.name || 'image'}...`);

    try {
      const cinemaPrompt = buildCinemaPrompt(selectedCamera, selectedLens, selectedFocalLength);
      const lightingPreset = LIGHTING_PRESETS.find(l => l.id === selectedLighting);
      
      // Build art style prompt
      const artStylePrompts = {
        'realistic': 'photorealistic, professional photography, natural lighting, high detail',
        'cinematic': 'cinematic, movie still, dramatic lighting, film grain, professional color grading',
        'cartoon': 'cartoon style, animated, bold colors, clean lines, expressive',
        'anime': 'anime style, manga, Japanese animation, vibrant colors, detailed eyes',
        'pixar': 'Pixar style, 3D animated, smooth render, family-friendly, expressive features',
        'watercolor': 'watercolor painting, soft edges, artistic, painterly style, delicate colors',
        'comic': 'comic book style, bold outlines, dynamic shading, graphic novel',
        'fantasy': 'fantasy art style, magical, ethereal, detailed, imaginative',
        'storybook': 'children\'s book illustration, soft colors, whimsical, gentle, friendly'
      };
      const artStylePrompt = artStylePrompts[cinemaArtStyle] || artStylePrompts['cinematic'];
      
      // Build prompt that describes re-creating the image with new camera settings and art style
      const variantPrompt = [
        prompt || 'recreate this image with the following settings',
        cinemaPrompt,
        lightingPreset?.prompt || '',
        artStylePrompt
      ].filter(Boolean).join(', ');

      const token = localStorage.getItem('azories-token');
      
      // Use image-to-image endpoint with the source
      const response = await fetch(`${API_URL}/api/pro-studio/generate-variant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          source_image: cinemaSourceImage.url,
          prompt: variantPrompt,
          camera: selectedCamera,
          lens: selectedLens,
          focal_length: selectedFocalLength,
          lighting: selectedLighting,
          aspect_ratio: aspectRatio,
          art_style: cinemaArtStyle,
          strength: 0.7 // Keep some of the original while applying new style
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newImage = {
          id: Date.now(),
          url: data.image_url,
          prompt: variantPrompt,
          sourceImage: cinemaSourceImage.url,
          settings: { selectedCamera, selectedLens, selectedFocalLength, selectedLighting, cinemaArtStyle }
        };
        setGeneratedImages(prev => [newImage, ...prev]);
        setSelectedHeroFrame(newImage);
        toast.success('Cinema variant generated!');
      } else {
        const error = await response.json();
        if (response.status === 402) {
          handleCreditError(error.detail);
        } else {
          toast.error(error.detail || 'Variant generation failed');
        }
      }
    } catch (error) {
      toast.error('Error generating variant');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Generate shots (9 angles from 1 image)
  // Helper to resize image to reduce payload size
  const resizeImageForAPI = async (imageData, maxSize = 1024) => {
    return new Promise((resolve) => {
      // If it's already a base64 data URL, process it directly
      if (imageData.startsWith('data:')) {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;
          
          // Scale down if larger than maxSize
          if (width > maxSize || height > maxSize) {
            const ratio = Math.min(maxSize / width, maxSize / height);
            width = Math.round(width * ratio);
            height = Math.round(height * ratio);
          }
          
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);
          
          // Return as base64 with reduced quality
          resolve(canvas.toDataURL('image/jpeg', 0.85));
        };
        img.onerror = () => resolve(imageData);
        img.src = imageData;
      } else if (imageData.startsWith('http')) {
        // For external URLs, we can't resize on client due to CORS
        // Return the original URL - backend will handle it
        resolve(imageData);
      } else {
        // Unknown format, return as is
        resolve(imageData);
      }
    });
  };

  // Poll task status helper
  const pollTaskStatus = async (taskId, onProgress, maxPolls = 120) => {
    const token = localStorage.getItem('azories-token');
    let polls = 0;
    let consecutiveErrors = 0;
    
    while (polls < maxPolls) {
      try {
        const response = await fetch(`${API_URL}/api/tasks/${taskId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Handle non-OK responses
        if (!response.ok) {
          // Handle gateway errors (502, 504) - retry silently
          if (response.status === 502 || response.status === 504 || response.status === 503) {
            consecutiveErrors++;
            console.log(`Task ${taskId}: Gateway error ${response.status}, retry ${consecutiveErrors}/10`);
            if (consecutiveErrors >= 10) {
              throw new Error('Server temporarily unavailable. The task may still be processing - please check the Gallery later.');
            }
            // Wait longer between retries for gateway errors
            await new Promise(resolve => setTimeout(resolve, 5000));
            polls++;
            continue;
          }
          // For other errors, try to parse error message
          let errorMsg = `Server error: ${response.status}`;
          try {
            const text = await response.text();
            if (text) {
              const errorData = JSON.parse(text);
              errorMsg = errorData.detail || errorMsg;
            }
          } catch (e) {
            // Ignore parse errors - use default message
          }
          throw new Error(errorMsg);
        }
        
        // Reset consecutive errors on success
        consecutiveErrors = 0;
        
        // Parse successful response
        let task;
        try {
          task = await response.json();
        } catch (parseErr) {
          console.error('Failed to parse task response:', parseErr);
          // Wait and retry
          await new Promise(resolve => setTimeout(resolve, 3000));
          polls++;
          continue;
        }
        
        if (onProgress && task.progress !== undefined) {
          onProgress(task.progress);
        }
        
        if (task.status === 'completed') {
          return task.result;
        } else if (task.status === 'failed') {
          throw new Error(task.error || 'Task failed');
        }
        
        // Still pending/processing - wait and poll again
        await new Promise(resolve => setTimeout(resolve, 3000));
        polls++;
      } catch (err) {
        // If it's a network error, retry
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
          consecutiveErrors++;
          if (consecutiveErrors < 10) {
            await new Promise(resolve => setTimeout(resolve, 5000));
            polls++;
            continue;
          }
        }
        throw err;
      }
    }
    
    throw new Error('Task timed out after ' + (maxPolls * 3) + ' seconds');
  };

  const generateShots = async () => {
    if (!shotsSourceImage) {
      toast.error('Please upload a source image first');
      return;
    }

    setIsLoading(true);
    setLoadingMessage('Starting shots generation...');
    setLoadingProgress(0);
    setShotsResults([]);

    try {
      const token = localStorage.getItem('azories-token');
      
      // Resize image to reduce payload size (max 1024px)
      const resizedImage = await resizeImageForAPI(shotsSourceImage, 1024);
      
      // Get character style if a character is selected
      const characterStyle = shotsSelectedCharacter?.style || null;
      
      // Start the task (returns immediately with task_id)
      const startResponse = await fetch(`${API_URL}/api/pro-studio/generate-shots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          source_image: resizedImage,
          character_id: shotsSelectedCharacter?.id,
          style: shotsStyle,
          character_style: characterStyle
        })
      });

      if (!startResponse.ok) {
        // Handle gateway errors
        if (startResponse.status === 502 || startResponse.status === 504) {
          throw new Error('Server is busy. Please try again in a moment.');
        }
        // Try to parse error response
        let errorDetail = 'Failed to start shots generation';
        try {
          const errorText = await startResponse.text();
          if (errorText) {
            const errorData = JSON.parse(errorText);
            errorDetail = errorData.detail || errorDetail;
          }
        } catch (e) {
          // Use default error message
        }
        if (startResponse.status === 402) {
          handleCreditError(errorDetail);
          return;
        }
        throw new Error(errorDetail);
      }
      
      // Parse successful response
      let responseData;
      try {
        responseData = await startResponse.json();
      } catch (parseErr) {
        throw new Error('Invalid response from server');
      }
      
      const { task_id } = responseData;
      
      if (!task_id) {
        throw new Error('No task ID returned from server');
      }
      
      setLoadingMessage('Generating 9 angles... This may take a few minutes.');
      
      // Poll for completion
      const result = await pollTaskStatus(task_id, (progress) => {
        setLoadingProgress(progress);
        if (progress < 20) {
          setLoadingMessage('Analyzing source image...');
        } else if (progress < 100) {
          const shotNum = Math.ceil((progress - 20) / 9);
          setLoadingMessage(`Generating shot ${Math.min(shotNum, 9)} of 9...`);
        }
      });
      
      if (result && result.shots) {
        setShotsResults(result.shots);
        setShowShotsReview(true);
        toast.success(`${result.total || result.shots.length} shots generated! Review and save your favorites.`);
      } else {
        toast.error('No shots were generated');
      }
      
      loadCredits();
    } catch (error) {
      console.error('Shots generation error:', error);
      toast.error(error.message || 'Error generating shots');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
      setLoadingProgress(0);
      loadCredits();
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
      const token = localStorage.getItem('azories-token');
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
          character: selectedCharacter.name,
          prompt: `${selectedCharacter.name} - ${expressionData.name} expression`
        };
        setGeneratedImages(prev => [newImage, ...prev]);
        toast.success(`${expressionData.name} expression generated!`);
        loadCredits(); // Refresh credits
        
        // Auto-save to character folder
        if (data.image_url) {
          await saveToCharacterFolder(
            selectedCharacter.id, 
            data.image_url, 
            `${expressionData.name} expression - ${prompt || 'portrait'}`,
            'expression'
          );
        }
      } else {
        const error = await response.json();
        if (response.status === 402) {
          handleCreditError(error.detail);
        } else {
          toast.error(error.detail || 'Failed to generate expression');
        }
      }
    } catch (error) {
      toast.error('Error generating expression');
      console.error(error);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
      loadCredits(); // Always refresh credits
    }
  };

  // Animate hero frame to video using fal.ai Kling (Pro feature)
  const animateToVideo = async () => {
    // Get the source image based on selected type
    let sourceImageUrl = null;
    let sourceName = '';
    
    if (videoSourceType === 'hero') {
      if (!selectedHeroFrame) {
        toast.error('Please select a hero frame to animate');
        return;
      }
      sourceImageUrl = selectedHeroFrame.url;
      sourceName = 'hero frame';
    } else if (videoSourceType === 'character') {
      // Use selected gallery image or fall back to master thumbnail
      if (videoSelectedImage?.url) {
        sourceImageUrl = videoSelectedImage.url;
        sourceName = `${videoSourceCharacter?.name || 'character'} image`;
      } else if (videoSourceCharacter?.thumbnail) {
        sourceImageUrl = videoSourceCharacter.thumbnail;
        sourceName = videoSourceCharacter.name;
      } else {
        toast.error('Please select an image from the character gallery');
        return;
      }
    } else if (videoSourceType === 'upload') {
      if (!videoUploadedImage) {
        toast.error('Please upload an image to animate');
        return;
      }
      sourceImageUrl = videoUploadedImage;
      sourceName = 'uploaded image';
    }

    setIsLoading(true);
    setLoadingProgress(0);
    setLoadingMessage(`Preparing image for ${sourceName}...`);
    
    // Resize image to reduce payload size (512px is good for video)
    const resizedImage = await resizeImageForAPI(sourceImageUrl, 512);
    sourceImageUrl = resizedImage;
    
    // Build enhanced prompt with style for consistency
    let enhancedPrompt = videoPrompt || 'subtle cinematic movement, breathing, natural motion';
    if (videoArtStyle && videoArtStyle !== 'none') {
      enhancedPrompt = `${videoArtStyle} style, ${enhancedPrompt}`;
    }

    try {
      const token = localStorage.getItem('azories-token');
      
      // Start the video generation task (returns immediately with task_id)
      const startResponse = await fetch(`${API_URL}/api/pro-studio/animate-hero`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: sourceImageUrl,
          motion_prompt: enhancedPrompt,
          model: 'kling',
          duration: videoDuration,
          art_style: videoArtStyle
        })
      });

      if (!startResponse.ok) {
        const error = await startResponse.json();
        if (startResponse.status === 402) {
          handleCreditError(error.detail);
          return;
        }
        throw new Error(error.detail || 'Failed to start video generation');
      }
      
      const { task_id } = await startResponse.json();
      
      if (!task_id) {
        throw new Error('No task ID returned from server');
      }
      
      setLoadingMessage(`Animating ${sourceName} with Kling AI... This may take 1-2 minutes.`);
      
      // Poll for completion
      const result = await pollTaskStatus(task_id, (progress) => {
        setLoadingProgress(progress);
        if (progress < 20) {
          setLoadingMessage('Initializing video generation...');
        } else if (progress < 50) {
          setLoadingMessage('Processing image with Kling AI...');
        } else if (progress < 80) {
          setLoadingMessage('Rendering video frames...');
        } else {
          setLoadingMessage('Finalizing video... almost done!');
        }
      });
      
      if (result && result.video_url) {
        const newVideo = {
          id: Date.now(),
          url: result.video_url,
          sourceImage: sourceImageUrl,
          model: 'kling'
        };
        setGeneratedVideos(prev => [newVideo, ...prev]);
        setLoadingProgress(100);
        toast.success('Video generated with high face fidelity!');
        
        // Save to character folder if using character source
        if (videoSourceType === 'character' && videoSourceCharacter?.id) {
          try {
            await saveToCharacterFolder(
              videoSourceCharacter.id,
              result.video_url,
              `Video - ${enhancedPrompt || 'animation'}`,
              'video'
            );
            toast.success(`Video also saved to ${videoSourceCharacter.name}'s folder`);
          } catch (saveErr) {
            console.error('Error saving video to character folder:', saveErr);
          }
        }
        
        // Also save to general gallery
        await saveToGallery(result.video_url, enhancedPrompt || 'Generated video', 'video');
      } else {
        toast.error('No video URL returned');
      }
      
      loadCredits();
    } catch (error) {
      console.error('Video generation error:', error);
      toast.error(error.message || 'Error animating image');
    } finally {
      setIsLoading(false);
      setLoadingProgress(0);
      loadCredits();
    }
  };

  // Simulate progress for long-running video generation
  const startVideoProgressSimulation = () => {
    let progress = 5;
    const interval = setInterval(() => {
      progress += Math.random() * 8;
      if (progress > 95) progress = 95; // Cap at 95% until actual completion
      setLoadingProgress(Math.round(progress));
      
      // Update message based on progress
      if (progress < 20) {
        setLoadingMessage('Initializing video generation...');
      } else if (progress < 40) {
        setLoadingMessage('Processing image frames...');
      } else if (progress < 60) {
        setLoadingMessage('Applying motion effects...');
      } else if (progress < 80) {
        setLoadingMessage('Rendering video...');
      } else {
        setLoadingMessage('Finalizing... almost done!');
      }
    }, 3000);
    
    // Store interval ID to clear it later
    window.videoProgressInterval = interval;
  };

  // Poll video generation status
  const pollVideoStatus = async (jobId) => {
    const token = localStorage.getItem('azories-token');
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/art-studio/animation-status/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.message) {
            setLoadingMessage(data.message);
          }
          if (data.progress) {
            setLoadingProgress(Math.max(loadingProgress, data.progress));
          }
          
          if (data.status === 'completed' && data.video_base64) {
            clearInterval(pollInterval);
            if (window.videoProgressInterval) {
              clearInterval(window.videoProgressInterval);
            }
            setLoadingProgress(100);
            const newVideo = {
              id: Date.now(),
              url: `data:video/mp4;base64,${data.video_base64}`,
              sourceImage: selectedHeroFrame?.url
            };
            setGeneratedVideos(prev => [newVideo, ...prev]);
            toast.success('Video generated!');
            setIsLoading(false);
            setLoadingMessage('');
            setLoadingProgress(0);
          } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            if (window.videoProgressInterval) {
              clearInterval(window.videoProgressInterval);
            }
            toast.error(data.message || 'Video generation failed');
            setIsLoading(false);
            setLoadingMessage('');
            setLoadingProgress(0);
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000);

    // Timeout after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (window.videoProgressInterval) {
        clearInterval(window.videoProgressInterval);
      }
      if (isLoading) {
        setIsLoading(false);
        setLoadingMessage('');
        setLoadingProgress(0);
        toast.error('Video generation timed out. Please try again.');
      }
    }, 600000);
  };

  // Save to gallery - enhanced to handle different input formats
  const saveToGallery = async (imageUrlOrItem, promptOrName = '', type = 'image') => {
    try {
      const token = localStorage.getItem('azories-token');
      
      // Handle both object format {url, name, prompt} and direct URL
      const imageUrl = typeof imageUrlOrItem === 'string' ? imageUrlOrItem : imageUrlOrItem?.url;
      const name = typeof imageUrlOrItem === 'object' ? (imageUrlOrItem?.name || imageUrlOrItem?.prompt || promptOrName) : promptOrName;
      const prompt = typeof imageUrlOrItem === 'object' ? (imageUrlOrItem?.prompt || '') : promptOrName;
      
      const response = await fetch(`${API_URL}/api/art-studio/gallery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: imageUrl,
          name: name || 'Pro Studio Image',
          prompt: prompt,
          style: type,
          type: type === 'video' ? 'animation' : 'image',
          source: 'pro_studio'  // Mark as Pro Studio item
        })
      });

      if (response.ok) {
        toast.success('Saved to gallery!');
        loadGallery();
      } else {
        const err = await response.json().catch(() => ({}));
        toast.error(err.detail || 'Failed to save');
      }
    } catch (error) {
      console.error('Save error:', error);
      toast.error('Failed to save');
    }
  };

  // Delete from gallery
  const deleteFromGallery = async (itemId, source = 'art-studio') => {
    // Handle character master images specially
    if (source === 'character' && itemId.startsWith('char-')) {
      const charId = itemId.replace('char-', '');
      if (!confirm('This will delete the entire character and all its generated images. Are you sure?')) return;
      await deleteCharacter(charId);
      return;
    }
    
    if (!confirm('Are you sure you want to delete this item?')) return;
    
    try {
      const token = localStorage.getItem('azories-token');
      let endpoint = `${API_URL}/api/art-studio/gallery/${itemId}`;
      
      // Use appropriate endpoint based on source
      if (source === 'character-gallery') {
        endpoint = `${API_URL}/api/pro-studio/character-gallery/${itemId}`;
      } else if (source === 'art-studio-video' || source === 'character-video') {
        endpoint = `${API_URL}/api/art-studio/gallery/${itemId}`;
      }
      
      const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast.success('Deleted successfully');
        loadGallery();
      } else {
        const err = await response.json().catch(() => ({}));
        toast.error(err.detail || 'Failed to delete');
      }
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Failed to delete');
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

  // Crop handlers
  const onCropComplete = useCallback((croppedArea, croppedAreaPixels) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const openCropModal = (imageUrl, type, parentId) => {
    setCropImage({ url: imageUrl, type, parentId });
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setCroppedAreaPixels(null);
    setShowCropModal(true);
  };

  const createCroppedImage = async () => {
    if (!cropImage || !croppedAreaPixels) return null;
    
    try {
      const image = new Image();
      image.crossOrigin = 'anonymous';
      
      return new Promise((resolve, reject) => {
        image.onload = () => {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          
          canvas.width = croppedAreaPixels.width;
          canvas.height = croppedAreaPixels.height;
          
          ctx.drawImage(
            image,
            croppedAreaPixels.x,
            croppedAreaPixels.y,
            croppedAreaPixels.width,
            croppedAreaPixels.height,
            0,
            0,
            croppedAreaPixels.width,
            croppedAreaPixels.height
          );
          
          canvas.toBlob((blob) => {
            if (blob) {
              const reader = new FileReader();
              reader.onloadend = () => {
                resolve(reader.result);
              };
              reader.readAsDataURL(blob);
            } else {
              reject(new Error('Failed to create blob'));
            }
          }, 'image/png', 0.95);
        };
        
        image.onerror = () => reject(new Error('Failed to load image'));
        image.src = cropImage.url;
      });
    } catch (error) {
      console.error('Error creating cropped image:', error);
      return null;
    }
  };

  const handleSaveCroppedImage = async () => {
    if (!cropImage || !croppedAreaPixels) {
      toast.error('Please adjust the crop area first');
      return;
    }
    
    setIsLoading(true);
    setLoadingMessage('Creating cropped image...');
    
    try {
      const croppedDataUrl = await createCroppedImage();
      if (!croppedDataUrl) {
        toast.error('Failed to create cropped image');
        return;
      }
      
      // Save to appropriate folder based on type
      if (cropImage.type === 'scene' && cropImage.parentId) {
        await saveToSceneFolder(cropImage.parentId, croppedDataUrl, 'Cropped image', 'cropped');
        loadSceneGallery(cropImage.parentId);
        toast.success('Cropped image saved to scene folder!');
      } else if (cropImage.type === 'character' && cropImage.parentId) {
        await saveToCharacterFolder(cropImage.parentId, croppedDataUrl, 'Cropped image', 'cropped');
        loadCharacterGallery(cropImage.parentId);
        toast.success('Cropped image saved to character folder!');
      } else {
        // Save to general gallery
        await saveToGallery(croppedDataUrl, 'Cropped image', 'image');
        loadGallery();
        toast.success('Cropped image saved to gallery!');
      }
      
      setShowCropModal(false);
    } catch (error) {
      console.error('Error saving cropped image:', error);
      toast.error('Failed to save cropped image');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Load character's generated images (character folder)
  const loadCharacterGallery = async (characterId) => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}/gallery`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCharacterGallery(data.images || []);
      }
    } catch (error) {
      console.error('Error loading character gallery:', error);
    }
  };

  // Save image to character folder
  const saveToCharacterFolder = async (characterId, imageUrl, prompt, type = 'generated') => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}/gallery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: imageUrl,
          prompt: prompt,
          type: type
        })
      });
      if (response.ok) {
        toast.success('Image saved to character folder!');
        // Refresh gallery if viewing this character
        if (viewingCharacter?.id === characterId) {
          loadCharacterGallery(characterId);
        }
      }
    } catch (error) {
      toast.error('Failed to save image');
    }
  };

  // View character details with gallery
  const openCharacterView = async (character) => {
    setViewingCharacter(character);
    await loadCharacterGallery(character.id);
  };

  // Close character view
  const closeCharacterView = () => {
    setViewingCharacter(null);
    setCharacterGallery([]);
  };

  // Load character gallery for video mode
  const loadVideoCharacterGallery = async (characterId) => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}/gallery`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        // Normalize image URLs - API returns 'image_url', we use 'url' internally
        const normalizedImages = (data.images || []).map(img => ({
          ...img,
          url: img.image_url || img.url // Ensure 'url' field exists
        }));
        setVideoCharacterGallery(normalizedImages);
      }
    } catch (error) {
      console.error('Error loading video character gallery:', error);
    }
  };

  // Handle character selection for video - load their gallery
  const handleVideoCharacterSelect = async (characterId) => {
    const character = characters.find(c => c.id === characterId);
    setVideoSourceCharacter(character);
    setVideoSelectedImage(null); // Reset selected image
    if (character) {
      await loadVideoCharacterGallery(characterId);
      // Auto-select master image with its description
      if (character.thumbnail) {
        setVideoSelectedImage({
          url: character.thumbnail,
          prompt: character.description || character.appearance_traits || 'Character master image',
          type: 'master'
        });
        // Pre-fill prompt with character description
        setVideoPrompt(`${character.name} - ${character.description || 'subtle cinematic movement'}`);
      }
    }
  };

  // Select an image from character gallery for video
  const selectVideoImage = (image) => {
    // Ensure we have a normalized url field
    const normalizedImage = {
      ...image,
      url: image.url || image.image_url
    };
    setVideoSelectedImage(normalizedImage);
    // Update prompt with the image's description
    if (image.prompt) {
      setVideoPrompt(image.prompt);
    }
  };

  // Load scene's generated images (scene folder)
  const loadSceneGallery = async (sceneId) => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/scenes/${sceneId}/gallery`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSceneGallery(data.images || []);
      }
    } catch (error) {
      console.error('Error loading scene gallery:', error);
    }
  };

  // Save image to scene folder
  const saveToSceneFolder = async (sceneId, imageUrl, prompt, type = 'generated', characterId = null) => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/pro-studio/scenes/${sceneId}/gallery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: imageUrl,
          prompt: prompt,
          type: type,
          character_id: characterId
        })
      });
      if (response.ok) {
        toast.success('Image saved to scene folder!');
        if (viewingScene?.id === sceneId) {
          loadSceneGallery(sceneId);
        }
      }
    } catch (error) {
      toast.error('Failed to save image');
    }
  };

  // View scene details with gallery
  const openSceneView = async (scene) => {
    setViewingScene(scene);
    await loadSceneGallery(scene.id);
  };

  // Close scene view
  const closeSceneView = () => {
    setViewingScene(null);
    setSceneGallery([]);
  };

  // Save any image to Art Studio gallery
  const saveToArtStudioGallery = async (imageUrl, prompt, type = 'pro-studio') => {
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/art-studio/gallery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: imageUrl,
          prompt: prompt || 'Pro Studio image',
          model: 'pro-studio',
          type: type
        })
      });
      if (response.ok) {
        toast.success('Saved to Art Studio Gallery!');
        loadGallery(); // Refresh gallery
      } else {
        toast.error('Failed to save to gallery');
      }
    } catch (error) {
      toast.error('Error saving to gallery');
    }
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
          
          {/* Credits Display */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-gradient-to-r from-amber-500/20 to-orange-500/20 px-4 py-2 rounded-full border border-amber-500/30">
              <FiZap className="text-amber-400" />
              <span className="text-amber-300 font-medium">{credits}</span>
              <span className="text-amber-400/70 text-sm">credits</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={goToPurchaseCredits}
                className="ml-2 text-amber-300 hover:text-amber-100 hover:bg-amber-500/20 h-6 px-2"
                title="Buy more credits"
              >
                <FiPlus size={14} />
              </Button>
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
      {/* Image Preview Modal - HIGHEST z-index */}
      <AnimatePresence>
        {previewImage && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/95 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
            onClick={() => setPreviewImage(null)}
          >
            <motion.div 
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="relative max-w-5xl max-h-[90vh]"
              onClick={e => e.stopPropagation()}
            >
              <img 
                src={previewImage.url} 
                alt={previewImage.prompt || 'Preview'} 
                className="max-w-full max-h-[85vh] object-contain rounded-lg"
              />
              <div className="absolute bottom-0 left-0 right-0 bg-black/80 p-4 rounded-b-lg">
                <p className="text-white text-sm mb-2">{previewImage.prompt || previewImage.character || 'Generated image'}</p>
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    onClick={(e) => {
                      e.stopPropagation();
                      // Create download link
                      const link = document.createElement('a');
                      link.href = previewImage.url;
                      link.download = `character-image-${Date.now()}.png`;
                      link.target = '_blank';
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                      toast.success('Download started');
                    }}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <FiDownload className="mr-1" /> Download
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={async (e) => {
                      e.stopPropagation();
                      // Save to main art studio gallery
                      try {
                        const token = localStorage.getItem('azories-token');
                        const response = await fetch(`${API_URL}/api/art-studio/gallery`, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}`
                          },
                          body: JSON.stringify({
                            image_url: previewImage.url,
                            prompt: previewImage.prompt || 'Character image',
                            model: 'pro-studio',
                            type: 'character'
                          })
                        });
                        if (response.ok) {
                          toast.success('Saved to Art Studio Gallery!');
                        } else {
                          toast.error('Failed to save to gallery');
                        }
                      } catch (error) {
                        toast.error('Error saving to gallery');
                      }
                    }}
                    className="border-purple-400/50 text-purple-300 hover:bg-purple-500/20 hover:border-purple-400"
                  >
                    <FiSave className="mr-1" /> Save to Gallery
                  </Button>
                  {selectedCharacter && (
                    <>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={async (e) => {
                          e.stopPropagation();
                          await saveToCharacterFolder(
                            selectedCharacter.id,
                            previewImage.url,
                            previewImage.prompt || 'Saved image',
                            'saved'
                          );
                        }}
                        className="border-purple-500/50 text-purple-300"
                      >
                        <FiFolder className="mr-1" /> Add to Folder
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            const token = localStorage.getItem('azories-token');
                            const response = await fetch(`${API_URL}/api/pro-studio/characters/${selectedCharacter.id}/add-reference`, {
                              method: 'POST',
                              headers: {
                                'Content-Type': 'application/json',
                                Authorization: `Bearer ${token}`
                              },
                              body: JSON.stringify({ image_url: previewImage.url })
                            });
                            if (response.ok) {
                              const data = await response.json();
                              toast.success(data.message);
                              // Refresh character list to show updated reference count
                              loadCharacters();
                            } else {
                              toast.error('Failed to add reference image');
                            }
                          } catch (error) {
                            toast.error('Error adding reference image');
                          }
                        }}
                        className="border-amber-500/50 text-amber-300"
                        title="Add to reference images for LoRA training"
                      >
                        <FiStar className="mr-1" /> Add to References
                      </Button>
                    </>
                  )}
                </div>
              </div>
              <button 
                onClick={() => setPreviewImage(null)}
                className="absolute top-4 right-4 bg-black/70 hover:bg-black/90 text-white p-2 rounded-full"
              >
                <FiX size={24} />
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Character View Modal */}
      <AnimatePresence>
        {viewingCharacter && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/95 backdrop-blur-sm z-[60] overflow-auto"
          >
            <div className="max-w-6xl mx-auto p-6">
              {/* Header with Back Button */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <Button 
                    variant="ghost" 
                    onClick={closeCharacterView}
                    className="text-gray-400 hover:text-white hover:bg-gray-800"
                  >
                    <FiArrowLeft className="mr-2" /> Back to Studio
                  </Button>
                  <div className="w-px h-8 bg-gray-700" />
                  <img 
                    src={viewingCharacter.thumbnail || viewingCharacter.reference_images?.[0]} 
                    alt={viewingCharacter.name}
                    className="w-12 h-12 rounded-full object-cover border-2 border-purple-500 cursor-pointer"
                    onClick={() => setPreviewImage({ url: viewingCharacter.thumbnail || viewingCharacter.reference_images?.[0], prompt: viewingCharacter.name })}
                  />
                  <div>
                    <h2 className="text-xl font-bold text-white">{viewingCharacter.name}</h2>
                    <p className="text-gray-400 text-sm">{viewingCharacter.style} • {viewingCharacter.genre}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline"
                    onClick={() => regenerateThumbnail(viewingCharacter.id)}
                    className="border-blue-400/50 text-blue-300 hover:bg-blue-500/20 hover:border-blue-400"
                    title="Regenerate thumbnail for better consistency"
                  >
                    <FiRefreshCw className="mr-2" /> New Look
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => { openEditModal(viewingCharacter); closeCharacterView(); }}
                    className="border-amber-400/50 text-amber-300 hover:bg-amber-500/20 hover:border-amber-400"
                  >
                    <FiEdit3 className="mr-2" /> Edit
                  </Button>
                  <Button 
                    onClick={() => { setSelectedCharacter(viewingCharacter); closeCharacterView(); }}
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                  >
                    <FiZap className="mr-2" /> Use for Generation
                  </Button>
                </div>
              </div>

              {/* Character Description */}
              {viewingCharacter.description && (
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4 mb-6">
                  <h3 className="text-white font-medium mb-2">Character Description</h3>
                  <p className="text-gray-300 text-sm whitespace-pre-wrap">{viewingCharacter.description}</p>
                </div>
              )}

              {/* Reference Images */}
              {viewingCharacter.reference_images?.length > 0 && (
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4 mb-6">
                  <h3 className="text-white font-medium mb-3">Reference Images ({viewingCharacter.reference_images.length})</h3>
                  <div className="grid grid-cols-4 md:grid-cols-6 gap-3">
                    {viewingCharacter.reference_images.map((img, idx) => (
                      <img 
                        key={idx}
                        src={img} 
                        alt={`Reference ${idx + 1}`}
                        className="w-full aspect-square object-cover rounded-lg cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all"
                        onClick={() => setPreviewImage({ url: img, prompt: `${viewingCharacter.name} reference ${idx + 1}` })}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Generated Images (Character Folder) */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <FiFolder className="text-purple-400" /> Character Folder ({characterGallery.length} images)
                </h3>
                {characterGallery.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FiImage className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No generated images yet</p>
                    <p className="text-sm">Select this character and generate images to build your collection</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {characterGallery.map((img) => (
                      <div 
                        key={img.id}
                        className="relative group cursor-pointer"
                        onClick={() => setPreviewImage({ url: img.image_url, prompt: img.prompt })}
                      >
                        <img 
                          src={img.image_url} 
                          alt={img.prompt || 'Generated'}
                          className="w-full aspect-square object-cover rounded-lg hover:ring-2 hover:ring-purple-500 transition-all"
                        />
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-2">
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={(e) => { e.stopPropagation(); openCropModal(img.image_url, 'character', viewingCharacter?.id); }}
                            title="Crop Image"
                          >
                            <FiCrop className="text-white" size={14} />
                          </Button>
                          <FiMaximize2 className="text-white" size={18} />
                        </div>
                        {img.type && (
                          <span className="absolute bottom-1 left-1 text-xs bg-purple-500/80 text-white px-1.5 py-0.5 rounded">
                            {img.type}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Character Modal */}
      <AnimatePresence>
        {editingCharacter && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div 
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-gray-900 rounded-xl border border-purple-500/30 p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">Edit Character</h2>
                <Button variant="ghost" size="sm" onClick={() => setEditingCharacter(null)}>
                  <FiX size={20} />
                </Button>
              </div>

              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label className="text-gray-300 text-sm font-medium block mb-1">Name</label>
                  <Input
                    value={editForm.name}
                    onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                    className="bg-gray-800/50 border-gray-700 text-white"
                  />
                </div>

                {/* Style */}
                <div>
                  <label className="text-gray-300 text-sm font-medium block mb-1">Visual Style</label>
                  <Select value={editForm.style} onValueChange={(v) => setEditForm(prev => ({ ...prev, style: v }))}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700 max-h-60">
                      {characterStyles.map((style) => (
                        <SelectItem key={style.id} value={style.id} className="text-white">
                          {style.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Genre */}
                <div>
                  <label className="text-gray-300 text-sm font-medium block mb-1">Genre</label>
                  <Select value={editForm.genre} onValueChange={(v) => setEditForm(prev => ({ ...prev, genre: v }))}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700 max-h-60">
                      {characterGenres.map((genre) => (
                        <SelectItem key={genre.id} value={genre.id} className="text-white">
                          {genre.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Description */}
                <div>
                  <label className="text-gray-300 text-sm font-medium block mb-1">Description</label>
                  <Textarea
                    value={editForm.description_prompt}
                    onChange={(e) => setEditForm(prev => ({ ...prev, description_prompt: e.target.value }))}
                    className="bg-gray-800/50 border-gray-700 text-white"
                    rows={3}
                  />
                </div>

                {/* Special Features */}
                <div>
                  <label className="text-gray-300 text-sm font-medium block mb-1">Special Features</label>
                  <Input
                    value={editForm.special_features}
                    onChange={(e) => setEditForm(prev => ({ ...prev, special_features: e.target.value }))}
                    placeholder="e.g., scar on cheek, glowing tattoos"
                    className="bg-gray-800/50 border-gray-700 text-white"
                  />
                </div>

                {/* Personality */}
                <div>
                  <label className="text-gray-300 text-sm font-medium block mb-1">Personality</label>
                  <Input
                    value={editForm.personality}
                    onChange={(e) => setEditForm(prev => ({ ...prev, personality: e.target.value }))}
                    placeholder="e.g., brave and curious"
                    className="bg-gray-800/50 border-gray-700 text-white"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <Button
                  onClick={() => regenerateThumbnail(editingCharacter.id)}
                  variant="outline"
                  className="border-purple-500/30 text-purple-300 hover:bg-purple-500/20"
                >
                  <FiRefreshCw className="mr-2" /> Regenerate Look
                </Button>
                <div className="flex-1" />
                <Button variant="outline" onClick={() => setEditingCharacter(null)}>
                  Cancel
                </Button>
                <Button 
                  onClick={saveCharacterEdits}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  Save Changes
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Scene View Modal */}
      <AnimatePresence>
        {viewingScene && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/95 backdrop-blur-sm z-[60] overflow-auto"
          >
            <div className="max-w-6xl mx-auto p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <Button 
                    variant="ghost" 
                    onClick={closeSceneView}
                    className="text-gray-400 hover:text-white hover:bg-gray-800"
                  >
                    <FiArrowLeft className="mr-2" /> Back to Scenes
                  </Button>
                  <div className="w-px h-8 bg-gray-700" />
                  <img 
                    src={viewingScene.thumbnail || viewingScene.reference_images?.[0]} 
                    alt={viewingScene.name}
                    className="w-16 h-10 rounded-lg object-cover cursor-pointer"
                    onClick={() => setPreviewImage({ url: viewingScene.thumbnail, prompt: viewingScene.name })}
                  />
                  <div>
                    <h2 className="text-xl font-bold text-white">{viewingScene.name}</h2>
                    <p className="text-gray-400 text-sm">{viewingScene.lighting} • {viewingScene.mood}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button 
                    onClick={() => { setSelectedScene(viewingScene); closeSceneView(); }}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <FiZap className="mr-2" /> Use for Generation
                  </Button>
                </div>
              </div>

              {/* Scene Description */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4 mb-6">
                <h3 className="text-white font-medium mb-2">Scene Description</h3>
                <p className="text-gray-300 text-sm whitespace-pre-wrap">{viewingScene.description}</p>
                <div className="flex gap-2 mt-3 flex-wrap">
                  {viewingScene.time_of_day && <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded">{viewingScene.time_of_day}</span>}
                  {viewingScene.weather && <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">{viewingScene.weather}</span>}
                  {viewingScene.location_type && <span className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded">{viewingScene.location_type}</span>}
                </div>
              </div>

              {/* Scene Folder/Gallery */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <FiFolder className="text-purple-400" /> Scene Folder ({sceneGallery.length} images)
                </h3>
                {sceneGallery.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FiImage className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No generated images yet</p>
                    <p className="text-sm">Select this scene and generate images to build your collection</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {sceneGallery.map((img) => (
                      <div 
                        key={img.id}
                        className="relative group cursor-pointer"
                        onClick={() => setPreviewImage({ url: img.image_url, prompt: img.prompt })}
                      >
                        <img 
                          src={img.image_url} 
                          alt={img.prompt || 'Generated'}
                          className="w-full aspect-video object-cover rounded-lg hover:ring-2 hover:ring-purple-500 transition-all"
                        />
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-1">
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={(e) => { e.stopPropagation(); openCropModal(img.image_url, 'scene', viewingScene?.id); }}
                            title="Crop Image"
                          >
                            <FiCrop className="text-white" size={14} />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost"
                            onClick={(e) => { e.stopPropagation(); saveToArtStudioGallery(img.image_url, img.prompt, 'scene'); }}
                            title="Save to Gallery"
                          >
                            <FiSave className="text-white" size={14} />
                          </Button>
                          <FiMaximize2 className="text-white" size={18} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isLoading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <div className="text-center max-w-sm">
              <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-white text-lg mb-3">{loadingMessage}</p>
              {loadingProgress > 0 && (
                <div className="w-64 mx-auto">
                  <div className="bg-gray-700 rounded-full h-2 overflow-hidden">
                    <motion.div 
                      className="bg-gradient-to-r from-purple-500 to-pink-500 h-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${loadingProgress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                  <p className="text-gray-400 text-sm mt-2">{loadingProgress}% complete</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Pro Studio Explanation Banner */}
        <div className="bg-gradient-to-r from-purple-900/40 to-pink-900/40 rounded-xl border border-purple-500/30 p-4 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
              <FiStar className="text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-white font-semibold mb-1">Pro Studio - Premium Character Consistency</h3>
              <p className="text-gray-300 text-sm">
                Create characters with <span className="text-purple-300 font-medium">AI-powered consistency</span> across all your book illustrations. 
                Train custom LoRA models for 100% accurate character recreation, or use PuLID for face consistency.
                <span className="text-amber-300 ml-1">Credits required for advanced features.</span>
              </p>
            </div>
            <div className="text-right flex-shrink-0">
              <div className="text-xs text-gray-400 mb-1">Your Balance</div>
              <div className="flex items-center gap-1 text-amber-400 font-bold">
                <FiZap size={14} />
                <span>{credits}</span>
              </div>
            </div>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="bg-black/40 border border-purple-500/20 p-1 mb-6 flex-wrap">
            <TabsTrigger value="characters" className="data-[state=active]:bg-purple-600">
              <FiUser className="mr-2" /> Characters
            </TabsTrigger>
            <TabsTrigger value="scenes" className="data-[state=active]:bg-purple-600">
              <FiLayers className="mr-2" /> Scenes
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
              {/* Create Character Panel - UNIFIED FORM */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                  <FiPlus className="text-purple-400" /> Create Character
                </h2>
                <p className="text-gray-400 text-sm mb-4">
                  Describe your character AND/OR upload reference images to create a consistent character.
                </p>
                
                {/* Character Name */}
                <Input
                  placeholder="Character name (e.g., Luna, Captain Rex)"
                  value={characterName}
                  onChange={(e) => setCharacterName(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                  data-testid="character-name-input"
                />

                {/* Style & Genre Selection */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div>
                    <label className="text-gray-400 text-xs mb-1 block">Visual Style</label>
                    <Select value={characterStyle} onValueChange={setCharacterStyle}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700 max-h-60">
                        {characterStyles.map((style) => (
                          <SelectItem key={style.id} value={style.id} className="text-white">
                            <span className="font-medium">{style.name}</span>
                            <span className="text-gray-400 text-xs ml-2">{style.description}</span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs mb-1 block">Genre</label>
                    <Select value={characterGenre} onValueChange={setCharacterGenre}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700 max-h-60">
                        {characterGenres.map((genre) => (
                          <SelectItem key={genre.id} value={genre.id} className="text-white">
                            <span className="font-medium">{genre.name}</span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Description - always shown */}
                <div className="space-y-3 mb-4">
                  <label className="text-gray-300 text-sm font-medium">Character Description</label>
                  <Textarea
                    placeholder="Describe your character in detail... (e.g., 'A young elven princess with silver hair that flows like moonlight, bright violet eyes, pointed ears adorned with crystal earrings')"
                    value={characterDescription}
                    onChange={(e) => setCharacterDescription(e.target.value)}
                    className="bg-gray-800/50 border-gray-700 text-white"
                    rows={3}
                  />
                </div>

                {/* Reference Images - always shown */}
                <div className="space-y-3 mb-4">
                  <label className="text-gray-300 text-sm font-medium">Reference Images (optional)</label>
                  <div className="border-2 border-dashed border-purple-500/30 rounded-lg p-4 text-center">
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
                      <FiUpload className="w-6 h-6 text-purple-400 mx-auto mb-1" />
                      <p className="text-gray-400 text-sm">Click to upload reference images</p>
                    </label>
                  </div>
                  
                  {/* Uploaded images preview */}
                  {characterImages.length > 0 && (
                    <div className="grid grid-cols-5 gap-2">
                      {characterImages.map((img, i) => (
                        <div key={img.id} className="relative group">
                          <img 
                            src={img.url} 
                            alt={`Ref ${i+1}`} 
                            className="w-full aspect-square object-cover rounded-lg cursor-pointer"
                            onClick={() => setPreviewImage({ url: img.url, prompt: `Reference ${i+1}` })}
                          />
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
                  
                  {/* Add from Gallery Button */}
                  <Button
                    variant="outline"
                    onClick={() => { setGalleryPickerMode('character'); setShowGalleryPicker(true); }}
                    className="w-full border-purple-500/30 text-purple-300 hover:bg-purple-500/20"
                    size="sm"
                  >
                    <FiFolder className="mr-2" /> Add from Gallery
                  </Button>
                </div>
                
                {/* Physical Traits (Collapsible) */}
                <details className="group mb-3">
                  <summary className="text-purple-400 text-sm cursor-pointer hover:text-purple-300">
                    + Add Physical Details (optional)
                  </summary>
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <Input
                      placeholder="Age (e.g., young adult)"
                      value={physicalTraits.age}
                      onChange={(e) => setPhysicalTraits(p => ({...p, age: e.target.value}))}
                      className="bg-gray-800/50 border-gray-700 text-white text-sm"
                    />
                    <Input
                      placeholder="Gender"
                      value={physicalTraits.gender}
                      onChange={(e) => setPhysicalTraits(p => ({...p, gender: e.target.value}))}
                      className="bg-gray-800/50 border-gray-700 text-white text-sm"
                    />
                    <Input
                      placeholder="Hair Color"
                      value={physicalTraits.hairColor}
                      onChange={(e) => setPhysicalTraits(p => ({...p, hairColor: e.target.value}))}
                      className="bg-gray-800/50 border-gray-700 text-white text-sm"
                    />
                    <Input
                      placeholder="Eye Color"
                      value={physicalTraits.eyeColor}
                      onChange={(e) => setPhysicalTraits(p => ({...p, eyeColor: e.target.value}))}
                      className="bg-gray-800/50 border-gray-700 text-white text-sm"
                    />
                  </div>
                </details>

                {/* Special Features & Personality */}
                <details className="group mb-4">
                  <summary className="text-purple-400 text-sm cursor-pointer hover:text-purple-300">
                    + Add Special Features & Personality (optional)
                  </summary>
                  <div className="space-y-2 mt-3">
                    <Input
                      placeholder="Special features (e.g., scar on cheek, glowing tattoos)"
                      value={specialFeatures}
                      onChange={(e) => setSpecialFeatures(e.target.value)}
                      className="bg-gray-800/50 border-gray-700 text-white text-sm"
                    />
                    <Input
                      placeholder="Personality (e.g., brave and curious)"
                      value={personality}
                      onChange={(e) => setPersonality(e.target.value)}
                      className="bg-gray-800/50 border-gray-700 text-white text-sm"
                    />
                  </div>
                </details>

                <Button 
                  onClick={() => {
                    if (!checkCreditsOrRedirect(1, 'Create Character')) return;
                    createCharacter();
                  }}
                  disabled={isCreatingCharacter || !characterName.trim() || (!characterDescription.trim() && characterImages.length < 1)}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  data-testid="create-character-btn"
                >
                  {isCreatingCharacter ? 'Creating...' : 'Create Character'}
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
                  <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto">
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
                          {/* Clickable thumbnail to view character */}
                          <div className="relative group">
                            <img 
                              src={char.thumbnail || char.reference_images?.[0] || '/placeholder-character.png'} 
                              alt={char.name}
                              className="w-16 h-16 rounded-full object-cover cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all"
                              onClick={() => openCharacterView(char)}
                            />
                            <div className="absolute inset-0 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <FiEye className="text-white" size={16} />
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="text-white font-medium truncate">{char.name}</p>
                              {char.lora_status === 'completed' && (
                                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full flex items-center gap-1 flex-shrink-0">
                                  <FiCheck size={10} /> LoRA
                                </span>
                              )}
                              {char.lora_status === 'training' && (
                                <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full animate-pulse flex-shrink-0">
                                  Training...
                                </span>
                              )}
                            </div>
                            <p className="text-gray-500 text-xs">{char.style} • {char.genre}</p>
                            {/* Reference images count */}
                            <p className="text-xs mt-1">
                              <span className={`${(char.reference_images?.length || 0) >= 3 ? 'text-green-400' : 'text-amber-400'}`}>
                                {char.reference_images?.length || 0}/3 refs
                              </span>
                              {(char.reference_images?.length || 0) < 3 && (
                                <span className="text-gray-600 ml-1">(need 3 for LoRA)</span>
                              )}
                            </p>
                          </div>
                          
                          <div className="flex items-center gap-1 flex-shrink-0">
                            {/* Edit button */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openEditModal(char)}
                              className="text-gray-400 hover:text-white hover:bg-gray-700/50 p-1.5"
                              title="Edit character"
                            >
                              <FiEdit3 size={14} />
                            </Button>
                            
                            {/* View Folder button */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openCharacterView(char)}
                              className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/20 p-1.5"
                              title="View character folder"
                            >
                              <FiFolder size={14} />
                            </Button>
                            
                            {/* Delete button */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deleteCharacter(char.id)}
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/20 p-1.5"
                              title="Delete character"
                            >
                              <FiTrash2 size={14} />
                            </Button>
                            
                            {/* Select button */}
                            <Button
                              size="sm"
                              variant={selectedCharacter?.id === char.id ? "default" : "outline"}
                              onClick={() => setSelectedCharacter(char)}
                              className={selectedCharacter?.id === char.id 
                                ? "bg-purple-600 text-white" 
                                : "border-purple-400/50 text-purple-300 hover:bg-purple-500/20 hover:border-purple-400"
                              }
                            >
                              {selectedCharacter?.id === char.id ? <FiCheck className="mr-1" /> : null}
                              {selectedCharacter?.id === char.id ? 'Selected' : 'Select'}
                            </Button>
                            
                            {/* Train LoRA button - only show when 3+ reference images */}
                            {falAvailable && char.lora_status !== 'completed' && char.lora_status !== 'training' && (char.reference_images?.length || 0) >= 3 && (
                              <Button
                                size="sm"
                                onClick={() => trainCharacterLora(char.id)}
                                disabled={isTrainingLora}
                                className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
                                title="Train LoRA model for 100% consistent character"
                              >
                                <FiZap className="mr-1" /> Train
                              </Button>
                            )}
                            {/* Show hint when not enough refs */}
                            {falAvailable && char.lora_status !== 'completed' && char.lora_status !== 'training' && (char.reference_images?.length || 0) < 3 && (
                              <span className="text-xs text-gray-500 ml-1" title="Add more reference images to enable LoRA training">
                                +{3 - (char.reference_images?.length || 0)} refs
                              </span>
                            )}
                          </div>
                        </div>
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
                  placeholder={`Describe what ${selectedCharacter.name} is doing... (e.g., 'running through a magical forest', 'standing on a cliff overlooking the ocean')`}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                  rows={3}
                  data-testid="consistent-gen-prompt"
                />

                {/* Scene & Settings Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                  {/* Scene Selection */}
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">Place in Scene (Optional)</label>
                    <Select 
                      value={selectedSceneForGeneration?.id || 'none'} 
                      onValueChange={(v) => setSelectedSceneForGeneration(v === 'none' ? null : scenes.find(s => s.id === v))}
                    >
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white text-sm">
                        <SelectValue placeholder="No scene" />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700">
                        <SelectItem value="none" className="text-white">No scene (use prompt)</SelectItem>
                        {scenes.map((scene) => (
                          <SelectItem key={scene.id} value={scene.id} className="text-white">
                            {scene.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Face Similarity */}
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">Face Match Strength</label>
                    <Select value={faceSimilarity} onValueChange={setFaceSimilarity}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700">
                        <SelectItem value="high" className="text-white">High (exact face)</SelectItem>
                        <SelectItem value="medium" className="text-white">Medium (balanced)</SelectItem>
                        <SelectItem value="low" className="text-white">Low (artistic)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Aspect Ratio */}
                  <div>
                    <label className="text-xs text-gray-400 mb-1 block">Aspect Ratio</label>
                    <Select value={aspectRatio} onValueChange={setAspectRatio}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white text-sm">
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
                </div>

                {selectedSceneForGeneration && (
                  <div className="mb-4 p-3 bg-purple-500/10 rounded-lg border border-purple-500/30">
                    <p className="text-sm text-purple-300">
                      <FiLayers className="inline mr-1" />
                      Character will be placed in: <strong>{selectedSceneForGeneration.name}</strong>
                    </p>
                  </div>
                )}

                <Button 
                  onClick={generateConsistentCharacterImage}
                  disabled={isLoading || !prompt.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  data-testid="generate-consistent-btn"
                >
                  <FiZap className="mr-2" /> 
                  Generate {selectedCharacter.name} 
                  {selectedSceneForGeneration ? ` in ${selectedSceneForGeneration.name}` : ''}
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

          {/* Scenes Tab */}
          <TabsContent value="scenes" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Create Scene Panel */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                  <FiLayers className="text-purple-400" /> Create Scene
                </h2>
                <p className="text-gray-400 text-sm mb-4">
                  Create consistent scenes/environments for your book illustrations.
                </p>

                {/* Scene Name */}
                <Input
                  placeholder="Scene name (e.g., Enchanted Forest, Cyber City)"
                  value={sceneName}
                  onChange={(e) => setSceneName(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                />

                {/* Scene Description */}
                <Textarea
                  placeholder="Describe the scene in detail... (e.g., 'A mystical forest with glowing mushrooms, ancient trees with faces, soft mist floating between the roots')"
                  value={sceneDescription}
                  onChange={(e) => setSceneDescription(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                  rows={3}
                />

                {/* Style & Genre */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div>
                    <label className="text-gray-400 text-xs mb-1 block">Visual Style</label>
                    <Select value={sceneStyle} onValueChange={setSceneStyle}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700 max-h-60">
                        {characterStyles.map((style) => (
                          <SelectItem key={style.id} value={style.id} className="text-white">{style.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs mb-1 block">Genre</label>
                    <Select value={sceneGenre} onValueChange={setSceneGenre}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700 max-h-60">
                        {characterGenres.map((genre) => (
                          <SelectItem key={genre.id} value={genre.id} className="text-white">{genre.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Location, Lighting, Mood */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div>
                    <label className="text-gray-400 text-xs mb-1 block">Location</label>
                    <Select value={sceneLocationType} onValueChange={setSceneLocationType}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700">
                        {sceneOptions.location_types?.map((loc) => (
                          <SelectItem key={loc.id} value={loc.id} className="text-white">{loc.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs mb-1 block">Lighting</label>
                    <Select value={sceneLighting} onValueChange={setSceneLighting}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700">
                        {sceneOptions.lighting?.map((light) => (
                          <SelectItem key={light.id} value={light.id} className="text-white">{light.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs mb-1 block">Mood</label>
                    <Select value={sceneMood} onValueChange={setSceneMood}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700">
                        {sceneOptions.moods?.map((mood) => (
                          <SelectItem key={mood.id} value={mood.id} className="text-white">{mood.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Time of Day & Weather (optional) */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <Input
                    placeholder="Time of day (e.g., sunset)"
                    value={sceneTimeOfDay}
                    onChange={(e) => setSceneTimeOfDay(e.target.value)}
                    className="bg-gray-800/50 border-gray-700 text-white text-sm"
                  />
                  <Input
                    placeholder="Weather (e.g., light rain)"
                    value={sceneWeather}
                    onChange={(e) => setSceneWeather(e.target.value)}
                    className="bg-gray-800/50 border-gray-700 text-white text-sm"
                  />
                </div>

                <Button 
                  onClick={() => {
                    if (!checkCreditsOrRedirect(1, 'Create Scene')) return;
                    createScene();
                  }}
                  disabled={isCreatingScene || !sceneName.trim() || !sceneDescription.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                >
                  {isCreatingScene ? 'Creating...' : 'Create Scene'}
                </Button>
              </div>

              {/* My Scenes Panel */}
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiLayers className="text-purple-400" /> My Scenes
                </h2>
                
                {scenes.length === 0 ? (
                  <div className="text-center py-12">
                    <FiLayers className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">No scenes yet</p>
                    <p className="text-gray-500 text-sm">Create your first scene for consistent backgrounds</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto">
                    {scenes.map((scene) => (
                      <div
                        key={scene.id}
                        className={`rounded-lg border-2 transition-all ${
                          selectedScene?.id === scene.id 
                            ? 'border-purple-500 bg-purple-900/30' 
                            : 'border-gray-700 hover:border-purple-500/50'
                        } p-3`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="relative group">
                            <img 
                              src={scene.thumbnail || scene.reference_images?.[0]} 
                              alt={scene.name}
                              className="w-20 h-14 rounded-lg object-cover cursor-pointer hover:ring-2 hover:ring-purple-500"
                              onClick={() => openSceneView(scene)}
                            />
                            {/* Crop overlay on hover */}
                            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-1">
                              <button 
                                onClick={(e) => { 
                                  e.stopPropagation(); 
                                  openCropModal(scene.thumbnail || scene.reference_images?.[0], 'scene', scene.id); 
                                }}
                                className="p-1 bg-purple-500/80 rounded hover:bg-purple-600"
                                title="Crop"
                              >
                                <FiCrop className="text-white" size={12} />
                              </button>
                              <button 
                                onClick={(e) => { 
                                  e.stopPropagation(); 
                                  openSceneView(scene); 
                                }}
                                className="p-1 bg-gray-700/80 rounded hover:bg-gray-600"
                                title="View Folder"
                              >
                                <FiFolder className="text-white" size={12} />
                              </button>
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-white font-medium truncate">{scene.name}</p>
                            <p className="text-gray-500 text-xs truncate">{scene.description_prompt}</p>
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {scene.lighting && <span className="text-xs bg-gray-700 px-1.5 py-0.5 rounded text-gray-300">{scene.lighting}</span>}
                              {scene.mood && <span className="text-xs bg-gray-700 px-1.5 py-0.5 rounded text-gray-300">{scene.mood}</span>}
                            </div>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openSceneView(scene)}
                              className="text-purple-400 hover:bg-purple-500/20 p-1"
                              title="View scene folder"
                            >
                              <FiFolder size={14} />
                            </Button>
                            <Button
                              size="sm"
                              variant={selectedScene?.id === scene.id ? "default" : "outline"}
                              onClick={() => setSelectedScene(scene)}
                              className={selectedScene?.id === scene.id ? "bg-purple-600" : "border-gray-600 text-gray-300"}
                            >
                              {selectedScene?.id === scene.id ? <FiCheck /> : 'Use'}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deleteScene(scene.id)}
                              className="text-red-400 hover:bg-red-500/20 p-1"
                            >
                              <FiTrash2 size={14} />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Generate with Scene */}
            {selectedScene && (
              <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiZap className="text-amber-400" /> Generate with Scene
                </h2>
                <p className="text-gray-400 text-sm mb-4">
                  Generate images using "{selectedScene.name}" settings. 
                  {selectedCharacter && ` Adding ${selectedCharacter.name} to the scene.`}
                </p>

                <Textarea
                  placeholder="Additional prompt (optional) - describe what's happening in this scene..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="bg-gray-800/50 border-gray-700 text-white mb-4"
                  rows={2}
                />

                <div className="flex gap-3">
                  <Button 
                    onClick={generateWithScene}
                    disabled={isLoading}
                    className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  >
                    <FiZap className="mr-2" /> Generate Scene Image
                  </Button>
                  {selectedCharacter && (
                    <div className="flex items-center gap-2 bg-gray-800/50 px-3 py-2 rounded-lg">
                      <img 
                        src={selectedCharacter.thumbnail} 
                        alt={selectedCharacter.name}
                        className="w-8 h-8 rounded-full object-cover"
                      />
                      <span className="text-sm text-gray-300">{selectedCharacter.name}</span>
                    </div>
                  )}
                </div>
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
                {/* Source Image Selector for Variants */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                    <FiImage className="text-purple-400" /> Source Image (Optional)
                  </h3>
                  <p className="text-xs text-gray-400 mb-3">
                    Select an existing image to create a variant with your cinema settings
                  </p>
                  
                  {cinemaSourceImage ? (
                    <div className="flex items-center gap-4">
                      <div className="relative">
                        <img 
                          src={cinemaSourceImage.url} 
                          alt={cinemaSourceImage.name}
                          className="w-24 h-24 object-cover rounded-lg border-2 border-purple-500"
                        />
                        <button
                          onClick={() => setCinemaSourceImage(null)}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                        >
                          <FiX size={14} />
                        </button>
                      </div>
                      <div>
                        <p className="text-white font-medium">{cinemaSourceImage.name}</p>
                        <p className="text-xs text-gray-400">From: {cinemaSourceImage.type}</p>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setShowCinemaSourcePicker(true)}
                          className="mt-2 border-purple-500/50 text-purple-300"
                        >
                          Change Image
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button
                      variant="outline"
                      onClick={() => setShowCinemaSourcePicker(true)}
                      className="w-full border-dashed border-gray-600 text-gray-400 hover:border-purple-500 hover:text-purple-300"
                    >
                      <FiPlus className="mr-2" /> Select Source Image
                    </Button>
                  )}
                </div>

                {/* Art Style Selector */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                    <FiSliders className="text-purple-400" /> Art Style
                  </h3>
                  <Select value={cinemaArtStyle} onValueChange={setCinemaArtStyle}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      <SelectItem value="cinematic" className="text-white">Cinematic (Default)</SelectItem>
                      <SelectItem value="realistic" className="text-white">Realistic / Photographic</SelectItem>
                      <SelectItem value="cartoon" className="text-white">Cartoon / Animated</SelectItem>
                      <SelectItem value="anime" className="text-white">Anime / Manga</SelectItem>
                      <SelectItem value="pixar" className="text-white">Pixar / 3D Animation</SelectItem>
                      <SelectItem value="watercolor" className="text-white">Watercolor / Painterly</SelectItem>
                      <SelectItem value="comic" className="text-white">Comic Book</SelectItem>
                      <SelectItem value="fantasy" className="text-white">Fantasy Art</SelectItem>
                      <SelectItem value="storybook" className="text-white">Children's Storybook</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-2">
                    This style will be applied to all generated images
                  </p>
                </div>

                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                  <h2 className="text-xl font-bold text-white mb-4">
                    {cinemaSourceImage ? 'Generate Variant' : 'Generate Hero Frame'}
                  </h2>
                  
                  <Textarea
                    placeholder={cinemaSourceImage 
                      ? "Describe how to modify the image... (e.g., 'make it more dramatic', 'add sunset lighting')"
                      : "Describe your scene... (e.g., 'A woman stands on a misty beach at sunrise, waves gently rolling in behind her')"
                    }
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="bg-gray-800/50 border-gray-700 text-white mb-4"
                    rows={3}
                    data-testid="cinema-prompt-input"
                  />

                  <div className="flex gap-3 mb-4">
                    {cinemaSourceImage ? (
                      <Button 
                        onClick={() => {
                          if (!checkCreditsOrRedirect(1, 'Generate Variant')) return;
                          generateCinemaVariant();
                        }}
                        disabled={isLoading}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                        data-testid="generate-variant-btn"
                      >
                        <FiRefreshCw className="mr-2" /> Generate Variant
                      </Button>
                    ) : (
                      <Button 
                        onClick={() => {
                          if (!checkCreditsOrRedirect(1, 'Generate Hero Frame')) return;
                          generateHeroFrame();
                        }}
                        disabled={isLoading || !prompt.trim()}
                        className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                        data-testid="generate-hero-btn"
                      >
                        <FiZap className="mr-2" /> Generate Hero Frame
                      </Button>
                    )}
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
                
                {/* Use Character Image */}
                {characters.length > 0 && (
                  <div className="mb-4">
                    <p className="text-gray-400 text-xs mb-2">Or select a character:</p>
                    <div className="flex gap-2 flex-wrap">
                      {characters.slice(0, 6).map((char) => (
                        <button
                          key={char.id}
                          onClick={() => handleShotsCharacterSelect(char)}
                          className={`relative group ${shotsSelectedCharacter?.id === char.id ? 'ring-2 ring-purple-500' : ''}`}
                          title={`Select ${char.name}`}
                        >
                          <img 
                            src={char.thumbnail || char.reference_images?.[0]} 
                            alt={char.name}
                            className="w-12 h-12 rounded-full object-cover border-2 border-gray-600 hover:border-purple-500 transition-colors"
                          />
                          {shotsSelectedCharacter?.id === char.id && (
                            <div className="absolute -bottom-1 -right-1 bg-purple-500 rounded-full p-0.5">
                              <FiCheck className="text-white" size={10} />
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                    
                    {/* Character Gallery - shown when a character is selected */}
                    {shotsSelectedCharacter && (
                      <div className="mt-3 p-3 bg-black/40 rounded-lg border border-purple-500/20">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-purple-300 text-xs font-medium">
                            {shotsSelectedCharacter.name}'s Gallery
                          </p>
                          <button 
                            onClick={() => {
                              setShotsSelectedCharacter(null);
                              setShotsCharacterGallery([]);
                            }}
                            className="text-gray-500 hover:text-gray-300 text-xs"
                          >
                            <FiX size={14} />
                          </button>
                        </div>
                        {shotsCharacterGallery.length > 0 ? (
                          <div className="grid grid-cols-4 gap-2 max-h-40 overflow-y-auto">
                            {shotsCharacterGallery.map((img, idx) => (
                              <button
                                key={idx}
                                onClick={() => {
                                  setShotsSourceImage(img.url);
                                  toast.success(`Using ${img.label || 'selected image'}`);
                                }}
                                className={`relative group aspect-square ${
                                  shotsSourceImage === img.url ? 'ring-2 ring-purple-500' : ''
                                }`}
                                title={img.label}
                              >
                                <img 
                                  src={img.url} 
                                  alt={img.label}
                                  className="w-full h-full object-cover rounded-lg"
                                />
                                <div className="absolute inset-0 bg-black/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                  <FiPlus className="text-white" size={16} />
                                </div>
                                {img.type === 'master' && (
                                  <div className="absolute top-1 left-1 bg-purple-500 text-white text-[8px] px-1 rounded">
                                    Master
                                  </div>
                                )}
                              </button>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-xs text-center py-2">
                            Loading gallery...
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Or Select from Gallery */}
                <Button
                  variant="outline"
                  onClick={() => { setGalleryPickerMode('shots'); setShowGalleryPicker(true); }}
                  className="w-full mb-4 border-purple-500/30 text-purple-300 hover:bg-purple-500/20"
                >
                  <FiFolder className="mr-2" /> Select from Gallery
                </Button>

                {/* Style Selector */}
                <div className="mb-4">
                  <label className="text-gray-400 text-xs mb-2 block">Art Style</label>
                  <Select value={shotsStyle} onValueChange={setShotsStyle}>
                    <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      <SelectItem value="realistic" className="text-white">Realistic / Photographic</SelectItem>
                      <SelectItem value="cinematic" className="text-white">Cinematic</SelectItem>
                      <SelectItem value="cartoon" className="text-white">Cartoon / Animated</SelectItem>
                      <SelectItem value="anime" className="text-white">Anime / Manga</SelectItem>
                      <SelectItem value="pixar" className="text-white">Pixar / 3D Animation</SelectItem>
                      <SelectItem value="watercolor" className="text-white">Watercolor / Painterly</SelectItem>
                      <SelectItem value="comic" className="text-white">Comic Book</SelectItem>
                      <SelectItem value="fantasy" className="text-white">Fantasy Art</SelectItem>
                      <SelectItem value="storybook" className="text-white">Children's Storybook</SelectItem>
                      {shotsSelectedCharacter?.style && (
                        <SelectItem value="character" className="text-purple-300">
                          Match Character ({shotsSelectedCharacter.style})
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                  {shotsSelectedCharacter?.style && shotsStyle !== 'character' && (
                    <p className="text-xs text-purple-400 mt-1">
                      Tip: Select "Match Character" to use {shotsSelectedCharacter.name}'s style
                    </p>
                  )}
                </div>

                <Button 
                  onClick={() => {
                    if (!checkCreditsOrRedirect(9, 'Generate 9 Shots')) return;
                    generateShots();
                  }}
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
                      <div 
                        key={i} 
                        className="relative group cursor-pointer"
                        onClick={() => setPreviewImage({ url: shot.url, prompt: SHOT_TYPES[i]?.name || `Shot ${i+1}` })}
                      >
                        <img src={shot.url} alt={shot.type} className="w-full aspect-square object-cover rounded-lg" />
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white text-xs p-1 text-center">
                          {SHOT_TYPES[i]?.name || `Shot ${i+1}`}
                        </div>
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); saveToGallery(shot); }}>
                            <FiSave className="text-white" size={14} />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); downloadMedia(shot.url, `shot-${i+1}.png`); }}>
                            <FiDownload className="text-white" size={14} />
                          </Button>
                          {selectedCharacter && (
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              onClick={async (e) => { 
                                e.stopPropagation(); 
                                try {
                                  const token = localStorage.getItem('azories-token');
                                  const response = await fetch(`${API_URL}/api/pro-studio/characters/${selectedCharacter.id}/add-reference`, {
                                    method: 'POST',
                                    headers: {
                                      'Content-Type': 'application/json',
                                      Authorization: `Bearer ${token}`
                                    },
                                    body: JSON.stringify({ image_url: shot.url })
                                  });
                                  if (response.ok) {
                                    const data = await response.json();
                                    toast.success(data.message);
                                    loadCharacters();
                                  }
                                } catch (error) {
                                  toast.error('Error adding reference');
                                }
                              }}
                              title="Add to character references"
                            >
                              <FiStar className="text-amber-400" size={14} />
                            </Button>
                          )}
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

                {/* Selected Source - Hero Frame, Character, Scene, or Upload */}
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-4">
                  <h3 className="text-white font-medium mb-3">Source Image</h3>
                  
                  {/* Source type selector */}
                  <div className="flex gap-2 mb-3">
                    <Button
                      size="sm"
                      variant={videoSourceType === 'hero' ? 'default' : 'outline'}
                      onClick={() => setVideoSourceType('hero')}
                      className={videoSourceType === 'hero' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}
                    >
                      Hero Frame
                    </Button>
                    <Button
                      size="sm"
                      variant={videoSourceType === 'character' ? 'default' : 'outline'}
                      onClick={() => setVideoSourceType('character')}
                      className={videoSourceType === 'character' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}
                    >
                      Character
                    </Button>
                    <Button
                      size="sm"
                      variant={videoSourceType === 'upload' ? 'default' : 'outline'}
                      onClick={() => setVideoSourceType('upload')}
                      className={videoSourceType === 'upload' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}
                    >
                      Upload
                    </Button>
                  </div>

                  {/* Hero Frame Source */}
                  {videoSourceType === 'hero' && (
                    selectedHeroFrame ? (
                      <div className="relative">
                        <img src={selectedHeroFrame.url} alt="Hero" className="w-full rounded-lg" />
                        <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded">
                          Ready to animate
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-6 text-gray-500 border-2 border-dashed border-gray-700 rounded-lg">
                        <FiImage className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Go to Cinema Studio to generate a hero frame</p>
                      </div>
                    )
                  )}

                  {/* Character Source */}
                  {videoSourceType === 'character' && (
                    <div className="space-y-3">
                      {/* Character Selector */}
                      <Select 
                        value={videoSourceCharacter?.id || ''} 
                        onValueChange={handleVideoCharacterSelect}
                      >
                        <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                          <SelectValue placeholder="Select a character" />
                        </SelectTrigger>
                        <SelectContent className="bg-gray-800 border-gray-700">
                          {characters.filter(c => c.thumbnail).map((char) => (
                            <SelectItem key={char.id} value={char.id} className="text-white">
                              {char.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      {videoSourceCharacter && (
                        <>
                          {/* Image Gallery Grid */}
                          <div className="space-y-2">
                            <p className="text-xs text-gray-400">Select an image from {videoSourceCharacter.name}'s gallery:</p>
                            <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto p-1">
                              {/* Master Image */}
                              {videoSourceCharacter.thumbnail && (
                                <div 
                                  className={`relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                                    videoSelectedImage?.type === 'master' 
                                      ? 'border-purple-500 ring-2 ring-purple-500/50' 
                                      : 'border-gray-700 hover:border-purple-500/50'
                                  }`}
                                  onClick={() => selectVideoImage({
                                    url: videoSourceCharacter.thumbnail,
                                    prompt: videoSourceCharacter.description || 'Master character image',
                                    type: 'master'
                                  })}
                                >
                                  <img 
                                    src={videoSourceCharacter.thumbnail} 
                                    alt="Master" 
                                    className="w-full aspect-square object-cover"
                                  />
                                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-1">
                                    <span className="text-[10px] text-yellow-400 font-medium">★ Master</span>
                                  </div>
                                </div>
                              )}
                              
                              {/* Gallery Images */}
                              {videoCharacterGallery.map((img, idx) => (
                                <div 
                                  key={img.id || idx}
                                  className={`relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                                    videoSelectedImage?.url === (img.image_url || img.url)
                                      ? 'border-purple-500 ring-2 ring-purple-500/50' 
                                      : 'border-gray-700 hover:border-purple-500/50'
                                  }`}
                                  onClick={() => selectVideoImage({
                                    ...img,
                                    url: img.image_url || img.url // Normalize to 'url'
                                  })}
                                >
                                  <img 
                                    src={img.image_url || img.url} 
                                    alt={`Gallery ${idx + 1}`} 
                                    className="w-full aspect-square object-cover"
                                  />
                                  {img.type && (
                                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-1">
                                      <span className="text-[10px] text-gray-300 capitalize">{img.type}</span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                            
                            {videoCharacterGallery.length === 0 && !videoSourceCharacter.thumbnail && (
                              <div className="text-center py-4 text-gray-500 border border-dashed border-gray-700 rounded-lg">
                                <FiImage className="w-6 h-6 mx-auto mb-1 opacity-50" />
                                <p className="text-xs">No images in gallery</p>
                              </div>
                            )}
                          </div>
                          
                          {/* Selected Image Preview */}
                          {videoSelectedImage && (
                            <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                              <div className="flex gap-3">
                                <img 
                                  src={videoSelectedImage.url} 
                                  alt="Selected" 
                                  className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                                />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-green-400 text-xs font-medium">✓ Selected</span>
                                    {videoSelectedImage.type === 'master' && (
                                      <span className="text-yellow-400 text-xs">★ Master</span>
                                    )}
                                  </div>
                                  <p className="text-gray-300 text-xs line-clamp-3">
                                    {videoSelectedImage.prompt || 'No description available'}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}
                        </>
                      )}
                      
                      {!videoSourceCharacter && (
                        <div className="text-center py-6 text-gray-500 border-2 border-dashed border-gray-700 rounded-lg">
                          <FiUser className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">Select a character to see their images</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Upload Source */}
                  {videoSourceType === 'upload' && (
                    <div className="space-y-3">
                      {videoUploadedImage ? (
                        <div className="relative">
                          <img src={videoUploadedImage} alt="Uploaded" className="w-full rounded-lg" />
                          <Button
                            size="sm"
                            variant="destructive"
                            className="absolute top-2 right-2"
                            onClick={() => { setVideoUploadedImage(null); setVideoPrompt(''); }}
                          >
                            <FiX className="w-4 h-4" />
                          </Button>
                          {videoPrompt && (
                            <div className="mt-2 p-2 bg-gray-800/50 rounded-lg">
                              <p className="text-xs text-gray-400">Description:</p>
                              <p className="text-sm text-gray-300 line-clamp-2">{videoPrompt}</p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {/* Browse from Gallery Button */}
                          <Button
                            variant="outline"
                            className="w-full border-purple-500/50 text-purple-400 hover:bg-purple-500/10"
                            onClick={() => {
                              setGalleryPickerMode('video');
                              setGalleryFilter('images');
                              setShowGalleryPicker(true);
                            }}
                          >
                            <FiFolder className="w-4 h-4 mr-2" /> Browse from Gallery
                          </Button>
                          
                          {/* Or upload */}
                          <div className="text-center text-gray-500 text-xs">or</div>
                          
                          <label className="block">
                            <div className="text-center py-4 text-gray-500 border-2 border-dashed border-gray-700 rounded-lg cursor-pointer hover:border-purple-500 transition-colors">
                              <FiUpload className="w-6 h-6 mx-auto mb-1 opacity-50" />
                              <p className="text-sm">Upload new image</p>
                            </div>
                            <input
                              type="file"
                              accept="image/*"
                              className="hidden"
                              onChange={(e) => {
                                const file = e.target.files[0];
                                if (file) {
                                  const reader = new FileReader();
                                  reader.onload = (ev) => setVideoUploadedImage(ev.target.result);
                                  reader.readAsDataURL(file);
                                }
                              }}
                            />
                          </label>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Video Generation Panel */}
              <div className="lg:col-span-2 space-y-4">
                <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
                  <h2 className="text-xl font-bold text-white mb-4">Animate to Video</h2>
                  
                  {/* Art Style Selector for Consistency */}
                  <div className="mb-4">
                    <label className="text-sm text-gray-400 mb-2 block">Art Style (for consistency)</label>
                    <Select value={videoArtStyle} onValueChange={setVideoArtStyle}>
                      <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                        <SelectValue placeholder="Select art style" />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700">
                        <SelectItem value="cinematic" className="text-white">🎬 Cinematic</SelectItem>
                        <SelectItem value="anime" className="text-white">🎌 Anime</SelectItem>
                        <SelectItem value="realistic" className="text-white">📷 Realistic</SelectItem>
                        <SelectItem value="cyberpunk" className="text-white">🌃 Cyberpunk</SelectItem>
                        <SelectItem value="fantasy" className="text-white">🧙 Fantasy</SelectItem>
                        <SelectItem value="cartoon" className="text-white">🎨 Cartoon</SelectItem>
                        <SelectItem value="watercolor" className="text-white">🖌️ Watercolor</SelectItem>
                        <SelectItem value="oil-painting" className="text-white">🎨 Oil Painting</SelectItem>
                        <SelectItem value="3d-render" className="text-white">💎 3D Render</SelectItem>
                        <SelectItem value="none" className="text-white">— No Style Override</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500 mt-1">Match your character's art style for consistent results</p>
                  </div>
                  
                  <Textarea
                    placeholder="Describe the motion... (e.g., 'gentle wind blowing hair, soft breathing, subtle camera dolly forward')"
                    value={videoPrompt}
                    onChange={(e) => setVideoPrompt(e.target.value)}
                    className="bg-gray-800/50 border-gray-700 text-white mb-4"
                    rows={3}
                    data-testid="video-prompt-input"
                  />

                  <Button 
                    onClick={() => {
                      if (!checkCreditsOrRedirect(5, 'Animate with Kling AI')) return;
                      animateToVideo();
                    }}
                    disabled={isLoading || (
                      (videoSourceType === 'hero' && !selectedHeroFrame) ||
                      (videoSourceType === 'character' && !videoSelectedImage?.url && !videoSourceCharacter?.thumbnail) ||
                      (videoSourceType === 'upload' && !videoUploadedImage)
                    )}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                    data-testid="animate-video-btn"
                  >
                    <FiPlay className="mr-2" /> Animate with Kling AI (Best Face Fidelity)
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

          {/* Gallery Tab - Unified Pro Studio Gallery */}
          <TabsContent value="gallery" className="space-y-6">
            <div className="bg-black/40 rounded-xl border border-purple-500/20 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <FiFolder className="text-purple-400" /> Pro Studio Gallery
                </h2>
                <div className="flex items-center gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={loadGallery}
                    className="border-gray-600 text-gray-300 hover:bg-gray-800"
                  >
                    <FiRefreshCw className="w-4 h-4 mr-1" /> Refresh
                  </Button>
                </div>
              </div>
              
              {/* Filter Tabs */}
              <div className="flex gap-2 mb-4 flex-wrap">
                <Button
                  size="sm"
                  variant={galleryFilter === 'all' ? 'default' : 'outline'}
                  onClick={() => setGalleryFilter('all')}
                  className={galleryFilter === 'all' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}
                >
                  All {galleryFilter === 'all' && `(${galleryTotal})`}
                </Button>
                <Button
                  size="sm"
                  variant={galleryFilter === 'images' ? 'default' : 'outline'}
                  onClick={() => setGalleryFilter('images')}
                  className={galleryFilter === 'images' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}
                >
                  <FiImage className="w-3 h-3 mr-1" /> Images {galleryFilter === 'images' && `(${galleryTotal})`}
                </Button>
                <Button
                  size="sm"
                  variant={galleryFilter === 'videos' ? 'default' : 'outline'}
                  onClick={() => setGalleryFilter('videos')}
                  className={galleryFilter === 'videos' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}
                >
                  <FiVideo className="w-3 h-3 mr-1" /> Videos {galleryFilter === 'videos' && `(${galleryTotal})`}
                </Button>
                <Button
                  size="sm"
                  variant={galleryFilter === 'characters' ? 'default' : 'outline'}
                  onClick={() => setGalleryFilter('characters')}
                  className={galleryFilter === 'characters' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}
                >
                  <FiUser className="w-3 h-3 mr-1" /> Characters {galleryFilter === 'characters' && `(${galleryTotal})`}
                </Button>
              </div>
              
              {filteredGallery.length === 0 && !galleryLoading ? (
                <div className="text-center py-16 text-gray-500">
                  <FiFolder className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">
                    {galleryTotal === 0 ? 'Your gallery is empty' : 'No items match this filter'}
                  </p>
                  <p className="text-sm mt-2">
                    {galleryTotal === 0 ? 'Create characters, generate images, and make videos to fill it up!' : 'Try a different filter'}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {filteredGallery.map((item) => {
                    // Determine if this is a video/animation
                    const isVideo = item.type === 'video' || item.type === 'animation' || item.is_animation || 
                                    (item.image_url && item.image_url.includes('video/'));
                    
                    return (
                    <div key={item.id} className="relative group rounded-lg overflow-hidden bg-gray-800 border border-gray-700 hover:border-purple-500/50 transition-colors">
                      {/* Media Preview */}
                      {isVideo ? (
                        <div className="relative w-full aspect-square bg-gray-900">
                          {/* Video thumbnail placeholder - shown by default on mobile */}
                          <div className="video-thumbnail absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900 flex flex-col items-center justify-center">
                            <FiFilm className="w-10 h-10 text-purple-400 mb-2" />
                            <span className="text-xs text-gray-400">Tap to play</span>
                          </div>
                          <video 
                            src={item.image_url || item.url} 
                            className="w-full h-full object-cover absolute inset-0" 
                            muted 
                            playsInline 
                            loop
                            preload="none"
                            onMouseEnter={(e) => {
                              // Only auto-play on non-touch devices
                              if (!('ontouchstart' in window)) {
                                e.target.play().catch(() => {});
                              }
                            }}
                            onMouseLeave={(e) => { 
                              e.target.pause(); 
                              e.target.currentTime = 0; 
                            }}
                            onClick={(e) => {
                              // Toggle play/pause on click for mobile
                              if (e.target.paused) {
                                e.target.play().catch(() => {});
                                e.target.parentElement.querySelector('.video-thumbnail')?.classList.add('hidden');
                              } else {
                                e.target.pause();
                              }
                            }}
                            onLoadedData={(e) => { 
                              e.target.currentTime = 0.1; 
                              e.target.parentElement.querySelector('.video-thumbnail')?.classList.add('hidden');
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.parentElement.querySelector('.video-fallback')?.classList.remove('hidden');
                              e.target.parentElement.querySelector('.video-thumbnail')?.classList.add('hidden');
                            }}
                          />
                          <div className="video-fallback hidden w-full h-full bg-gray-800 flex flex-col items-center justify-center absolute inset-0">
                            <FiVideo className="w-10 h-10 text-purple-400 mb-2" />
                            <span className="text-xs text-gray-400">Video unavailable</span>
                          </div>
                          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="bg-black/50 rounded-full p-2">
                              <FiPlay className="w-6 h-6 text-white" />
                            </div>
                          </div>
                        </div>
                      ) : (
                        <>
                          {/* Placeholder skeleton */}
                          <div className="img-placeholder absolute inset-0 bg-gradient-to-br from-gray-700 to-gray-800 animate-pulse" />
                          <img 
                            src={item.image_url || item.url} 
                            alt={item.prompt || 'Gallery item'} 
                            className="w-full aspect-square object-cover relative z-10"
                            loading="lazy"
                            decoding="async"
                            onLoad={(e) => {
                              // Successfully loaded - hide placeholder
                              e.target.style.opacity = '1';
                              const placeholder = e.target.parentElement.querySelector('.img-placeholder');
                              if (placeholder) placeholder.style.display = 'none';
                            }}
                            onError={(e) => {
                              // Failed to load - show fallback
                              e.target.style.display = 'none';
                              const placeholder = e.target.parentElement.querySelector('.img-placeholder');
                              if (placeholder) placeholder.style.display = 'none';
                              const fallback = e.target.parentElement.querySelector('.image-fallback');
                              if (fallback) fallback.classList.remove('hidden');
                            }}
                            style={{ opacity: 0, transition: 'opacity 0.2s ease-out' }}
                          />
                          <div className="image-fallback hidden w-full aspect-square bg-gray-700 flex flex-col items-center justify-center absolute inset-0 z-20">
                            <div className="text-center text-gray-500">
                              <FiImage className="w-8 h-8 mx-auto mb-2 opacity-50" />
                              <span className="text-xs block">Unavailable</span>
                              <span className="text-[10px] opacity-50 block mt-1">{item.name || item.character_name || 'Unknown'}</span>
                            </div>
                            {/* Always visible delete button for broken images */}
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="mt-2 bg-red-500/30 hover:bg-red-500/50"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteFromGallery(item.id, item.source);
                              }}
                            >
                              <FiTrash2 className="text-red-400 w-4 h-4 mr-1" />
                              <span className="text-red-400 text-xs">Delete</span>
                            </Button>
                          </div>
                        </>
                      )}
                      
                      {/* Video indicator */}
                      {isVideo && (
                        <div className="absolute top-2 right-2 bg-pink-500 text-white text-xs px-1.5 py-0.5 rounded flex items-center gap-1">
                          <FiVideo className="w-3 h-3" />
                          Video
                        </div>
                      )}
                      
                      {/* Hover Actions */}
                      <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 p-2">
                        <div className="flex gap-1">
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="bg-white/10 hover:bg-white/20"
                            onClick={(e) => {
                              e.stopPropagation();
                              setExpandedItem({
                                type: isVideo ? 'video' : 'image',
                                url: item.image_url || item.url,
                                name: item.prompt || item.name || 'Gallery item'
                              });
                            }}
                            title={isVideo ? "Play Video" : "Expand"}
                          >
                            {isVideo ? (
                              <FiPlay className="text-white w-4 h-4" />
                            ) : (
                              <FiMaximize2 className="text-white w-4 h-4" />
                            )}
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="bg-white/10 hover:bg-white/20"
                            onClick={() => downloadMedia(item.image_url || item.url, `gallery-${item.id}.${item.type === 'video' ? 'mp4' : 'png'}`)}
                            title="Download"
                          >
                            <FiDownload className="text-white w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="bg-white/10 hover:bg-white/20"
                            onClick={() => {
                              setSelectedHeroFrame({ id: item.id, url: item.image_url || item.url, prompt: item.prompt });
                              toast.success('Selected as source image');
                            }}
                            title="Use as source"
                          >
                            <FiImage className="text-white w-4 h-4" />
                          </Button>
                          {!isVideo && (
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="bg-white/10 hover:bg-white/20"
                              onClick={() => {
                                setVideoSourceType('upload');
                                setVideoUploadedImage(item.image_url || item.url);
                                setVideoPrompt(item.prompt || '');
                                setActiveTab('video');
                                toast.success('Ready for video animation');
                              }}
                              title="Animate to video"
                            >
                              <FiVideo className="text-white w-4 h-4" />
                            </Button>
                          )}
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="bg-red-500/20 hover:bg-red-500/40"
                            onClick={() => deleteFromGallery(item.id, item.source)}
                            title="Delete"
                          >
                            <FiTrash2 className="text-red-400 w-4 h-4" />
                          </Button>
                        </div>
                        {item.prompt && (
                          <p className="text-white/80 text-xs text-center line-clamp-2 px-1">
                            {item.prompt.substring(0, 60)}...
                          </p>
                        )}
                      </div>
                      
                      {/* Badges */}
                      <div className="absolute top-1 left-1 flex flex-col gap-1">
                        {isVideo && (
                          <span className="bg-purple-500 text-white text-[10px] px-1.5 py-0.5 rounded flex items-center gap-0.5">
                            <FiVideo size={10} /> Video
                          </span>
                        )}
                        {item.is_master && (
                          <span className="bg-yellow-500 text-black text-[10px] px-1.5 py-0.5 rounded font-medium">
                            ★ Master
                          </span>
                        )}
                        {item.character_name && (
                          <span className="bg-blue-500/80 text-white text-[10px] px-1.5 py-0.5 rounded">
                            {item.character_name}
                          </span>
                        )}
                      </div>
                    </div>
                  )})}
                </div>
                
                {/* Infinite scroll loader */}
                {galleryHasMore && (
                  <div className="flex justify-center py-6">
                    <Button
                      variant="outline"
                      onClick={loadMoreGallery}
                      disabled={galleryLoading}
                      className="border-purple-500/50 text-purple-300 hover:bg-purple-500/20"
                    >
                      {galleryLoading ? (
                        <>
                          <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Loading...
                        </>
                      ) : (
                        <>
                          Load More ({galleryTotal - gallery.length} remaining)
                        </>
                      )}
                    </Button>
                  </div>
                )}
                
                {/* Loading overlay for initial load */}
                {galleryLoading && gallery.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-16">
                    <FiRefreshCw className="w-8 h-8 text-purple-400 animate-spin mb-4" />
                    <p className="text-gray-400">Loading gallery...</p>
                  </div>
                )}
              </>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </main>
      
      {/* Gallery Picker Modal - Universal for all features */}
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
              className="bg-gray-900 rounded-xl border border-purple-500/20 w-full max-w-5xl max-h-[85vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">
                  {galleryPickerMode === 'character' ? 'Select Images for Character' : 
                   galleryPickerMode === 'video' ? 'Select Image for Video' :
                   galleryPickerMode === 'shots' ? 'Select Source Image' : 'Select from Gallery'}
                </h3>
                <button onClick={() => setShowGalleryPicker(false)} className="text-gray-400 hover:text-white">
                  <FiX size={20} />
                </button>
              </div>
              
              {/* Quick Filters */}
              <div className="px-4 py-2 border-b border-gray-800 flex gap-2 flex-wrap">
                <Button
                  size="sm"
                  variant={galleryFilter === 'all' ? 'default' : 'outline'}
                  onClick={() => setGalleryFilter('all')}
                  className={`text-xs ${galleryFilter === 'all' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}`}
                >
                  All
                </Button>
                <Button
                  size="sm"
                  variant={galleryFilter === 'images' ? 'default' : 'outline'}
                  onClick={() => setGalleryFilter('images')}
                  className={`text-xs ${galleryFilter === 'images' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}`}
                >
                  Images Only
                </Button>
                <Button
                  size="sm"
                  variant={galleryFilter === 'characters' ? 'default' : 'outline'}
                  onClick={() => setGalleryFilter('characters')}
                  className={`text-xs ${galleryFilter === 'characters' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}`}
                >
                  Characters
                </Button>
                {galleryPickerMode !== 'video' && (
                  <Button
                    size="sm"
                    variant={galleryFilter === 'videos' ? 'default' : 'outline'}
                    onClick={() => setGalleryFilter('videos')}
                    className={`text-xs ${galleryFilter === 'videos' ? 'bg-purple-600' : 'border-gray-600 text-gray-300'}`}
                  >
                    Videos
                  </Button>
                )}
                
                {/* Upload button */}
                <label className="ml-auto">
                  <Button size="sm" variant="outline" className="border-gray-600 text-gray-300 text-xs cursor-pointer" asChild>
                    <span>
                      <FiUpload className="w-3 h-3 mr-1" /> Upload New
                    </span>
                  </Button>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file) {
                        const reader = new FileReader();
                        reader.onload = (event) => {
                          if (galleryPickerCallback) {
                            galleryPickerCallback({
                              url: event.target.result,
                              prompt: file.name,
                              source: 'upload'
                            });
                          }
                          setShowGalleryPicker(false);
                          toast.success('Image uploaded and selected');
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                  />
                </label>
              </div>
              
              <div className="p-4 overflow-y-auto max-h-[55vh]">
                {filteredGallery.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FiFolder className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No images found</p>
                    <p className="text-sm mt-2">
                      {gallery.length === 0 
                        ? 'Create characters and generate images to see them here' 
                        : 'Try a different filter or upload a new image'}
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3">
                    {filteredGallery
                      .filter(item => galleryPickerMode === 'video' ? item.type !== 'video' : true)
                      .map((item) => (
                      <div 
                        key={item.id} 
                        className="relative cursor-pointer rounded-lg overflow-hidden border-2 border-gray-700 hover:border-purple-500 transition-colors group"
                        onClick={() => {
                          const imageData = {
                            id: item.id,
                            url: item.image_url || item.url,
                            prompt: item.prompt,
                            character_name: item.character_name,
                            source: item.source
                          };
                          
                          if (galleryPickerCallback) {
                            galleryPickerCallback(imageData);
                            if (galleryPickerMode !== 'character') {
                              setShowGalleryPicker(false);
                            }
                            toast.success('Image selected');
                          } else if (galleryPickerMode === 'character') {
                            const newImage = {
                              id: Date.now() + Math.random(),
                              url: item.image_url || item.url,
                              name: item.prompt?.substring(0, 20) || 'Gallery Image'
                            };
                            setCharacterImages(prev => [...prev, newImage]);
                            toast.success('Image added to character references');
                          } else if (galleryPickerMode === 'video') {
                            setVideoUploadedImage(item.image_url || item.url);
                            setVideoPrompt(item.prompt || '');
                            setVideoSourceType('upload');
                            setShowGalleryPicker(false);
                            toast.success('Image selected for video');
                          } else {
                            setShotsSourceImage(item.image_url || item.url);
                            setShowGalleryPicker(false);
                            toast.success('Source image selected');
                          }
                        }}
                      >
                        {item.type === 'video' || item.is_animation ? (
                          <video 
                            src={item.image_url || item.url} 
                            className="w-full aspect-square object-cover"
                            muted
                            playsInline
                          />
                        ) : (
                          <img 
                            src={item.image_url || item.url} 
                            alt={item.prompt || ''} 
                            className="w-full aspect-square object-cover"
                          />
                        )}
                        
                        {/* Badges */}
                        <div className="absolute top-1 left-1 flex flex-col gap-0.5">
                          {item.is_master && (
                            <span className="bg-yellow-500 text-black text-[9px] px-1 py-0.5 rounded font-medium">★ Master</span>
                          )}
                          {item.character_name && (
                            <span className="bg-blue-500/90 text-white text-[9px] px-1 py-0.5 rounded truncate max-w-[80px]">
                              {item.character_name}
                            </span>
                          )}
                          {(item.type === 'video' || item.is_animation) && (
                            <span className="bg-purple-500 text-white text-[9px] px-1 py-0.5 rounded flex items-center gap-0.5">
                              <FiVideo size={8} />
                            </span>
                          )}
                        </div>
                        
                        {/* Hover overlay with prompt */}
                        <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-1">
                          <p className="text-white/90 text-[10px] line-clamp-2">
                            {item.prompt?.substring(0, 50) || 'No description'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="p-4 border-t border-gray-800 flex justify-between items-center">
                <span className="text-sm text-gray-400">
                  {filteredGallery.length} item{filteredGallery.length !== 1 ? 's' : ''} available
                </span>
                <div className="flex gap-3">
                  <Button variant="ghost" onClick={() => setShowGalleryPicker(false)}>
                    Cancel
                  </Button>
                  {galleryPickerMode === 'character' && (
                    <Button onClick={() => setShowGalleryPicker(false)} className="bg-purple-600 hover:bg-purple-700">
                      Done ({characterImages.length} selected)
                    </Button>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Shots Review Modal */}
      <AnimatePresence>
        {showShotsReview && shotsResults.length > 0 && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowShotsReview(false)}
          >
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-xl border border-purple-500/30 w-full max-w-6xl max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">Generated Shots</h3>
                  <p className="text-sm text-gray-400">{shotsResults.length} angles generated • Select to save or download</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      // Save all to gallery
                      for (const shot of shotsResults) {
                        await saveToGallery(shot.url, shot.type || 'shot', 'shot');
                      }
                      toast.success('All shots saved to gallery!');
                      loadGallery();
                    }}
                    className="border-green-400/50 text-green-300 hover:bg-green-500/20"
                  >
                    <FiSave className="mr-1" /> Save All
                  </Button>
                  <button onClick={() => setShowShotsReview(false)} className="text-gray-400 hover:text-white">
                    <FiX size={24} />
                  </button>
                </div>
              </div>
              
              <div className="p-4 overflow-y-auto max-h-[70vh]">
                <div className="grid grid-cols-3 gap-4">
                  {shotsResults.map((shot, idx) => (
                    <div key={idx} className="relative group rounded-xl overflow-hidden bg-gray-800 border border-gray-700">
                      <img 
                        src={shot.url} 
                        alt={shot.type || `Shot ${idx + 1}`}
                        className="w-full aspect-square object-cover"
                      />
                      <div className="absolute top-2 left-2 bg-black/70 px-2 py-1 rounded text-xs text-white">
                        {shot.type || `Angle ${idx + 1}`}
                      </div>
                      
                      {/* Hover actions */}
                      <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => downloadMedia(shot.url, `shot-${shot.type || idx + 1}.png`)}
                            className="bg-white/20 hover:bg-white/30"
                          >
                            <FiDownload className="mr-1" /> Download
                          </Button>
                          <Button
                            size="sm"
                            onClick={async () => {
                              await saveToGallery(shot.url, shot.type || `Shot ${idx + 1}`, 'shot');
                              toast.success('Saved to gallery!');
                              loadGallery();
                            }}
                            className="bg-purple-600 hover:bg-purple-700"
                          >
                            <FiSave className="mr-1" /> Save
                          </Button>
                        </div>
                        {selectedCharacter && (
                          <Button
                            size="sm"
                            onClick={async () => {
                              await saveToCharacterFolder(
                                selectedCharacter.id,
                                shot.url,
                                shot.type || `Shot ${idx + 1}`,
                                'shot'
                              );
                              toast.success(`Saved to ${selectedCharacter.name}'s folder!`);
                            }}
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            <FiUser className="mr-1" /> Save to {selectedCharacter.name}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="p-4 border-t border-gray-800 flex justify-between">
                <span className="text-gray-400 text-sm">
                  Tip: Hover over each shot for save options
                </span>
                <Button variant="ghost" onClick={() => setShowShotsReview(false)}>
                  Close
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Generation Preview Modal - Shows newly generated image with save options */}
      <AnimatePresence>
        {showGenerationPreview && generationPreviewData && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/95 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
            onClick={() => setShowGenerationPreview(false)}
          >
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-xl border border-purple-500/30 w-full max-w-4xl max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FiCheck className="text-green-400" /> Image Generated!
                  </h3>
                  <p className="text-sm text-gray-400">
                    {generationPreviewData.type === 'character' 
                      ? `For ${generationPreviewData.characterName}` 
                      : `Scene: ${generationPreviewData.sceneName}`}
                    {generationPreviewData.method && ` • Using ${generationPreviewData.method}`}
                  </p>
                </div>
                <button 
                  onClick={() => setShowGenerationPreview(false)} 
                  className="text-gray-400 hover:text-white p-2"
                >
                  <FiX size={24} />
                </button>
              </div>
              
              {/* Image Preview */}
              <div className="p-6 flex justify-center bg-black/50">
                <img 
                  src={generationPreviewData.image?.url} 
                  alt={generationPreviewData.prompt || 'Generated image'}
                  className="max-w-full max-h-[50vh] object-contain rounded-lg shadow-2xl"
                />
              </div>
              
              {/* Prompt */}
              {generationPreviewData.prompt && (
                <div className="px-6 pb-4">
                  <p className="text-gray-400 text-sm italic">"{generationPreviewData.prompt}"</p>
                </div>
              )}
              
              {/* Actions */}
              <div className="p-4 border-t border-gray-800 bg-gray-900/80">
                <div className="flex flex-wrap gap-3 justify-center">
                  {/* Save to Character Folder */}
                  {generationPreviewData.characterId && (
                    <Button
                      onClick={async () => {
                        await saveToCharacterFolder(
                          generationPreviewData.characterId,
                          generationPreviewData.image.url,
                          generationPreviewData.prompt,
                          generationPreviewData.method || 'generated'
                        );
                        toast.success(`Saved to ${generationPreviewData.characterName}'s folder!`);
                        loadCharacterGallery(generationPreviewData.characterId);
                      }}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <FiUser className="mr-2" /> Save to {generationPreviewData.characterName}
                    </Button>
                  )}
                  
                  {/* Save to Scene Folder */}
                  {generationPreviewData.sceneId && (
                    <Button
                      onClick={async () => {
                        await saveToSceneFolder(
                          generationPreviewData.sceneId,
                          generationPreviewData.image.url,
                          generationPreviewData.prompt,
                          'generated',
                          generationPreviewData.characterId
                        );
                        toast.success(`Saved to ${generationPreviewData.sceneName}!`);
                        loadSceneGallery(generationPreviewData.sceneId);
                      }}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <FiGrid className="mr-2" /> Save to {generationPreviewData.sceneName}
                    </Button>
                  )}
                  
                  {/* Save to Both - when scene uses a character */}
                  {generationPreviewData.sceneId && generationPreviewData.characterId && (
                    <Button
                      onClick={async () => {
                        // Save to scene folder
                        await saveToSceneFolder(
                          generationPreviewData.sceneId,
                          generationPreviewData.image.url,
                          generationPreviewData.prompt,
                          'generated',
                          generationPreviewData.characterId
                        );
                        // Save to character folder
                        await saveToCharacterFolder(
                          generationPreviewData.characterId,
                          generationPreviewData.image.url,
                          generationPreviewData.prompt,
                          'scene'
                        );
                        toast.success(`Saved to both ${generationPreviewData.sceneName} and ${generationPreviewData.characterName}!`);
                        loadSceneGallery(generationPreviewData.sceneId);
                        loadCharacterGallery(generationPreviewData.characterId);
                      }}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                    >
                      <FiSave className="mr-2" /> Save to Both
                    </Button>
                  )}
                  
                  {/* Save to Main Gallery */}
                  <Button
                    variant="outline"
                    onClick={async () => {
                      await saveToGallery(
                        generationPreviewData.image.url,
                        generationPreviewData.prompt,
                        generationPreviewData.type
                      );
                      toast.success('Saved to Gallery!');
                      loadGallery();
                    }}
                    className="border-green-400/50 text-green-300 hover:bg-green-500/20"
                  >
                    <FiSave className="mr-2" /> Save to Gallery
                  </Button>
                  
                  {/* Download */}
                  <Button
                    variant="outline"
                    onClick={() => {
                      downloadMedia(generationPreviewData.image.url, `generated-${Date.now()}.png`);
                    }}
                    className="border-gray-500 text-gray-300 hover:bg-gray-700"
                  >
                    <FiDownload className="mr-2" /> Download
                  </Button>
                </div>
                
                {/* Close / Dismiss */}
                <div className="flex justify-center mt-4">
                  <Button 
                    variant="ghost" 
                    onClick={() => setShowGenerationPreview(false)}
                    className="text-gray-400"
                  >
                    Close Preview
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Cinema Source Image Picker Modal */}
      <AnimatePresence>
        {showCinemaSourcePicker && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowCinemaSourcePicker(false)}
          >
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-xl border border-purple-500/30 w-full max-w-5xl max-h-[85vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">Select Source Image</h3>
                  <p className="text-sm text-gray-400">Choose an image to create a variant with cinema settings</p>
                </div>
                <button onClick={() => setShowCinemaSourcePicker(false)} className="text-gray-400 hover:text-white">
                  <FiX size={24} />
                </button>
              </div>
              
              {/* Tabs for source selection */}
              <div className="p-4 overflow-y-auto max-h-[70vh]">
                <Tabs defaultValue="characters" className="w-full">
                  <TabsList className="bg-gray-800/50 mb-4">
                    <TabsTrigger value="characters" className="data-[state=active]:bg-purple-600 text-gray-300">
                      <FiUser className="mr-2" /> Characters
                    </TabsTrigger>
                    <TabsTrigger value="scenes" className="data-[state=active]:bg-purple-600 text-gray-300">
                      <FiLayers className="mr-2" /> Scenes
                    </TabsTrigger>
                    <TabsTrigger value="gallery" className="data-[state=active]:bg-purple-600 text-gray-300">
                      <FiGrid className="mr-2" /> Gallery
                    </TabsTrigger>
                  </TabsList>
                  
                  {/* Characters Tab */}
                  <TabsContent value="characters">
                    {characters.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <FiUser className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No characters created yet</p>
                        <p className="text-xs mt-2">Create characters in the Characters tab first</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {characters.map((char) => (
                          <button
                            key={char.id}
                            onClick={() => {
                              const imgUrl = char.thumbnail || char.reference_images?.[0];
                              if (imgUrl) {
                                setCinemaSourceImage({
                                  url: imgUrl,
                                  name: char.name,
                                  type: 'Character'
                                });
                                setShowCinemaSourcePicker(false);
                                toast.success(`Selected ${char.name}`);
                              } else {
                                toast.error('This character has no image');
                              }
                            }}
                            className="group relative rounded-xl overflow-hidden border-2 border-transparent hover:border-purple-500 transition-all"
                          >
                            {char.thumbnail || char.reference_images?.[0] ? (
                              <img 
                                src={char.thumbnail || char.reference_images?.[0]} 
                                alt={char.name}
                                className="w-full aspect-square object-cover"
                              />
                            ) : (
                              <div className="w-full aspect-square bg-gray-800 flex items-center justify-center">
                                <FiUser className="text-gray-600 w-8 h-8" />
                              </div>
                            )}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end justify-center pb-3">
                              <span className="text-white font-medium text-sm">{char.name}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                  
                  {/* Scenes Tab */}
                  <TabsContent value="scenes">
                    {scenes.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <FiLayers className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No scenes created yet</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {scenes.map((scene) => (
                          <button
                            key={scene.id}
                            onClick={() => {
                              if (scene.preview_url) {
                                setCinemaSourceImage({
                                  url: scene.preview_url,
                                  name: scene.name,
                                  type: 'Scene'
                                });
                                setShowCinemaSourcePicker(false);
                                toast.success(`Selected ${scene.name}`);
                              } else {
                                toast.error('This scene has no preview image');
                              }
                            }}
                            className="group relative rounded-xl overflow-hidden border-2 border-transparent hover:border-purple-500 transition-all"
                          >
                            {scene.preview_url ? (
                              <img 
                                src={scene.preview_url} 
                                alt={scene.name}
                                className="w-full aspect-video object-cover"
                              />
                            ) : (
                              <div className="w-full aspect-video bg-gray-800 flex items-center justify-center">
                                <FiLayers className="text-gray-600 w-8 h-8" />
                              </div>
                            )}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-3">
                              <span className="text-white font-medium">{scene.name}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                  
                  {/* Gallery Tab */}
                  <TabsContent value="gallery">
                    {gallery.filter(item => item.type !== 'video').length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <FiGrid className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No images in gallery</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
                        {gallery.filter(item => item.type !== 'video').slice(0, 20).map((item) => (
                          <button
                            key={item.id}
                            onClick={() => {
                              setCinemaSourceImage({
                                url: item.image_url || item.url,
                                name: item.prompt?.slice(0, 30) || 'Gallery Image',
                                type: 'Gallery'
                              });
                              setShowCinemaSourcePicker(false);
                              toast.success('Image selected');
                            }}
                            className="group relative rounded-lg overflow-hidden border-2 border-transparent hover:border-purple-500 transition-all"
                          >
                            <img 
                              src={item.image_url || item.url} 
                              alt={item.prompt || 'Gallery'}
                              className="w-full aspect-square object-cover"
                            />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <FiPlus className="text-white w-6 h-6" />
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
              
              {/* Footer */}
              <div className="p-4 border-t border-gray-800 flex justify-end">
                <Button variant="ghost" onClick={() => setShowCinemaSourcePicker(false)}>
                  Cancel
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Crop Modal */}
      <AnimatePresence>
        {showCropModal && cropImage && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/95 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
          >
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-xl border border-purple-500/30 w-full max-w-4xl max-h-[90vh] overflow-hidden"
            >
              {/* Header */}
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FiCrop className="text-purple-400" /> Crop Image
                  </h3>
                  <p className="text-sm text-gray-400">Drag to position, scroll to zoom</p>
                </div>
                <button 
                  onClick={() => setShowCropModal(false)} 
                  className="text-gray-400 hover:text-white p-2"
                >
                  <FiX size={24} />
                </button>
              </div>
              
              {/* Crop Area */}
              <div className="relative h-[50vh] bg-black">
                <Cropper
                  image={cropImage.url}
                  crop={crop}
                  zoom={zoom}
                  aspect={cropAspect}
                  onCropChange={setCrop}
                  onZoomChange={setZoom}
                  onCropComplete={onCropComplete}
                />
              </div>
              
              {/* Controls */}
              <div className="p-4 border-t border-gray-800 space-y-4">
                {/* Aspect Ratio Selection */}
                <div>
                  <label className="text-gray-400 text-xs mb-2 block">Aspect Ratio</label>
                  <div className="flex gap-2 flex-wrap">
                    {[
                      { label: '16:9', value: 16/9 },
                      { label: '4:3', value: 4/3 },
                      { label: '1:1', value: 1 },
                      { label: '3:4', value: 3/4 },
                      { label: '9:16', value: 9/16 },
                      { label: 'Free', value: undefined }
                    ].map((ar) => (
                      <button
                        key={ar.label}
                        onClick={() => setCropAspect(ar.value)}
                        className={`px-3 py-1 text-sm rounded ${
                          cropAspect === ar.value
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                        }`}
                      >
                        {ar.label}
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Zoom Slider */}
                <div>
                  <label className="text-gray-400 text-xs mb-2 block">Zoom: {zoom.toFixed(1)}x</label>
                  <input
                    type="range"
                    min={1}
                    max={3}
                    step={0.1}
                    value={zoom}
                    onChange={(e) => setZoom(Number(e.target.value))}
                    className="w-full accent-purple-500"
                  />
                </div>
                
                {/* Action Buttons */}
                <div className="flex gap-3 justify-end">
                  <Button 
                    variant="ghost" 
                    onClick={() => setShowCropModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleSaveCroppedImage}
                    disabled={isLoading}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <FiSave className="mr-2" /> Save Cropped Image
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Expanded View Modal for Images/Videos */}
      <AnimatePresence>
        {expandedItem && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/95 z-[200] flex items-center justify-center p-4"
            onClick={() => setExpandedItem(null)}
          >
            {/* Close button */}
            <button
              onClick={() => setExpandedItem(null)}
              className="absolute top-4 right-4 text-white/70 hover:text-white bg-white/10 hover:bg-white/20 p-2 rounded-full transition-colors z-10"
            >
              <FiX className="w-6 h-6" />
            </button>
            
            {/* Download button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                downloadMedia(expandedItem.url, `azories-${expandedItem.type}-${Date.now()}.${expandedItem.type === 'video' ? 'mp4' : 'png'}`);
              }}
              className="absolute top-4 right-16 text-white/70 hover:text-white bg-white/10 hover:bg-white/20 p-2 rounded-full transition-colors z-10"
            >
              <FiDownload className="w-6 h-6" />
            </button>
            
            {/* Media content */}
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="max-w-[90vw] max-h-[90vh] relative"
              onClick={(e) => e.stopPropagation()}
            >
              {expandedItem.type === 'video' ? (
                <video
                  src={expandedItem.url}
                  controls
                  autoPlay
                  loop
                  className="max-w-full max-h-[85vh] rounded-lg"
                />
              ) : (
                <img
                  src={expandedItem.url}
                  alt={expandedItem.name}
                  className="max-w-full max-h-[85vh] object-contain rounded-lg"
                />
              )}
              
              {/* Caption */}
              <p className="text-center text-white/70 mt-3 text-sm">
                {expandedItem.name}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
