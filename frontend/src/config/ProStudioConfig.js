// Pro Studio Configuration - Camera, Lens, and Model Options
// Based on professional film equipment and AI model capabilities

// Cinema Studio - Camera Bodies
export const CAMERA_BODIES = [
  {
    id: 'arri-alexa-35',
    name: 'ARRI Alexa 35',
    brand: 'ARRI',
    description: 'Industry standard for cinematic production',
    characteristics: 'Rich colors, natural skin tones, filmic look',
    icon: '🎬'
  },
  {
    id: 'arri-alexa-mini',
    name: 'ARRI Alexa Mini',
    brand: 'ARRI',
    description: 'Compact cinema camera for versatile shots',
    characteristics: 'Same quality as Alexa 35, more portable',
    icon: '🎥'
  },
  {
    id: 'red-v-raptor',
    name: 'RED V-Raptor',
    brand: 'RED',
    description: '8K cinema camera with global shutter',
    characteristics: 'Ultra sharp, vibrant colors, documentary style',
    icon: '🔴'
  },
  {
    id: 'red-komodo',
    name: 'RED Komodo',
    brand: 'RED',
    description: 'Compact 6K cinema camera',
    characteristics: 'Clean, modern look, great dynamic range',
    icon: '🎞️'
  },
  {
    id: 'sony-venice-2',
    name: 'Sony Venice 2',
    brand: 'Sony',
    description: '8.6K full-frame cinema camera',
    characteristics: 'Excellent low light, natural colors',
    icon: '📹'
  },
  {
    id: 'blackmagic-ursa',
    name: 'Blackmagic URSA Mini Pro',
    brand: 'Blackmagic',
    description: '12K cinema camera',
    characteristics: 'High resolution, film-like grain',
    icon: '⬛'
  },
  {
    id: 'canon-c500',
    name: 'Canon C500 Mark II',
    brand: 'Canon',
    description: 'Full-frame cinema camera',
    characteristics: 'Warm tones, pleasing skin, classic look',
    icon: '📷'
  }
];

// Cinema Studio - Lenses
export const CINEMA_LENSES = [
  {
    id: 'panavision-series',
    name: 'Panavision C Series',
    brand: 'Panavision',
    focalLengths: ['24mm', '35mm', '50mm', '75mm', '100mm'],
    characteristics: 'Dreamy bokeh, classic Hollywood look, soft edges',
    style: 'cinematic'
  },
  {
    id: 'panavision-primo',
    name: 'Panavision Primo 70',
    brand: 'Panavision',
    focalLengths: ['27mm', '35mm', '50mm', '65mm', '100mm'],
    characteristics: 'Ultra sharp center, smooth falloff, modern cinema',
    style: 'modern'
  },
  {
    id: 'cooke-s4',
    name: 'Cooke S4/i',
    brand: 'Cooke',
    focalLengths: ['18mm', '25mm', '35mm', '50mm', '75mm', '100mm'],
    characteristics: 'Warm, creamy, the "Cooke Look", beautiful skin',
    style: 'warm'
  },
  {
    id: 'cooke-anamorphic',
    name: 'Cooke Anamorphic/i',
    brand: 'Cooke',
    focalLengths: ['25mm', '32mm', '40mm', '50mm', '75mm', '100mm'],
    characteristics: 'Oval bokeh, lens flares, epic widescreen',
    style: 'anamorphic'
  },
  {
    id: 'zeiss-supreme',
    name: 'Zeiss Supreme Prime',
    brand: 'Zeiss',
    focalLengths: ['18mm', '25mm', '35mm', '50mm', '85mm', '100mm'],
    characteristics: 'Clean, neutral, high contrast, modern',
    style: 'clean'
  },
  {
    id: 'hawk-v-lite',
    name: 'Hawk V-Lite',
    brand: 'Vantage',
    focalLengths: ['25mm', '35mm', '50mm', '75mm', '110mm'],
    characteristics: 'Anamorphic flares, warm highlights, vintage feel',
    style: 'vintage'
  },
  {
    id: 'helios-44',
    name: 'Helios 44-2',
    brand: 'Helios',
    focalLengths: ['58mm'],
    characteristics: 'Swirly bokeh, character, dreamy distortion',
    style: 'artistic'
  },
  {
    id: 'petzval-lens',
    name: 'Petzval 85mm',
    brand: 'Lomography',
    focalLengths: ['85mm'],
    characteristics: 'Extreme swirly bokeh, artistic blur, vintage portrait',
    style: 'portrait'
  },
  {
    id: 'leica-summilux',
    name: 'Leica Summilux-C',
    brand: 'Leica',
    focalLengths: ['18mm', '25mm', '35mm', '50mm', '75mm', '100mm'],
    characteristics: 'Precise, crisp, subtle warmth, documentary',
    style: 'documentary'
  }
];

// AI Video Models
export const VIDEO_MODELS = [
  {
    id: 'sora-2',
    name: 'Sora 2',
    provider: 'OpenAI',
    description: 'Latest generation video model with exceptional quality',
    strengths: ['Cinematic quality', 'Complex scenes', 'Realistic physics'],
    maxDuration: 20,
    aspectRatios: ['16:9', '9:16', '1:1', '4:3'],
    available: true,
    creditsPerSecond: 10
  },
  {
    id: 'veo-3.1',
    name: 'Veo 3.1',
    provider: 'Google DeepMind',
    description: 'Ultra-realistic video with natural motion',
    strengths: ['Human motion', 'Facial expressions', 'Lighting'],
    maxDuration: 16,
    aspectRatios: ['16:9', '9:16', '1:1'],
    available: true,
    creditsPerSecond: 12
  },
  {
    id: 'kling-3.0',
    name: 'Kling 3.0',
    provider: 'Kuaishou',
    description: 'Character-focused with multi-shot sequences',
    strengths: ['Character consistency', 'Dialogue', 'Natural expressions'],
    maxDuration: 10,
    aspectRatios: ['16:9', '9:16', '1:1', '4:3', '3:4'],
    available: true,
    creditsPerSecond: 8
  },
  {
    id: 'runway-gen3',
    name: 'Runway Gen-3 Alpha',
    provider: 'Runway',
    description: 'Fast generation with motion brush control',
    strengths: ['Speed', 'Motion control', 'Style transfer'],
    maxDuration: 10,
    aspectRatios: ['16:9', '9:16', '1:1'],
    available: true,
    creditsPerSecond: 6
  },
  {
    id: 'pika-2.0',
    name: 'Pika 2.0',
    provider: 'Pika Labs',
    description: 'Versatile with strong style adherence',
    strengths: ['Artistic styles', 'Animation', 'Lip sync'],
    maxDuration: 8,
    aspectRatios: ['16:9', '9:16', '1:1'],
    available: true,
    creditsPerSecond: 5
  }
];

// AI Image Models
export const IMAGE_MODELS = [
  {
    id: 'flux-dev',
    name: 'FLUX.1 Dev',
    provider: 'fal.ai',
    description: 'Fast, high-quality text-to-image with excellent consistency',
    strengths: ['Speed', 'Quality', 'Consistency'],
    resolutions: ['1024x1024', '1536x1024', '1024x1536'],
    available: true,
    tag: 'NEW'
  },
  {
    id: 'flux-pro',
    name: 'FLUX Pro 1.1',
    provider: 'fal.ai',
    description: 'Premium quality generation with enhanced details',
    strengths: ['Premium Quality', 'Fine Details', 'Photorealism'],
    resolutions: ['1024x1024', '1536x1024', '1024x1536'],
    available: true,
    tag: 'BEST'
  },
  {
    id: 'nano-banana-pro',
    name: 'Nano Banana Pro',
    provider: 'Google',
    description: 'Most realistic image generation',
    strengths: ['Photorealism', 'Accurate details', 'Natural lighting'],
    resolutions: ['1024x1024', '1536x1024', '1024x1536', '2048x2048', '4096x4096'],
    available: true,
    tag: 'TOP'
  },
  {
    id: 'gpt-image-1',
    name: 'GPT Image 1',
    provider: 'OpenAI',
    description: 'Versatile with excellent prompt following',
    strengths: ['Prompt accuracy', 'Creativity', 'Consistency'],
    resolutions: ['1024x1024', '1536x1024', '1024x1536'],
    available: true
  },
  {
    id: 'ideogram-2',
    name: 'Ideogram 2.0',
    provider: 'Ideogram',
    description: 'Excellent text rendering and design',
    strengths: ['Text in images', 'Logos', 'Typography'],
    resolutions: ['1024x1024', '1536x1024', '1024x1536'],
    available: true
  }
];

// Character Consistency Models (fal.ai)
export const CHARACTER_CONSISTENCY_MODELS = [
  {
    id: 'flux-pulid',
    name: 'FLUX PuLID',
    provider: 'fal.ai',
    description: 'Face/identity preservation - generate consistent faces from a single reference',
    type: 'face-id',
    strengths: ['Instant consistency', 'No training needed', 'Single reference image'],
    available: true,
    tag: 'NEW'
  },
  {
    id: 'flux-lora',
    name: 'FLUX LoRA',
    provider: 'fal.ai',
    description: 'Generate with trained character models - highest consistency',
    type: 'lora',
    strengths: ['Highest consistency', 'Trained identity', 'Unlimited generations'],
    available: true,
    tag: 'BEST'
  },
  {
    id: 'lora-trainer',
    name: 'Portrait LoRA Trainer',
    provider: 'fal.ai',
    description: 'Train custom character LoRA for true identity preservation',
    type: 'training',
    strengths: ['Creates permanent model', '100% consistent', 'Use across all scenes'],
    trainingTime: '5-15 minutes',
    minImages: 3,
    maxImages: 20,
    available: true,
    tag: 'PRO'
  }
];

// Aspect Ratios
export const ASPECT_RATIOS = [
  { id: '1:1', name: 'Square (1:1)', width: 1024, height: 1024, description: 'Instagram, Profile' },
  { id: '16:9', name: 'Landscape (16:9)', width: 1536, height: 864, description: 'YouTube, Cinema' },
  { id: '9:16', name: 'Portrait (9:16)', width: 864, height: 1536, description: 'TikTok, Stories' },
  { id: '4:3', name: 'Standard (4:3)', width: 1024, height: 768, description: 'Classic TV' },
  { id: '3:4', name: 'Portrait (3:4)', width: 768, height: 1024, description: 'Portrait Photos' },
  { id: '21:9', name: 'Ultra-Wide (21:9)', width: 1536, height: 640, description: 'Cinematic' },
  { id: '2:3', name: 'Book Cover (2:3)', width: 683, height: 1024, description: 'Book Illustrations' }
];

// Character Expressions for variation
export const EXPRESSIONS = [
  { id: 'neutral', name: 'Neutral', prompt: 'neutral expression, calm face' },
  { id: 'happy', name: 'Happy', prompt: 'happy expression, warm smile, joyful' },
  { id: 'smiling', name: 'Smiling', prompt: 'gentle smile, friendly expression' },
  { id: 'laughing', name: 'Laughing', prompt: 'laughing, genuine joy, bright expression' },
  { id: 'serious', name: 'Serious', prompt: 'serious expression, focused, determined' },
  { id: 'thoughtful', name: 'Thoughtful', prompt: 'thoughtful expression, contemplative, pondering' },
  { id: 'surprised', name: 'Surprised', prompt: 'surprised expression, wide eyes, amazed' },
  { id: 'sad', name: 'Sad', prompt: 'sad expression, melancholy, emotional' },
  { id: 'angry', name: 'Angry', prompt: 'angry expression, intense, fierce' },
  { id: 'confident', name: 'Confident', prompt: 'confident expression, self-assured, powerful' },
  { id: 'shy', name: 'Shy', prompt: 'shy expression, bashful, looking away slightly' },
  { id: 'mysterious', name: 'Mysterious', prompt: 'mysterious expression, enigmatic, intriguing' }
];

// Shot Types for multi-angle generation
export const SHOT_TYPES = [
  { id: 'front', name: 'Front View', prompt: 'front facing, looking at camera, eye contact' },
  { id: 'three-quarter-left', name: '3/4 Left', prompt: 'three quarter view from left, slight turn' },
  { id: 'three-quarter-right', name: '3/4 Right', prompt: 'three quarter view from right, slight turn' },
  { id: 'profile-left', name: 'Profile Left', prompt: 'side profile view from left, looking left' },
  { id: 'profile-right', name: 'Profile Right', prompt: 'side profile view from right, looking right' },
  { id: 'looking-up', name: 'Looking Up', prompt: 'looking upward, low angle perspective' },
  { id: 'looking-down', name: 'Looking Down', prompt: 'looking downward, high angle perspective' },
  { id: 'over-shoulder', name: 'Over Shoulder', prompt: 'over the shoulder view, back partially visible' },
  { id: 'back-view', name: 'Back View', prompt: 'back view, showing from behind' }
];

// Lighting Presets
export const LIGHTING_PRESETS = [
  { id: 'natural', name: 'Natural Light', prompt: 'natural daylight, soft shadows, realistic' },
  { id: 'golden-hour', name: 'Golden Hour', prompt: 'golden hour lighting, warm sunset glow, soft' },
  { id: 'blue-hour', name: 'Blue Hour', prompt: 'blue hour, twilight, cool tones, atmospheric' },
  { id: 'studio', name: 'Studio Light', prompt: 'professional studio lighting, clean, even' },
  { id: 'dramatic', name: 'Dramatic', prompt: 'dramatic lighting, high contrast, shadows' },
  { id: 'neon', name: 'Neon Glow', prompt: 'neon lights, colorful glow, cyberpunk lighting' },
  { id: 'candlelight', name: 'Candlelight', prompt: 'warm candlelight, intimate, flickering' },
  { id: 'moonlight', name: 'Moonlight', prompt: 'soft moonlight, nighttime, ethereal glow' },
  { id: 'overcast', name: 'Overcast', prompt: 'overcast sky, soft diffused light, no harsh shadows' },
  { id: 'backlit', name: 'Backlit', prompt: 'backlit, rim lighting, silhouette edge, dramatic' }
];

// Build camera + lens prompt enhancement
export function buildCinemaPrompt(cameraId, lensId, focalLength) {
  const camera = CAMERA_BODIES.find(c => c.id === cameraId);
  const lens = CINEMA_LENSES.find(l => l.id === lensId);
  
  if (!camera || !lens) return '';
  
  return `shot on ${camera.name} with ${lens.name} ${focalLength || ''}, ${camera.characteristics}, ${lens.characteristics}`;
}

// Build character consistency prompt
export function buildCharacterPrompt(character) {
  const parts = [];
  
  if (character.gender) parts.push(character.gender.toLowerCase());
  if (character.ageGroup) parts.push(character.ageGroup.toLowerCase());
  if (character.bodyType) parts.push(`${character.bodyType.toLowerCase()} build`);
  if (character.skinTone) parts.push(`${character.skinTone.toLowerCase()} skin`);
  if (character.hairColor && character.hairStyle) {
    parts.push(`${character.hairColor.toLowerCase()} ${character.hairStyle.toLowerCase()} hair`);
  }
  if (character.eyeColor) parts.push(`${character.eyeColor.toLowerCase()} eyes`);
  if (character.clothing) parts.push(`wearing ${character.clothing.toLowerCase()} attire`);
  if (character.expression) parts.push(`${character.expression.toLowerCase()} expression`);
  if (character.additionalDetails) parts.push(character.additionalDetails);
  
  return parts.join(', ');
}

export default {
  CAMERA_BODIES,
  CINEMA_LENSES,
  VIDEO_MODELS,
  IMAGE_MODELS,
  ASPECT_RATIOS,
  EXPRESSIONS,
  SHOT_TYPES,
  LIGHTING_PRESETS,
  buildCinemaPrompt,
  buildCharacterPrompt
};
