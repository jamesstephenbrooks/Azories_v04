import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  FiUser, FiImage, FiLayers, FiType, FiZap, FiGrid, 
  FiSave, FiDownload, FiPlus, FiTrash2, FiPlay,
  FiArrowLeft, FiFolder, FiSettings, FiCopy, FiRefreshCw,
  FiUpload, FiSliders, FiMaximize2, FiStar, FiMove, FiBook, FiX
} from 'react-icons/fi';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Custom Node Types

// Character Node - Define character traits - Resizable
const CharacterNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-purple-900/90 to-purple-800/90 rounded-xl border-2 ${selected ? 'border-purple-400' : 'border-purple-600/50'} shadow-xl backdrop-blur-sm w-[250px] h-[260px]`}>
      <Handle type="target" position={Position.Left} className="!bg-purple-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-purple-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-purple-500/30 flex items-center justify-center flex-shrink-0">
          <FiUser className="text-purple-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Character</h4>
        </div>
        {selected && (
          <span className="text-[9px] text-purple-300 bg-purple-500/20 px-1.5 py-0.5 rounded">DEL to remove</span>
        )}
      </div>
      
      <div className="p-2 space-y-2 overflow-auto h-[calc(100%-40px)]">
        <input
          type="text"
          placeholder="Character name..."
          value={data.name || ''}
          onChange={(e) => data.onChange?.('name', e.target.value)}
          className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-purple-500/30 text-white text-xs focus:outline-none focus:border-purple-400"
        />
        
        <div className="grid grid-cols-2 gap-2">
          <select 
            value={data.gender || 'Female'}
            onChange={(e) => data.onChange?.('gender', e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-purple-500/30 text-white text-xs"
          >
            <option value="Female">Female</option>
            <option value="Male">Male</option>
            <option value="Non-binary">Non-binary</option>
          </select>
          <select 
            value={data.age || 'Adult'}
            onChange={(e) => data.onChange?.('age', e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-purple-500/30 text-white text-xs"
          >
            <option value="Child">Child</option>
            <option value="Teen">Teen</option>
            <option value="Adult">Adult</option>
            <option value="Elder">Elder</option>
          </select>
        </div>
        
        <textarea
          placeholder="Appearance details..."
          value={data.appearance || ''}
          onChange={(e) => data.onChange?.('appearance', e.target.value)}
          className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-purple-500/30 text-white text-xs focus:outline-none focus:border-purple-400 resize-none"
          style={{ minHeight: '40px' }}
        />
        
        {/* Transparent background toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={data.transparentBg || false}
            onChange={(e) => data.onChange?.('transparentBg', e.target.checked)}
            className="w-3 h-3 rounded bg-black/30 border-purple-500/30 text-purple-500 focus:ring-purple-400"
          />
          <span className="text-[10px] text-purple-300">Transparent background (for compositing)</span>
        </label>
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-purple-400 !w-3 !h-3" />
    </div>
  );
};

// Scene Node - Define environment/setting - Fixed size
const SceneNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-emerald-900/90 to-emerald-800/90 rounded-xl border-2 ${selected ? 'border-emerald-400' : 'border-emerald-600/50'} shadow-xl backdrop-blur-sm w-[250px] h-[240px]`}>
      <Handle type="target" position={Position.Left} className="!bg-emerald-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-emerald-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-emerald-500/30 flex items-center justify-center flex-shrink-0">
          <FiLayers className="text-emerald-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Scene</h4>
        </div>
      </div>
      
      <div className="p-2 space-y-2 overflow-auto h-[calc(100%-40px)]">
        <select 
          value={data.preset || ''}
          onChange={(e) => data.onChange?.('preset', e.target.value)}
          className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-emerald-500/30 text-white text-xs"
        >
          <option value="">Custom scene...</option>
          <option value="forest">Enchanted Forest</option>
          <option value="castle">Castle Interior</option>
          <option value="beach">Tropical Beach</option>
          <option value="city">Modern City</option>
          <option value="space">Outer Space</option>
          <option value="underwater">Underwater</option>
          <option value="mountain">Mountain Peak</option>
          <option value="library">Ancient Library</option>
          <option value="dreamscape">Dreamscape</option>
          <option value="sunset-cliffs">Sunset Cliffs</option>
          <option value="aurora">Northern Lights</option>
          <option value="cherry-blossom">Cherry Blossom</option>
          <option value="ruins">Ancient Ruins</option>
          <option value="throne-room">Throne Room</option>
          <option value="tavern">Medieval Tavern</option>
          <option value="garden">Secret Garden</option>
          <option value="desert">Desert Oasis</option>
          <option value="crystal-cave">Crystal Cave</option>
          <option value="floating-islands">Floating Islands</option>
          <option value="moonlit-lake">Moonlit Lake</option>
          <option value="battlefield">Battlefield</option>
          <option value="village">Village Square</option>
          <option value="ship-deck">Ship Deck</option>
          <option value="academy">Magic Academy</option>
        </select>
        
        <textarea
          placeholder="Scene description..."
          value={data.description || ''}
          onChange={(e) => data.onChange?.('description', e.target.value)}
          className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-emerald-500/30 text-white text-xs focus:outline-none focus:border-emerald-400 resize-none"
          style={{ minHeight: '40px' }}
        />
        
        <div className="grid grid-cols-2 gap-2">
          <select 
            value={data.timeOfDay || 'day'}
            onChange={(e) => data.onChange?.('timeOfDay', e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-emerald-500/30 text-white text-xs"
          >
            <option value="dawn">Dawn</option>
            <option value="day">Day</option>
            <option value="sunset">Sunset</option>
            <option value="night">Night</option>
          </select>
          <select 
            value={data.mood || 'peaceful'}
            onChange={(e) => data.onChange?.('mood', e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-emerald-500/30 text-white text-xs"
          >
            <option value="peaceful">Peaceful</option>
            <option value="dramatic">Dramatic</option>
            <option value="mysterious">Mysterious</option>
            <option value="joyful">Joyful</option>
          </select>
        </div>
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-emerald-400 !w-3 !h-3" />
    </div>
  );
};

// Style Node - Art style selection with dropdown - Expanded with all styles (synced with Easy Mode)
const ALL_STYLE_CATEGORIES = [
  { category: 'Realistic', styles: ['realistic', 'portrait', 'cinematic', 'hyperrealistic'] },
  { category: 'Illustration', styles: ['cartoon', 'anime', 'manga', 'disney', 'pixar', 'chibi', 'comic', 'graphic-novel'] },
  { category: 'Traditional', styles: ['oil-painting', 'watercolor', 'acrylic', 'pastel', 'charcoal', 'pencil', 'ink', 'gouache'] },
  { category: 'Digital', styles: ['digital-art', 'concept-art', 'matte-painting', 'vector', 'low-poly', 'vaporwave', 'synthwave'] },
  { category: '3D', styles: ['3d-render', 'clay-render', 'isometric', 'diorama', 'unreal-engine'] },
  { category: 'Fantasy', styles: ['fantasy', 'ethereal-fantasy', 'dark-fantasy', 'sci-fi', 'cyberpunk', 'steampunk', 'solarpunk', 'surreal-dreamscape', 'luminous-ethereal', 'celestial-fantasy'] },
  { category: 'Children', styles: ['storybook', 'picture-book', 'whimsical', 'crayon', 'paper-cutout', 'felt'] },
  { category: 'Retro', styles: ['pixel-art', 'retro-game', 'vintage-poster', 'art-deco', 'art-nouveau', 'pop-art'] },
  { category: 'Cultural', styles: ['ukiyo-e', 'chinese-ink', 'persian-miniature', 'aboriginal', 'tribal', 'celtic'] },
  { category: 'Stylized', styles: ['minimalist', 'abstract', 'surreal', 'impressionist', 'expressionist', 'cubist'] }
];

const STYLE_LABELS = {
  'realistic': 'Realistic', 'portrait': 'Portrait', 'cinematic': 'Cinematic', 'hyperrealistic': 'Hyperreal',
  'cartoon': 'Cartoon', 'anime': 'Anime', 'manga': 'Manga', 'disney': 'Disney', 'pixar': 'Pixar',
  'chibi': 'Chibi', 'comic': 'Comic', 'graphic-novel': 'Graphic Novel',
  'oil-painting': 'Oil Paint', 'watercolor': 'Watercolor', 'acrylic': 'Acrylic', 'pastel': 'Pastel',
  'charcoal': 'Charcoal', 'pencil': 'Pencil', 'ink': 'Ink', 'gouache': 'Gouache',
  'digital-art': 'Digital', 'concept-art': 'Concept', 'matte-painting': 'Matte', 'vector': 'Vector',
  'low-poly': 'Low Poly', 'vaporwave': 'Vaporwave', 'synthwave': 'Synthwave',
  '3d-render': '3D Render', 'clay-render': 'Clay', 'isometric': 'Isometric', 'diorama': 'Diorama', 'unreal-engine': 'Game',
  'fantasy': 'Fantasy', 'ethereal-fantasy': 'Ethereal', 'dark-fantasy': 'Dark', 'sci-fi': 'Sci-Fi', 'cyberpunk': 'Cyberpunk',
  'steampunk': 'Steampunk', 'solarpunk': 'Solarpunk', 'surreal-dreamscape': 'Dreamscape', 'luminous-ethereal': 'Luminous', 'celestial-fantasy': 'Celestial',
  'storybook': 'Storybook', 'picture-book': 'Picture', 'whimsical': 'Whimsical', 'crayon': 'Crayon',
  'paper-cutout': 'Paper', 'felt': 'Felt',
  'pixel-art': 'Pixel', 'retro-game': 'Retro', 'vintage-poster': 'Vintage', 'art-deco': 'Art Deco',
  'art-nouveau': 'Nouveau', 'pop-art': 'Pop Art',
  'ukiyo-e': 'Ukiyo-e', 'chinese-ink': 'Chinese', 'persian-miniature': 'Persian', 'aboriginal': 'Aboriginal',
  'tribal': 'Tribal', 'celtic': 'Celtic',
  'minimalist': 'Minimal', 'abstract': 'Abstract', 'surreal': 'Surreal', 'impressionist': 'Impress.',
  'expressionist': 'Express.', 'cubist': 'Cubist'
};

// Flatten all styles for dropdown
const ALL_STYLES_FLAT = ALL_STYLE_CATEGORIES.flatMap(cat => 
  cat.styles.map(s => ({ id: s, label: STYLE_LABELS[s], category: cat.category }))
);

const StyleNode = ({ data, selected }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredStyles = searchTerm 
    ? ALL_STYLES_FLAT.filter(s => 
        s.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.category.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : ALL_STYLES_FLAT;
  
  // Group by category for display
  const groupedStyles = filteredStyles.reduce((acc, style) => {
    if (!acc[style.category]) acc[style.category] = [];
    acc[style.category].push(style);
    return acc;
  }, {});
  
  return (
    <div className={`bg-gradient-to-br from-amber-900/90 to-amber-800/90 rounded-xl border-2 ${selected ? 'border-amber-400' : 'border-amber-600/50'} shadow-xl backdrop-blur-sm min-w-[200px]`}>
      <Handle type="target" position={Position.Left} className="!bg-amber-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-amber-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-amber-500/30 flex items-center justify-center flex-shrink-0">
          <FiSliders className="text-amber-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Art Style</h4>
        </div>
      </div>
      
      <div className="p-2">
        {/* Custom dropdown trigger */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 rounded-lg bg-black/40 border border-amber-500/30 text-white text-xs text-left flex items-center justify-between hover:border-amber-400 transition-colors"
        >
          <span>{STYLE_LABELS[data.style] || 'Select style...'}</span>
          <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {/* Dropdown menu */}
        {isOpen && (
          <div className="absolute z-50 mt-1 w-56 bg-[#1a1520] border border-amber-500/30 rounded-lg shadow-xl max-h-64 overflow-hidden">
            {/* Search input */}
            <div className="p-2 border-b border-amber-500/20">
              <input
                type="text"
                placeholder="Search styles..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-2 py-1.5 rounded bg-black/30 border border-amber-500/20 text-white text-xs focus:outline-none focus:border-amber-400"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
            
            {/* Styles list grouped by category */}
            <div className="max-h-48 overflow-y-auto">
              {Object.entries(groupedStyles).map(([category, styles]) => (
                <div key={category}>
                  <div className="px-2 py-1 text-[10px] font-semibold text-amber-400 uppercase tracking-wider bg-black/20 sticky top-0">
                    {category}
                  </div>
                  {styles.map(style => (
                    <button
                      key={style.id}
                      onClick={() => {
                        data.onChange?.('style', style.id);
                        setIsOpen(false);
                        setSearchTerm('');
                      }}
                      className={`w-full px-3 py-1.5 text-left text-xs transition-colors ${
                        data.style === style.id 
                          ? 'bg-amber-500/30 text-white' 
                          : 'text-white/70 hover:bg-amber-500/20 hover:text-white'
                      }`}
                    >
                      {style.label}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-amber-400 !w-3 !h-3" />
    </div>
  );
};

// Reference Image Node - Fixed small size (no resizing to avoid errors)
const ReferenceNode = ({ data, selected }) => {
  const fileInputRef = useRef(null);
  
  const handleUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        data.onChange?.('image', reader.result);
      };
      reader.readAsDataURL(file);
    }
  };
  
  return (
    <div className={`bg-gradient-to-br from-cyan-900/90 to-cyan-800/90 rounded-xl border-2 ${selected ? 'border-cyan-400' : 'border-cyan-600/50'} shadow-xl backdrop-blur-sm w-[160px] h-[180px]`}>
      <Handle type="target" position={Position.Left} className="!bg-cyan-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-cyan-600/30 flex items-center gap-2">
        <div className="w-5 h-5 rounded-lg bg-cyan-500/30 flex items-center justify-center flex-shrink-0">
          <FiImage className="text-cyan-300 w-3 h-3" />
        </div>
        <h4 className="text-xs font-semibold text-white truncate flex-1">Reference</h4>
      </div>
      
      <div className="p-2 h-[130px]">
        {data.image ? (
          <div className="relative w-full h-full">
            <img 
              src={data.image} 
              alt="Reference" 
              className="w-full h-full object-cover rounded-lg"
            />
            <button
              onClick={() => data.onChange?.('image', null)}
              className="absolute top-1 right-1 p-1 bg-red-500 rounded-full hover:bg-red-600 z-10"
            >
              <FiTrash2 className="w-2 h-2 text-white" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full h-full border-2 border-dashed border-cyan-500/30 rounded-lg flex flex-col items-center justify-center hover:border-cyan-400 transition-colors"
          >
            <FiUpload className="w-5 h-5 text-cyan-400 mb-1" />
            <span className="text-[10px] text-cyan-300">Upload</span>
          </button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleUpload}
          className="hidden"
        />
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-cyan-400 !w-3 !h-3" />
    </div>
  );
};

// Prompt Node - Custom text prompt
const PromptNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-rose-900/90 to-rose-800/90 rounded-xl border-2 ${selected ? 'border-rose-400' : 'border-rose-600/50'} shadow-xl min-w-[280px] backdrop-blur-sm`}>
      <Handle type="target" position={Position.Left} className="!bg-rose-400 !w-3 !h-3" />
      
      <div className="p-3 border-b border-rose-600/30 flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-rose-500/30 flex items-center justify-center">
          <FiType className="text-rose-300" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-white">Prompt</h4>
          <p className="text-xs text-rose-300">Custom text</p>
        </div>
      </div>
      
      <div className="p-3">
        <textarea
          placeholder="Add custom prompt details..."
          value={data.text || ''}
          onChange={(e) => data.onChange?.('text', e.target.value)}
          rows={3}
          className="w-full px-3 py-2 rounded-lg bg-black/30 border border-rose-500/30 text-white text-xs focus:outline-none focus:border-rose-400 resize-none"
        />
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-rose-400 !w-3 !h-3" />
    </div>
  );
};

// Combine Node - Merge multiple inputs
const CombineNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-violet-900/90 to-violet-800/90 rounded-xl border-2 ${selected ? 'border-violet-400' : 'border-violet-600/50'} shadow-xl min-w-[120px] backdrop-blur-sm`}>
      <Handle type="target" position={Position.Left} id="a" className="!bg-violet-400 !w-3 !h-3" style={{ top: '30%' }} />
      <Handle type="target" position={Position.Left} id="b" className="!bg-violet-400 !w-3 !h-3" style={{ top: '50%' }} />
      <Handle type="target" position={Position.Left} id="c" className="!bg-violet-400 !w-3 !h-3" style={{ top: '70%' }} />
      
      <div className="p-3 flex items-center justify-center">
        <div className="w-10 h-10 rounded-lg bg-violet-500/30 flex items-center justify-center">
          <FiGrid className="text-violet-300 w-5 h-5" />
        </div>
      </div>
      <div className="pb-2 text-center">
        <span className="text-xs text-violet-300">Combine</span>
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-violet-400 !w-3 !h-3" />
    </div>
  );
};

// Output Node - Fixed size with expand preview option
const OutputNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-pink-900/90 to-pink-800/90 rounded-xl border-2 ${selected ? 'border-pink-400' : 'border-pink-600/50'} shadow-xl backdrop-blur-sm w-[220px] h-[240px]`}>
      <Handle type="target" position={Position.Left} className="!bg-pink-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-pink-600/30 flex items-center gap-2">
        <div className="w-5 h-5 rounded-lg bg-pink-500/30 flex items-center justify-center flex-shrink-0">
          <FiZap className="text-pink-300 w-3 h-3" />
        </div>
        <h4 className="text-xs font-semibold text-white flex-1">Output</h4>
      </div>
      
      <div className="p-2 h-[190px]">
        {data.generating ? (
          <div className="w-full h-full bg-black/30 rounded-lg flex flex-col items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-10 h-10 border-4 border-pink-500/30 border-t-pink-500 rounded-full"
            />
            <span className="text-xs text-pink-300 mt-2">Generating...</span>
          </div>
        ) : data.image ? (
          <div className="relative w-full h-full">
            <img 
              src={data.image} 
              alt="Generated" 
              className="w-full h-full object-cover rounded-lg"
            />
            {/* Action buttons */}
            <div className="absolute bottom-2 left-2 right-2 flex gap-1 justify-center">
              <button
                onClick={() => data.onExpand?.(data.image)}
                className="p-1.5 bg-blue-600/80 rounded-lg hover:bg-blue-600 flex-1 flex items-center justify-center"
                title="Expand Preview"
              >
                <FiMaximize2 className="w-3 h-3 text-white" />
              </button>
              <button
                onClick={() => data.onSaveToGallery?.(data.image)}
                className="p-1.5 bg-green-600/80 rounded-lg hover:bg-green-600 flex-1 flex items-center justify-center"
                title="Save to Gallery"
              >
                <FiSave className="w-3 h-3 text-white" />
              </button>
              <button
                onClick={() => data.onDownload?.(data.image)}
                className="p-1.5 bg-purple-600/80 rounded-lg hover:bg-purple-600 flex-1 flex items-center justify-center"
                title="Download"
              >
                <FiDownload className="w-3 h-3 text-white" />
              </button>
            </div>
          </div>
        ) : (
          <div className="w-full h-full bg-black/30 rounded-lg flex flex-col items-center justify-center">
            <FiImage className="w-8 h-8 text-pink-300/30 mb-2" />
            <span className="text-[10px] text-pink-300/50 text-center px-2">Run workflow to generate</span>
          </div>
        )}
      </div>
    </div>
  );
};

// Define node types
const nodeTypes = {
  character: CharacterNode,
  scene: SceneNode,
  style: StyleNode,
  reference: ReferenceNode,
  prompt: PromptNode,
  combine: CombineNode,
  output: OutputNode
};

// Initial nodes for new workflow
const defaultNodes = [
  {
    id: 'character-1',
    type: 'character',
    position: { x: 50, y: 50 },
    data: { name: '', gender: 'Female', age: 'Adult', appearance: '' }
  },
  {
    id: 'style-1',
    type: 'style',
    position: { x: 50, y: 350 },
    data: { style: 'fantasy' }
  },
  {
    id: 'combine-1',
    type: 'combine',
    position: { x: 400, y: 150 },
    data: {}
  },
  {
    id: 'output-1',
    type: 'output',
    position: { x: 600, y: 100 },
    data: { image: null, generating: false }
  }
];

const defaultEdges = [
  { id: 'e1', source: 'character-1', target: 'combine-1', targetHandle: 'a', animated: true },
  { id: 'e2', source: 'style-1', target: 'combine-1', targetHandle: 'b', animated: true },
  { id: 'e3', source: 'combine-1', target: 'output-1', animated: true }
];

export default function ArtStudioExpert() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(defaultEdges);
  const [isGenerating, setIsGenerating] = useState(false);
  const [savedWorkflows, setSavedWorkflows] = useState([]);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [userBooks, setUserBooks] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState('general');
  const [expandedImage, setExpandedImage] = useState(null); // For full-size preview modal
  
  // Load user's books
  useEffect(() => {
    if (token) {
      loadUserBooks();
    }
  }, [token]);
  
  // Import character from Easy Mode if URL param exists
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('import') === 'character') {
      const exportData = localStorage.getItem('artStudioExport');
      if (exportData) {
        try {
          const data = JSON.parse(exportData);
          if (data.character) {
            // Update the character node with imported data
            setNodes(nds => nds.map(node => {
              if (node.type === 'character') {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    name: data.character.name || '',
                    gender: data.character.gender || 'Female',
                    age: data.character.ageGroup || 'Adult',
                    description: data.character.additionalDetails || '',
                    onChange: (k, v) => updateNodeData(node.id, k, v)
                  }
                };
              }
              if (node.type === 'style' && data.style) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    style: data.style,
                    onChange: (k, v) => updateNodeData(node.id, k, v)
                  }
                };
              }
              if (node.type === 'reference' && data.referenceImage) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    image: data.referenceImage,
                    onChange: (k, v) => updateNodeData(node.id, k, v)
                  }
                };
              }
              return node;
            }));
            
            // Clear the export data
            localStorage.removeItem('artStudioExport');
            
            // Remove the URL param
            window.history.replaceState({}, '', '/art-studio/expert');
          }
        } catch (e) {
          console.error('Failed to import character data:', e);
        }
      }
    }
  }, []);
  
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
  
  // Node data change handler
  const updateNodeData = useCallback((nodeId, key, value) => {
    setNodes(nds => nds.map(node => {
      if (node.id === nodeId) {
        return {
          ...node,
          data: {
            ...node.data,
            [key]: value,
            onChange: (k, v) => updateNodeData(nodeId, k, v)
          }
        };
      }
      return node;
    }));
  }, [setNodes]);
  
  // Initialize nodes with onChange handlers
  useEffect(() => {
    setNodes(nds => nds.map(node => ({
      ...node,
      data: {
        ...node.data,
        onChange: (k, v) => updateNodeData(node.id, k, v)
      }
    })));
  }, []);
  
  const onConnect = useCallback((params) => {
    setEdges(eds => addEdge({ ...params, animated: true }, eds));
  }, [setEdges]);
  
  // Delete selected nodes
  const deleteSelectedNodes = useCallback(() => {
    setNodes(nds => nds.filter(node => !node.selected));
    setEdges(eds => eds.filter(edge => {
      const sourceExists = nodes.find(n => n.id === edge.source && !n.selected);
      const targetExists = nodes.find(n => n.id === edge.target && !n.selected);
      return sourceExists && targetExists;
    }));
  }, [setNodes, setEdges, nodes]);
  
  // Handle keyboard shortcuts for deletion
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.key === 'Delete' || e.key === 'Backspace') && !e.target.matches('input, textarea')) {
        deleteSelectedNodes();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [deleteSelectedNodes]);
  
  // Add new node
  const addNode = (type) => {
    const newNode = {
      id: `${type}-${Date.now()}`,
      type,
      position: { x: Math.random() * 300 + 100, y: Math.random() * 200 + 100 },
      data: getDefaultDataForType(type)
    };
    newNode.data.onChange = (k, v) => updateNodeData(newNode.id, k, v);
    setNodes(nds => [...nds, newNode]);
  };
  
  const getDefaultDataForType = (type) => {
    switch (type) {
      case 'character': return { name: '', gender: 'Female', age: 'Adult', appearance: '' };
      case 'scene': return { preset: '', description: '', timeOfDay: 'day', mood: 'peaceful' };
      case 'style': return { style: 'fantasy' };
      case 'reference': return { image: null };
      case 'prompt': return { text: '' };
      case 'combine': return {};
      case 'output': return { image: null, generating: false };
      default: return {};
    }
  };
  
  // Build prompt from connected nodes
  const buildPromptFromWorkflow = () => {
    const outputNode = nodes.find(n => n.type === 'output');
    if (!outputNode) return { prompt: '', transparentBg: false };
    
    const getConnectedNodes = (targetId) => {
      const connectedEdges = edges.filter(e => e.target === targetId);
      return connectedEdges.map(e => nodes.find(n => n.id === e.source)).filter(Boolean);
    };
    
    let hasTransparentBg = false;
    
    const processNode = (node) => {
      if (!node) return '';
      
      if (node.type === 'combine') {
        const inputs = getConnectedNodes(node.id);
        return inputs.map(processNode).filter(Boolean).join(', ');
      }
      
      if (node.type === 'character') {
        const parts = [];
        if (node.data.name) parts.push(node.data.name);
        if (node.data.gender) parts.push(node.data.gender.toLowerCase() + ' character');
        if (node.data.age) parts.push(node.data.age.toLowerCase());
        if (node.data.appearance) parts.push(node.data.appearance);
        // Check for transparent background
        if (node.data.transparentBg) {
          hasTransparentBg = true;
          parts.push('isolated on transparent background, no background, PNG cutout style');
        }
        return parts.join(', ');
      }
      
      if (node.type === 'scene') {
        const parts = [];
        if (node.data.preset) parts.push(node.data.preset + ' setting');
        if (node.data.description) parts.push(node.data.description);
        if (node.data.timeOfDay) parts.push(node.data.timeOfDay + ' time');
        if (node.data.mood) parts.push(node.data.mood + ' atmosphere');
        return parts.join(', ');
      }
      
      if (node.type === 'style') {
        return `${node.data.style || 'fantasy'} art style`;
      }
      
      if (node.type === 'prompt') {
        return node.data.text || '';
      }
      
      return '';
    };
    
    const connectedToOutput = getConnectedNodes(outputNode.id);
    const promptParts = connectedToOutput.map(processNode).filter(Boolean);
    
    return {
      prompt: promptParts.join(', ') + ', highly detailed, professional illustration',
      transparentBg: hasTransparentBg
    };
  };
  
  // Run the workflow
  const runWorkflow = async () => {
    if (!token) {
      navigate('/login');
      return;
    }
    
    const prompt = buildPromptFromWorkflow();
    console.log('Built prompt:', prompt);
    
    if (!prompt || prompt === ', highly detailed, professional illustration') {
      alert('Please add some nodes and connect them to the output. Make sure Character or Scene nodes have content.');
      return;
    }
    
    setIsGenerating(true);
    
    // Update output node to show generating state
    setNodes(nds => nds.map(node => {
      if (node.type === 'output') {
        return { ...node, data: { ...node.data, generating: true, image: null } };
      }
      return node;
    }));
    
    try {
      console.log('Sending request to API...');
      const response = await fetch(`${API_URL}/api/art-studio/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt,
          style: nodes.find(n => n.type === 'style')?.data?.style || 'fantasy',
          type: 'workflow',
          bookId: selectedBookId !== 'general' ? selectedBookId : null,
          workflowName: workflowName
        })
      });
      
      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Generation successful, image received');
        
        // Update output node with result
        setNodes(nds => nds.map(node => {
          if (node.type === 'output') {
            return {
              ...node,
              data: {
                ...node.data,
                generating: false,
                image: data.image_url,
                onDownload: (url) => downloadImage(url),
                onSaveToGallery: (url) => saveToGallery(url),
                onExpand: (url) => setExpandedImage(url)
              }
            };
          }
          return node;
        }));
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Generation failed:', errorData);
        throw new Error(errorData.detail || 'Generation failed');
      }
    } catch (error) {
      console.error('Workflow error:', error);
      alert(`Failed to generate image: ${error.message}`);
      
      setNodes(nds => nds.map(node => {
        if (node.type === 'output') {
          return { ...node, data: { ...node.data, generating: false } };
        }
        return node;
      }));
    } finally {
      setIsGenerating(false);
    }
  };
  
  const downloadImage = (url) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = `azories-workflow-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // Save image to Art Studio gallery
  const saveToGallery = async (imageUrl) => {
    try {
      const characterNode = nodes.find(n => n.type === 'character');
      const sceneNode = nodes.find(n => n.type === 'scene');
      const styleNode = nodes.find(n => n.type === 'style');
      
      const response = await fetch(`${API_URL}/api/art-studio/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: imageUrl,
          name: characterNode?.data?.name || sceneNode?.data?.name || 'Workflow Generation',
          type: characterNode ? 'character' : 'scene',
          style: styleNode?.data?.style || 'fantasy',
          bookId: selectedBookId !== 'general' ? selectedBookId : null,
          characterData: characterNode?.data || null,
          sceneData: sceneNode?.data || null
        })
      });
      
      if (response.ok) {
        alert('Image saved to gallery!');
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Failed to save image to gallery');
    }
  };
  
  // Save workflow
  const saveWorkflow = async () => {
    try {
      const workflow = {
        name: workflowName,
        nodes: nodes.map(n => ({ ...n, data: { ...n.data, onChange: undefined, onDownload: undefined } })),
        edges,
        bookId: selectedBookId !== 'general' ? selectedBookId : null
      };
      
      const response = await fetch(`${API_URL}/api/art-studio/workflow/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(workflow)
      });
      
      if (response.ok) {
        alert('Workflow saved!');
        loadWorkflows();
      }
    } catch (error) {
      console.error('Save error:', error);
    }
  };
  
  // Load workflows
  const loadWorkflows = async () => {
    try {
      const response = await fetch(`${API_URL}/api/art-studio/workflows`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSavedWorkflows(data.workflows || []);
      }
    } catch (error) {
      console.error('Load error:', error);
    }
  };
  
  useEffect(() => {
    if (token) loadWorkflows();
  }, [token]);
  
  // Node palette items
  const nodeTypes_palette = [
    { type: 'character', icon: FiUser, label: 'Character', color: 'purple' },
    { type: 'scene', icon: FiLayers, label: 'Scene', color: 'emerald' },
    { type: 'style', icon: FiSliders, label: 'Style', color: 'amber' },
    { type: 'reference', icon: FiImage, label: 'Reference', color: 'cyan' },
    { type: 'prompt', icon: FiType, label: 'Prompt', color: 'rose' },
    { type: 'combine', icon: FiGrid, label: 'Combine', color: 'violet' },
    { type: 'output', icon: FiZap, label: 'Output', color: 'pink' }
  ];
  
  return (
    <div className="h-screen bg-gradient-to-br from-[#0a0a12] to-[#1a1025] flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/30 backdrop-blur-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/art-studio')}
            className="text-white/70 hover:text-white"
          >
            <FiArrowLeft className="w-5 h-5 mr-2" />
            Back to Easy Mode
          </Button>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <FiStar className="text-amber-400" />
              Expert Studio
            </h1>
            <p className="text-xs text-white/50">Node-based workflow editor</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Book Assignment */}
          <div className="flex items-center gap-2">
            <FiBook className="text-purple-400 w-4 h-4" />
            <Select value={selectedBookId} onValueChange={setSelectedBookId}>
              <SelectTrigger className="w-40 bg-black/30 border-white/20 text-white text-xs">
                <SelectValue placeholder="Assign to..." />
              </SelectTrigger>
              <SelectContent className="bg-[#1a1520] border-white/20">
                <SelectItem value="general" className="text-white hover:bg-white/10 text-xs">
                  📁 General Library
                </SelectItem>
                {userBooks.map(book => (
                  <SelectItem key={book.id} value={book.id} className="text-white hover:bg-white/10 text-xs">
                    📖 {book.title?.substring(0, 20)}...
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <Input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="w-40 bg-black/30 border-white/20 text-white text-sm"
            placeholder="Workflow name..."
          />
          <Button 
            variant="outline" 
            onClick={saveWorkflow}
            className="border-white/20 text-white"
          >
            <FiSave className="w-4 h-4 mr-2" />
            Save
          </Button>
          <Button 
            onClick={runWorkflow}
            disabled={isGenerating}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
          >
            <FiPlay className="w-4 h-4 mr-2" />
            {isGenerating ? 'Running...' : 'Run Workflow'}
          </Button>
        </div>
      </header>
      
      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Node Palette */}
        <div className="w-16 bg-black/30 border-r border-white/10 p-2 space-y-2">
          {nodeTypes_palette.map(item => (
            <button
              key={item.type}
              onClick={() => addNode(item.type)}
              className={`w-full aspect-square rounded-lg bg-${item.color}-500/20 hover:bg-${item.color}-500/40 flex flex-col items-center justify-center gap-1 transition-colors group`}
              title={item.label}
            >
              <item.icon className={`w-5 h-5 text-${item.color}-400`} />
              <span className="text-[10px] text-white/60 group-hover:text-white">{item.label}</span>
            </button>
          ))}
        </div>
        
        {/* React Flow Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            className="bg-transparent"
          >
            <Background color="#333" gap={20} />
            <Controls className="!bg-black/50 !border-white/10" />
            <MiniMap 
              className="!bg-black/50 !border-white/10"
              nodeColor={(node) => {
                const colors = {
                  character: '#a855f7',
                  scene: '#10b981',
                  style: '#f59e0b',
                  reference: '#06b6d4',
                  prompt: '#f43f5e',
                  combine: '#8b5cf6',
                  output: '#ec4899'
                };
                return colors[node.type] || '#888';
              }}
            />
            
            <Panel position="bottom-left" className="!bg-black/50 !border-white/10 rounded-lg p-2">
              <p className="text-xs text-white/50">
                Drag nodes • Connect handles • Run workflow
              </p>
            </Panel>
          </ReactFlow>
        </div>
      </div>
      
      {/* Expanded Image Preview Modal */}
      <AnimatePresence>
        {expandedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8"
            onClick={() => setExpandedImage(null)}
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.8 }}
              className="relative max-w-4xl max-h-[90vh]"
              onClick={(e) => e.stopPropagation()}
            >
              <img 
                src={expandedImage} 
                alt="Full size preview" 
                className="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
              />
              <button
                onClick={() => setExpandedImage(null)}
                className="absolute top-2 right-2 p-2 bg-black/70 hover:bg-black rounded-full text-white"
              >
                <FiX className="w-5 h-5" />
              </button>
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3">
                <Button
                  onClick={() => saveToGallery(expandedImage)}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <FiSave className="w-4 h-4 mr-2" />
                  Save to Gallery
                </Button>
                <Button
                  onClick={() => downloadImage(expandedImage)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <FiDownload className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
