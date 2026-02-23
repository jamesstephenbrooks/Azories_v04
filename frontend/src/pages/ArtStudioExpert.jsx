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
  FiUpload, FiSliders, FiMaximize2, FiStar, FiMove, FiBook, FiX,
  FiList, FiClock, FiCheck
} from 'react-icons/fi';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Custom Node Types

// Delete button component for nodes
const NodeDeleteButton = ({ onDelete }) => (
  <button
    onClick={(e) => {
      e.stopPropagation();
      onDelete?.();
    }}
    className="absolute top-0.5 right-0.5 w-3 h-3 rounded-full bg-red-500/80 hover:bg-red-500 flex items-center justify-center transition-colors z-10"
    title="Delete node"
    data-testid="node-delete-btn"
  >
    <FiX className="w-2 h-2 text-white" />
  </button>
);

// Character Node - Define character traits - Resizable
const CharacterNode = ({ data, selected }) => {
  return (
    <div className={`relative bg-gradient-to-br from-purple-900/90 to-purple-800/90 rounded-xl border-2 ${selected ? 'border-purple-400' : 'border-purple-600/50'} shadow-xl backdrop-blur-sm w-[250px] h-[260px]`}>
      <Handle type="target" position={Position.Left} className="!bg-purple-400 !w-3 !h-3" />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      {/* Copy button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          data.onCopyNode?.();
        }}
        className="absolute top-0.5 right-5 w-4 h-4 rounded bg-blue-500/80 hover:bg-blue-500 flex items-center justify-center transition-colors z-10"
        title="Duplicate node"
        data-testid="character-node-copy-btn"
      >
        <FiCopy className="w-2.5 h-2.5 text-white" />
      </button>
      
      <div className="p-2 border-b border-purple-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-purple-500/30 flex items-center justify-center flex-shrink-0">
          <FiUser className="text-purple-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Character</h4>
        </div>
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
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-purple-500/30 text-white text-xs appearance-none"
            style={{ colorScheme: 'dark' }}
          >
            <option value="Female" className="bg-[#1a1520] text-white">Female</option>
            <option value="Male" className="bg-[#1a1520] text-white">Male</option>
            <option value="Non-binary" className="bg-[#1a1520] text-white">Non-binary</option>
          </select>
          <select 
            value={data.age || 'Adult'}
            onChange={(e) => data.onChange?.('age', e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-purple-500/30 text-white text-xs appearance-none"
            style={{ colorScheme: 'dark' }}
          >
            <option value="Child" className="bg-[#1a1520] text-white">Child</option>
            <option value="Teen" className="bg-[#1a1520] text-white">Teen</option>
            <option value="Adult" className="bg-[#1a1520] text-white">Adult</option>
            <option value="Elder" className="bg-[#1a1520] text-white">Elder</option>
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
    <div className={`relative bg-gradient-to-br from-emerald-900/90 to-emerald-800/90 rounded-xl border-2 ${selected ? 'border-emerald-400' : 'border-emerald-600/50'} shadow-xl backdrop-blur-sm w-[250px] h-[240px]`}>
      <Handle type="target" position={Position.Left} className="!bg-emerald-400 !w-3 !h-3" />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      {/* Copy button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          data.onCopyNode?.();
        }}
        className="absolute top-0.5 right-5 w-4 h-4 rounded bg-blue-500/80 hover:bg-blue-500 flex items-center justify-center transition-colors z-10"
        title="Duplicate node"
        data-testid="scene-node-copy-btn"
      >
        <FiCopy className="w-2.5 h-2.5 text-white" />
      </button>
      
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
          className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-emerald-500/30 text-white text-xs appearance-none"
          style={{ colorScheme: 'dark' }}
        >
          <option value="" className="bg-[#1a1520] text-white">Custom scene...</option>
          <option value="forest" className="bg-[#1a1520] text-white">Enchanted Forest</option>
          <option value="castle" className="bg-[#1a1520] text-white">Castle Interior</option>
          <option value="beach" className="bg-[#1a1520] text-white">Tropical Beach</option>
          <option value="city" className="bg-[#1a1520] text-white">Modern City</option>
          <option value="space" className="bg-[#1a1520] text-white">Outer Space</option>
          <option value="underwater" className="bg-[#1a1520] text-white">Underwater</option>
          <option value="mountain" className="bg-[#1a1520] text-white">Mountain Peak</option>
          <option value="library" className="bg-[#1a1520] text-white">Ancient Library</option>
          <option value="dreamscape" className="bg-[#1a1520] text-white">Dreamscape</option>
          <option value="sunset-cliffs" className="bg-[#1a1520] text-white">Sunset Cliffs</option>
          <option value="aurora" className="bg-[#1a1520] text-white">Northern Lights</option>
          <option value="cherry-blossom" className="bg-[#1a1520] text-white">Cherry Blossom</option>
          <option value="ruins" className="bg-[#1a1520] text-white">Ancient Ruins</option>
          <option value="throne-room" className="bg-[#1a1520] text-white">Throne Room</option>
          <option value="tavern" className="bg-[#1a1520] text-white">Medieval Tavern</option>
          <option value="garden" className="bg-[#1a1520] text-white">Secret Garden</option>
          <option value="desert" className="bg-[#1a1520] text-white">Desert Oasis</option>
          <option value="crystal-cave" className="bg-[#1a1520] text-white">Crystal Cave</option>
          <option value="floating-islands" className="bg-[#1a1520] text-white">Floating Islands</option>
          <option value="moonlit-lake" className="bg-[#1a1520] text-white">Moonlit Lake</option>
          <option value="battlefield" className="bg-[#1a1520] text-white">Battlefield</option>
          <option value="village" className="bg-[#1a1520] text-white">Village Square</option>
          <option value="ship-deck" className="bg-[#1a1520] text-white">Ship Deck</option>
          <option value="academy" className="bg-[#1a1520] text-white">Magic Academy</option>
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
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-emerald-500/30 text-white text-xs appearance-none"
            style={{ colorScheme: 'dark' }}
          >
            <option value="dawn" className="bg-[#1a1520] text-white">Dawn</option>
            <option value="day" className="bg-[#1a1520] text-white">Day</option>
            <option value="sunset" className="bg-[#1a1520] text-white">Sunset</option>
            <option value="night" className="bg-[#1a1520] text-white">Night</option>
          </select>
          <select 
            value={data.mood || 'peaceful'}
            onChange={(e) => data.onChange?.('mood', e.target.value)}
            className="px-2 py-1.5 rounded-lg bg-black/30 border border-emerald-500/30 text-white text-xs appearance-none"
            style={{ colorScheme: 'dark' }}
          >
            <option value="peaceful" className="bg-[#1a1520] text-white">Peaceful</option>
            <option value="dramatic" className="bg-[#1a1520] text-white">Dramatic</option>
            <option value="mysterious" className="bg-[#1a1520] text-white">Mysterious</option>
            <option value="joyful" className="bg-[#1a1520] text-white">Joyful</option>
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
    <div className={`relative bg-gradient-to-br from-amber-900/90 to-amber-800/90 rounded-xl border-2 ${selected ? 'border-amber-400' : 'border-amber-600/50'} shadow-xl backdrop-blur-sm min-w-[200px]`}>
      <Handle type="target" position={Position.Left} className="!bg-amber-400 !w-3 !h-3" />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      {/* Copy button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          data.onCopyNode?.();
        }}
        className="absolute top-0.5 right-5 w-4 h-4 rounded bg-blue-500/80 hover:bg-blue-500 flex items-center justify-center transition-colors z-10"
        title="Duplicate node"
        data-testid="style-node-copy-btn"
      >
        <FiCopy className="w-2.5 h-2.5 text-white" />
      </button>
      
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
    <div className={`relative bg-gradient-to-br from-cyan-900/90 to-cyan-800/90 rounded-xl border-2 ${selected ? 'border-cyan-400' : 'border-cyan-600/50'} shadow-xl backdrop-blur-sm w-[160px] h-[180px]`}>
      <Handle type="target" position={Position.Left} className="!bg-cyan-400 !w-3 !h-3" />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      {/* Copy button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          data.onCopyNode?.();
        }}
        className="absolute top-0.5 right-5 w-4 h-4 rounded bg-blue-500/80 hover:bg-blue-500 flex items-center justify-center transition-colors z-10"
        title="Duplicate node"
        data-testid="reference-node-copy-btn"
      >
        <FiCopy className="w-2.5 h-2.5 text-white" />
      </button>
      
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
    <div className={`relative bg-gradient-to-br from-rose-900/90 to-rose-800/90 rounded-xl border-2 ${selected ? 'border-rose-400' : 'border-rose-600/50'} shadow-xl min-w-[280px] backdrop-blur-sm`}>
      <Handle type="target" position={Position.Left} className="!bg-rose-400 !w-3 !h-3" />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      {/* Copy button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          data.onCopyNode?.();
        }}
        className="absolute top-0.5 right-5 w-4 h-4 rounded bg-blue-500/80 hover:bg-blue-500 flex items-center justify-center transition-colors z-10"
        title="Duplicate node"
        data-testid="prompt-node-copy-btn"
      >
        <FiCopy className="w-2.5 h-2.5 text-white" />
      </button>
      
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
    <div className={`relative bg-gradient-to-br from-violet-900/90 to-violet-800/90 rounded-xl border-2 ${selected ? 'border-violet-400' : 'border-violet-600/50'} shadow-xl min-w-[120px] backdrop-blur-sm`}>
      {/* Multiple input handles - a, b, c, d for flexibility */}
      <Handle type="target" position={Position.Left} id="a" className="!bg-violet-400 !w-3 !h-3" style={{ top: '20%' }} />
      <Handle type="target" position={Position.Left} id="b" className="!bg-violet-400 !w-3 !h-3" style={{ top: '40%' }} />
      <Handle type="target" position={Position.Left} id="c" className="!bg-violet-400 !w-3 !h-3" style={{ top: '60%' }} />
      <Handle type="target" position={Position.Left} id="d" className="!bg-violet-400 !w-3 !h-3" style={{ top: '80%' }} />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      <div className="p-3 flex items-center justify-center">
        <div className="w-10 h-10 rounded-lg bg-violet-500/30 flex items-center justify-center">
          <FiGrid className="text-violet-300 w-5 h-5" />
        </div>
      </div>
      <div className="pb-2 text-center">
        <span className="text-xs text-violet-300">Combine</span>
        <p className="text-[9px] text-violet-400/50">4 inputs</p>
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-violet-400 !w-3 !h-3" />
    </div>
  );
};

// Image Node - For workflow continuation or manual image upload
const ImageNode = ({ data, selected }) => {
  const fileInputRef = useRef(null);
  
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      data.onChange?.('image', event.target.result);
      data.onChange?.('label', file.name.split('.')[0] || 'Uploaded Image');
    };
    reader.readAsDataURL(file);
  };
  
  return (
    <div className={`relative bg-gradient-to-br from-yellow-900/90 to-orange-800/90 rounded-xl border-2 ${selected ? 'border-yellow-400' : 'border-yellow-600/50'} shadow-xl backdrop-blur-sm w-[180px]`}>
      <Handle type="target" position={Position.Left} className="!bg-yellow-400 !w-3 !h-3" />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      {/* Copy button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          data.onCopyNode?.();
        }}
        className="absolute top-0.5 right-5 w-4 h-4 rounded bg-blue-500/80 hover:bg-blue-500 flex items-center justify-center transition-colors z-10"
        title="Duplicate node"
        data-testid="image-node-copy-btn"
      >
        <FiCopy className="w-2.5 h-2.5 text-white" />
      </button>
      
      <div className="p-2 border-b border-yellow-600/30 flex items-center gap-2">
        <div className="w-5 h-5 rounded-lg bg-yellow-500/30 flex items-center justify-center flex-shrink-0">
          <FiRefreshCw className="text-yellow-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">{data.label || 'Image Input'}</h4>
          <p className="text-[9px] text-yellow-300/70">{data.image ? 'Ready' : 'Upload or select'}</p>
        </div>
      </div>
      
      <div className="p-2">
        {data.image ? (
          <div className="relative w-full aspect-square">
            <img 
              src={data.image} 
              alt="Input" 
              className="w-full h-full object-cover rounded-lg border border-yellow-500/30"
            />
            {/* Clear button */}
            <button
              onClick={() => {
                data.onChange?.('image', null);
                data.onChange?.('label', 'Image Input');
              }}
              className="absolute top-1 right-1 p-1 bg-red-500/80 rounded hover:bg-red-500 transition-colors"
              title="Remove image"
            >
              <FiX className="w-3 h-3 text-white" />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Upload from device */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full py-2 bg-yellow-500/20 hover:bg-yellow-500/30 rounded-lg text-xs text-yellow-300 flex items-center justify-center gap-1.5 transition-colors"
            >
              <FiUpload className="w-3 h-3" />
              Upload Image
            </button>
            
            {/* Select from gallery */}
            <button
              onClick={() => data.onSelectFromGallery?.()}
              className="w-full py-2 bg-purple-500/20 hover:bg-purple-500/30 rounded-lg text-xs text-purple-300 flex items-center justify-center gap-1.5 transition-colors"
            >
              <FiImage className="w-3 h-3" />
              From Gallery
            </button>
          </div>
        )}
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-yellow-400 !w-3 !h-3" />
    </div>
  );
};

// Output Node - Fixed size with expand preview option and lock functionality
const OutputNode = ({ data, selected }) => {
  const isLocked = data.locked ?? false; // Default to unlocked for backward compatibility
  
  return (
    <div className={`relative bg-gradient-to-br from-pink-900/90 to-pink-800/90 rounded-xl border-2 ${selected ? 'border-pink-400' : isLocked ? 'border-yellow-500/70' : 'border-pink-600/50'} shadow-xl backdrop-blur-sm w-[220px] h-[340px]`}>
      <Handle type="target" position={Position.Left} className="!bg-pink-400 !w-3 !h-3" />
      <Handle type="source" position={Position.Right} className="!bg-yellow-400 !w-3 !h-3" id="continue" />
      <NodeDeleteButton onDelete={data.onDelete} />
      
      {/* Copy button in header */}
      {data.image && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onCopyNode?.();
          }}
          className="absolute top-0.5 right-5 w-4 h-4 rounded bg-blue-500/80 hover:bg-blue-500 flex items-center justify-center transition-colors z-10"
          title="Duplicate this output node"
          data-testid="output-node-copy-btn"
        >
          <FiCopy className="w-2.5 h-2.5 text-white" />
        </button>
      )}
      
      <div className="p-2 border-b border-pink-600/30 flex items-center gap-2">
        <div className="w-5 h-5 rounded-lg bg-pink-500/30 flex items-center justify-center flex-shrink-0">
          <FiZap className="text-pink-300 w-3 h-3" />
        </div>
        <h4 className="text-xs font-semibold text-white flex-1">Output</h4>
        {/* Lock indicator and toggle */}
        {data.image && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              data.onChange?.('locked', !isLocked);
            }}
            className={`p-1 rounded transition-colors ${isLocked ? 'bg-yellow-500/30 text-yellow-300' : 'bg-white/10 text-white/50 hover:text-white'}`}
            title={isLocked ? 'Locked - output won\'t change when re-running. Click to unlock.' : 'Unlocked - output may change when re-running. Click to lock.'}
          >
            {isLocked ? (
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a5 5 0 00-5 5v2a2 2 0 00-2 2v5a2 2 0 002 2h10a2 2 0 002-2v-5a2 2 0 00-2-2H7V7a3 3 0 015.905-.75 1 1 0 001.937-.5A5.002 5.002 0 0010 2z" />
              </svg>
            )}
          </button>
        )}
      </div>
      
      <div className="p-2 h-[180px]">
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
            {/* Lock overlay indicator */}
            {isLocked && (
              <div className="absolute top-1 left-1 bg-yellow-500/80 px-1.5 py-0.5 rounded text-[9px] text-black font-medium flex items-center gap-1">
                <svg className="w-2 h-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                Locked
              </div>
            )}
            {/* Action buttons row 1 */}
            <div className="absolute bottom-2 left-2 right-2 flex gap-1 justify-center">
              <button
                onClick={() => data.onExpand?.(data.image)}
                className="p-1.5 bg-blue-600/80 rounded-lg hover:bg-blue-600 flex-1 flex items-center justify-center"
                title="Expand Preview"
                data-testid="output-expand-btn"
              >
                <FiMaximize2 className="w-3 h-3 text-white" />
              </button>
              <button
                onClick={() => data.onSaveToGallery?.(data.image)}
                className="p-1.5 bg-green-600/80 rounded-lg hover:bg-green-600 flex-1 flex items-center justify-center"
                title="Save to Gallery"
                data-testid="output-save-gallery-btn"
              >
                <FiSave className="w-3 h-3 text-white" />
              </button>
              <button
                onClick={() => data.onDownload?.(data.image)}
                className="p-1.5 bg-purple-600/80 rounded-lg hover:bg-purple-600 flex-1 flex items-center justify-center"
                title="Download"
                data-testid="output-download-btn"
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
      
      {/* Bottom action buttons when image exists */}
      {data.image && (
        <div className="px-2 pb-2 space-y-1.5">
          {/* Save to Book button */}
          <button
            onClick={() => data.onSaveToBook?.(data.image)}
            className="w-full py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-lg text-xs font-medium text-white flex items-center justify-center gap-1"
            title="Save this image to a book's library"
            data-testid="output-save-book-btn"
          >
            <FiBook className="w-3 h-3" /> Save to Book
          </button>
          
          {/* Continue Workflow button */}
          <button
            onClick={() => data.onContinueWorkflow?.(data.image)}
            className="w-full py-1.5 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-500 hover:to-orange-500 rounded-lg text-xs font-medium text-white flex items-center justify-center gap-1"
            title="Use this output as input for a new branch"
            data-testid="output-continue-btn"
          >
            <FiRefreshCw className="w-3 h-3" /> Continue Workflow
          </button>
        </div>
      )}
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
  output: OutputNode,
  image: ImageNode
};

// Initial nodes for new workflow
const defaultNodes = [
  {
    id: 'character-1',
    type: 'character',
    position: { x: 50, y: 50 },
    data: { name: '', gender: 'Female', age: 'Adult', appearance: '', transparentBg: false }
  },
  {
    id: 'style-1',
    type: 'style',
    position: { x: 50, y: 320 },
    data: { style: 'fantasy' }
  },
  {
    id: 'reference-1',
    type: 'reference',
    position: { x: 50, y: 450 },
    data: { image: null }
  },
  {
    id: 'combine-1',
    type: 'combine',
    position: { x: 350, y: 180 },
    data: {}
  },
  {
    id: 'output-1',
    type: 'output',
    position: { x: 550, y: 130 },
    data: { image: null, generating: false }
  }
];

const defaultEdges = [
  { id: 'e1', source: 'character-1', target: 'combine-1', targetHandle: 'a', animated: true },
  { id: 'e2', source: 'style-1', target: 'combine-1', targetHandle: 'b', animated: true },
  { id: 'e3', source: 'reference-1', target: 'combine-1', targetHandle: 'c', animated: true },
  { id: 'e4', source: 'combine-1', target: 'output-1', animated: true }
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
  const [showWorkflowPanel, setShowWorkflowPanel] = useState(false); // Workflow save/load panel
  const [isSavingWorkflow, setIsSavingWorkflow] = useState(false);
  const [workflowSaveMessage, setWorkflowSaveMessage] = useState('');
  
  // Save to book modal state
  const [showSaveToBookModal, setShowSaveToBookModal] = useState(false);
  const [imageToSave, setImageToSave] = useState(null);
  
  // Gallery picker state for Image nodes
  const [showGalleryPicker, setShowGalleryPicker] = useState(false);
  const [galleryImages, setGalleryImages] = useState([]);
  const [galleryPickerCallback, setGalleryPickerCallback] = useState(null);
  const [galleryTab, setGalleryTab] = useState('art'); // 'art' or 'pro'
  
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
          console.log('Importing character data from Easy Mode:', data);
          
          if (data.character) {
            // Build appearance string from Easy Mode character traits
            const appearanceParts = [];
            if (data.character.skinTone) appearanceParts.push(`${data.character.skinTone} skin`);
            if (data.character.hairColor && data.character.hairStyle) {
              appearanceParts.push(`${data.character.hairColor} ${data.character.hairStyle} hair`);
            }
            if (data.character.eyeColor) appearanceParts.push(`${data.character.eyeColor} eyes`);
            if (data.character.bodyType) appearanceParts.push(`${data.character.bodyType} build`);
            if (data.character.clothing) appearanceParts.push(`${data.character.clothing} clothing`);
            if (data.character.expression) appearanceParts.push(`${data.character.expression} expression`);
            if (data.character.additionalDetails) appearanceParts.push(data.character.additionalDetails);
            
            const appearanceString = appearanceParts.join(', ');
            
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
                    appearance: appearanceString,
                    transparentBg: data.character.transparentBackground || false
                  }
                };
              }
              if (node.type === 'style' && data.style) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    style: data.style
                  }
                };
              }
              if (node.type === 'reference' && data.referenceImage) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    image: data.referenceImage
                  }
                };
              }
              return node;
            }));
            
            // Clear the export data
            localStorage.removeItem('artStudioExport');
            
            // Remove the URL param
            window.history.replaceState({}, '', '/art-studio/expert');
            
            console.log('Character imported successfully!');
          }
        } catch (e) {
          console.error('Failed to import character data:', e);
        }
      }
    }
  }, [setNodes]);
  
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
  
  // Delete specific node by ID
  const deleteNodeById = useCallback((nodeId) => {
    setNodes(nds => nds.filter(node => node.id !== nodeId));
    setEdges(eds => eds.filter(edge => edge.source !== nodeId && edge.target !== nodeId));
  }, [setNodes, setEdges]);
  
  // Copy/Duplicate a node with offset position - preserves ALL data including images
  const copyNode = useCallback((nodeId) => {
    const nodeToCopy = nodes.find(n => n.id === nodeId);
    if (!nodeToCopy) return;
    
    const newNodeId = `${nodeToCopy.type}-${Date.now()}`;
    const offsetX = 50;
    const offsetY = 50;
    
    // Deep copy the data, excluding function handlers but KEEPING images and all content
    const copiedData = { ...nodeToCopy.data };
    delete copiedData.onChange;
    delete copiedData.onDelete;
    delete copiedData.onCopyNode;
    delete copiedData.onContinueWorkflow;
    delete copiedData.onDownload;
    delete copiedData.onSaveToGallery;
    delete copiedData.onSaveToBook;
    delete copiedData.onExpand;
    
    // KEEP the image for all node types including output (user requested to preserve images when copying)
    // Only reset generating state
    if (nodeToCopy.type === 'output') {
      copiedData.generating = false;
      copiedData.locked = false; // New nodes are unlocked
    }
    
    const newNode = {
      id: newNodeId,
      type: nodeToCopy.type,
      position: { 
        x: nodeToCopy.position.x + offsetX, 
        y: nodeToCopy.position.y + offsetY 
      },
      data: copiedData
    };
    
    // Add handlers
    newNode.data.onChange = (k, v) => updateNodeData(newNodeId, k, v);
    newNode.data.onDelete = () => deleteNodeById(newNodeId);
    newNode.data.onCopyNode = () => copyNode(newNodeId);
    
    setNodes(nds => [...nds, newNode]);
    console.log(`Copied node ${nodeId} to ${newNodeId}`);
    return newNodeId;
  }, [nodes, setNodes, updateNodeData, deleteNodeById]);
  
  // Copy multiple selected nodes with their connections
  const copySelectedNodes = useCallback(() => {
    const selectedNodes = nodes.filter(n => selectedNodeIds.has(n.id));
    if (selectedNodes.length === 0) return;
    
    const idMapping = {}; // Old ID -> New ID
    const newNodes = [];
    const offsetX = 100;
    const offsetY = 100;
    
    // First pass: create new nodes
    selectedNodes.forEach(node => {
      const newNodeId = `${node.type}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
      idMapping[node.id] = newNodeId;
      
      // Deep copy data, preserving ALL content including images
      const copiedData = { ...node.data };
      delete copiedData.onChange;
      delete copiedData.onDelete;
      delete copiedData.onCopyNode;
      delete copiedData.onContinueWorkflow;
      delete copiedData.onDownload;
      delete copiedData.onSaveToGallery;
      delete copiedData.onSaveToBook;
      delete copiedData.onExpand;
      
      if (node.type === 'output') {
        copiedData.generating = false;
        copiedData.locked = false;
      }
      
      const newNode = {
        id: newNodeId,
        type: node.type,
        position: {
          x: node.position.x + offsetX,
          y: node.position.y + offsetY
        },
        data: copiedData
      };
      
      newNode.data.onChange = (k, v) => updateNodeData(newNodeId, k, v);
      newNode.data.onDelete = () => deleteNodeById(newNodeId);
      newNode.data.onCopyNode = () => copyNode(newNodeId);
      
      newNodes.push(newNode);
    });
    
    // Second pass: recreate edges between copied nodes
    const selectedIds = new Set(selectedNodes.map(n => n.id));
    const newEdges = edges
      .filter(e => selectedIds.has(e.source) && selectedIds.has(e.target))
      .map(e => ({
        ...e,
        id: `e-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
        source: idMapping[e.source],
        target: idMapping[e.target]
      }));
    
    setNodes(nds => [...nds, ...newNodes]);
    setEdges(eds => [...eds, ...newEdges]);
    setSelectedNodeIds(new Set(newNodes.map(n => n.id))); // Select the new nodes
    
    console.log(`Copied ${newNodes.length} nodes and ${newEdges.length} edges`);
  }, [nodes, edges, selectedNodeIds, setNodes, setEdges, updateNodeData, deleteNodeById, copyNode]);
  
  // Continue workflow from an output image - creates an ImageNode for further branching
  const continueWorkflow = useCallback((imageUrl, sourceNodeId) => {
    const sourceNode = nodes.find(n => n.id === sourceNodeId);
    const newNodeId = `image-${Date.now()}`;
    
    const newNode = {
      id: newNodeId,
      type: 'image',
      position: { 
        x: (sourceNode?.position?.x || 600) + 100, 
        y: (sourceNode?.position?.y || 130) 
      },
      data: {
        image: imageUrl,
        label: 'Workflow Output',
        onChange: (k, v) => updateNodeData(newNodeId, k, v),
        onDelete: () => deleteNodeById(newNodeId),
        onCopyNode: () => copyNode(newNodeId)
      }
    };
    
    setNodes(nds => [...nds, newNode]);
    console.log(`Created continuation node from ${sourceNodeId}`);
  }, [nodes, setNodes, updateNodeData, deleteNodeById]);
  
  // Save image to Art Studio gallery (useCallback for proper dependency handling)
  const saveToGallery = useCallback(async (imageUrl) => {
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
  }, [nodes, token, selectedBookId]);
  
  // Save image to a specific book's library
  const saveToBook = useCallback(async (imageUrl, bookId) => {
    if (!bookId || bookId === 'general') {
      // Fall back to general gallery
      await saveToGallery(imageUrl);
      return;
    }
    
    try {
      const characterNode = nodes.find(n => n.type === 'character');
      const sceneNode = nodes.find(n => n.type === 'scene');
      const styleNode = nodes.find(n => n.type === 'style');
      
      const response = await fetch(`${API_URL}/api/books/${bookId}/images`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: imageUrl,
          name: characterNode?.data?.name || sceneNode?.data?.preset || 'Workflow Image',
          type: characterNode ? 'character' : sceneNode ? 'scene' : 'illustration',
          style: styleNode?.data?.style || 'fantasy',
          metadata: {
            characterData: characterNode?.data || null,
            sceneData: sceneNode?.data || null,
            workflowName: workflowName
          }
        })
      });
      
      if (response.ok) {
        const bookName = userBooks.find(b => b.id === bookId)?.title || 'book';
        alert(`Image saved to "${bookName}" library!`);
      } else {
        throw new Error('Failed to save to book');
      }
    } catch (error) {
      console.error('Save to book error:', error);
      alert('Failed to save image to book library');
    }
  }, [nodes, token, workflowName, userBooks, saveToGallery]);
  
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
    const nodeId = `${type}-${Date.now()}`;
    const newNode = {
      id: nodeId,
      type,
      position: { x: Math.random() * 300 + 100, y: Math.random() * 200 + 100 },
      data: getDefaultDataForType(type)
    };
    newNode.data.onChange = (k, v) => updateNodeData(nodeId, k, v);
    newNode.data.onDelete = () => deleteNodeById(nodeId);
    newNode.data.onCopyNode = () => copyNode(nodeId);
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
      case 'image': return { image: null, label: 'Image Input' };
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
    
    const { prompt, transparentBg } = buildPromptFromWorkflow();
    console.log('Built prompt:', prompt, 'Transparent BG:', transparentBg);
    
    if (!prompt || prompt === ', highly detailed, professional illustration') {
      alert('Please add some nodes and connect them to the output. Make sure Character or Scene nodes have content.');
      return;
    }
    
    // Get reference images from Reference nodes
    const referenceNodes = nodes.filter(n => n.type === 'reference' && n.data.image);
    const characterReferenceImage = referenceNodes[0]?.data?.image || null;
    const styleReferenceImage = referenceNodes[1]?.data?.image || null;
    
    // Get style settings
    const styleNode = nodes.find(n => n.type === 'style');
    const selectedStyle = styleNode?.data?.style || 'fantasy';
    
    // Get character data for advanced settings
    const characterNode = nodes.find(n => n.type === 'character');
    const characterData = characterNode ? {
      name: characterNode.data.name,
      gender: characterNode.data.gender,
      age: characterNode.data.age,
      appearance: characterNode.data.appearance
    } : null;
    
    // Get scene data
    const sceneNode = nodes.find(n => n.type === 'scene');
    const sceneData = sceneNode ? {
      preset: sceneNode.data.preset,
      description: sceneNode.data.description,
      timeOfDay: sceneNode.data.timeOfDay,
      mood: sceneNode.data.mood
    } : null;
    
    setIsGenerating(true);
    
    // Update UNLOCKED output nodes to show generating state (locked ones stay as-is)
    setNodes(nds => nds.map(node => {
      if (node.type === 'output' && !node.data.locked) {
        return { ...node, data: { ...node.data, generating: true, image: null } };
      }
      return node;
    }));
    
    try {
      console.log('Sending request to API with expert mode settings...');
      const response = await fetch(`${API_URL}/api/art-studio/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt,
          style: selectedStyle,
          type: 'workflow',
          bookId: selectedBookId !== 'general' ? selectedBookId : null,
          workflowName: workflowName,
          transparentBackground: transparentBg,
          // Expert mode extras
          characterReferenceImage,
          styleReferenceImage,
          characterData,
          sceneData,
          aspectRatio: '1:1',
          quality: 'high',
          expertMode: true
        })
      });
      
      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Generation successful, image received');
        
        // Update UNLOCKED output nodes with result and auto-lock them
        setNodes(nds => nds.map(node => {
          if (node.type === 'output' && !node.data.locked) {
            return {
              ...node,
              data: {
                ...node.data,
                generating: false,
                image: data.image_url,
                locked: true, // Auto-lock after generation
                onDownload: (url) => downloadImage(url),
                onSaveToGallery: (url) => saveToGallery(url),
                onSaveToBook: (url) => openSaveToBookModal(url),
                onExpand: (url) => setExpandedImage(url),
                onCopyNode: () => copyNode(node.id),
                onContinueWorkflow: (url) => continueWorkflow(url, node.id)
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
      
      // Reset generating state on unlocked outputs
      setNodes(nds => nds.map(node => {
        if (node.type === 'output' && !node.data.locked) {
          return { ...node, data: { ...node.data, generating: false } };
        }
        return node;
      }));
    } finally {
      setIsGenerating(false);
    }
  };
  
  // Open save to book modal with selected image
  const openSaveToBookModal = (imageUrl) => {
    setImageToSave(imageUrl);
    setShowSaveToBookModal(true);
  };
  
  // Run workflow on selected nodes only
  const runSelectedWorkflow = async () => {
    if (selectedNodeIds.size === 0) {
      alert('Please select nodes first using drag selection');
      return;
    }
    
    // For now, run the entire workflow but only update selected output nodes
    // In future, this could be enhanced to only process connected sub-graphs
    await runWorkflow();
  };
  
  const downloadImage = (url) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = `azories-workflow-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // Save workflow
  const saveWorkflow = async () => {
    if (!workflowName.trim()) {
      alert('Please enter a workflow name');
      return;
    }
    
    setIsSavingWorkflow(true);
    setWorkflowSaveMessage('');
    
    try {
      const workflow = {
        name: workflowName,
        nodes: nodes.map(n => ({ ...n, data: { ...n.data, onChange: undefined, onDownload: undefined, onSaveToGallery: undefined, onExpand: undefined } })),
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
        const result = await response.json();
        setWorkflowSaveMessage(result.updated ? 'Workflow updated!' : 'Workflow saved!');
        loadWorkflows();
        setTimeout(() => setWorkflowSaveMessage(''), 3000);
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      console.error('Save error:', error);
      setWorkflowSaveMessage('Failed to save workflow');
    } finally {
      setIsSavingWorkflow(false);
    }
  };
  
  // Load a specific workflow
  const loadWorkflow = (workflow) => {
    if (!workflow.nodes || !workflow.edges) {
      alert('Invalid workflow data');
      return;
    }
    
    // Restore nodes with onChange handlers
    const restoredNodes = workflow.nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        onChange: (k, v) => updateNodeData(node.id, k, v)
      }
    }));
    
    setNodes(restoredNodes);
    setEdges(workflow.edges);
    setWorkflowName(workflow.name);
    setShowWorkflowPanel(false);
  };
  
  // Delete a saved workflow
  const deleteWorkflow = async (workflowId) => {
    if (!confirm('Delete this workflow?')) return;
    
    try {
      await fetch(`${API_URL}/api/art-studio/workflow/${workflowId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      loadWorkflows();
    } catch (error) {
      console.error('Delete error:', error);
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
    { type: 'image', icon: FiRefreshCw, label: 'Image', color: 'yellow' },
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
            data-testid="workflow-name-input"
          />
          
          {/* Workflow Panel Toggle */}
          <Button 
            variant="outline" 
            onClick={() => setShowWorkflowPanel(!showWorkflowPanel)}
            className="border-cyan-500/50 text-cyan-300 hover:bg-cyan-500/20"
            data-testid="open-workflows-btn"
          >
            <FiList className="w-4 h-4 mr-2" />
            Workflows
            {savedWorkflows.length > 0 && (
              <span className="ml-1.5 text-[10px] bg-cyan-500/30 px-1.5 py-0.5 rounded-full">{savedWorkflows.length}</span>
            )}
          </Button>
          
          <Button 
            variant="outline" 
            onClick={saveWorkflow}
            disabled={isSavingWorkflow}
            className="border-white/20 text-white"
            data-testid="save-workflow-btn"
          >
            {isSavingWorkflow ? (
              <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <FiSave className="w-4 h-4 mr-2" />
            )}
            {workflowSaveMessage || 'Save'}
          </Button>
          
          <Button 
            onClick={runWorkflow}
            disabled={isGenerating}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            data-testid="run-workflow-btn"
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
        <div className="flex-1 relative" ref={canvasRef}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            className="bg-transparent"
            selectionOnDrag
            selectionMode="partial"
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
            
            {/* Selection Actions Toolbar - Top Left */}
            <Panel position="top-left" className="!m-2">
              <div className="flex gap-2 bg-black/70 backdrop-blur-sm border border-white/20 rounded-lg p-2">
                {/* Run Selected Workflow */}
                <button
                  onClick={runWorkflow}
                  disabled={isGenerating}
                  className={`p-2 rounded-lg transition-all ${
                    isGenerating 
                      ? 'bg-gray-500/30 text-gray-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white hover:from-yellow-400 hover:to-orange-400 shadow-lg shadow-yellow-500/20'
                  }`}
                  title="Run Workflow (⚡)"
                  data-testid="lightning-run-btn"
                >
                  <FiZap className={`w-5 h-5 ${isGenerating ? 'animate-pulse' : ''}`} />
                </button>
                
                {/* Copy Selected Nodes */}
                <button
                  onClick={() => {
                    const selected = nodes.filter(n => n.selected);
                    if (selected.length === 0) return;
                    
                    const idMapping = {};
                    const newNodes = [];
                    const offsetX = 100;
                    const offsetY = 100;
                    
                    selected.forEach(node => {
                      const newNodeId = `${node.type}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
                      idMapping[node.id] = newNodeId;
                      
                      const copiedData = { ...node.data };
                      delete copiedData.onChange;
                      delete copiedData.onDelete;
                      delete copiedData.onCopyNode;
                      delete copiedData.onContinueWorkflow;
                      delete copiedData.onDownload;
                      delete copiedData.onSaveToGallery;
                      delete copiedData.onSaveToBook;
                      delete copiedData.onExpand;
                      
                      if (node.type === 'output') {
                        copiedData.generating = false;
                        copiedData.locked = false;
                      }
                      
                      newNodes.push({
                        id: newNodeId,
                        type: node.type,
                        position: { x: node.position.x + offsetX, y: node.position.y + offsetY },
                        data: {
                          ...copiedData,
                          onChange: (k, v) => updateNodeData(newNodeId, k, v),
                          onDelete: () => deleteNodeById(newNodeId),
                          onCopyNode: () => copyNode(newNodeId)
                        }
                      });
                    });
                    
                    const selectedIds = new Set(selected.map(n => n.id));
                    const newEdges = edges
                      .filter(e => selectedIds.has(e.source) && selectedIds.has(e.target))
                      .map(e => ({
                        ...e,
                        id: `e-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
                        source: idMapping[e.source],
                        target: idMapping[e.target]
                      }));
                    
                    setNodes(nds => [...nds, ...newNodes]);
                    setEdges(eds => [...eds, ...newEdges]);
                  }}
                  disabled={!nodes.some(n => n.selected)}
                  className={`p-2 rounded-lg transition-all ${
                    !nodes.some(n => n.selected)
                      ? 'bg-gray-500/30 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-500/30 text-blue-300 hover:bg-blue-500/50'
                  }`}
                  title="Copy Selected Nodes"
                  data-testid="copy-selected-btn"
                >
                  <FiCopy className="w-5 h-5" />
                </button>
                
                {/* Selection count */}
                {nodes.filter(n => n.selected).length > 0 && (
                  <div className="px-2 flex items-center text-xs text-white/70">
                    {nodes.filter(n => n.selected).length} selected
                  </div>
                )}
              </div>
            </Panel>
            
            <Panel position="bottom-left" className="!bg-black/50 !border-white/10 rounded-lg p-2">
              <p className="text-xs text-white/50">
                Drag to select nodes • Copy selection • Lock outputs to preserve them
              </p>
            </Panel>
          </ReactFlow>
        </div>
      </div>
      
      {/* Workflow Save/Load Panel */}
      <AnimatePresence>
        {showWorkflowPanel && (
          <motion.div
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-80 bg-gradient-to-b from-[#1a1520] to-[#0d0a10] border-l border-white/10 shadow-2xl z-40 flex flex-col"
            data-testid="workflow-panel"
          >
            {/* Panel Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <FiFolder className="text-cyan-400" />
                Saved Workflows
              </h3>
              <button
                onClick={() => setShowWorkflowPanel(false)}
                className="p-1.5 rounded-lg hover:bg-white/10 text-white/60 hover:text-white"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            
            {/* Current Workflow Section */}
            <div className="p-4 border-b border-white/10 bg-cyan-500/5">
              <h4 className="text-xs font-medium text-cyan-400 uppercase tracking-wider mb-3">Current Workflow</h4>
              <div className="flex gap-2">
                <Input
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  className="flex-1 bg-black/30 border-white/20 text-white text-sm"
                  placeholder="Workflow name..."
                  data-testid="panel-workflow-name"
                />
                <Button 
                  onClick={saveWorkflow}
                  disabled={isSavingWorkflow}
                  size="sm"
                  className="bg-cyan-600 hover:bg-cyan-700"
                  data-testid="panel-save-btn"
                >
                  {isSavingWorkflow ? <FiRefreshCw className="w-4 h-4 animate-spin" /> : <FiSave className="w-4 h-4" />}
                </Button>
              </div>
              {workflowSaveMessage && (
                <p className={`text-xs mt-2 ${workflowSaveMessage.includes('Failed') ? 'text-red-400' : 'text-green-400'}`}>
                  <FiCheck className="w-3 h-3 inline mr-1" />
                  {workflowSaveMessage}
                </p>
              )}
            </div>
            
            {/* Saved Workflows List */}
            <div className="flex-1 overflow-y-auto p-4">
              {savedWorkflows.length === 0 ? (
                <div className="text-center py-12">
                  <FiFolder className="w-12 h-12 mx-auto text-white/20 mb-3" />
                  <p className="text-white/40 text-sm">No saved workflows yet</p>
                  <p className="text-white/30 text-xs mt-1">Save your first workflow to reuse later</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {savedWorkflows.map((workflow) => (
                    <div 
                      key={workflow.id}
                      className="bg-black/30 rounded-lg border border-white/10 hover:border-cyan-500/50 transition-colors group"
                    >
                      <div className="p-3">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="text-white font-medium text-sm truncate flex-1">{workflow.name}</h5>
                          <button
                            onClick={() => deleteWorkflow(workflow.id)}
                            className="p-1 rounded hover:bg-red-500/20 text-white/40 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Delete workflow"
                          >
                            <FiTrash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-white/40 mb-3">
                          <FiClock className="w-3 h-3" />
                          {workflow.updated_at ? new Date(workflow.updated_at).toLocaleDateString() : 'Unknown date'}
                          <span className="ml-auto">{workflow.nodes?.length || 0} nodes</span>
                        </div>
                        <Button
                          onClick={() => loadWorkflow(workflow)}
                          size="sm"
                          variant="outline"
                          className="w-full border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20 text-xs"
                          data-testid={`load-workflow-${workflow.id}`}
                        >
                          <FiDownload className="w-3 h-3 mr-1.5" />
                          Load Workflow
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Panel Footer */}
            <div className="p-4 border-t border-white/10 bg-black/20">
              <p className="text-[10px] text-white/30 text-center">
                Workflows save your node setup for reuse
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
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
      
      {/* Save to Book Modal with Dropdown */}
      <AnimatePresence>
        {showSaveToBookModal && imageToSave && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-8"
            onClick={() => setShowSaveToBookModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-gradient-to-b from-[#2a2035] to-[#1a1520] rounded-2xl border border-white/10 shadow-2xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <FiBook className="text-emerald-400" />
                  Save to Book
                </h3>
                <button
                  onClick={() => setShowSaveToBookModal(false)}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-colors"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>
              
              {/* Image Preview */}
              <div className="mb-4 rounded-xl overflow-hidden border border-white/10 aspect-square max-h-48 mx-auto">
                <img 
                  src={imageToSave} 
                  alt="Image to save" 
                  className="w-full h-full object-cover"
                />
              </div>
              
              {/* Book Selection */}
              <div className="mb-6">
                <label className="text-sm text-white/70 mb-2 block">Select Book</label>
                <select
                  value={selectedBookId}
                  onChange={(e) => setSelectedBookId(e.target.value)}
                  className="w-full bg-black/40 border border-white/20 rounded-lg px-4 py-3 text-white appearance-none"
                  data-testid="save-to-book-dropdown"
                >
                  <option value="general">General Gallery (No Book)</option>
                  {userBooks.map(book => (
                    <option key={book.id} value={book.id}>{book.title}</option>
                  ))}
                </select>
              </div>
              
              {/* Actions */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowSaveToBookModal(false)}
                  className="flex-1 border-white/20 text-white"
                >
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    await saveToBook(imageToSave, selectedBookId);
                    setShowSaveToBookModal(false);
                    setImageToSave(null);
                  }}
                  className="flex-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500"
                >
                  <FiCheck className="w-4 h-4 mr-2" />
                  Save
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
