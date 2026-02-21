import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  ReactFlowProvider,
  Controls,
  Background,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { 
  FiUser, FiImage, FiLayers, FiType, FiZap, FiDownload, 
  FiPlus, FiTrash2, FiSave, FiUpload, FiArrowLeft, FiPlay,
  FiGrid, FiSun, FiMoon
} from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Custom Node Components
const CharacterNode = ({ data, isConnectable }) => {
  return (
    <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl p-4 min-w-[220px] shadow-lg border-2 border-purple-400">
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} className="w-3 h-3 bg-purple-300" />
      <div className="flex items-center gap-2 mb-3">
        <FiUser className="w-5 h-5 text-white" />
        <span className="font-bold text-white">Character</span>
      </div>
      <div className="space-y-2">
        <Input 
          placeholder="Character name" 
          value={data.name || ''} 
          onChange={(e) => data.onChange?.('name', e.target.value)}
          className="bg-white/20 border-white/30 text-white placeholder:text-white/50 text-sm"
        />
        <Textarea 
          placeholder="Description (age, appearance, clothing...)" 
          value={data.description || ''} 
          onChange={(e) => data.onChange?.('description', e.target.value)}
          className="bg-white/20 border-white/30 text-white placeholder:text-white/50 text-sm min-h-[60px]"
        />
        {data.referenceImage && (
          <img src={data.referenceImage} alt="Reference" className="w-full h-20 object-cover rounded-lg" />
        )}
        <Button 
          variant="outline" 
          size="sm" 
          className="w-full text-xs border-white/30 text-white hover:bg-white/20"
          onClick={() => data.onUploadRef?.()}
        >
          <FiUpload className="w-3 h-3 mr-1" /> Reference Image
        </Button>
      </div>
    </div>
  );
};

const StyleNode = ({ data, isConnectable }) => {
  const styles = [
    { value: 'illustration', label: "Children's Illustration" },
    { value: 'watercolor', label: 'Watercolor' },
    { value: 'anime', label: 'Anime/Manga' },
    { value: 'comic', label: 'Comic Book' },
    { value: 'pixar', label: '3D Pixar' },
    { value: 'fantasy', label: 'Fantasy Art' },
    { value: 'storybook', label: 'Classic Storybook' },
    { value: 'sketch', label: 'Pencil Sketch' },
    { value: 'realistic', label: 'Realistic' },
    { value: 'scifi', label: 'Sci-Fi' },
  ];

  return (
    <div className="bg-gradient-to-br from-pink-500 to-rose-600 rounded-xl p-4 min-w-[200px] shadow-lg border-2 border-pink-300">
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} className="w-3 h-3 bg-pink-300" />
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} className="w-3 h-3 bg-pink-300" />
      <div className="flex items-center gap-2 mb-3">
        <FiLayers className="w-5 h-5 text-white" />
        <span className="font-bold text-white">Style</span>
      </div>
      <Select value={data.style || 'illustration'} onValueChange={(v) => data.onChange?.('style', v)}>
        <SelectTrigger className="bg-white/20 border-white/30 text-white text-sm">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {styles.map(s => (
            <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

const SceneNode = ({ data, isConnectable }) => {
  return (
    <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl p-4 min-w-[220px] shadow-lg border-2 border-emerald-300">
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} className="w-3 h-3 bg-emerald-300" />
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} className="w-3 h-3 bg-emerald-300" />
      <div className="flex items-center gap-2 mb-3">
        <FiImage className="w-5 h-5 text-white" />
        <span className="font-bold text-white">Scene</span>
      </div>
      <div className="space-y-2">
        <Input 
          placeholder="Scene name" 
          value={data.name || ''} 
          onChange={(e) => data.onChange?.('name', e.target.value)}
          className="bg-white/20 border-white/30 text-white placeholder:text-white/50 text-sm"
        />
        <Textarea 
          placeholder="Environment description (forest, castle, bedroom...)" 
          value={data.description || ''} 
          onChange={(e) => data.onChange?.('description', e.target.value)}
          className="bg-white/20 border-white/30 text-white placeholder:text-white/50 text-sm min-h-[60px]"
        />
        <div className="flex gap-2">
          <Select value={data.timeOfDay || 'day'} onValueChange={(v) => data.onChange?.('timeOfDay', v)}>
            <SelectTrigger className="bg-white/20 border-white/30 text-white text-xs flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Day</SelectItem>
              <SelectItem value="night">Night</SelectItem>
              <SelectItem value="sunset">Sunset</SelectItem>
              <SelectItem value="dawn">Dawn</SelectItem>
            </SelectContent>
          </Select>
          <Select value={data.weather || 'clear'} onValueChange={(v) => data.onChange?.('weather', v)}>
            <SelectTrigger className="bg-white/20 border-white/30 text-white text-xs flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="clear">Clear</SelectItem>
              <SelectItem value="cloudy">Cloudy</SelectItem>
              <SelectItem value="rainy">Rainy</SelectItem>
              <SelectItem value="snowy">Snowy</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
};

const PromptNode = ({ data, isConnectable }) => {
  return (
    <div className="bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl p-4 min-w-[220px] shadow-lg border-2 border-amber-300">
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} className="w-3 h-3 bg-amber-300" />
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} className="w-3 h-3 bg-amber-300" />
      <div className="flex items-center gap-2 mb-3">
        <FiType className="w-5 h-5 text-white" />
        <span className="font-bold text-white">Action/Prompt</span>
      </div>
      <Textarea 
        placeholder="What is happening in this scene? (e.g., 'Emma is reading a book under a tree')" 
        value={data.prompt || ''} 
        onChange={(e) => data.onChange?.('prompt', e.target.value)}
        className="bg-white/20 border-white/30 text-white placeholder:text-white/50 text-sm min-h-[80px]"
      />
    </div>
  );
};

const CombineNode = ({ data, isConnectable }) => {
  return (
    <div className="bg-gradient-to-br from-indigo-500 to-blue-600 rounded-xl p-4 min-w-[180px] shadow-lg border-2 border-indigo-300">
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} className="w-3 h-3 bg-indigo-300" id="input" />
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} className="w-3 h-3 bg-indigo-300" />
      <div className="flex items-center gap-2 mb-2">
        <FiGrid className="w-5 h-5 text-white" />
        <span className="font-bold text-white">Combine</span>
      </div>
      <p className="text-white/70 text-xs">Merges character, scene, style & prompt into one</p>
    </div>
  );
};

const OutputNode = ({ data, isConnectable }) => {
  return (
    <div className="bg-gradient-to-br from-gray-700 to-gray-900 rounded-xl p-4 min-w-[250px] shadow-lg border-2 border-gray-500">
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} className="w-3 h-3 bg-gray-400" />
      <div className="flex items-center gap-2 mb-3">
        <FiZap className="w-5 h-5 text-yellow-400" />
        <span className="font-bold text-white">Generate Output</span>
      </div>
      <div className="space-y-2">
        <div className="aspect-square bg-black/30 rounded-lg overflow-hidden flex items-center justify-center">
          {data.generating ? (
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-white/70 text-sm">Generating...</p>
            </div>
          ) : data.generatedImage ? (
            <img src={data.generatedImage} alt="Generated" className="w-full h-full object-cover" />
          ) : (
            <p className="text-white/50 text-sm text-center px-4">Connect nodes and click Generate</p>
          )}
        </div>
        <Button 
          className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold"
          onClick={() => data.onGenerate?.()}
          disabled={data.generating}
        >
          <FiPlay className="w-4 h-4 mr-2" />
          Generate Image
        </Button>
        {data.generatedImage && (
          <Button 
            variant="outline" 
            className="w-full border-white/30 text-white hover:bg-white/20"
            onClick={() => data.onDownload?.()}
          >
            <FiDownload className="w-4 h-4 mr-2" />
            Download
          </Button>
        )}
      </div>
    </div>
  );
};

const nodeTypes = {
  character: CharacterNode,
  style: StyleNode,
  scene: SceneNode,
  prompt: PromptNode,
  combine: CombineNode,
  output: OutputNode,
};

// Initial nodes for a starter workflow
const initialNodes = [
  {
    id: 'character-1',
    type: 'character',
    position: { x: 50, y: 100 },
    data: { name: '', description: '', referenceImage: null },
  },
  {
    id: 'style-1',
    type: 'style',
    position: { x: 50, y: 350 },
    data: { style: 'illustration' },
  },
  {
    id: 'scene-1',
    type: 'scene',
    position: { x: 320, y: 50 },
    data: { name: '', description: '', timeOfDay: 'day', weather: 'clear' },
  },
  {
    id: 'prompt-1',
    type: 'prompt',
    position: { x: 320, y: 320 },
    data: { prompt: '' },
  },
  {
    id: 'combine-1',
    type: 'combine',
    position: { x: 600, y: 200 },
    data: {},
  },
  {
    id: 'output-1',
    type: 'output',
    position: { x: 820, y: 150 },
    data: { generating: false, generatedImage: null },
  },
];

const initialEdges = [
  { id: 'e1', source: 'character-1', target: 'combine-1', animated: true, style: { stroke: '#a855f7' } },
  { id: 'e2', source: 'style-1', target: 'combine-1', animated: true, style: { stroke: '#ec4899' } },
  { id: 'e3', source: 'scene-1', target: 'combine-1', animated: true, style: { stroke: '#10b981' } },
  { id: 'e4', source: 'prompt-1', target: 'combine-1', animated: true, style: { stroke: '#f59e0b' } },
  { id: 'e5', source: 'combine-1', target: 'output-1', animated: true, style: { stroke: '#6366f1' } },
];

function ArtStudioFlow() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [savedWorkflows, setSavedWorkflows] = useState([]);
  const [workflowName, setWorkflowName] = useState('My Workflow');
  const fileInputRef = useRef(null);

  // Check Pro access
  useEffect(() => {
    if (user && user.subscription !== 'pro' && user.role !== 'admin') {
      toast.error('Art Studio requires Pro subscription');
      navigate('/library');
    }
  }, [user, navigate]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  // Update node data
  const updateNodeData = useCallback((nodeId, key, value) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: { ...node.data, [key]: value },
          };
        }
        return node;
      })
    );
  }, [setNodes]);

  // Build prompt from connected nodes
  const buildPromptFromWorkflow = useCallback(() => {
    const combineNode = nodes.find(n => n.type === 'combine');
    if (!combineNode) return null;

    // Find all nodes connected to combine
    const connectedEdges = edges.filter(e => e.target === combineNode.id);
    const connectedNodeIds = connectedEdges.map(e => e.source);
    const connectedNodes = nodes.filter(n => connectedNodeIds.includes(n.id));

    let characterDesc = '';
    let sceneDesc = '';
    let styleValue = 'illustration';
    let actionPrompt = '';

    connectedNodes.forEach(node => {
      if (node.type === 'character') {
        const name = node.data.name || 'A character';
        const desc = node.data.description || '';
        characterDesc = `${name}${desc ? ': ' + desc : ''}`;
      } else if (node.type === 'scene') {
        const name = node.data.name || 'A scene';
        const desc = node.data.description || '';
        const time = node.data.timeOfDay || 'day';
        const weather = node.data.weather || 'clear';
        sceneDesc = `${name}${desc ? ': ' + desc : ''}, ${time}time, ${weather} weather`;
      } else if (node.type === 'style') {
        styleValue = node.data.style || 'illustration';
      } else if (node.type === 'prompt') {
        actionPrompt = node.data.prompt || '';
      }
    });

    const fullPrompt = [actionPrompt, characterDesc, sceneDesc].filter(Boolean).join('. ');
    return { prompt: fullPrompt, style: styleValue };
  }, [nodes, edges]);

  // Generate image
  const generateImage = useCallback(async () => {
    const outputNode = nodes.find(n => n.type === 'output');
    if (!outputNode) {
      toast.error('Add an Output node to generate images');
      return;
    }

    const workflow = buildPromptFromWorkflow();
    if (!workflow || !workflow.prompt) {
      toast.error('Connect nodes and add descriptions to generate');
      return;
    }

    // Set generating state
    setNodes(nds => nds.map(n => 
      n.id === outputNode.id ? { ...n, data: { ...n.data, generating: true } } : n
    ));

    try {
      const response = await fetch(`${API_URL}/api/ai/generate-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: workflow.prompt,
          style: workflow.style
        })
      });

      const data = await response.json();
      
      if (data.success && data.image_base64) {
        const imageUrl = `data:image/png;base64,${data.image_base64}`;
        setNodes(nds => nds.map(n => 
          n.id === outputNode.id ? { ...n, data: { ...n.data, generating: false, generatedImage: imageUrl } } : n
        ));
        toast.success('Image generated!');
      } else {
        throw new Error(data.detail || 'Failed to generate');
      }
    } catch (error) {
      console.error('Generation error:', error);
      toast.error('Failed to generate image');
      setNodes(nds => nds.map(n => 
        n.id === outputNode.id ? { ...n, data: { ...n.data, generating: false } } : n
      ));
    }
  }, [nodes, buildPromptFromWorkflow, token, setNodes]);

  // Download generated image
  const downloadImage = useCallback(() => {
    const outputNode = nodes.find(n => n.type === 'output');
    if (outputNode?.data?.generatedImage) {
      const link = document.createElement('a');
      link.href = outputNode.data.generatedImage;
      link.download = `art-studio-${Date.now()}.png`;
      link.click();
    }
  }, [nodes]);

  // Add new node
  const addNode = useCallback((type) => {
    const newNode = {
      id: `${type}-${Date.now()}`,
      type,
      position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: type === 'character' ? { name: '', description: '' } :
            type === 'style' ? { style: 'illustration' } :
            type === 'scene' ? { name: '', description: '', timeOfDay: 'day', weather: 'clear' } :
            type === 'prompt' ? { prompt: '' } :
            type === 'combine' ? {} :
            { generating: false, generatedImage: null }
    };
    setNodes((nds) => [...nds, newNode]);
  }, [setNodes]);

  // Add callbacks to node data
  const nodesWithCallbacks = nodes.map(node => ({
    ...node,
    data: {
      ...node.data,
      onChange: (key, value) => updateNodeData(node.id, key, value),
      onGenerate: generateImage,
      onDownload: downloadImage,
      onUploadRef: () => {
        fileInputRef.current?.click();
      }
    }
  }));

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/library')} className="text-white">
            <FiArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <FiLayers className="text-purple-400" />
              Art Studio
              <span className="text-xs bg-purple-500 px-2 py-0.5 rounded-full">PRO</span>
            </h1>
            <p className="text-xs text-gray-400">Node-based character & scene creation</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Input 
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="w-40 bg-gray-700 border-gray-600 text-white text-sm"
          />
          <Button variant="outline" className="border-gray-600 text-white hover:bg-gray-700">
            <FiSave className="w-4 h-4 mr-2" />
            Save
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Sidebar - Node Palette */}
        <div className="w-48 bg-gray-800 border-r border-gray-700 p-3 space-y-2">
          <p className="text-xs text-gray-400 uppercase font-bold mb-3">Add Nodes</p>
          
          <button
            onClick={() => addNode('character')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 text-sm transition-colors"
          >
            <FiUser className="w-4 h-4" />
            Character
          </button>
          
          <button
            onClick={() => addNode('scene')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 text-sm transition-colors"
          >
            <FiImage className="w-4 h-4" />
            Scene
          </button>
          
          <button
            onClick={() => addNode('style')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-pink-600/20 hover:bg-pink-600/40 text-pink-300 text-sm transition-colors"
          >
            <FiLayers className="w-4 h-4" />
            Style
          </button>
          
          <button
            onClick={() => addNode('prompt')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 text-sm transition-colors"
          >
            <FiType className="w-4 h-4" />
            Prompt
          </button>
          
          <button
            onClick={() => addNode('combine')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 text-sm transition-colors"
          >
            <FiGrid className="w-4 h-4" />
            Combine
          </button>
          
          <button
            onClick={() => addNode('output')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-600/20 hover:bg-gray-600/40 text-gray-300 text-sm transition-colors"
          >
            <FiZap className="w-4 h-4" />
            Output
          </button>

          <div className="pt-4 border-t border-gray-700 mt-4">
            <p className="text-xs text-gray-400 uppercase font-bold mb-2">Tips</p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Connect nodes by dragging from dots</li>
              <li>• All inputs flow into Combine</li>
              <li>• Combine connects to Output</li>
              <li>• Click Generate to create</li>
            </ul>
          </div>
        </div>

        {/* React Flow Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodesWithCallbacks}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            className="bg-gray-900"
          >
            <Controls className="bg-gray-800 border-gray-700 text-white" />
            <MiniMap 
              className="bg-gray-800 border border-gray-700"
              nodeColor={(node) => {
                switch (node.type) {
                  case 'character': return '#a855f7';
                  case 'style': return '#ec4899';
                  case 'scene': return '#10b981';
                  case 'prompt': return '#f59e0b';
                  case 'combine': return '#6366f1';
                  case 'output': return '#4b5563';
                  default: return '#666';
                }
              }}
            />
            <Background color="#374151" gap={20} />
          </ReactFlow>
        </div>
      </div>

      {/* Hidden file input for reference images */}
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/*"
        onChange={(e) => {
          // Handle reference image upload
          const file = e.target.files?.[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = () => {
              // Find the first character node and set reference
              const charNode = nodes.find(n => n.type === 'character');
              if (charNode) {
                updateNodeData(charNode.id, 'referenceImage', reader.result);
              }
            };
            reader.readAsDataURL(file);
          }
        }}
      />
    </div>
  );
}

export default function ArtStudio() {
  return (
    <ReactFlowProvider>
      <ArtStudioFlow />
    </ReactFlowProvider>
  );
}
