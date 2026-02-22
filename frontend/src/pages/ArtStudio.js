import { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { 
  FiImage, FiUser, FiLayers, FiGrid, FiSave, FiDownload, 
  FiTrash2, FiPlus, FiZap, FiSliders, FiDroplet, FiRefreshCw,
  FiArrowLeft, FiFolder, FiStar, FiCopy, FiEdit2, FiUpload, FiBook, FiCheck,
  FiEye, FiMaximize2, FiSettings, FiX, FiChevronDown, FiChevronUp, FiSearch,
  FiPlay, FiVideo
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
  clothing: ['Casual', 'Formal', 'Fantasy', 'Sci-Fi', 'Futuristic', 'Cyberpunk', 'Medieval', 'Victorian', 'Modern', 'Athletic', 'Armor', 'Streetwear'],
  expression: ['Happy', 'Sad', 'Angry', 'Surprised', 'Neutral', 'Thoughtful', 'Confident', 'Shy']
};

// Art styles with example images - organized by category
// QUICK TEMPLATES - One-click style presets for popular looks (easy for kids!)
const QUICK_TEMPLATES = [
  {
    id: 'fantasy-sunset',
    name: 'Fantasy Sunset Portrait',
    description: 'Dreamy portrait with castle, sunset sky & flowing hair',
    image: 'https://customer-assets.emergentagent.com/job_d83020fd-599b-40ee-9260-c2ebcb28493d/artifacts/xb429ogq_u5425155785_httpss.mj.runjZ4M-NmR9eE_swap_this_girl_into_this_9e29b079-46de-4c87-a9b3-027581d9bbfa_0%20%281%29.png',
    style: 'surreal-portrait',
    lighting: 'golden-hour',
    customStyle: 'fantasy double exposure portrait, castle on cliff in background, dramatic sunset sky with orange and purple clouds, flowing wavy hair with teal blue and blonde highlights, stylish glasses reflecting fantasy scene, extremely detailed digital painting, 8K masterpiece, trending on ArtStation',
    popular: true
  },
  {
    id: 'neon-cyberpunk',
    name: 'Neon Cyberpunk',
    description: 'Pink & blue neon lighting, futuristic vibes',
    image: 'https://static.prod-images.emergentagent.com/jobs/d83020fd-599b-40ee-9260-c2ebcb28493d/images/2aca1b80f7281f04f681e4b095ecc45747ca4144ced5a77a0727272b14942396.png',
    style: 'neon-portrait',
    lighting: 'neon-pink-blue',
    customStyle: 'cyberpunk neon portrait, dramatic pink and blue split lighting, futuristic city background, glowing neon accents, hyper detailed digital art',
    popular: true
  },
  {
    id: 'ethereal-fairy',
    name: 'Ethereal Fairy Tale',
    description: 'Magical glowing portrait with soft dreamy lighting',
    image: 'https://images.pexels.com/photos/31882421/pexels-photo-31882421.jpeg?w=100&h=100&fit=crop',
    style: 'fantasy-portrait',
    lighting: 'soft-glow',
    customStyle: 'ethereal fairy tale portrait, soft magical glow, enchanted forest background, flowing silky hair, luminous skin, butterfly particles, dreamy atmosphere, professional fantasy art',
    popular: true
  },
  {
    id: 'anime-hero',
    name: 'Anime Hero',
    description: 'Bold anime style with dramatic action pose',
    image: 'https://images.unsplash.com/photo-1613376023733-0a73315d9b06?w=100&h=100&fit=crop',
    style: 'anime',
    lighting: 'dramatic',
    customStyle: 'epic anime portrait, vibrant colors, dynamic wind effect on hair, detailed cel shading, Studio Ghibli quality, expressive eyes, heroic expression',
    popular: true
  },
  {
    id: 'chrome-future',
    name: 'Chrome Future',
    description: 'Metallic futuristic with liquid chrome elements',
    image: 'https://images.unsplash.com/photo-1637317099769-ecf4d610d30c?w=100&h=100&fit=crop',
    style: 'chrome-aesthetic',
    lighting: 'studio',
    customStyle: 'chrome metallic portrait, liquid metal collar and accessories, futuristic fashion, smooth stylized features, pink and silver color palette, professional digital art',
    popular: true
  },
  {
    id: 'storybook-magic',
    name: 'Storybook Magic',
    description: 'Whimsical children\'s book illustration style',
    image: 'https://images.unsplash.com/photo-1608889825103-eb5ed706fc64?w=100&h=100&fit=crop',
    style: 'storybook',
    lighting: 'soft-glow',
    customStyle: 'beautiful children\'s book illustration, whimsical charming style, warm inviting colors, magical sparkles, enchanting quality, appealing character design',
    popular: true
  }
];

const ART_STYLE_CATEGORIES = [
  {
    category: 'Sci-Fi & Futuristic',
    styles: [
      { id: 'scifi-portrait', name: 'Sci-Fi Portrait', description: 'Futuristic stylized portrait with chrome elements', image: 'https://static.prod-images.emergentagent.com/jobs/d83020fd-599b-40ee-9260-c2ebcb28493d/images/2aca1b80f7281f04f681e4b095ecc45747ca4144ced5a77a0727272b14942396.png' },
      { id: 'stylized-digital', name: 'Stylized Digital', description: 'Highly stylized digital art, doll-like features', image: 'https://images.unsplash.com/photo-1707912079134-becf5a3598e2?w=100&h=100&fit=crop' },
      { id: 'concept-portrait', name: 'Concept Art Portrait', description: 'AAA game concept art quality', image: 'https://images.pexels.com/photos/7650991/pexels-photo-7650991.jpeg?w=100&h=100&fit=crop' },
      { id: 'chrome-aesthetic', name: 'Chrome Aesthetic', description: 'Liquid metal, chrome, reflective surfaces', image: 'https://images.unsplash.com/photo-1637317099769-ecf4d610d30c?w=100&h=100&fit=crop' },
      { id: 'ethereal-scifi', name: 'Ethereal Sci-Fi', description: 'Dreamy sci-fi with soft atmospheric effects', image: 'https://images.pexels.com/photos/22608985/pexels-photo-22608985.jpeg?w=100&h=100&fit=crop' },
      { id: 'cyberpunk', name: 'Cyberpunk', description: 'Neon-lit futuristic dystopia', image: 'https://images.pexels.com/photos/8107899/pexels-photo-8107899.jpeg?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Advanced Portrait',
    styles: [
      { id: 'neon-portrait', name: 'Neon Portrait', description: 'Dramatic pink/blue neon lighting, hyper-detailed', image: 'https://images.pexels.com/photos/8108554/pexels-photo-8108554.jpeg?w=100&h=100&fit=crop' },
      { id: 'surreal-portrait', name: 'Surreal Double Exposure', description: 'Double exposure with fantasy elements, flowing hair', image: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=100&h=100&fit=crop' },
      { id: 'hyper-digital', name: 'Hyper-Detailed Digital', description: 'Ultra polished digital art, extreme detail', image: 'https://images.unsplash.com/photo-1634986666676-ec8fd927c23d?w=100&h=100&fit=crop' },
      { id: 'aesthetic-portrait', name: 'Aesthetic Portrait', description: 'Trendy aesthetic with soft gradients and glow', image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop' },
      { id: 'fantasy-portrait', name: 'Fantasy Portrait', description: 'Magical portrait with ethereal lighting', image: 'https://images.pexels.com/photos/31882421/pexels-photo-31882421.jpeg?w=100&h=100&fit=crop' },
      { id: 'dramatic-glamour', name: 'Dramatic Glamour', description: 'High fashion with dramatic lighting and detail', image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Realistic',
    styles: [
      { id: 'realistic', name: 'Photorealistic', description: 'Ultra-realistic rendering', image: 'https://images.unsplash.com/photo-1648333676834-d69d732d3528?w=100&h=100&fit=crop' },
      { id: 'portrait', name: 'Portrait', description: 'Classic portrait photography', image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop' },
      { id: 'cinematic', name: 'Cinematic', description: 'Movie-like dramatic lighting', image: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=100&h=100&fit=crop' },
      { id: 'hyperrealistic', name: 'Hyperrealistic', description: 'Extreme detail and realism', image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Illustration',
    styles: [
      { id: 'cartoon', name: 'Cartoon', description: 'Fun colorful cartoon style', image: 'https://images.unsplash.com/photo-1569003339405-ea396a5a8a90?w=100&h=100&fit=crop' },
      { id: 'anime', name: 'Anime', description: 'Japanese animation style', image: 'https://images.unsplash.com/photo-1613376023733-0a73315d9b06?w=100&h=100&fit=crop' },
      { id: 'manga', name: 'Manga', description: 'Japanese comic style', image: 'https://images.unsplash.com/photo-1612178537253-bccd437b730e?w=100&h=100&fit=crop' },
      { id: 'disney', name: 'Disney Style', description: 'Classic Disney animation', image: 'https://images.unsplash.com/photo-1597466765990-64ad1c35dafc?w=100&h=100&fit=crop' },
      { id: 'pixar', name: 'Pixar Style', description: '3D animated movie look', image: 'https://images.unsplash.com/photo-1608889825103-eb5ed706fc64?w=100&h=100&fit=crop' },
      { id: 'chibi', name: 'Chibi', description: 'Cute super-deformed style', image: 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=100&h=100&fit=crop' },
      { id: 'comic', name: 'Comic Book', description: 'Western comic book style', image: 'https://images.pexels.com/photos/7809123/pexels-photo-7809123.jpeg?w=100&h=100&fit=crop' },
      { id: 'graphic-novel', name: 'Graphic Novel', description: 'Detailed comic art', image: 'https://images.unsplash.com/photo-1608889825205-eebdb9fc5806?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Traditional Art',
    styles: [
      { id: 'oil-painting', name: 'Oil Painting', description: 'Classic oil on canvas', image: 'https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=100&h=100&fit=crop' },
      { id: 'watercolor', name: 'Watercolor', description: 'Soft flowing watercolors', image: 'https://images.pexels.com/photos/4860077/pexels-photo-4860077.jpeg?w=100&h=100&fit=crop' },
      { id: 'acrylic', name: 'Acrylic', description: 'Bold acrylic painting', image: 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=100&h=100&fit=crop' },
      { id: 'pastel', name: 'Pastel', description: 'Soft pastel drawing', image: 'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=100&h=100&fit=crop' },
      { id: 'charcoal', name: 'Charcoal', description: 'Dramatic charcoal sketch', image: 'https://images.unsplash.com/photo-1531913764164-f85c52e6e654?w=100&h=100&fit=crop' },
      { id: 'pencil', name: 'Pencil Sketch', description: 'Hand-drawn pencil art', image: 'https://images.unsplash.com/photo-1572853285455-1e3f2a5e4c91?w=100&h=100&fit=crop' },
      { id: 'ink', name: 'Ink Drawing', description: 'Clean ink illustration', image: 'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=100&h=100&fit=crop' },
      { id: 'gouache', name: 'Gouache', description: 'Opaque watercolor style', image: 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Digital Art',
    styles: [
      { id: 'digital-art', name: 'Digital Art', description: 'Modern digital painting', image: 'https://images.unsplash.com/photo-1634986666676-ec8fd927c23d?w=100&h=100&fit=crop' },
      { id: 'concept-art', name: 'Concept Art', description: 'Professional concept style', image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&h=100&fit=crop' },
      { id: 'matte-painting', name: 'Matte Painting', description: 'Epic environment art', image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=100&h=100&fit=crop' },
      { id: 'vector', name: 'Vector Art', description: 'Clean vector graphics', image: 'https://images.unsplash.com/photo-1557683316-973673baf926?w=100&h=100&fit=crop' },
      { id: 'low-poly', name: 'Low Poly', description: 'Geometric low-polygon style', image: 'https://images.unsplash.com/photo-1550684376-efcbd6e3f031?w=100&h=100&fit=crop' },
      { id: 'vaporwave', name: 'Vaporwave', description: 'Retro 80s aesthetic', image: 'https://images.unsplash.com/photo-1550684849-26e4e0bfa21d?w=100&h=100&fit=crop' },
      { id: 'synthwave', name: 'Synthwave', description: 'Neon retro-futurism', image: 'https://images.pexels.com/photos/31002072/pexels-photo-31002072.jpeg?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: '3D & Render',
    styles: [
      { id: '3d-render', name: '3D Render', description: 'Modern 3D rendered look', image: 'https://images.unsplash.com/photo-1633356122102-3fe601e05bd2?w=100&h=100&fit=crop' },
      { id: 'clay-render', name: 'Clay Render', description: 'Soft clay material look', image: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=100&h=100&fit=crop' },
      { id: 'isometric', name: 'Isometric', description: 'Isometric 3D view', image: 'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=100&h=100&fit=crop' },
      { id: 'diorama', name: 'Diorama', description: 'Miniature scene look', image: 'https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=100&h=100&fit=crop' },
      { id: 'unreal-engine', name: 'Game Engine', description: 'Video game quality', image: 'https://images.unsplash.com/photo-1552820728-8b83bb6b2b0c?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Fantasy & Sci-Fi',
    styles: [
      { id: 'fantasy', name: 'Fantasy Art', description: 'Epic fantasy illustration', image: 'https://images.unsplash.com/photo-1767709879762-c7a6ce819aeb?w=100&h=100&fit=crop' },
      { id: 'ethereal-fantasy', name: 'Ethereal Fantasy', description: 'Dreamy, soft flowing digital art with mystical atmosphere', image: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=100&h=100&fit=crop' },
      { id: 'dark-fantasy', name: 'Dark Fantasy', description: 'Gothic dark fantasy', image: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=100&h=100&fit=crop' },
      { id: 'sci-fi', name: 'Sci-Fi', description: 'Futuristic science fiction', image: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=100&h=100&fit=crop' },
      { id: 'cyberpunk', name: 'Cyberpunk', description: 'Neon-lit dystopian', image: 'https://images.pexels.com/photos/20278554/pexels-photo-20278554.jpeg?w=100&h=100&fit=crop' },
      { id: 'steampunk', name: 'Steampunk', description: 'Victorian machinery', image: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=100&h=100&fit=crop' },
      { id: 'solarpunk', name: 'Solarpunk', description: 'Green utopian future', image: 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=100&h=100&fit=crop' },
      { id: 'surreal-dreamscape', name: 'Surreal Dreamscape', description: 'Surreal flowing landscapes with magical elements', image: 'https://images.unsplash.com/photo-1507400492013-162706c8c05e?w=100&h=100&fit=crop' },
      { id: 'luminous-ethereal', name: 'Luminous Ethereal', description: 'Celestial dreamscape with glowing light, cosmic skies, polished digital art', image: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=100&h=100&fit=crop' },
      { id: 'celestial-fantasy', name: 'Celestial Fantasy', description: 'Divine beings, nebula skies, luminous smooth rendering', image: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Children\'s Book',
    styles: [
      { id: 'storybook', name: 'Storybook', description: 'Classic children\'s book', image: 'https://images.pexels.com/photos/9258376/pexels-photo-9258376.jpeg?w=100&h=100&fit=crop' },
      { id: 'picture-book', name: 'Picture Book', description: 'Colorful picture book', image: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=100&h=100&fit=crop' },
      { id: 'whimsical', name: 'Whimsical', description: 'Playful and dreamy', image: 'https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=100&h=100&fit=crop' },
      { id: 'crayon', name: 'Crayon', description: 'Child\'s crayon drawing', image: 'https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=100&h=100&fit=crop' },
      { id: 'paper-cutout', name: 'Paper Cutout', description: 'Layered paper craft', image: 'https://images.unsplash.com/photo-1582201942988-13e60e4556ee?w=100&h=100&fit=crop' },
      { id: 'felt', name: 'Felt Art', description: 'Soft felt texture', image: 'https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Retro & Vintage',
    styles: [
      { id: 'pixel-art', name: 'Pixel Art', description: 'Retro 8-bit graphics', image: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=100&h=100&fit=crop' },
      { id: 'retro-game', name: 'Retro Game', description: '16-bit video game', image: 'https://images.unsplash.com/photo-1551103782-8ab07afd45c1?w=100&h=100&fit=crop' },
      { id: 'vintage-poster', name: 'Vintage Poster', description: 'Old advertising poster', image: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=100&h=100&fit=crop' },
      { id: 'art-deco', name: 'Art Deco', description: '1920s art deco style', image: 'https://images.unsplash.com/photo-1533154683836-84ea7a0bc310?w=100&h=100&fit=crop' },
      { id: 'art-nouveau', name: 'Art Nouveau', description: 'Organic flowing lines', image: 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=100&h=100&fit=crop' },
      { id: 'pop-art', name: 'Pop Art', description: 'Bold pop art style', image: 'https://images.unsplash.com/photo-1561214115-f2f134cc4912?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Cultural',
    styles: [
      { id: 'ukiyo-e', name: 'Ukiyo-e', description: 'Japanese woodblock print', image: 'https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=100&h=100&fit=crop' },
      { id: 'chinese-ink', name: 'Chinese Ink', description: 'Traditional Chinese ink', image: 'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=100&h=100&fit=crop' },
      { id: 'persian-miniature', name: 'Persian Miniature', description: 'Detailed Persian art', image: 'https://images.unsplash.com/photo-1545156521-77bd85671d30?w=100&h=100&fit=crop' },
      { id: 'aboriginal', name: 'Aboriginal', description: 'Dot painting style', image: 'https://images.unsplash.com/photo-1578926375605-eaf7559b1458?w=100&h=100&fit=crop' },
      { id: 'tribal', name: 'Tribal', description: 'African tribal art', image: 'https://images.unsplash.com/photo-1582582621959-48d27397dc69?w=100&h=100&fit=crop' },
      { id: 'celtic', name: 'Celtic', description: 'Intricate Celtic designs', image: 'https://images.unsplash.com/photo-1560260240-c6ef90a160c0?w=100&h=100&fit=crop' },
    ]
  },
  {
    category: 'Stylized',
    styles: [
      { id: 'minimalist', name: 'Minimalist', description: 'Simple clean design', image: 'https://images.unsplash.com/photo-1557683316-973673baf926?w=100&h=100&fit=crop' },
      { id: 'abstract', name: 'Abstract', description: 'Abstract artistic style', image: 'https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=100&h=100&fit=crop' },
      { id: 'surreal', name: 'Surrealist', description: 'Dreamlike surrealism', image: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=100&h=100&fit=crop' },
      { id: 'impressionist', name: 'Impressionist', description: 'Monet-like brushwork', image: 'https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?w=100&h=100&fit=crop' },
      { id: 'expressionist', name: 'Expressionist', description: 'Emotional bold style', image: 'https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=100&h=100&fit=crop' },
      { id: 'cubist', name: 'Cubist', description: 'Picasso-like cubism', image: 'https://images.unsplash.com/photo-1577083552431-6e5fd01988ec?w=100&h=100&fit=crop' },
    ]
  }
];

// Flatten for easy access
const ART_STYLES = ART_STYLE_CATEGORIES.flatMap(cat => 
  cat.styles.map(style => ({ ...style, category: cat.category }))
);

// Scene presets
const SCENE_PRESETS = [
  { id: 'forest', name: 'Enchanted Forest', prompt: 'magical forest with glowing flowers and mystical lighting', thumbnail: 'https://images.unsplash.com/photo-1770203691538-23b02e1b11ce?w=400&h=225&fit=crop' },
  { id: 'castle', name: 'Castle Interior', prompt: 'grand castle interior with stone walls and chandeliers', thumbnail: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=225&fit=crop' },
  { id: 'beach', name: 'Tropical Beach', prompt: 'beautiful tropical beach with crystal clear water and palm trees', thumbnail: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=225&fit=crop' },
  { id: 'city', name: 'Modern City', prompt: 'bustling modern city street with skyscrapers', thumbnail: 'https://images.unsplash.com/photo-1747499967281-c0c5eec9933c?w=400&h=225&fit=crop' },
  { id: 'space', name: 'Outer Space', prompt: 'cosmic space scene with stars and nebulae', thumbnail: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400&h=225&fit=crop' },
  { id: 'underwater', name: 'Underwater', prompt: 'underwater scene with coral reefs and sea life', thumbnail: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=225&fit=crop' },
  { id: 'mountain', name: 'Mountain Peak', prompt: 'majestic mountain peak with snow and clouds', thumbnail: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=225&fit=crop' },
  { id: 'library', name: 'Ancient Library', prompt: 'ancient library with towering bookshelves and warm lighting', thumbnail: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=400&h=225&fit=crop' },
  { id: 'dreamscape', name: 'Dreamscape', prompt: 'surreal dreamlike landscape with floating islands and ethereal light', thumbnail: 'https://images.unsplash.com/photo-1766307543930-a35e9417b2d5?w=400&h=225&fit=crop' },
  { id: 'sunset-cliffs', name: 'Sunset Cliffs', prompt: 'dramatic coastal cliffs at golden hour with crashing waves below', thumbnail: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400&h=225&fit=crop' },
  { id: 'aurora', name: 'Northern Lights', prompt: 'arctic landscape under dancing aurora borealis lights', thumbnail: 'https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=400&h=225&fit=crop' },
  { id: 'cherry-blossom', name: 'Cherry Blossom', prompt: 'peaceful Japanese garden with cherry blossom trees and koi pond', thumbnail: 'https://images.unsplash.com/photo-1522383225653-ed111181a951?w=400&h=225&fit=crop' },
  { id: 'ruins', name: 'Ancient Ruins', prompt: 'mysterious ancient ruins overgrown with vines and moss', thumbnail: 'https://images.unsplash.com/photo-1558998708-ed5f8bb29920?w=400&h=225&fit=crop' },
  { id: 'throne-room', name: 'Throne Room', prompt: 'majestic royal throne room with red carpets and golden decorations', thumbnail: 'https://images.unsplash.com/photo-1574108425255-4e3b4e21caa0?w=400&h=225&fit=crop' },
  { id: 'tavern', name: 'Medieval Tavern', prompt: 'cozy medieval tavern with fireplace and wooden beams', thumbnail: 'https://images.unsplash.com/photo-1617202074052-fa303398aa00?w=400&h=225&fit=crop' },
  { id: 'garden', name: 'Secret Garden', prompt: 'hidden secret garden with magical flowers and stone pathways', thumbnail: 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=400&h=225&fit=crop' },
  { id: 'desert', name: 'Desert Oasis', prompt: 'golden desert dunes with a lush oasis and palm trees', thumbnail: 'https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=400&h=225&fit=crop' },
  { id: 'crystal-cave', name: 'Crystal Cave', prompt: 'underground cave filled with glowing crystals and stalactites', thumbnail: 'https://images.unsplash.com/photo-1544476915-ed1370594142?w=400&h=225&fit=crop' },
  { id: 'floating-islands', name: 'Floating Islands', prompt: 'magical floating islands in the sky with waterfalls', thumbnail: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400&h=225&fit=crop' },
  { id: 'moonlit-lake', name: 'Moonlit Lake', prompt: 'serene lake reflecting the full moon with mist on the water', thumbnail: 'https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=400&h=225&fit=crop' },
  { id: 'battlefield', name: 'Battlefield', prompt: 'dramatic battlefield scene with banners and distant armies', thumbnail: 'https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=400&h=225&fit=crop' },
  { id: 'village', name: 'Village Square', prompt: 'charming fantasy village square with cobblestone streets', thumbnail: 'https://images.unsplash.com/photo-1569701813229-33284b643e3c?w=400&h=225&fit=crop' },
  { id: 'ship-deck', name: 'Ship Deck', prompt: 'wooden sailing ship deck with ocean waves and stormy skies', thumbnail: 'https://images.unsplash.com/photo-1534190239940-9ba8944ea261?w=400&h=225&fit=crop' },
  { id: 'academy', name: 'Magic Academy', prompt: 'grand magical academy with floating books and mystical artifacts', thumbnail: 'https://images.unsplash.com/photo-1568667256549-094345857637?w=400&h=225&fit=crop' }
];

export default function ArtStudio() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const referenceInputRef = useRef(null);
  const styleRefInputRef = useRef(null);
  const charRefInputRef = useRef(null);
  
  // Main state
  const [activeTab, setActiveTab] = useState('character'); // character, scene, gallery
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [gallery, setGallery] = useState([]);
  const [selectedGalleryItem, setSelectedGalleryItem] = useState(null);
  const [userBooks, setUserBooks] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState('general'); // 'general' or book ID
  
  // Reference image state - DUAL REFERENCES
  const [styleReferenceImage, setStyleReferenceImage] = useState(null); // For art style/look and feel
  const [characterReferenceImage, setCharacterReferenceImage] = useState(null); // For character appearance
  const [extractedStylePrompt, setExtractedStylePrompt] = useState(''); // AI-extracted prompt from style ref
  const [extractedCharPrompt, setExtractedCharPrompt] = useState(''); // AI-extracted prompt from char ref
  const [isExtractingPrompt, setIsExtractingPrompt] = useState(false);
  const [showGalleryPicker, setShowGalleryPicker] = useState(false);
  const [galleryPickerTarget, setGalleryPickerTarget] = useState('style'); // 'style' or 'character'
  
  // Prompt history state
  const [promptHistory, setPromptHistory] = useState([]);
  const [showHistoryDropdown, setShowHistoryDropdown] = useState(false);
  
  // Style search and category collapse state
  const [styleSearchQuery, setStyleSearchQuery] = useState('');
  const [collapsedCategories, setCollapsedCategories] = useState({}); // All expanded by default
  const [selectedTemplate, setSelectedTemplate] = useState(null); // Quick template selection
  
  // Animation state
  const [showAnimateModal, setShowAnimateModal] = useState(false);
  const [animatingImage, setAnimatingImage] = useState(null);
  const [animationMotion, setAnimationMotion] = useState('gentle breathing, hair flowing');
  const [animationStyle, setAnimationStyle] = useState('natural');
  const [isAnimating, setIsAnimating] = useState(false);
  const [animatedVideo, setAnimatedVideo] = useState(null);
  
  // Gallery type filter state
  const [galleryTypeFilter, setGalleryTypeFilter] = useState('all'); // 'all', 'images', 'animations'
  
  // Apply a quick template (one-click setup)
  const applyQuickTemplate = (template) => {
    setSelectedTemplate(template.id);
    setSelectedStyle(template.style);
    setLightingPreset(template.lighting);
    setCustomStyleDescription(template.customStyle);
  };
  
  // Animation progress state
  const [animationProgress, setAnimationProgress] = useState(0);
  const [animationMessage, setAnimationMessage] = useState('');
  const [animationJobId, setAnimationJobId] = useState(null);
  
  // Animate an image using Sora 2 with polling
  const animateImage = async () => {
    if (!animatingImage) return;
    
    setIsAnimating(true);
    setAnimationProgress(0);
    setAnimationMessage('Starting animation...');
    setAnimatedVideo(null);
    
    try {
      toast.info('Animation started - this takes 2-5 minutes. Watch the progress bar!', {
        duration: 5000
      });
      
      // Start the animation job
      const startResponse = await fetch(`${API_URL}/api/art-studio/animate-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          image_url: animatingImage,
          motion_prompt: animationMotion,
          duration: 4,
          style: animationStyle
        })
      });
      
      const startData = await startResponse.json();
      
      if (!startData.success || !startData.job_id) {
        throw new Error(startData.detail || 'Failed to start animation');
      }
      
      const jobId = startData.job_id;
      setAnimationJobId(jobId);
      
      // Poll for status using recursive setTimeout to avoid stale closures
      const pollStatus = async () => {
        try {
          const statusResponse = await fetch(`${API_URL}/api/art-studio/animation-status/${jobId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          
          if (!statusResponse.ok) {
            console.error('Status response not ok:', statusResponse.status);
            // Continue polling
            setTimeout(pollStatus, 3000);
            return;
          }
          
          const statusData = await statusResponse.json();
          console.log('Animation status:', statusData);
          
          // Update progress
          setAnimationProgress(statusData.progress || 0);
          setAnimationMessage(statusData.message || 'Processing...');
          
          if (statusData.status === 'completed') {
            const videoUrl = `data:video/mp4;base64,${statusData.video_base64}`;
            setAnimatedVideo(videoUrl);
            toast.success('Animation complete!');
            setIsAnimating(false);
            setAnimationJobId(null);
          } else if (statusData.status === 'failed') {
            toast.error(statusData.message || 'Animation failed');
            setIsAnimating(false);
            setAnimationJobId(null);
          } else {
            // Continue polling
            setTimeout(pollStatus, 3000);
          }
        } catch (pollError) {
          console.error('Polling error:', pollError);
          // Continue polling on transient errors
          setTimeout(pollStatus, 3000);
        }
      };
      
      // Start polling
      pollStatus();
      
      // Timeout after 10 minutes
      setTimeout(() => {
        setIsAnimating(prev => {
          if (prev) {
            toast.error('Animation timed out. Please try again.');
            setAnimationJobId(null);
            return false;
          }
          return prev;
        });
      }, 600000);
      
    } catch (error) {
      console.error('Animation error:', error);
      toast.error('Animation: ' + (error.message || 'An error occurred'));
      setIsAnimating(false);
      setAnimationJobId(null);
    }
  };
  
  // Open animate modal for a specific image
  const openAnimateModal = (imageUrl) => {
    setAnimatingImage(imageUrl);
    setAnimatedVideo(null);
    setShowAnimateModal(true);
  };
  
  // PRO FEATURES STATE
  const [showStylePreview, setShowStylePreview] = useState(false);
  const [negativePrompt, setNegativePrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('1:1'); // 1:1, 16:9, 9:16, 4:3, 3:4
  const [qualityLevel, setQualityLevel] = useState('high'); // low, medium, high, ultra
  const [variationCount, setVariationCount] = useState(1); // 1-4 variations
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [compareStyles, setCompareStyles] = useState([]); // For compare mode
  const [showCompareMode, setShowCompareMode] = useState(false);
  const [generationHistory, setGenerationHistory] = useState([]); // Recent generations
  const [galleryFilter, setGalleryFilter] = useState('all'); // 'all' or book_id
  
  // Custom style description for advanced users
  const [customStyleDescription, setCustomStyleDescription] = useState('');
  const [lightingPreset, setLightingPreset] = useState('natural'); // natural, neon-pink-blue, golden-hour, dramatic, soft-glow, studio
  
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
    additionalDetails: '',
    transparentBackground: false  // For compositing characters into scenes
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
  
  // Character Profiles state (for consistency)
  const [characterProfiles, setCharacterProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showProfileSelector, setShowProfileSelector] = useState(false);
  
  // Load gallery and books on mount
  useEffect(() => {
    if (token) {
      loadGallery();
      loadUserBooks();
      loadPromptHistory();
      loadCharacterProfiles();
    }
  }, [token]);
  
  const loadCharacterProfiles = async () => {
    try {
      const response = await fetch(`${API_URL}/api/art-studio/character-profiles`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCharacterProfiles(data.profiles || []);
      }
    } catch (error) {
      console.error('Failed to load character profiles:', error);
    }
  };
  
  const saveCharacterProfile = async () => {
    if (!character.name) {
      alert('Please enter a character name');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/art-studio/character-profiles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: character.name,
          description: buildCharacterPrompt(),
          reference_images: characterReferenceImage ? [characterReferenceImage] : [],
          traits: {
            gender: character.gender,
            ageGroup: character.ageGroup,
            bodyType: character.bodyType,
            skinTone: character.skinTone,
            hairColor: character.hairColor,
            hairStyle: character.hairStyle,
            eyeColor: character.eyeColor,
            clothing: character.clothing,
            expression: character.expression
          },
          style_preferences: [selectedStyle],
          book_id: selectedBookId !== 'general' ? selectedBookId : null
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(`Character profile "${character.name}" saved! Use this profile for consistent character generation.`);
        loadCharacterProfiles();
        setShowProfileModal(false);
      }
    } catch (error) {
      console.error('Failed to save character profile:', error);
      alert('Failed to save character profile');
    }
  };
  
  const generateWithProfile = async (profileId) => {
    if (!token) {
      navigate('/login');
      return;
    }
    
    setIsGenerating(true);
    setGeneratedImage(null);
    
    try {
      const params = new URLSearchParams({
        profile_id: profileId,
        prompt: character.additionalDetails || 'standing pose, looking at viewer',
        style: selectedStyle
      });
      
      if (scene.customPrompt) {
        params.append('scene', scene.customPrompt);
      }
      
      const response = await fetch(`${API_URL}/api/art-studio/generate-consistent?${params}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGeneratedImage(data.image_url);
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
  
  const loadPromptHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/api/art-studio/prompt-history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPromptHistory(data.history || []);
      }
    } catch (error) {
      console.error('Failed to load prompt history:', error);
    }
  };
  
  const savePromptToHistory = async (prompt) => {
    if (!prompt.trim()) return;
    // Don't save duplicates
    if (promptHistory.includes(prompt)) return;
    
    try {
      await fetch(`${API_URL}/api/art-studio/prompt-history`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ prompt })
      });
      // Update local state
      setPromptHistory(prev => [prompt, ...prev].slice(0, 20)); // Keep last 20
    } catch (error) {
      console.error('Failed to save prompt to history:', error);
    }
  };
  
  // Extract prompt from reference image using AI
  const extractPromptFromImage = async (imageUrl, target) => {
    if (!token) return;
    
    setIsExtractingPrompt(true);
    try {
      const response = await fetch(`${API_URL}/api/art-studio/analyze-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          image_url: imageUrl,
          analysis_type: target === 'style' ? 'style' : 'character'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (target === 'style') {
          setExtractedStylePrompt(data.extracted_prompt || '');
        } else {
          setExtractedCharPrompt(data.extracted_prompt || '');
        }
      }
    } catch (error) {
      console.error('Failed to extract prompt:', error);
    } finally {
      setIsExtractingPrompt(false);
    }
  };
  
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
    
    // Build a rich character description for high quality output
    if (character.name) {
      traits.push(`${character.name}`);
    }
    traits.push(`${character.gender} character`);
    traits.push(`${character.ageGroup.toLowerCase()} age`);
    traits.push(`${character.bodyType.toLowerCase()} body type`);
    traits.push(`beautiful ${character.skinTone.toLowerCase()} skin`);
    traits.push(`${character.hairColor.toLowerCase()} ${character.hairStyle.toLowerCase()} hair`);
    traits.push(`stunning ${character.eyeColor.toLowerCase()} eyes`);
    traits.push(`wearing ${character.clothing.toLowerCase()} attire`);
    traits.push(`${character.expression.toLowerCase()} expression`);
    
    if (character.additionalDetails) {
      traits.push(character.additionalDetails);
    }
    
    // Add quality boosters for better generation
    traits.push('beautiful detailed face');
    traits.push('expressive eyes');
    traits.push('professional portrait');
    
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
      let useTransparentBg = false;
      
      // Quality level mapping
      const qualityBoosts = {
        low: '',
        medium: ', detailed',
        high: ', highly detailed, professional quality, sharp focus',
        ultra: ', ultra detailed, 8K resolution, masterpiece quality, best quality, sharp focus, professional lighting'
      };
      
      if (activeTab === 'character') {
        fullPrompt = `${buildCharacterPrompt()}, ${styleData?.name || 'fantasy'} art style${qualityBoosts[qualityLevel] || qualityBoosts.high}`;
        useTransparentBg = character.transparentBackground;
        // Add transparent background instruction to prompt if enabled
        if (useTransparentBg) {
          fullPrompt += ', isolated on transparent background, PNG cutout style, no background, clean edges';
        }
        // Save additional details to history
        if (character.additionalDetails?.trim()) {
          savePromptToHistory(character.additionalDetails.trim());
        }
        
        // Use IP-Adapter style endpoint if character reference is provided
        if (characterReferenceImage) {
          try {
            const consistentResponse = await fetch(`${API_URL}/api/art-studio/generate-with-reference`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                prompt: fullPrompt,
                characterReferenceImage: characterReferenceImage,
                styleReferenceImage: styleReferenceImage,
                style: selectedStyle,
                transparentBackground: useTransparentBg
              })
            });
            
            if (consistentResponse.ok) {
              const data = await consistentResponse.json();
              setGeneratedImage(data.image_url);
              // Update extracted prompts with the detailed descriptions
              if (data.character_description) {
                setExtractedCharPrompt(data.character_description);
              }
              if (data.style_description) {
                setExtractedStylePrompt(data.style_description);
              }
              setGenerationHistory(prev => [{
                image: data.image_url,
                prompt: fullPrompt,
                style: selectedStyle,
                timestamp: new Date(),
                type: 'consistent_character'
              }, ...prev].slice(0, 20));
              loadGallery();
              setIsGenerating(false);
              return; // Exit early - we used the consistent endpoint
            }
          } catch (err) {
            console.log('Consistent generation failed, falling back to standard:', err);
            // Fall through to standard generation
          }
        }
      } else if (activeTab === 'scene') {
        fullPrompt = `${buildScenePrompt()}, ${styleData?.name || 'fantasy'} art style${qualityBoosts[qualityLevel] || qualityBoosts.high}`;
        // Save custom prompt to history
        if (scene.customPrompt?.trim()) {
          savePromptToHistory(scene.customPrompt.trim());
        }
      }
      
      // Add extracted prompts from reference images if available (for fallback standard generation)
      if (extractedStylePrompt) {
        fullPrompt += `, art style like: ${extractedStylePrompt}`;
      }
      if (extractedCharPrompt && activeTab === 'character') {
        fullPrompt += `, character reference: ${extractedCharPrompt}`;
      }
      
      // Add negative prompt if specified
      const finalNegativePrompt = negativePrompt.trim() || 'blurry, low quality, distorted, deformed, bad anatomy, watermark, signature';
      
      const response = await fetch(`${API_URL}/api/art-studio/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: fullPrompt,
          negativePrompt: finalNegativePrompt,
          style: selectedStyle,
          type: activeTab,
          characterData: activeTab === 'character' ? character : null,
          sceneData: activeTab === 'scene' ? scene : null,
          styleReferenceImage: styleReferenceImage,
          characterReferenceImage: characterReferenceImage,
          bookId: selectedBookId !== 'general' ? selectedBookId : null,
          transparentBackground: useTransparentBg,
          aspectRatio: aspectRatio,
          qualityLevel: qualityLevel,
          customStyleDescription: customStyleDescription,
          lightingPreset: lightingPreset
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGeneratedImage(data.image_url);
        // Add to generation history
        setGenerationHistory(prev => [{
          image: data.image_url,
          prompt: fullPrompt,
          style: selectedStyle,
          timestamp: new Date()
        }, ...prev].slice(0, 20)); // Keep last 20
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
          sceneData: scene,
          bookId: selectedBookId !== 'general' ? selectedBookId : null
        })
      });
      
      if (response.ok) {
        loadGallery();
        alert('Image saved to gallery!');
      }
    } catch (error) {
      console.error('Failed to save:', error);
    }
  };
  
  // Handle reference image upload - supports both style and character targets
  const handleReferenceUpload = (e, target = null) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        if (target === 'style') {
          setStyleReferenceImage(reader.result);
        } else if (target === 'character') {
          setCharacterReferenceImage(reader.result);
        } else {
          // Legacy fallback - use gallery picker target
          if (galleryPickerTarget === 'style') {
            setStyleReferenceImage(reader.result);
          } else {
            setCharacterReferenceImage(reader.result);
          }
        }
      };
      reader.readAsDataURL(file);
    }
    // Reset file input
    e.target.value = '';
  };
  
  // Select gallery image as reference
  const selectGalleryAsReference = (imageUrl) => {
    if (galleryPickerTarget === 'style') {
      setStyleReferenceImage(imageUrl);
    } else {
      setCharacterReferenceImage(imageUrl);
    }
    setShowGalleryPicker(false);
  };
  
  // Download generated image
  const downloadImage = async (imageUrl, filename) => {
    try {
      // Fetch the image as blob to bypass CORS issues
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `azories-art-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Cleanup
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback: open in new tab
      window.open(imageUrl, '_blank');
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
              data-testid="back-button"
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
          
          <div className="flex items-center gap-3">
            {/* Pro Studio Link */}
            <Button 
              onClick={() => navigate('/pro-studio')}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
              data-testid="pro-studio-btn"
            >
              <FiVideo className="w-4 h-4 mr-2" />
              Pro Studio
              <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-white/20 rounded">NEW</span>
            </Button>
            
            {/* Expert Mode Link */}
            <Button 
              variant="outline" 
              onClick={() => navigate('/art-studio/expert')}
              className="border-amber-500/50 text-amber-300 hover:bg-amber-500/20"
              data-testid="expert-mode-btn"
            >
              <FiStar className="w-4 h-4 mr-2" />
              Expert Mode
              <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-amber-500/30 rounded">Node Workflow</span>
            </Button>
            
            {/* Book Assignment Dropdown */}
            <div className="flex items-center gap-2">
              <FiBook className="text-purple-400 w-4 h-4" />
              <Select value={selectedBookId} onValueChange={setSelectedBookId}>
                <SelectTrigger className="w-48 bg-black/30 border-white/20 text-white text-sm" data-testid="book-assignment-select">
                  <SelectValue placeholder="Assign to book..." />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1520] border-white/20">
                  <SelectItem value="general" className="text-white hover:bg-white/10">
                    📁 General Library
                  </SelectItem>
                  {userBooks.map(book => (
                    <SelectItem key={book.id} value={book.id} className="text-white hover:bg-white/10">
                      📖 {book.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button 
              variant="outline" 
              className="border-purple-500/50 text-purple-300 hover:bg-purple-500/20"
              onClick={() => setActiveTab('gallery')}
              data-testid="gallery-button"
            >
              <FiFolder className="w-4 h-4 mr-2" />
              My Gallery ({gallery.length})
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 flex-wrap">
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
            variant={activeTab === 'animate' ? 'default' : 'outline'}
            onClick={() => setActiveTab('animate')}
            className={activeTab === 'animate' ? 'bg-gradient-to-r from-pink-600 to-purple-600' : 'border-pink-500/50 text-pink-300 hover:bg-pink-500/20'}
            data-testid="animate-tab-btn"
          >
            <FiVideo className="w-4 h-4 mr-2" />
            Animate
            <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-pink-500/30 rounded">NEW</span>
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

        {/* Main Content with Art Styles Sidebar */}
        <div className="flex gap-6">
          {/* Left Sidebar - Art Styles (scrollable) */}
          {(activeTab === 'character' || activeTab === 'scene') && (
            <div className="w-64 flex-shrink-0">
              <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-4 sticky top-4 max-h-[calc(100vh-180px)] overflow-y-auto">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2 sticky top-0 bg-[#1a1520] py-2 -mt-2 -mx-4 px-4 border-b border-white/10 z-10">
                  <FiSliders className="text-purple-400" />
                  Art Styles
                  <span className="text-xs text-white/40 ml-auto">{ART_STYLES.length} styles</span>
                </h3>
                
                {/* Search Bar */}
                <div className="relative mb-3">
                  <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                  <input
                    type="text"
                    placeholder="Search styles..."
                    value={styleSearchQuery}
                    onChange={(e) => setStyleSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-black/30 border border-white/20 rounded-lg text-white text-sm placeholder:text-white/40 focus:border-purple-500/50 focus:outline-none"
                    data-testid="style-search-input"
                  />
                  {styleSearchQuery && (
                    <button
                      onClick={() => setStyleSearchQuery('')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
                    >
                      <FiX className="w-4 h-4" />
                    </button>
                  )}
                </div>
                
                {/* QUICK TEMPLATES - One-click popular styles (EASY FOR KIDS!) */}
                <div className="mb-4 pb-4 border-b border-white/10">
                  <h4 className="text-xs font-bold text-yellow-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                    <FiStar className="w-3 h-3" />
                    Quick Templates
                    <span className="text-white/40 font-normal">(1-click!)</span>
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {QUICK_TEMPLATES.map(template => (
                      <button
                        key={template.id}
                        onClick={() => applyQuickTemplate(template)}
                        data-testid={`template-${template.id}`}
                        className={`relative group rounded-lg overflow-hidden aspect-square border-2 transition-all ${
                          selectedTemplate === template.id
                            ? 'border-yellow-400 shadow-lg shadow-yellow-400/30'
                            : 'border-white/10 hover:border-white/30'
                        }`}
                      >
                        <img 
                          src={template.image} 
                          alt={template.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                        <div className="absolute bottom-0 left-0 right-0 p-1.5">
                          <p className="text-[9px] font-medium text-white truncate">{template.name}</p>
                        </div>
                        {selectedTemplate === template.id && (
                          <div className="absolute top-1 right-1 w-4 h-4 bg-yellow-400 rounded-full flex items-center justify-center">
                            <FiCheck className="w-2.5 h-2.5 text-black" />
                          </div>
                        )}
                        {template.popular && selectedTemplate !== template.id && (
                          <div className="absolute top-1 left-1">
                            <span className="text-[8px] bg-pink-500 text-white px-1 py-0.5 rounded">Popular</span>
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                  <p className="text-[10px] text-white/40 mt-2 text-center">
                    Click a template to apply style + lighting + effects instantly!
                  </p>
                </div>
                
                {/* Style Preview Button */}
                <button
                  onClick={() => setShowStylePreview(true)}
                  className="w-full mb-4 py-2 px-3 rounded-lg bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 text-white text-sm flex items-center justify-center gap-2 hover:from-purple-500/30 hover:to-pink-500/30 transition-all"
                  data-testid="open-style-preview-btn"
                >
                  <FiEye className="w-4 h-4" />
                  Preview All Styles
                </button>
                
                {ART_STYLE_CATEGORIES.map(category => {
                  // Filter styles based on search
                  const filteredStyles = styleSearchQuery
                    ? category.styles.filter(style =>
                        style.name.toLowerCase().includes(styleSearchQuery.toLowerCase()) ||
                        style.description.toLowerCase().includes(styleSearchQuery.toLowerCase())
                      )
                    : category.styles;
                  
                  // Don't show empty categories when searching
                  if (styleSearchQuery && filteredStyles.length === 0) return null;
                  
                  const isCollapsed = collapsedCategories[category.category];
                  
                  return (
                    <div key={category.category} className="mb-4">
                      <button
                        onClick={() => setCollapsedCategories(prev => ({
                          ...prev,
                          [category.category]: !prev[category.category]
                        }))}
                        className="w-full flex items-center justify-between text-xs font-medium text-purple-400 uppercase tracking-wider mb-2 hover:text-purple-300 transition-colors"
                      >
                        <span className="flex items-center gap-1">
                          {category.category}
                          <span className="text-white/30 normal-case">({filteredStyles.length})</span>
                        </span>
                        {isCollapsed ? <FiChevronDown className="w-3 h-3" /> : <FiChevronUp className="w-3 h-3" />}
                      </button>
                      
                      {!isCollapsed && (
                        <div className="space-y-1">
                          {filteredStyles.map(style => (
                            <button
                              key={style.id}
                              onClick={() => setSelectedStyle(style.id)}
                              data-testid={`style-${style.id}`}
                              className={`w-full text-left px-2 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                                selectedStyle === style.id
                                  ? 'bg-purple-500/30 border border-purple-500/50 text-white'
                                  : 'hover:bg-white/5 text-white/70 hover:text-white border border-transparent'
                              }`}
                            >
                              {/* Style Preview Image */}
                              <div className="w-10 h-10 rounded-md overflow-hidden flex-shrink-0 bg-black/30">
                                {style.image && (
                                  <img 
                                    src={style.image} 
                                    alt={style.name}
                                    className="w-full h-full object-cover"
                                    loading="lazy"
                                  />
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-medium truncate">{style.name}</span>
                                  {selectedStyle === style.id && (
                                    <FiCheck className="w-3 h-3 text-purple-400 flex-shrink-0" />
                                  )}
                                </div>
                                <p className="text-[10px] text-white/40 truncate">{style.description}</p>
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
                
                {/* Advanced Options Panel */}
                <div className="mt-4 pt-4 border-t border-white/10">
                  <button
                    onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                    className="w-full flex items-center justify-between text-white/70 hover:text-white transition-colors"
                  >
                    <span className="flex items-center gap-2 text-sm font-medium">
                      <FiSettings className="w-4 h-4" />
                      Pro Options
                    </span>
                    {showAdvancedOptions ? <FiChevronUp className="w-4 h-4" /> : <FiChevronDown className="w-4 h-4" />}
                  </button>
                  
                  <AnimatePresence>
                    {showAdvancedOptions && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 space-y-4">
                          {/* Quality Level */}
                          <div>
                            <label className="text-xs text-white/60 mb-1.5 block">Quality Level</label>
                            <div className="grid grid-cols-4 gap-1">
                              {['low', 'medium', 'high', 'ultra'].map(q => (
                                <button
                                  key={q}
                                  onClick={() => setQualityLevel(q)}
                                  className={`py-1.5 px-2 text-[10px] rounded-md transition-all capitalize ${
                                    qualityLevel === q
                                      ? 'bg-purple-500 text-white'
                                      : 'bg-white/10 text-white/60 hover:bg-white/20'
                                  }`}
                                >
                                  {q}
                                </button>
                              ))}
                            </div>
                          </div>
                          
                          {/* Aspect Ratio */}
                          <div>
                            <label className="text-xs text-white/60 mb-1.5 block">Aspect Ratio</label>
                            <div className="grid grid-cols-5 gap-1">
                              {['1:1', '16:9', '9:16', '4:3', '3:4'].map(ar => (
                                <button
                                  key={ar}
                                  onClick={() => setAspectRatio(ar)}
                                  className={`py-1.5 px-1 text-[10px] rounded-md transition-all ${
                                    aspectRatio === ar
                                      ? 'bg-purple-500 text-white'
                                      : 'bg-white/10 text-white/60 hover:bg-white/20'
                                  }`}
                                >
                                  {ar}
                                </button>
                              ))}
                            </div>
                          </div>
                          
                          {/* Negative Prompt */}
                          <div>
                            <label className="text-xs text-white/60 mb-1.5 block">
                              Negative Prompt <span className="text-white/40">(things to avoid)</span>
                            </label>
                            <Textarea
                              value={negativePrompt}
                              onChange={(e) => setNegativePrompt(e.target.value)}
                              placeholder="blurry, low quality, distorted, watermark..."
                              className="bg-black/30 border-white/20 text-white text-xs min-h-[60px]"
                              data-testid="negative-prompt-input"
                            />
                          </div>
                          
                          {/* Lighting Preset */}
                          <div>
                            <label className="text-xs text-white/60 mb-1.5 block">Lighting Preset</label>
                            <div className="grid grid-cols-3 gap-1">
                              {[
                                { id: 'natural', name: 'Natural' },
                                { id: 'neon-pink-blue', name: 'Neon Pink/Blue' },
                                { id: 'golden-hour', name: 'Golden Hour' },
                                { id: 'dramatic', name: 'Dramatic' },
                                { id: 'soft-glow', name: 'Soft Glow' },
                                { id: 'studio', name: 'Studio' },
                              ].map(preset => (
                                <button
                                  key={preset.id}
                                  onClick={() => setLightingPreset(preset.id)}
                                  className={`py-1.5 px-1 text-[10px] rounded-md transition-all ${
                                    lightingPreset === preset.id
                                      ? 'bg-pink-500 text-white'
                                      : 'bg-white/10 text-white/60 hover:bg-white/20'
                                  }`}
                                  data-testid={`lighting-${preset.id}`}
                                >
                                  {preset.name}
                                </button>
                              ))}
                            </div>
                          </div>
                          
                          {/* Custom Style Description */}
                          <div>
                            <label className="text-xs text-white/60 mb-1.5 block">
                              Custom Style Description <span className="text-pink-400">(Pro)</span>
                            </label>
                            <Textarea
                              value={customStyleDescription}
                              onChange={(e) => setCustomStyleDescription(e.target.value)}
                              placeholder="Describe your exact style: neon lighting, flowing detailed hair, hyper-detailed skin, dramatic atmosphere..."
                              className="bg-black/30 border-white/20 text-white text-xs min-h-[80px]"
                              data-testid="custom-style-input"
                            />
                            <p className="text-[10px] text-white/40 mt-1">
                              Add specific style details that presets don't cover. Great for matching reference images.
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          )}

          {/* Main Content Area */}
          <div className="flex-1">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Center Panel - Builder/Controls */}
              <div className="lg:col-span-2 space-y-6">
                {activeTab === 'character' && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <FiUser className="text-purple-400" />
                        Character Builder
                      </h2>
                      
                      {/* Character Profile Actions */}
                      <div className="flex items-center gap-2">
                        {characterProfiles.length > 0 && (
                          <div className="relative">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setShowProfileSelector(!showProfileSelector)}
                              className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/20 text-xs"
                              data-testid="use-profile-btn"
                            >
                              <FiUser className="w-3 h-3 mr-1" />
                              Use Profile ({characterProfiles.length})
                            </Button>
                            
                            {/* Profile Selector Dropdown */}
                            {showProfileSelector && (
                              <div className="absolute right-0 top-full mt-1 z-20 w-64 bg-[#1a1520] border border-cyan-500/30 rounded-lg shadow-xl max-h-64 overflow-y-auto">
                                <div className="p-2 border-b border-white/10">
                                  <span className="text-xs text-white/50">Saved Character Profiles</span>
                                </div>
                                {characterProfiles.map((profile, idx) => (
                                  <button
                                    key={profile.id || idx}
                                    onClick={() => {
                                      setSelectedProfile(profile);
                                      generateWithProfile(profile.id);
                                      setShowProfileSelector(false);
                                    }}
                                    className="w-full px-3 py-2 text-left hover:bg-cyan-500/20 border-b border-white/5 last:border-0"
                                  >
                                    <div className="text-sm text-white font-medium">{profile.name}</div>
                                    <div className="text-xs text-white/50 truncate">{profile.description?.substring(0, 50)}...</div>
                                    <div className="text-[10px] text-cyan-400 mt-1">
                                      {profile.generation_count || 0} images generated
                                    </div>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={saveCharacterProfile}
                          className="border-green-500/50 text-green-400 hover:bg-green-500/20 text-xs"
                          data-testid="save-profile-btn"
                        >
                          <FiSave className="w-3 h-3 mr-1" />
                          Save Profile
                        </Button>
                      </div>
                    </div>
                    
                    {/* Info about character consistency */}
                    {selectedProfile && (
                      <div className="mb-4 p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                        <div className="flex items-center gap-2 text-cyan-400 text-sm">
                          <FiUser className="w-4 h-4" />
                          <span>Using profile: <strong>{selectedProfile.name}</strong></span>
                          <button 
                            onClick={() => setSelectedProfile(null)}
                            className="ml-auto text-xs text-white/50 hover:text-white"
                          >
                            Clear
                          </button>
                        </div>
                      </div>
                    )}
                    
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
                
                {/* Trait Selectors - Using shadcn Select for iPad compatibility */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(CHARACTER_TRAITS).map(([trait, options]) => (
                    <div key={trait}>
                      <label className="text-xs text-white/50 mb-1 block capitalize">
                        {trait.replace(/([A-Z])/g, ' $1').trim()}
                      </label>
                      <Select
                        value={character[trait]}
                        onValueChange={(value) => setCharacter({ ...character, [trait]: value })}
                      >
                        <SelectTrigger 
                          className="w-full bg-black/30 border-white/20 text-white text-sm rounded-lg h-10"
                          data-testid={`character-trait-${trait}`}
                        >
                          <SelectValue placeholder={`Select ${trait}`} />
                        </SelectTrigger>
                        <SelectContent className="bg-[#1a1520] border-purple-500/30 max-h-60">
                          {options.map(opt => (
                            <SelectItem 
                              key={opt} 
                              value={opt} 
                              className="text-white hover:bg-purple-500/20 cursor-pointer"
                            >
                              {opt}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ))}
                </div>
                
                {/* Additional Details with History */}
                <div className="mt-4 relative">
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm text-white/70">Additional Details</label>
                    {promptHistory.length > 0 && (
                      <button
                        onClick={() => setShowHistoryDropdown(!showHistoryDropdown)}
                        className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                        data-testid="history-toggle-btn"
                      >
                        <FiRefreshCw className="w-3 h-3" />
                        History ({promptHistory.length})
                      </button>
                    )}
                  </div>
                  
                  {/* History Dropdown */}
                  {showHistoryDropdown && promptHistory.length > 0 && (
                    <div className="absolute right-0 top-6 z-20 w-72 bg-[#1a1520] border border-purple-500/30 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                      <div className="p-2 border-b border-white/10">
                        <span className="text-xs text-white/50">Recent prompts</span>
                      </div>
                      {promptHistory.map((prompt, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setCharacter({ ...character, additionalDetails: prompt });
                            setShowHistoryDropdown(false);
                          }}
                          className="w-full px-3 py-2 text-left text-xs text-white/70 hover:bg-purple-500/20 hover:text-white border-b border-white/5 last:border-0"
                        >
                          <p className="truncate">{prompt}</p>
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <Textarea
                    value={character.additionalDetails}
                    onChange={(e) => setCharacter({ ...character, additionalDetails: e.target.value })}
                    placeholder="Add any extra details like accessories, pose, background elements..."
                    className="bg-black/30 border-white/20 text-white min-h-[80px]"
                    data-testid="additional-details-textarea"
                  />
                  
                  {/* Transparent Background Option */}
                  <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg bg-black/20 border border-white/10 hover:border-purple-500/50 transition-colors mt-3">
                    <input
                      type="checkbox"
                      checked={character.transparentBackground || false}
                      onChange={(e) => setCharacter({ ...character, transparentBackground: e.target.checked })}
                      className="w-4 h-4 rounded bg-black/30 border-purple-500/30 text-purple-500 focus:ring-purple-400"
                      data-testid="transparent-bg-checkbox"
                    />
                    <div>
                      <span className="text-sm font-medium text-white">Transparent Background</span>
                      <p className="text-xs text-white/50">Generate character without background (for compositing into scenes)</p>
                    </div>
                  </label>
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
                
                {/* Scene Presets - Visual Grid with Landscape Thumbnails */}
                <div className="mb-6">
                  <label className="text-sm text-white/70 mb-3 block">Scene Preset</label>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-[320px] overflow-y-auto pr-2">
                    {SCENE_PRESETS.map(preset => (
                      <button
                        key={preset.id}
                        onClick={() => setScene({ ...scene, preset: preset.id })}
                        className={`relative rounded-lg overflow-hidden border-2 transition-all group ${
                          scene.preset === preset.id 
                            ? 'border-purple-500 ring-2 ring-purple-500/30' 
                            : 'border-transparent hover:border-white/30'
                        }`}
                        data-testid={`scene-preset-${preset.id}`}
                      >
                        <div className="aspect-video bg-black/40">
                          {preset.thumbnail ? (
                            <img 
                              src={preset.thumbnail} 
                              alt={preset.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <FiLayers className="w-6 h-6 text-white/30" />
                            </div>
                          )}
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent">
                          <div className="absolute bottom-0 left-0 right-0 p-2">
                            <p className="text-white text-xs font-medium truncate">{preset.name}</p>
                          </div>
                        </div>
                        {scene.preset === preset.id && (
                          <div className="absolute top-2 right-2 w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                            <FiCheck className="w-3 h-3 text-white" />
                          </div>
                        )}
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
                
                {/* Custom Prompt with History */}
                <div className="relative">
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm text-white/70">Custom Scene Description</label>
                    {promptHistory.length > 0 && (
                      <button
                        onClick={() => setShowHistoryDropdown(!showHistoryDropdown)}
                        className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                        data-testid="scene-history-toggle-btn"
                      >
                        <FiRefreshCw className="w-3 h-3" />
                        History ({promptHistory.length})
                      </button>
                    )}
                  </div>
                  
                  {/* History Dropdown */}
                  {showHistoryDropdown && promptHistory.length > 0 && (
                    <div className="absolute right-0 top-6 z-20 w-72 bg-[#1a1520] border border-purple-500/30 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                      <div className="p-2 border-b border-white/10">
                        <span className="text-xs text-white/50">Recent prompts</span>
                      </div>
                      {promptHistory.map((prompt, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setScene({ ...scene, customPrompt: prompt });
                            setShowHistoryDropdown(false);
                          }}
                          className="w-full px-3 py-2 text-left text-xs text-white/70 hover:bg-purple-500/20 hover:text-white border-b border-white/5 last:border-0"
                        >
                          <p className="truncate">{prompt}</p>
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <Textarea
                    value={scene.customPrompt}
                    onChange={(e) => setScene({ ...scene, customPrompt: e.target.value })}
                    placeholder="Describe your scene in detail..."
                    className="bg-black/30 border-white/20 text-white min-h-[100px]"
                    data-testid="scene-custom-prompt-textarea"
                  />
                </div>
              </motion.div>
            )}

            {/* Animate Tab - Dedicated animation workspace */}
            {activeTab === 'animate' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6"
              >
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <FiVideo className="text-pink-400" />
                      Animate Your Images
                    </h2>
                    <p className="text-white/50 text-sm mt-1">Bring your characters and scenes to life with AI animation</p>
                  </div>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Select Image Section */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white">1. Select an Image</h3>
                    
                    {/* Current Selection */}
                    {animatingImage ? (
                      <div className="relative rounded-xl overflow-hidden border-2 border-pink-500/50">
                        <img src={animatingImage} alt="Selected for animation" className="w-full aspect-square object-cover" />
                        <button
                          onClick={() => setAnimatingImage(null)}
                          className="absolute top-2 right-2 p-2 bg-black/60 rounded-full text-white hover:bg-black/80"
                        >
                          <FiX className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="border-2 border-dashed border-white/20 rounded-xl p-6 text-center">
                        <FiImage className="w-10 h-10 text-white/30 mx-auto mb-3" />
                        <p className="text-white/50 mb-3 text-sm">Select from gallery or upload an image</p>
                        <label className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg cursor-pointer text-white text-sm transition-colors">
                          <FiUpload className="w-4 h-4" />
                          Upload Image
                          <input
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={async (e) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                const reader = new FileReader();
                                reader.onload = (event) => {
                                  setAnimatingImage(event.target.result);
                                };
                                reader.readAsDataURL(file);
                              }
                            }}
                          />
                        </label>
                      </div>
                    )}
                    
                    {/* Gallery Preview for Selection */}
                    <div className="bg-black/20 rounded-xl p-4 max-h-[250px] overflow-y-auto">
                      <p className="text-xs text-white/50 mb-3">Or select from Gallery ({gallery.filter(g => g.type !== 'animation').length} images)</p>
                      {gallery.filter(g => g.type !== 'animation').length === 0 ? (
                        <p className="text-white/40 text-sm text-center py-4">No images yet. Create some or upload above!</p>
                      ) : (
                        <div className="grid grid-cols-4 gap-2">
                          {gallery.filter(g => g.type !== 'animation').map((item) => (
                            <button
                              key={item._id}
                              onClick={() => setAnimatingImage(item.image_url)}
                              className={`relative rounded-lg overflow-hidden border-2 transition-all ${
                                animatingImage === item.image_url ? 'border-pink-500' : 'border-transparent hover:border-white/30'
                              }`}
                            >
                              <img src={item.image_url} alt={item.name} className="w-full aspect-square object-cover" />
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Animation Settings Section */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white">2. Animation Settings</h3>
                    
                    {/* Motion Description */}
                    <div>
                      <label className="text-sm text-white/70 mb-2 block">Motion Description</label>
                      <textarea
                        value={animationMotion}
                        onChange={(e) => setAnimationMotion(e.target.value)}
                        placeholder="gentle breathing, hair flowing in the wind, soft blinking, subtle head movement..."
                        className="w-full bg-black/30 border border-white/20 rounded-lg px-4 py-3 text-white min-h-[100px]"
                        data-testid="animate-motion-input"
                      />
                    </div>
                    
                    {/* Animation Style */}
                    <div>
                      <label className="text-sm text-white/70 mb-2 block">Animation Style</label>
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { id: 'natural', name: 'Natural', desc: 'Subtle, realistic movement' },
                          { id: 'dramatic', name: 'Dramatic', desc: 'Bold, cinematic motion' },
                          { id: 'subtle', name: 'Subtle', desc: 'Barely noticeable, calm' }
                        ].map(style => (
                          <button
                            key={style.id}
                            onClick={() => setAnimationStyle(style.id)}
                            className={`p-3 rounded-lg text-left transition-all ${
                              animationStyle === style.id
                                ? 'bg-pink-500/30 border-2 border-pink-500'
                                : 'bg-white/5 border-2 border-transparent hover:border-white/20'
                            }`}
                          >
                            <p className="text-white font-medium text-sm">{style.name}</p>
                            <p className="text-white/50 text-xs">{style.desc}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                    
                    {/* Info Box */}
                    <div className="bg-gradient-to-r from-pink-500/10 to-purple-500/10 border border-pink-500/20 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-pink-500/20 rounded-lg">
                          <FiZap className="w-5 h-5 text-pink-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium text-sm">Powered by Sora 2 AI</p>
                          <p className="text-white/50 text-xs mt-1">Creates a 4-second animated video. Generation takes 2-5 minutes.</p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Progress Bar (shown while animating) */}
                    {isAnimating && (
                      <div className="bg-black/30 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-white/70 text-sm">Progress</span>
                          <span className="text-pink-400 font-medium">{animationProgress}%</span>
                        </div>
                        <div className="h-3 bg-black/50 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-pink-500 to-purple-500 transition-all duration-500"
                            style={{ width: `${animationProgress}%` }}
                          />
                        </div>
                        <p className="text-white/50 text-xs text-center">{animationMessage}</p>
                      </div>
                    )}
                    
                    {/* Generate Button */}
                    <Button
                      onClick={animateImage}
                      disabled={isAnimating || !animatingImage}
                      className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 py-6 text-lg"
                      data-testid="animate-generate-btn"
                    >
                      {isAnimating ? (
                        <>
                          <FiRefreshCw className="w-5 h-5 mr-2 animate-spin" />
                          Generating... {animationProgress}%
                        </>
                      ) : (
                        <>
                          <FiPlay className="w-5 h-5 mr-2" />
                          Create Animation
                        </>
                      )}
                    </Button>
                    
                    {/* Result */}
                    {animatedVideo && (
                      <div className="mt-4">
                        <p className="text-sm text-white/70 mb-2">Your Animated Result:</p>
                        <div className="rounded-xl overflow-hidden border border-pink-500/30">
                          <video 
                            src={animatedVideo} 
                            controls 
                            autoPlay 
                            loop 
                            muted
                            playsInline
                            className="w-full"
                            onLoadedData={(e) => e.target.play().catch(() => {})}
                          />
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-3">
                          <Button
                            onClick={async () => {
                              try {
                                console.log('Saving animation to gallery...');
                                const response = await fetch(`${API_URL}/api/art-studio/save-animation`, {
                                  method: 'POST',
                                  headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                  },
                                  body: JSON.stringify({
                                    video_url: animatedVideo,
                                    name: `Animation ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
                                    motion_prompt: animationMotion,
                                    style: animationStyle
                                  })
                                });
                                const data = await response.json();
                                console.log('Save response:', data);
                                if (response.ok && data.success) {
                                  toast.success('Animation saved to gallery!');
                                  fetchGallery();
                                } else {
                                  throw new Error(data.detail || 'Failed to save');
                                }
                              } catch (error) {
                                console.error('Save animation error:', error);
                                toast.error('Failed to save: ' + error.message);
                              }
                            }}
                            className="bg-green-600 hover:bg-green-700"
                            data-testid="save-animation-btn"
                          >
                            <FiSave className="w-4 h-4 mr-2" />
                            Save
                          </Button>
                          <Button
                            onClick={() => {
                              // Create blob from base64 for better download
                              try {
                                const base64Data = animatedVideo.split(',')[1];
                                const byteCharacters = atob(base64Data);
                                const byteNumbers = new Array(byteCharacters.length);
                                for (let i = 0; i < byteCharacters.length; i++) {
                                  byteNumbers[i] = byteCharacters.charCodeAt(i);
                                }
                                const byteArray = new Uint8Array(byteNumbers);
                                const blob = new Blob([byteArray], { type: 'video/mp4' });
                                const url = URL.createObjectURL(blob);
                                const link = document.createElement('a');
                                link.href = url;
                                link.download = `azories-animation-1080p-${Date.now()}.mp4`;
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                URL.revokeObjectURL(url);
                                toast.success('Downloading 1080p video...');
                              } catch (error) {
                                console.error('Download error:', error);
                                // Fallback to direct link
                                const link = document.createElement('a');
                                link.href = animatedVideo;
                                link.download = `azories-animation-1080p-${Date.now()}.mp4`;
                                link.click();
                              }
                            }}
                            className="bg-purple-600 hover:bg-purple-700"
                            data-testid="download-animation-btn"
                          >
                            <FiDownload className="w-4 h-4 mr-2" />
                            1080p
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setAnimatedVideo(null)}
                            className="border-white/20 text-white"
                          >
                            New
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'gallery' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6"
              >
                <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <FiGrid className="text-purple-400" />
                    My Gallery
                  </h2>
                  
                  {/* Gallery Filters */}
                  <div className="flex items-center gap-3">
                    {/* Type Filter */}
                    <div className="flex items-center gap-2">
                      <div className="flex bg-black/30 rounded-lg p-0.5">
                        <button
                          onClick={() => setGalleryTypeFilter('all')}
                          className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                            galleryTypeFilter === 'all' ? 'bg-purple-600 text-white' : 'text-white/60 hover:text-white'
                          }`}
                        >
                          All
                        </button>
                        <button
                          onClick={() => setGalleryTypeFilter('images')}
                          className={`px-3 py-1.5 text-xs rounded-md transition-all flex items-center gap-1 ${
                            galleryTypeFilter === 'images' ? 'bg-purple-600 text-white' : 'text-white/60 hover:text-white'
                          }`}
                        >
                          <FiImage className="w-3 h-3" />
                          Images
                        </button>
                        <button
                          onClick={() => setGalleryTypeFilter('animations')}
                          className={`px-3 py-1.5 text-xs rounded-md transition-all flex items-center gap-1 ${
                            galleryTypeFilter === 'animations' ? 'bg-pink-600 text-white' : 'text-white/60 hover:text-white'
                          }`}
                        >
                          <FiVideo className="w-3 h-3" />
                          Animations
                        </button>
                      </div>
                    </div>
                    
                    {/* Book Filter */}
                    <select
                      value={galleryFilter}
                      onChange={(e) => setGalleryFilter(e.target.value)}
                      className="bg-black/30 border border-white/20 rounded-lg px-3 py-1.5 text-white text-xs"
                      data-testid="gallery-filter"
                    >
                      <option value="all">All Books</option>
                      {userBooks.map(book => (
                        <option key={book.id || book._id} value={book.id || book._id}>
                          {book.title}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                {(() => {
                  // Apply both filters
                  let filteredGallery = gallery;
                  
                  // Filter by book
                  if (galleryFilter !== 'all') {
                    filteredGallery = filteredGallery.filter(item => item.book_id === galleryFilter);
                  }
                  
                  // Filter by type
                  if (galleryTypeFilter === 'images') {
                    filteredGallery = filteredGallery.filter(item => item.type !== 'animation');
                  } else if (galleryTypeFilter === 'animations') {
                    filteredGallery = filteredGallery.filter(item => item.type === 'animation');
                  }
                  
                  const imageCount = gallery.filter(g => g.type !== 'animation').length;
                  const animationCount = gallery.filter(g => g.type === 'animation').length;
                  
                  return (
                    <>
                      <p className="text-xs text-white/40 mb-4">
                        {imageCount} images, {animationCount} animations
                      </p>
                      {filteredGallery.length === 0 ? (
                        <div className="text-center py-12">
                          {galleryTypeFilter === 'animations' ? (
                            <>
                              <FiVideo className="w-16 h-16 text-white/20 mx-auto mb-4" />
                              <p className="text-white/50">No animations yet. Create some in the Animate tab!</p>
                            </>
                          ) : (
                            <>
                              <FiImage className="w-16 h-16 text-white/20 mx-auto mb-4" />
                              <p className="text-white/50">
                                {galleryFilter === 'all' 
                                  ? 'No images yet. Start creating!' 
                                  : 'No images for this book yet.'}
                              </p>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          {filteredGallery.map((item) => (
                            <div
                              key={item._id}
                              className={`relative group rounded-lg overflow-hidden border-2 transition-all cursor-pointer ${
                                selectedGalleryItem?._id === item._id
                                  ? item.type === 'animation' ? 'border-pink-500' : 'border-purple-500'
                                  : 'border-transparent hover:border-white/30'
                              }`}
                              onClick={() => setSelectedGalleryItem(item)}
                            >
                              {item.type === 'animation' ? (
                                <video
                                  src={item.image_url}
                                  className="w-full aspect-square object-cover"
                                  muted
                                  loop
                                  onMouseEnter={(e) => e.target.play()}
                                  onMouseLeave={(e) => { e.target.pause(); e.target.currentTime = 0; }}
                                />
                              ) : (
                                <img
                                  src={item.image_url}
                                  alt={item.name}
                                  className="w-full aspect-square object-cover"
                                />
                              )}
                              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="absolute bottom-0 left-0 right-0 p-3">
                                  <p className="text-white text-sm font-medium truncate">{item.name}</p>
                                  <p className="text-white/50 text-xs flex items-center gap-1">
                                    {item.type === 'animation' ? <FiVideo className="w-3 h-3" /> : <FiImage className="w-3 h-3" />}
                                    {item.type === 'animation' ? 'Animation' : item.style}
                                  </p>
                                </div>
                              </div>
                              {/* Animation badge */}
                              {item.type === 'animation' && (
                                <div className="absolute top-2 left-2 px-2 py-0.5 bg-pink-500 rounded text-xs text-white flex items-center gap-1">
                                  <FiPlay className="w-2.5 h-2.5" />
                                  Video
                                </div>
                              )}
                              {/* Animate button (only for images) */}
                              {item.type !== 'animation' && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openAnimateModal(item.image_url);
                                  }}
                                  className="absolute top-2 left-2 p-1.5 bg-pink-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                  title="Animate this image"
                                >
                                  <FiPlay className="w-3 h-3 text-white" />
                                </button>
                              )}
                              {/* Delete button */}
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
                    </>
                  );
                })()}
              </motion.div>
            )}
            
            {/* DUAL Reference Images Section */}
            {(activeTab === 'character' || activeTab === 'scene') && (
              <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <FiImage className="text-purple-400" />
                  Reference Images
                </h3>
                <p className="text-sm text-white/50 mb-4">
                  Use separate images for style inspiration and character reference
                </p>
                
                <div className="grid grid-cols-2 gap-4">
                  {/* Style Reference */}
                  <div className="space-y-2">
                    <label className="text-xs text-purple-300 font-medium flex items-center gap-1">
                      <FiDroplet className="w-3 h-3" />
                      Style Reference
                    </label>
                    <p className="text-[10px] text-white/40">Art style, colors, lighting, mood</p>
                    
                    <div className="relative">
                      {styleReferenceImage ? (
                        <div className="relative w-full aspect-square rounded-lg overflow-hidden border-2 border-purple-500 group">
                          <img src={styleReferenceImage} alt="Style ref" className="w-full h-full object-cover" />
                          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2">
                            <button
                              onClick={() => extractPromptFromImage(styleReferenceImage, 'style')}
                              disabled={isExtractingPrompt}
                              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded-lg text-xs text-white flex items-center gap-1"
                            >
                              <FiZap className="w-3 h-3" />
                              {isExtractingPrompt ? 'Analyzing...' : 'Extract Style'}
                            </button>
                            <button
                              onClick={() => {
                                setStyleReferenceImage(null);
                                setExtractedStylePrompt('');
                              }}
                              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded-lg text-xs text-white"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="w-full aspect-square rounded-lg border-2 border-dashed border-white/20 flex flex-col items-center justify-center">
                          <FiDroplet className="w-6 h-6 text-white/30 mb-2" />
                          <span className="text-[10px] text-white/40 mb-2">Add style reference</span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => styleRefInputRef.current?.click()}
                              className="px-2 py-1 bg-purple-600/50 hover:bg-purple-600 rounded text-[10px] text-white flex items-center gap-1"
                            >
                              <FiUpload className="w-3 h-3" />
                              Upload
                            </button>
                            <button
                              onClick={() => {
                                setGalleryPickerTarget('style');
                                setShowGalleryPicker(true);
                              }}
                              className="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-[10px] text-white flex items-center gap-1"
                            >
                              <FiImage className="w-3 h-3" />
                              Gallery
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {extractedStylePrompt && (
                      <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
                        <p className="text-[10px] text-purple-300 mb-1">Extracted style:</p>
                        <p className="text-xs text-white/70">{extractedStylePrompt.substring(0, 100)}...</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Character Reference */}
                  <div className="space-y-2">
                    <label className="text-xs text-pink-300 font-medium flex items-center gap-1">
                      <FiUser className="w-3 h-3" />
                      Character Reference
                    </label>
                    <p className="text-[10px] text-white/40">Face, pose, outfit, features</p>
                    
                    <div className="relative">
                      {characterReferenceImage ? (
                        <div className="relative w-full aspect-square rounded-lg overflow-hidden border-2 border-pink-500 group">
                          <img src={characterReferenceImage} alt="Char ref" className="w-full h-full object-cover" />
                          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2">
                            <button
                              onClick={() => extractPromptFromImage(characterReferenceImage, 'character')}
                              disabled={isExtractingPrompt}
                              className="px-3 py-1.5 bg-pink-600 hover:bg-pink-700 rounded-lg text-xs text-white flex items-center gap-1"
                            >
                              <FiZap className="w-3 h-3" />
                              {isExtractingPrompt ? 'Analyzing...' : 'Extract Char'}
                            </button>
                            <button
                              onClick={() => {
                                setCharacterReferenceImage(null);
                                setExtractedCharPrompt('');
                              }}
                              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded-lg text-xs text-white"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="w-full aspect-square rounded-lg border-2 border-dashed border-white/20 flex flex-col items-center justify-center">
                          <FiUser className="w-6 h-6 text-white/30 mb-2" />
                          <span className="text-[10px] text-white/40 mb-2">Add character reference</span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => charRefInputRef.current?.click()}
                              className="px-2 py-1 bg-pink-600/50 hover:bg-pink-600 rounded text-[10px] text-white flex items-center gap-1"
                            >
                              <FiUpload className="w-3 h-3" />
                              Upload
                            </button>
                            <button
                              onClick={() => {
                                setGalleryPickerTarget('character');
                                setShowGalleryPicker(true);
                              }}
                              className="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-[10px] text-white flex items-center gap-1"
                            >
                              <FiImage className="w-3 h-3" />
                              Gallery
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {extractedCharPrompt && (
                      <div className="p-2 bg-pink-500/10 rounded-lg border border-pink-500/20">
                        <p className="text-[10px] text-pink-300 mb-1">Extracted character:</p>
                        <p className="text-xs text-white/70">{extractedCharPrompt.substring(0, 100)}...</p>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Hidden file inputs for reference uploads */}
                <input
                  ref={styleRefInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleReferenceUpload(e, 'style')}
                  className="hidden"
                />
                <input
                  ref={charRefInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleReferenceUpload(e, 'character')}
                  className="hidden"
                />
                
                {/* Hidden file inputs */}
                <input
                  ref={referenceInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleReferenceUpload}
                  className="hidden"
                />
                
                {/* Prompt History Scroll - Under Reference Image */}
                {promptHistory.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <h4 className="text-sm font-medium text-white/70 mb-2 flex items-center gap-2">
                      <FiRefreshCw className="w-3 h-3 text-purple-400" />
                      Recent Prompts ({promptHistory.length})
                    </h4>
                    <div className="max-h-32 overflow-y-auto space-y-1 pr-2 custom-scrollbar">
                      {promptHistory.map((prompt, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            if (activeTab === 'character') {
                              setCharacter({ ...character, additionalDetails: prompt });
                            } else {
                              setScene({ ...scene, customPrompt: prompt });
                            }
                          }}
                          className="w-full px-3 py-2 text-left text-xs text-white/60 hover:text-white hover:bg-purple-500/20 rounded-lg transition-colors"
                        >
                          <p className="truncate">{prompt}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Copy to Expert Mode Button */}
                {activeTab === 'character' && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <Button
                      variant="outline"
                      onClick={() => {
                        // Save current character to localStorage for Expert Mode
                        const exportData = {
                          character: character,
                          style: selectedStyle,
                          referenceImage: characterReferenceImage
                        };
                        localStorage.setItem('artStudioExport', JSON.stringify(exportData));
                        navigate('/art-studio/expert?import=character');
                      }}
                      className="w-full border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/20"
                      data-testid="copy-to-expert-btn"
                    >
                      <FiZap className="w-4 h-4 mr-2" />
                      Copy to Expert Mode (Node Editor)
                    </Button>
                  </div>
                )}
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
                    <p className="text-white/40 text-xs mt-1">This may take a moment</p>
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
                <div className="mt-4 space-y-3">
                  {/* LIGHTING & CUSTOM STYLE - Always Visible */}
                  <div className="bg-gradient-to-r from-pink-500/10 to-purple-500/10 border border-pink-500/20 rounded-lg p-3 space-y-3">
                    <h4 className="text-xs font-semibold text-pink-300 uppercase tracking-wider flex items-center gap-1">
                      <FiStar className="w-3 h-3" />
                      Lighting & Style
                    </h4>
                    
                    {/* Lighting Preset */}
                    <div>
                      <label className="text-[10px] text-white/60 mb-1.5 block">Lighting</label>
                      <div className="grid grid-cols-3 gap-1">
                        {[
                          { id: 'natural', name: 'Natural', icon: '☀️' },
                          { id: 'neon-pink-blue', name: 'Neon', icon: '💜' },
                          { id: 'golden-hour', name: 'Golden', icon: '🌅' },
                          { id: 'dramatic', name: 'Dramatic', icon: '🎭' },
                          { id: 'soft-glow', name: 'Soft', icon: '✨' },
                          { id: 'studio', name: 'Studio', icon: '📸' },
                        ].map(preset => (
                          <button
                            key={preset.id}
                            onClick={() => setLightingPreset(preset.id)}
                            className={`py-1.5 px-1 text-[10px] rounded-md transition-all flex items-center justify-center gap-1 ${
                              lightingPreset === preset.id
                                ? 'bg-pink-500 text-white shadow-lg shadow-pink-500/30'
                                : 'bg-white/10 text-white/60 hover:bg-white/20'
                            }`}
                            data-testid={`lighting-${preset.id}`}
                          >
                            <span>{preset.icon}</span>
                            <span>{preset.name}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                    
                    {/* Custom Style Description */}
                    <div>
                      <label className="text-[10px] text-white/60 mb-1 block">
                        Custom Style (Optional)
                      </label>
                      <textarea
                        value={customStyleDescription}
                        onChange={(e) => setCustomStyleDescription(e.target.value)}
                        placeholder="Add extra style details: flowing hair, double exposure, fantasy castle background, dreamy atmosphere..."
                        className="w-full bg-black/30 border border-white/20 rounded-lg px-2 py-1.5 text-white text-[11px] min-h-[50px] resize-none focus:border-pink-500/50 focus:outline-none"
                        data-testid="custom-style-quick"
                      />
                    </div>
                  </div>
                
                  <Button
                    onClick={generateImage}
                    disabled={isGenerating}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                    data-testid="generate-image-btn"
                  >
                    <FiZap className="w-4 h-4 mr-2" />
                    {isGenerating ? 'Generating...' : 'Generate Image'}
                  </Button>
                  
                  {generatedImage && (
                    <>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => saveToGallery(generatedImage, character.name || 'Untitled')}
                          variant="outline"
                          className="flex-1 border-white/20 text-white hover:bg-white/10"
                          data-testid="save-to-gallery-btn"
                        >
                          <FiSave className="w-4 h-4 mr-2" />
                          Save to Gallery
                        </Button>
                        <Button
                          onClick={generateImage}
                          variant="outline"
                          className="border-white/20 text-white hover:bg-white/10"
                          title="Regenerate"
                        >
                          <FiRefreshCw className="w-4 h-4" />
                        </Button>
                      </div>
                      <Button
                        onClick={() => downloadImage(generatedImage, `${character.name || 'art'}-${selectedStyle}.png`)}
                        variant="outline"
                        className="w-full border-green-500/50 text-green-400 hover:bg-green-500/20"
                        data-testid="download-image-btn"
                      >
                        <FiDownload className="w-4 h-4 mr-2" />
                        Download Image
                      </Button>
                      <Button
                        onClick={() => selectGalleryAsReference(generatedImage)}
                        variant="outline"
                        className="w-full border-blue-500/50 text-blue-400 hover:bg-blue-500/20"
                        data-testid="use-as-reference-btn"
                      >
                        <FiImage className="w-4 h-4 mr-2" />
                        Use as Reference
                      </Button>
                    </>
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
                    data-testid="copy-url-btn"
                  >
                    <FiCopy className="w-4 h-4 mr-2" />
                    Copy URL for Book
                  </Button>
                  <Button
                    onClick={() => downloadImage(selectedGalleryItem.image_url, `${selectedGalleryItem.name}.png`)}
                    variant="outline"
                    className="w-full border-green-500/50 text-green-400 hover:bg-green-500/20"
                    data-testid="download-gallery-image-btn"
                  >
                    <FiDownload className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                  <Button
                    onClick={() => selectGalleryAsReference(selectedGalleryItem.image_url)}
                    variant="outline"
                    className="w-full border-blue-500/50 text-blue-400 hover:bg-blue-500/20"
                  >
                    <FiImage className="w-4 h-4 mr-2" />
                    Use as Reference
                  </Button>
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
                  {(styleReferenceImage || characterReferenceImage) && ' (with reference image)'}
                </p>
              </div>
            )}
          </div>
        </div>
        </div>
        </div>
      </div>
      
      {/* Gallery Picker Modal - For selecting style or character reference */}
      <AnimatePresence>
        {showGalleryPicker && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
            onClick={() => setShowGalleryPicker(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1a1520] rounded-xl border border-white/10 p-6 max-w-2xl w-full max-h-[80vh] overflow-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white">
                    Select {galleryPickerTarget === 'style' ? 'Style' : 'Character'} Reference
                  </h3>
                  <p className="text-sm text-white/50">
                    {galleryPickerTarget === 'style' 
                      ? 'Choose an image to match its art style, colors, and mood'
                      : 'Choose an image to match its character appearance and features'}
                  </p>
                </div>
                <button
                  onClick={() => setShowGalleryPicker(false)}
                  className="text-white/50 hover:text-white p-2"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>
              
              {gallery.length === 0 ? (
                <div className="text-center py-12">
                  <FiImage className="w-16 h-16 text-white/20 mx-auto mb-4" />
                  <p className="text-white/50">No images in your gallery yet</p>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-3">
                  {gallery.map((item) => (
                    <button
                      key={item._id}
                      onClick={() => {
                        if (galleryPickerTarget === 'style') {
                          setStyleReferenceImage(item.image_url);
                        } else {
                          setCharacterReferenceImage(item.image_url);
                        }
                        setShowGalleryPicker(false);
                      }}
                      className={`relative aspect-square rounded-lg overflow-hidden border-2 transition-colors group ${
                        galleryPickerTarget === 'style' 
                          ? 'border-transparent hover:border-purple-500' 
                          : 'border-transparent hover:border-pink-500'
                      }`}
                    >
                      <img
                        src={item.image_url}
                        alt={item.name}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <span className="text-white font-medium">Use as {galleryPickerTarget === 'style' ? 'Style' : 'Character'}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Style Preview Gallery Modal */}
      <AnimatePresence>
        {showStylePreview && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 overflow-y-auto"
            onClick={() => setShowStylePreview(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-gradient-to-br from-[#2d1f3d] to-[#1a1520] rounded-2xl p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white">Style Gallery</h2>
                  <p className="text-white/60 text-sm">Preview all {ART_STYLES.length} art styles - click to select</p>
                </div>
                <button
                  onClick={() => setShowStylePreview(false)}
                  className="p-2 hover:bg-white/10 rounded-lg text-white/60 hover:text-white transition-colors"
                >
                  <FiX className="w-6 h-6" />
                </button>
              </div>
              
              {ART_STYLE_CATEGORIES.map(category => (
                <div key={category.category} className="mb-8">
                  <h3 className="text-lg font-semibold text-purple-400 mb-4">{category.category}</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {category.styles.map(style => (
                      <button
                        key={style.id}
                        onClick={() => {
                          setSelectedStyle(style.id);
                          setShowStylePreview(false);
                        }}
                        className={`group relative rounded-xl overflow-hidden transition-all hover:scale-105 ${
                          selectedStyle === style.id
                            ? 'ring-2 ring-purple-500 ring-offset-2 ring-offset-[#1a1520]'
                            : ''
                        }`}
                      >
                        <div className="aspect-square bg-black/30">
                          {style.image && (
                            <img
                              src={style.image.replace('w=100&h=100', 'w=300&h=300')}
                              alt={style.name}
                              className="w-full h-full object-cover"
                              loading="lazy"
                            />
                          )}
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="absolute bottom-0 left-0 right-0 p-3">
                            <p className="text-white font-medium text-sm">{style.name}</p>
                            <p className="text-white/60 text-xs">{style.description}</p>
                          </div>
                        </div>
                        {selectedStyle === style.id && (
                          <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center">
                            <FiCheck className="w-4 h-4 text-white" />
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Generation History Panel - Floating */}
      {generationHistory.length > 0 && (
        <div className="fixed bottom-4 right-4 z-40">
          <div className="bg-black/80 backdrop-blur-sm rounded-xl border border-white/10 p-2 max-w-[200px]">
            <p className="text-[10px] text-white/50 mb-2 px-1">Recent</p>
            <div className="flex gap-1 flex-wrap max-h-[100px] overflow-hidden">
              {generationHistory.slice(0, 6).map((gen, idx) => (
                <button
                  key={idx}
                  onClick={() => setGeneratedImage(gen.image)}
                  className="w-12 h-12 rounded-md overflow-hidden hover:ring-2 hover:ring-purple-500 transition-all flex-shrink-0"
                >
                  <img src={gen.image} alt="Recent" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Animation Modal */}
      <AnimatePresence>
        {showAnimateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
            onClick={() => setShowAnimateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-gradient-to-br from-[#2d1f3d] to-[#1a1520] rounded-2xl p-6 max-w-2xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <FiVideo className="text-pink-400" />
                    Animate Image
                  </h2>
                  <p className="text-white/60 text-sm">Bring your image to life with AI animation</p>
                </div>
                <button
                  onClick={() => setShowAnimateModal(false)}
                  className="p-2 hover:bg-white/10 rounded-lg text-white/60 hover:text-white"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>
              
              <div className="grid grid-cols-2 gap-6">
                {/* Original Image */}
                <div>
                  <p className="text-xs text-white/50 mb-2">Original Image</p>
                  <div className="aspect-square rounded-xl overflow-hidden bg-black/30">
                    {animatingImage && (
                      <img src={animatingImage} alt="To animate" className="w-full h-full object-cover" />
                    )}
                  </div>
                </div>
                
                {/* Animated Result or Settings */}
                <div>
                  {animatedVideo ? (
                    <>
                      <p className="text-xs text-white/50 mb-2">Animated Result</p>
                      <div className="aspect-square rounded-xl overflow-hidden bg-black/30">
                        <video 
                          src={animatedVideo} 
                          controls 
                          autoPlay 
                          loop 
                          muted
                          playsInline
                          className="w-full h-full object-cover"
                          onLoadedData={(e) => e.target.play().catch(() => {})}
                        />
                      </div>
                    </>
                  ) : (
                    <>
                      <p className="text-xs text-white/50 mb-2">Animation Settings</p>
                      <div className="space-y-4">
                        {/* Motion Description */}
                        <div>
                          <label className="text-xs text-white/70 mb-1 block">Motion Description</label>
                          <textarea
                            value={animationMotion}
                            onChange={(e) => setAnimationMotion(e.target.value)}
                            placeholder="gentle breathing, hair flowing, soft blinking..."
                            className="w-full bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-white text-sm min-h-[80px]"
                          />
                        </div>
                        
                        {/* Animation Style */}
                        <div>
                          <label className="text-xs text-white/70 mb-1 block">Animation Style</label>
                          <div className="grid grid-cols-3 gap-2">
                            {['natural', 'dramatic', 'subtle'].map(style => (
                              <button
                                key={style}
                                onClick={() => setAnimationStyle(style)}
                                className={`py-2 px-3 rounded-lg text-xs capitalize transition-all ${
                                  animationStyle === style
                                    ? 'bg-pink-500 text-white'
                                    : 'bg-white/10 text-white/60 hover:bg-white/20'
                                }`}
                              >
                                {style}
                              </button>
                            ))}
                          </div>
                        </div>
                        
                        <div className="text-[10px] text-white/40 space-y-1 bg-black/20 p-2 rounded-lg">
                          <p className="flex items-center gap-1">
                            <span className="text-yellow-400">⚡</span>
                            Animation creates a 4-second video using Sora 2 AI
                          </p>
                          <p className="flex items-center gap-1">
                            <span className="text-blue-400">⏱️</span>
                            May take 2-5 minutes - please be patient
                          </p>
                          <p className="flex items-center gap-1">
                            <span className="text-purple-400">💎</span>
                            Uses Emergent Universal Key credits
                          </p>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="mt-6 flex gap-3">
                {animatedVideo ? (
                  <>
                    <Button
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = animatedVideo;
                        link.download = `azories-animated-${Date.now()}.mp4`;
                        link.click();
                      }}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600"
                    >
                      <FiDownload className="w-4 h-4 mr-2" />
                      Download Video
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setAnimatedVideo(null)}
                      className="border-white/20 text-white"
                    >
                      Animate Again
                    </Button>
                  </>
                ) : (
                  <Button
                    onClick={animateImage}
                    disabled={isAnimating || !animatingImage}
                    className="flex-1 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700"
                  >
                    {isAnimating ? (
                      <>
                        <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Animating... (1-3 min)
                      </>
                    ) : (
                      <>
                        <FiPlay className="w-4 h-4 mr-2" />
                        Animate Image
                      </>
                    )}
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
