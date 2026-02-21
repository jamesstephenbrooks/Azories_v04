import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  Panel,
  NodeResizer
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  FiUser, FiImage, FiLayers, FiType, FiZap, FiGrid, 
  FiSave, FiDownload, FiPlus, FiTrash2, FiPlay,
  FiArrowLeft, FiFolder, FiSettings, FiCopy, FiRefreshCw,
  FiUpload, FiSliders, FiMaximize, FiStar, FiMove
} from 'react-icons/fi';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Custom Node Types

// Character Node - Define character traits - Resizable
const CharacterNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-purple-900/90 to-purple-800/90 rounded-xl border-2 ${selected ? 'border-purple-400' : 'border-purple-600/50'} shadow-xl backdrop-blur-sm h-full w-full min-w-[250px] min-h-[200px]`}>
      <NodeResizer 
        color="#a855f7" 
        isVisible={selected} 
        minWidth={250} 
        minHeight={200}
        handleStyle={{ width: 8, height: 8 }}
      />
      <Handle type="target" position={Position.Left} className="!bg-purple-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-purple-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-purple-500/30 flex items-center justify-center flex-shrink-0">
          <FiUser className="text-purple-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Character</h4>
        </div>
        {selected && (
          <FiMove className="w-3 h-3 text-purple-400 flex-shrink-0" />
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
          className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-purple-500/30 text-white text-xs focus:outline-none focus:border-purple-400 resize-none flex-1"
          style={{ minHeight: '40px' }}
        />
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-purple-400 !w-3 !h-3" />
    </div>
  );
};

// Scene Node - Define environment/setting - Resizable
const SceneNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-emerald-900/90 to-emerald-800/90 rounded-xl border-2 ${selected ? 'border-emerald-400' : 'border-emerald-600/50'} shadow-xl backdrop-blur-sm h-full w-full min-w-[250px] min-h-[200px]`}>
      <NodeResizer 
        color="#10b981" 
        isVisible={selected} 
        minWidth={250} 
        minHeight={200}
        handleStyle={{ width: 8, height: 8 }}
      />
      <Handle type="target" position={Position.Left} className="!bg-emerald-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-emerald-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-emerald-500/30 flex items-center justify-center flex-shrink-0">
          <FiLayers className="text-emerald-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Scene</h4>
        </div>
        {selected && (
          <FiMove className="w-3 h-3 text-emerald-400 flex-shrink-0" />
        )}
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
          <option value="village">Medieval Village</option>
          <option value="ocean">Ocean/Beach</option>
          <option value="mountain">Mountain Peak</option>
          <option value="city">Fantasy City</option>
          <option value="library">Ancient Library</option>
          <option value="garden">Magical Garden</option>
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

// Style Node - Art style selection - Expanded with all styles
const ALL_STYLE_CATEGORIES = [
  { category: 'Realistic', styles: ['realistic', 'portrait', 'cinematic', 'hyperrealistic'] },
  { category: 'Illustration', styles: ['cartoon', 'anime', 'manga', 'disney', 'pixar', 'chibi', 'comic', 'graphic-novel'] },
  { category: 'Traditional', styles: ['oil-painting', 'watercolor', 'acrylic', 'pastel', 'charcoal', 'pencil', 'ink', 'gouache'] },
  { category: 'Digital', styles: ['digital-art', 'concept-art', 'matte-painting', 'vector', 'low-poly', 'vaporwave', 'synthwave'] },
  { category: '3D', styles: ['3d-render', 'clay-render', 'isometric', 'diorama', 'unreal-engine'] },
  { category: 'Fantasy', styles: ['fantasy', 'dark-fantasy', 'sci-fi', 'cyberpunk', 'steampunk', 'solarpunk'] },
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
  'fantasy': 'Fantasy', 'dark-fantasy': 'Dark', 'sci-fi': 'Sci-Fi', 'cyberpunk': 'Cyberpunk',
  'steampunk': 'Steampunk', 'solarpunk': 'Solarpunk',
  'storybook': 'Storybook', 'picture-book': 'Picture', 'whimsical': 'Whimsical', 'crayon': 'Crayon',
  'paper-cutout': 'Paper', 'felt': 'Felt',
  'pixel-art': 'Pixel', 'retro-game': 'Retro', 'vintage-poster': 'Vintage', 'art-deco': 'Art Deco',
  'art-nouveau': 'Nouveau', 'pop-art': 'Pop Art',
  'ukiyo-e': 'Ukiyo-e', 'chinese-ink': 'Chinese', 'persian-miniature': 'Persian', 'aboriginal': 'Aboriginal',
  'tribal': 'Tribal', 'celtic': 'Celtic',
  'minimalist': 'Minimal', 'abstract': 'Abstract', 'surreal': 'Surreal', 'impressionist': 'Impress.',
  'expressionist': 'Express.', 'cubist': 'Cubist'
};

const StyleNode = ({ data, selected }) => {
  const [activeCategory, setActiveCategory] = useState(0);
  
  return (
    <div className={`bg-gradient-to-br from-amber-900/90 to-amber-800/90 rounded-xl border-2 ${selected ? 'border-amber-400' : 'border-amber-600/50'} shadow-xl backdrop-blur-sm h-full w-full min-w-[280px] min-h-[200px]`}>
      <NodeResizer 
        color="#f59e0b" 
        isVisible={selected} 
        minWidth={280} 
        minHeight={200}
        handleStyle={{ width: 8, height: 8 }}
      />
      <Handle type="target" position={Position.Left} className="!bg-amber-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-amber-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-amber-500/30 flex items-center justify-center flex-shrink-0">
          <FiSliders className="text-amber-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Style: {STYLE_LABELS[data.style] || 'Fantasy'}</h4>
        </div>
        {selected && <FiMove className="w-3 h-3 text-amber-400" />}
      </div>
      
      <div className="p-2 h-[calc(100%-40px)] overflow-auto">
        {/* Category tabs */}
        <div className="flex flex-wrap gap-1 mb-2">
          {ALL_STYLE_CATEGORIES.map((cat, idx) => (
            <button
              key={cat.category}
              onClick={() => setActiveCategory(idx)}
              className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                activeCategory === idx 
                  ? 'bg-amber-500 text-white' 
                  : 'bg-black/30 text-amber-200 hover:bg-amber-500/30'
              }`}
            >
              {cat.category}
            </button>
          ))}
        </div>
        
        {/* Styles grid */}
        <div className="grid grid-cols-4 gap-1">
          {ALL_STYLE_CATEGORIES[activeCategory]?.styles.map(styleId => (
            <button
              key={styleId}
              onClick={() => data.onChange?.('style', styleId)}
              className={`px-1 py-1 rounded text-[10px] transition-colors truncate ${
                data.style === styleId 
                  ? 'bg-amber-500 text-white' 
                  : 'bg-black/30 text-amber-200 hover:bg-amber-500/30'
              }`}
              title={STYLE_LABELS[styleId]}
            >
              {STYLE_LABELS[styleId]}
            </button>
          ))}
        </div>
      </div>
      
      <Handle type="source" position={Position.Right} className="!bg-amber-400 !w-3 !h-3" />
    </div>
  );
};

// Reference Image Node - Resizable
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
    <div className={`bg-gradient-to-br from-cyan-900/90 to-cyan-800/90 rounded-xl border-2 ${selected ? 'border-cyan-400' : 'border-cyan-600/50'} shadow-xl backdrop-blur-sm h-full w-full min-w-[150px] min-h-[150px]`}>
      <NodeResizer 
        color="#06b6d4" 
        isVisible={selected} 
        minWidth={150} 
        minHeight={150}
        handleStyle={{ width: 8, height: 8 }}
      />
      <Handle type="target" position={Position.Left} className="!bg-cyan-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-cyan-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-cyan-500/30 flex items-center justify-center flex-shrink-0">
          <FiImage className="text-cyan-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Reference</h4>
        </div>
        {selected && (
          <FiMove className="w-3 h-3 text-cyan-400 flex-shrink-0" />
        )}
      </div>
      
      <div className="p-2 h-[calc(100%-40px)]">
        {data.image ? (
          <div className="relative h-full">
            <img 
              src={data.image} 
              alt="Reference" 
              className="w-full h-full object-cover rounded-lg"
            />
            <button
              onClick={() => data.onChange?.('image', null)}
              className="absolute top-1 right-1 p-1 bg-red-500 rounded-full hover:bg-red-600"
            >
              <FiTrash2 className="w-3 h-3 text-white" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full h-full border-2 border-dashed border-cyan-500/30 rounded-lg flex flex-col items-center justify-center hover:border-cyan-400 transition-colors"
          >
            <FiUpload className="w-6 h-6 text-cyan-400 mb-1" />
            <span className="text-xs text-cyan-300">Upload</span>
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

// Output Node - Final generation - Resizable
const OutputNode = ({ data, selected }) => {
  return (
    <div className={`bg-gradient-to-br from-pink-900/90 to-pink-800/90 rounded-xl border-2 ${selected ? 'border-pink-400' : 'border-pink-600/50'} shadow-xl backdrop-blur-sm h-full w-full min-w-[200px] min-h-[180px]`}>
      <NodeResizer 
        color="#ec4899" 
        isVisible={selected} 
        minWidth={200} 
        minHeight={180}
        handleStyle={{ width: 8, height: 8 }}
      />
      <Handle type="target" position={Position.Left} className="!bg-pink-400 !w-3 !h-3" />
      
      <div className="p-2 border-b border-pink-600/30 flex items-center gap-2">
        <div className="w-6 h-6 rounded-lg bg-pink-500/30 flex items-center justify-center flex-shrink-0">
          <FiZap className="text-pink-300 w-3 h-3" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-semibold text-white truncate">Output</h4>
        </div>
        {selected && (
          <FiMove className="w-3 h-3 text-pink-400 flex-shrink-0" />
        )}
      </div>
      
      <div className="p-2 h-[calc(100%-40px)]">
        {data.generating ? (
          <div className="w-full h-full bg-black/30 rounded-lg flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-10 h-10 border-4 border-pink-500/30 border-t-pink-500 rounded-full"
            />
          </div>
        ) : data.image ? (
          <div className="relative h-full">
            <img 
              src={data.image} 
              alt="Generated" 
              className="w-full h-full object-cover rounded-lg"
            />
            <div className="absolute bottom-2 right-2 flex gap-1">
              <button
                onClick={() => data.onDownload?.(data.image)}
                className="p-1.5 bg-black/50 rounded-lg hover:bg-black/70"
              >
                <FiDownload className="w-4 h-4 text-white" />
              </button>
            </div>
          </div>
        ) : (
          <div className="w-full h-full bg-black/30 rounded-lg flex flex-col items-center justify-center">
            <FiImage className="w-10 h-10 text-pink-300/30 mb-2" />
            <span className="text-xs text-pink-300/50">Run workflow to generate</span>
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
  
  // Load user's books
  useEffect(() => {
    if (token) {
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
    if (!outputNode) return '';
    
    const getConnectedNodes = (targetId) => {
      const connectedEdges = edges.filter(e => e.target === targetId);
      return connectedEdges.map(e => nodes.find(n => n.id === e.source)).filter(Boolean);
    };
    
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
    
    return promptParts.join(', ') + ', highly detailed, professional illustration';
  };
  
  // Run the workflow
  const runWorkflow = async () => {
    if (!token) {
      navigate('/login');
      return;
    }
    
    const prompt = buildPromptFromWorkflow();
    if (!prompt || prompt === ', highly detailed, professional illustration') {
      alert('Please add some nodes and connect them to the output');
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
      const response = await fetch(`${API_URL}/api/art-studio/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt,
          style: nodes.find(n => n.type === 'style')?.data?.style || 'fantasy',
          type: 'workflow'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Update output node with result
        setNodes(nds => nds.map(node => {
          if (node.type === 'output') {
            return {
              ...node,
              data: {
                ...node.data,
                generating: false,
                image: data.image_url,
                onDownload: (url) => downloadImage(url)
              }
            };
          }
          return node;
        }));
      } else {
        throw new Error('Generation failed');
      }
    } catch (error) {
      console.error('Workflow error:', error);
      alert('Failed to generate image');
      
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
  
  // Save workflow
  const saveWorkflow = async () => {
    try {
      const workflow = {
        name: workflowName,
        nodes: nodes.map(n => ({ ...n, data: { ...n.data, onChange: undefined, onDownload: undefined } })),
        edges
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
          <Input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="w-48 bg-black/30 border-white/20 text-white text-sm"
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
                Drag nodes • Connect handles • Select to resize • Run workflow
              </p>
            </Panel>
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
