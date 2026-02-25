"""
Starter Library Image Generator
Generates AI-illustrated images for children's book creation platform
"""

import os
import asyncio
import logging
import base64
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Import the OpenAI image generation from emergentintegrations
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

# Get API key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

async def generate_starter_image(
    prompt: str,
    name: str,
    category: str,
    tags: List[str],
    art_style: str,
    image_id: str
) -> Optional[Dict]:
    """
    Generate a single starter library image using GPT-Image-1
    
    Args:
        prompt: The full image generation prompt
        name: Display name for the image
        category: 'character', 'scene', 'object', or 'action'
        tags: List of searchable tags
        art_style: 'watercolour', 'realistic', 'comic', 'sketch'
        image_id: Unique identifier for the image
    
    Returns:
        Dict with image data or None if failed
    """
    if not EMERGENT_LLM_KEY:
        logging.error("EMERGENT_LLM_KEY not found in environment")
        return None
    
    try:
        # Add art style instructions to prompt
        style_instructions = {
            'watercolour': "painted in soft watercolour style with gentle washes and flowing colors, delicate brushstrokes",
            'realistic': "realistic illustrated style with detailed rendering, professional children's book illustration quality",
            'comic': "dynamic comic book style with bold lines, vibrant colors, and expressive features",
            'sketch': "pencil sketch style with detailed line work, crosshatching, and artistic shading"
        }
        
        style_suffix = style_instructions.get(art_style, style_instructions['realistic'])
        
        # Build the full prompt
        full_prompt = f"{prompt}, {style_suffix}, age-appropriate for children, vibrant and inspiring, high quality children's book illustration, safe for all ages"
        
        logging.info(f"Generating image: {name} ({art_style} style)")
        
        # Initialize the image generator
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        # Generate the image
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            # Convert to base64
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            image_url = f"data:image/png;base64,{image_base64}"
            
            return {
                "id": image_id,
                "url": image_url,
                "name": name,
                "category": category,
                "tags": tags + [art_style],
                "art_style": art_style,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            logging.error(f"No image generated for: {name}")
            return None
            
    except Exception as e:
        logging.error(f"Error generating image {name}: {e}")
        return None


async def generate_sample_characters() -> List[Dict]:
    """
    Generate 5 sample character images (one of each art style) for approval
    """
    samples = [
        {
            "prompt": "A friendly young girl with curly brown hair and bright eyes, wearing a colorful adventure outfit with a backpack, smiling warmly, diverse ethnicity, half-body portrait",
            "name": "Adventure Girl - Watercolour",
            "category": "character",
            "tags": ["child", "girl", "adventure", "friendly", "diverse"],
            "art_style": "watercolour",
            "image_id": "sample_char_1"
        },
        {
            "prompt": "A brave young wizard boy with messy black hair and round glasses, wearing a flowing purple robe with gold stars, holding a glowing wand, magical sparkles around him",
            "name": "Young Wizard - Realistic",
            "category": "character",
            "tags": ["wizard", "boy", "magic", "fantasy", "hero"],
            "art_style": "realistic",
            "image_id": "sample_char_2"
        },
        {
            "prompt": "A heroic young Black girl astronaut in a bright orange spacesuit, helmet under her arm, confident pose, stars reflecting in her visor, determined expression",
            "name": "Space Explorer - Comic",
            "category": "character",
            "tags": ["astronaut", "girl", "space", "hero", "diverse", "scifi"],
            "art_style": "comic",
            "image_id": "sample_char_3"
        },
        {
            "prompt": "A mischievous fairy with iridescent wings, pointed ears, wearing a dress made of flower petals, sitting on a mushroom, playful expression, magical dust floating around",
            "name": "Garden Fairy - Sketch",
            "category": "character",
            "tags": ["fairy", "fantasy", "magical", "nature", "whimsical"],
            "art_style": "sketch",
            "image_id": "sample_char_4"
        },
        {
            "prompt": "A friendly robot companion with big round eyes, a rounded body with colorful buttons, small antenna, waving happily, cute and approachable design for children",
            "name": "Friendly Robot - Watercolour",
            "category": "character",
            "tags": ["robot", "friendly", "scifi", "companion", "cute"],
            "art_style": "watercolour",
            "image_id": "sample_char_5"
        }
    ]
    
    generated_samples = []
    
    for sample in samples:
        result = await generate_starter_image(**sample)
        if result:
            generated_samples.append(result)
            logging.info(f"Generated: {sample['name']}")
        else:
            logging.error(f"Failed to generate: {sample['name']}")
    
    return generated_samples


if __name__ == "__main__":
    # Test the generator
    async def test():
        samples = await generate_sample_characters()
        print(f"Generated {len(samples)} sample images")
        for s in samples:
            print(f"  - {s['name']} ({s['art_style']})")
    
    asyncio.run(test())
