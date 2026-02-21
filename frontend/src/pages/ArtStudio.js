import { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  FiImage, FiUser, FiLayers, FiGrid, FiSave, FiDownload, 
  FiTrash2, FiPlus, FiZap, FiSliders, FiDroplet, FiRefreshCw,
  FiArrowLeft, FiFolder, FiStar, FiCopy, FiEdit2, FiUpload, FiBook, FiCheck
} from 'react-icons/fi';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Node types for the visual workflow
const NODE_TYPES = {
  CHARACTER: 'character',
  SCENE: 'scene',
  STYLE: 'style',
  GENERATE: 'generate',
  EDIT: 'edit',
  UPSCALE: 'upscale'
};

// Character traits for the builder
const CHARACTER_TRAITS = {
  gender: ['Male', 'Female', 'Non-binary', 'Other'],
  ageGroup: ['Child', 'Teen', 'Young Adult', 'Adult', 'Elderly'],
  bodyType: ['Slim', 'Average', 'Athletic', 'Curvy', 'Muscular'],
  skinTone: ['Very Light', 'Light', 'Medium', 'Tan', 'Dark', 'Very Dark'],
  hairColor: ['Black', 'Brown', 'Blonde', 'Red', 'Gray', 'White', 'Blue', 'Pink', 'Purple', 'Green'],
  hairStyle: ['Short', 'Medium', 'Long', 'Curly', 'Straight', 'Wavy', 'Braided', 'Bald', 'Mohawk'],
  eyeColor: ['Brown', 'Blue', 'Green', 'Hazel', 'Gray', 'Amber', 'Red', 'Purple'],
  clothing: ['Casual', 'Formal', 'Fantasy', 'Sci-Fi', 'Medieval', 'Victorian', 'Modern', 'Athletic'],
  expression: ['Happy', 'Sad', 'Angry', 'Surprised', 'Neutral', 'Thoughtful', 'Confident', 'Shy']
};

// Art styles with example images
const ART_STYLES = [
  { id: 'realistic', name: 'Realistic', description: 'Photorealistic rendering', 
    exampleImage: 'https://images.unsplash.com/photo-1767256483514-76135f5a0713?w=200&h=200&fit=crop' },
  { id: 'anime', name: 'Anime', description: 'Japanese animation style',
    exampleImage: 'https://images.unsplash.com/photo-1613376023733-0a73315d9b06?w=200&h=200&fit=crop' },
  { id: 'cartoon', name: 'Cartoon', description: 'Colorful cartoon style',
    exampleImage: 'https://images.unsplash.com/photo-1767557125491-b3483567d843?w=200&h=200&fit=crop' },
  { id: 'watercolor', name: 'Watercolor', description: 'Soft watercolor painting',
    exampleImage: 'https://images.unsplash.com/photo-1700212964225-d31af38e3e91?w=200&h=200&fit=crop' },
  { id: 'oil-painting', name: 'Oil Painting', description: 'Classic oil painting style',
    exampleImage: 'https://images.unsplash.com/photo-1767256483514-76135f5a0713?w=200&h=200&fit=crop' },
  { id: 'pixel-art', name: 'Pixel Art', description: 'Retro pixel graphics',
    exampleImage: 'https://images.unsplash.com/photo-1759171052927-83f3b3a72b2b?w=200&h=200&fit=crop' },
  { id: 'comic', name: 'Comic Book', description: 'Bold comic book style',
    exampleImage: 'https://images.pexels.com/photos/7809123/pexels-photo-7809123.jpeg?w=200&h=200&fit=crop' },
  { id: 'fantasy', name: 'Fantasy Art', description: 'Magical fantasy illustration',
    exampleImage: 'https://images.unsplash.com/photo-1770034285769-4a5a3f410346?w=200&h=200&fit=crop' },
  { id: '3d-render', name: '3D Render', description: 'Modern 3D rendered look',
    exampleImage: 'https://images.pexels.com/photos/11798029/pexels-photo-11798029.jpeg?w=200&h=200&fit=crop' },
  { id: 'sketch', name: 'Pencil Sketch', description: 'Hand-drawn pencil sketch',
    exampleImage: 'https://images.unsplash.com/photo-1758521232708-d738b0eaa94a?w=200&h=200&fit=crop' }
];

// Scene presets
const SCENE_PRESETS = [
  { id: 'forest', name: 'Enchanted Forest', prompt: 'magical forest with glowing flowers and mystical lighting' },
  { id: 'castle', name: 'Castle Interior', prompt: 'grand castle interior with stone walls and chandeliers' },
  { id: 'beach', name: 'Tropical Beach', prompt: 'beautiful tropical beach with crystal clear water and palm trees' },
  { id: 'city', name: 'Modern City', prompt: 'bustling modern city street with skyscrapers' },
  { id: 'space', name: 'Outer Space', prompt: 'cosmic space scene with stars and nebulae' },
  { id: 'underwater', name: 'Underwater', prompt: 'underwater scene with coral reefs and sea life' },
  { id: 'mountain', name: 'Mountain Peak', prompt: 'majestic mountain peak with snow and clouds' },
  { id: 'library', name: 'Ancient Library', prompt: 'ancient library with towering bookshelves and warm lighting' }
];

export default function ArtStudio() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const referenceInputRef = useRef(null);
  
  // Main state
  const [activeTab, setActiveTab] = useState('character'); // character, scene, gallery
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [gallery, setGallery] = useState([]);
  const [selectedGalleryItem, setSelectedGalleryItem] = useState(null);
  const [userBooks, setUserBooks] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState('general'); // 'general' or book ID
  
  // Reference image state
  const [referenceImage, setReferenceImage] = useState(null);
  const [showGalleryPicker, setShowGalleryPicker] = useState(false);
  
  // Character builder state
  const [character, setCharacter] = useState({
    name: '',
    gender: 'Female',
    ageGroup: 'Young Adult',
    bodyType: 'Average',
    skinTone: 'Medium',
    hairColor: 'Brown',
    hairStyle: 'Long',
    eyeColor: 'Brown',
    clothing: 'Fantasy',
    expression: 'Confident',
    additionalDetails: ''
  });
  
  // Scene builder state
  const [scene, setScene] = useState({
    preset: '',
    customPrompt: '',
    timeOfDay: 'day',
    weather: 'clear',
    mood: 'peaceful'
  });
  
  // Style state
  const [selectedStyle, setSelectedStyle] = useState('fantasy');
  
  // Load gallery and books on mount
  useEffect(() => {
    if (token) {
      loadGallery();
      loadUserBooks();
    }
  }, [token]);
  
  const loadUserBooks = async () => {
    try {
      const response = await fetch(`${API_URL}/api/books/my`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUserBooks(data || []);
      }
    } catch (error) {
      console.error('Failed to load books:', error);
    }
  };
  
  const loadGallery = async () => {
    try {
      const response = await fetch(`${API_URL}/api/art-studio/gallery`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setGallery(data.images || []);
      }
    } catch (error) {
      console.error('Failed to load gallery:', error);
    }
  };
  
  const buildCharacterPrompt = () => {
    const traits = [];
    traits.push(`${character.gender} character`);
    traits.push(`${character.ageGroup.toLowerCase()} age`);
    traits.push(`${character.bodyType.toLowerCase()} body type`);
    traits.push(`${character.skinTone.toLowerCase()} skin tone`);
    traits.push(`${character.hairColor.toLowerCase()} ${character.hairStyle.toLowerCase()} hair`);
    traits.push(`${character.eyeColor.toLowerCase()} eyes`);
    traits.push(`${character.clothing.toLowerCase()} clothing style`);
    traits.push(`${character.expression.toLowerCase()} expression`);
    
    if (character.additionalDetails) {
      traits.push(character.additionalDetails);
    }
    
    return traits.join(', ');
  };
  
  const buildScenePrompt = () => {
    let prompt = '';
    
    if (scene.preset) {
      const presetData = SCENE_PRESETS.find(p => p.id === scene.preset);
      prompt = presetData?.prompt || '';
    }
    
    if (scene.customPrompt) {
      prompt = prompt ? `${prompt}, ${scene.customPrompt}` : scene.customPrompt;
    }
    
    prompt += `, ${scene.timeOfDay} time`;
    prompt += `, ${scene.weather} weather`;
    prompt += `, ${scene.mood} atmosphere`;
    
    return prompt;
  };
  
  const generateImage = async () => {
    if (!token) {
      navigate('/login');
      return;
    }
    
    setIsGenerating(true);
    setGeneratedImage(null);
    
    try {
      // Build the full prompt
      let fullPrompt = '';
      const styleData = ART_STYLES.find(s => s.id === selectedStyle);
      
      if (activeTab === 'character') {
        fullPrompt = `${buildCharacterPrompt()}, ${styleData?.name || 'fantasy'} art style, highly detailed, professional illustration`;
      } else if (activeTab === 'scene') {
        fullPrompt = `${buildScenePrompt()}, ${styleData?.name || 'fantasy'} art style, highly detailed, professional illustration`;
      }
      
      const response = await fetch(`${API_URL}/api/art-studio/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: fullPrompt,
          style: selectedStyle,
          type: activeTab,
          characterData: activeTab === 'character' ? character : null,
          sceneData: activeTab === 'scene' ? scene : null,
          referenceImage: referenceImage,
          bookId: selectedBookId !== 'general' ? selectedBookId : null
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGeneratedImage(data.image_url);
        // Refresh gallery
        loadGallery();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to generate image');
      }
    } catch (error) {
      console.error('Generation error:', error);
      alert('Failed to generate image. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };
  
  const saveToGallery = async (imageUrl, name) => {
    try {
      const response = await fetch(`${API_URL}/api/art-studio/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: imageUrl,
          name: name || `Art ${new Date().toLocaleDateString()}`,
          type: activeTab,
          style: selectedStyle,
          characterData: character,
          sceneData: scene
        })
      });
      
      if (response.ok) {
        loadGallery();
      }
    } catch (error) {
      console.error('Failed to save:', error);
    }
  };
  
  const deleteFromGallery = async (imageId) => {
    try {
      await fetch(`${API_URL}/api/art-studio/gallery/${imageId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      loadGallery();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#1a1520] to-[#0d0a10] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Pro Feature</h2>
          <p className="text-white/60 mb-6">Sign in to access the Art Studio</p>
          <Button onClick={() => navigate('/login')} className="bg-purple-600 hover:bg-purple-700">
            Sign In
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a1520] to-[#0d0a10]">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/library')}
              className="text-white/70 hover:text-white"
            >
              <FiArrowLeft className="w-5 h-5 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <FiDroplet className="text-purple-400" />
                Art Studio
              </h1>
              <p className="text-sm text-white/50">Create characters, scenes & illustrations for your books</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              className="border-purple-500/50 text-purple-300 hover:bg-purple-500/20"
              onClick={() => setActiveTab('gallery')}
            >
              <FiFolder className="w-4 h-4 mr-2" />
              My Gallery ({gallery.length})
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <Button
            variant={activeTab === 'character' ? 'default' : 'outline'}
            onClick={() => setActiveTab('character')}
            className={activeTab === 'character' ? 'bg-purple-600' : 'border-white/20 text-white/70'}
          >
            <FiUser className="w-4 h-4 mr-2" />
            Character Builder
          </Button>
          <Button
            variant={activeTab === 'scene' ? 'default' : 'outline'}
            onClick={() => setActiveTab('scene')}
            className={activeTab === 'scene' ? 'bg-purple-600' : 'border-white/20 text-white/70'}
          >
            <FiLayers className="w-4 h-4 mr-2" />
            Scene Creator
          </Button>
          <Button
            variant={activeTab === 'gallery' ? 'default' : 'outline'}
            onClick={() => setActiveTab('gallery')}
            className={activeTab === 'gallery' ? 'bg-purple-600' : 'border-white/20 text-white/70'}
          >
            <FiGrid className="w-4 h-4 mr-2" />
            Gallery
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Builder/Controls */}
          <div className="lg:col-span-2 space-y-6">
            {activeTab === 'character' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6"
              >
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiUser className="text-purple-400" />
                  Character Builder
                </h2>
                
                {/* Character Name */}
                <div className="mb-4">
                  <label className="text-sm text-white/70 mb-1 block">Character Name</label>
                  <Input
                    value={character.name}
                    onChange={(e) => setCharacter({ ...character, name: e.target.value })}
                    placeholder="Enter character name..."
                    className="bg-black/30 border-white/20 text-white"
                  />
                </div>
                
                {/* Trait Selectors */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(CHARACTER_TRAITS).map(([trait, options]) => (
                    <div key={trait}>
                      <label className="text-xs text-white/50 mb-1 block capitalize">
                        {trait.replace(/([A-Z])/g, ' $1').trim()}
                      </label>
                      <select
                        value={character[trait]}
                        onChange={(e) => setCharacter({ ...character, [trait]: e.target.value })}
                        className="w-full bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none"
                      >
                        {options.map(opt => (
                          <option key={opt} value={opt} className="bg-[#1a1520]">{opt}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
                
                {/* Additional Details */}
                <div className="mt-4">
                  <label className="text-sm text-white/70 mb-1 block">Additional Details</label>
                  <Textarea
                    value={character.additionalDetails}
                    onChange={(e) => setCharacter({ ...character, additionalDetails: e.target.value })}
                    placeholder="Add any extra details like accessories, pose, background elements..."
                    className="bg-black/30 border-white/20 text-white min-h-[80px]"
                  />
                </div>
              </motion.div>
            )}

            {activeTab === 'scene' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6"
              >
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiLayers className="text-purple-400" />
                  Scene Creator
                </h2>
                
                {/* Scene Presets */}
                <div className="mb-4">
                  <label className="text-sm text-white/70 mb-2 block">Scene Presets</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {SCENE_PRESETS.map(preset => (
                      <button
                        key={preset.id}
                        onClick={() => setScene({ ...scene, preset: preset.id })}
                        className={`p-3 rounded-lg border text-left transition-all ${
                          scene.preset === preset.id
                            ? 'border-purple-500 bg-purple-500/20'
                            : 'border-white/10 bg-black/20 hover:border-white/30'
                        }`}
                      >
                        <span className="text-sm font-medium text-white">{preset.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Scene Options */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <label className="text-xs text-white/50 mb-1 block">Time of Day</label>
                    <select
                      value={scene.timeOfDay}
                      onChange={(e) => setScene({ ...scene, timeOfDay: e.target.value })}
                      className="w-full bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-white text-sm"
                    >
                      <option value="dawn">Dawn</option>
                      <option value="day">Day</option>
                      <option value="dusk">Dusk</option>
                      <option value="night">Night</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-white/50 mb-1 block">Weather</label>
                    <select
                      value={scene.weather}
                      onChange={(e) => setScene({ ...scene, weather: e.target.value })}
                      className="w-full bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-white text-sm"
                    >
                      <option value="clear">Clear</option>
                      <option value="cloudy">Cloudy</option>
                      <option value="rainy">Rainy</option>
                      <option value="snowy">Snowy</option>
                      <option value="foggy">Foggy</option>
                      <option value="stormy">Stormy</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-white/50 mb-1 block">Mood</label>
                    <select
                      value={scene.mood}
                      onChange={(e) => setScene({ ...scene, mood: e.target.value })}
                      className="w-full bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-white text-sm"
                    >
                      <option value="peaceful">Peaceful</option>
                      <option value="mysterious">Mysterious</option>
                      <option value="dramatic">Dramatic</option>
                      <option value="romantic">Romantic</option>
                      <option value="scary">Scary</option>
                      <option value="epic">Epic</option>
                    </select>
                  </div>
                </div>
                
                {/* Custom Prompt */}
                <div>
                  <label className="text-sm text-white/70 mb-1 block">Custom Scene Description</label>
                  <Textarea
                    value={scene.customPrompt}
                    onChange={(e) => setScene({ ...scene, customPrompt: e.target.value })}
                    placeholder="Describe your scene in detail..."
                    className="bg-black/30 border-white/20 text-white min-h-[100px]"
                  />
                </div>
              </motion.div>
            )}

            {activeTab === 'gallery' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6"
              >
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <FiGrid className="text-purple-400" />
                  My Gallery
                </h2>
                
                {gallery.length === 0 ? (
                  <div className="text-center py-12">
                    <FiImage className="w-16 h-16 text-white/20 mx-auto mb-4" />
                    <p className="text-white/50">No images yet. Start creating!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {gallery.map((item) => (
                      <div
                        key={item._id}
                        className={`relative group rounded-lg overflow-hidden border-2 transition-all cursor-pointer ${
                          selectedGalleryItem?._id === item._id
                            ? 'border-purple-500'
                            : 'border-transparent hover:border-white/30'
                        }`}
                        onClick={() => setSelectedGalleryItem(item)}
                      >
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-full aspect-square object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="absolute bottom-0 left-0 right-0 p-3">
                            <p className="text-white text-sm font-medium truncate">{item.name}</p>
                            <p className="text-white/50 text-xs">{item.style}</p>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteFromGallery(item._id);
                          }}
                          className="absolute top-2 right-2 p-1.5 bg-red-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <FiTrash2 className="w-3 h-3 text-white" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* Style Selector (always visible for character/scene) */}
            {(activeTab === 'character' || activeTab === 'scene') && (
              <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <FiSliders className="text-purple-400" />
                  Art Style
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                  {ART_STYLES.map(style => (
                    <button
                      key={style.id}
                      onClick={() => setSelectedStyle(style.id)}
                      className={`p-3 rounded-lg border text-center transition-all ${
                        selectedStyle === style.id
                          ? 'border-purple-500 bg-purple-500/20'
                          : 'border-white/10 bg-black/20 hover:border-white/30'
                      }`}
                    >
                      <span className="text-sm font-medium text-white block">{style.name}</span>
                      <span className="text-xs text-white/50">{style.description}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Preview & Generate */}
          <div className="space-y-4">
            {/* Preview Area */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-4">
              <h3 className="text-lg font-semibold text-white mb-3">Preview</h3>
              
              <div className="aspect-square bg-black/30 rounded-lg overflow-hidden flex items-center justify-center">
                {isGenerating ? (
                  <div className="text-center">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full mx-auto mb-3"
                    />
                    <p className="text-white/70">Generating...</p>
                  </div>
                ) : generatedImage ? (
                  <img
                    src={generatedImage}
                    alt="Generated"
                    className="w-full h-full object-cover"
                  />
                ) : selectedGalleryItem ? (
                  <img
                    src={selectedGalleryItem.image_url}
                    alt={selectedGalleryItem.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center p-4">
                    <FiImage className="w-16 h-16 text-white/20 mx-auto mb-2" />
                    <p className="text-white/40 text-sm">
                      {activeTab === 'gallery' ? 'Select an image' : 'Configure and generate'}
                    </p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              {(activeTab === 'character' || activeTab === 'scene') && (
                <div className="mt-4 space-y-2">
                  <Button
                    onClick={generateImage}
                    disabled={isGenerating}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                  >
                    <FiZap className="w-4 h-4 mr-2" />
                    {isGenerating ? 'Generating...' : 'Generate Image'}
                  </Button>
                  
                  {generatedImage && (
                    <div className="flex gap-2">
                      <Button
                        onClick={() => saveToGallery(generatedImage, character.name || 'Untitled')}
                        variant="outline"
                        className="flex-1 border-white/20 text-white hover:bg-white/10"
                      >
                        <FiSave className="w-4 h-4 mr-2" />
                        Save
                      </Button>
                      <Button
                        onClick={generateImage}
                        variant="outline"
                        className="border-white/20 text-white hover:bg-white/10"
                      >
                        <FiRefreshCw className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {/* Gallery Item Actions */}
              {activeTab === 'gallery' && selectedGalleryItem && (
                <div className="mt-4 space-y-2">
                  <Button
                    onClick={() => {
                      navigator.clipboard.writeText(selectedGalleryItem.image_url);
                      alert('Image URL copied!');
                    }}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    <FiCopy className="w-4 h-4 mr-2" />
                    Copy URL for Book
                  </Button>
                  <a
                    href={selectedGalleryItem.image_url}
                    download
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button
                      variant="outline"
                      className="w-full border-white/20 text-white hover:bg-white/10"
                    >
                      <FiDownload className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </a>
                </div>
              )}
            </div>

            {/* Prompt Preview */}
            {(activeTab === 'character' || activeTab === 'scene') && (
              <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-4">
                <h3 className="text-sm font-semibold text-white/70 mb-2">Generated Prompt</h3>
                <p className="text-xs text-white/50 leading-relaxed">
                  {activeTab === 'character' ? buildCharacterPrompt() : buildScenePrompt()}
                  , {ART_STYLES.find(s => s.id === selectedStyle)?.name || 'fantasy'} art style
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
