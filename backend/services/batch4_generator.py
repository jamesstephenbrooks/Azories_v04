#!/usr/bin/env python3
"""
Batch 4 Generator: Action & Emotion Scenes
Generates 50 AI-illustrated images for children's books
Categories: Character Actions (25) + Emotional Moments (25)
Art Styles: Watercolour, Realistic, Comic, Sketch
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'frontend/public/starter-library/actions'

# Action & Emotion scene prompts - 50 total
BATCH_4_PROMPTS = [
    # === WATERCOLOUR STYLE (13 images) - Actions & Emotions ===
    {"id": "act_001", "style": "watercolour", "prompt": "A child jumping joyfully through puddles in the rain, splashing water everywhere, pure happiness", "name": "Jumping in Puddles", "tags": ["action", "joy", "rain", "child", "playful"]},
    {"id": "act_002", "style": "watercolour", "prompt": "Two children hugging warmly after being reunited, emotional reunion moment, friendship", "name": "Warm Reunion Hug", "tags": ["emotion", "friendship", "hug", "children", "love"]},
    {"id": "act_003", "style": "watercolour", "prompt": "A child reaching up to catch floating bubbles in a sunny garden, wonder and delight", "name": "Catching Bubbles", "tags": ["action", "wonder", "play", "child", "garden"]},
    {"id": "act_004", "style": "watercolour", "prompt": "A young child crying happy tears while opening a birthday present, overwhelming joy", "name": "Happy Birthday Tears", "tags": ["emotion", "joy", "birthday", "surprise", "celebration"]},
    {"id": "act_005", "style": "watercolour", "prompt": "Children running excitedly toward a beach, arms outstretched, summer freedom", "name": "Running to the Beach", "tags": ["action", "excitement", "beach", "summer", "freedom"]},
    {"id": "act_006", "style": "watercolour", "prompt": "A child comforting a friend who is sad, showing empathy and kindness", "name": "Comforting a Friend", "tags": ["emotion", "empathy", "friendship", "kindness", "care"]},
    {"id": "act_007", "style": "watercolour", "prompt": "A child climbing a tree with determination and concentration, adventure", "name": "Climbing Adventure", "tags": ["action", "determination", "adventure", "nature", "brave"]},
    {"id": "act_008", "style": "watercolour", "prompt": "A child looking up at stars with absolute wonder and amazement, night sky", "name": "Stargazing Wonder", "tags": ["emotion", "wonder", "night", "stars", "curiosity"]},
    {"id": "act_009", "style": "watercolour", "prompt": "Children dancing together in a circle, celebration and joy, movement", "name": "Circle Dance Joy", "tags": ["action", "dance", "celebration", "friendship", "movement"]},
    {"id": "act_010", "style": "watercolour", "prompt": "A child scared hiding under blankets from thunder, but being brave", "name": "Being Brave", "tags": ["emotion", "fear", "brave", "comfort", "child"]},
    {"id": "act_011", "style": "watercolour", "prompt": "A child triumphantly finishing a race, arms raised in victory", "name": "Victory Finish", "tags": ["action", "triumph", "sports", "achievement", "pride"]},
    {"id": "act_012", "style": "watercolour", "prompt": "A child sharing their snack with a hungry bird, kindness moment", "name": "Sharing with Bird", "tags": ["emotion", "kindness", "sharing", "nature", "caring"]},
    {"id": "act_013", "style": "watercolour", "prompt": "A child making their first snowman, excitement and creativity in winter", "name": "Building Snowman", "tags": ["action", "winter", "creative", "joy", "snow"]},

    # === REALISTIC ILLUSTRATED STYLE (13 images) ===
    {"id": "act_014", "style": "realistic", "prompt": "A child scoring their first goal, pure ecstatic celebration, sports triumph", "name": "First Goal Celebration", "tags": ["action", "sports", "triumph", "celebration", "soccer"]},
    {"id": "act_015", "style": "realistic", "prompt": "A child nervously performing on stage for the first time, courage moment", "name": "Stage Courage", "tags": ["emotion", "nervous", "brave", "performance", "stage"]},
    {"id": "act_016", "style": "realistic", "prompt": "Children having a pillow fight, feathers flying, laughter and fun", "name": "Pillow Fight Fun", "tags": ["action", "play", "laughter", "children", "fun"]},
    {"id": "act_017", "style": "realistic", "prompt": "A child feeling proud showing their artwork to parents, achievement", "name": "Proud Artist Moment", "tags": ["emotion", "pride", "art", "achievement", "family"]},
    {"id": "act_018", "style": "realistic", "prompt": "A child diving into a swimming pool, summer splash, carefree moment", "name": "Pool Dive Splash", "tags": ["action", "swimming", "summer", "splash", "carefree"]},
    {"id": "act_019", "style": "realistic", "prompt": "A child feeling disappointed losing a game but being a good sport", "name": "Good Sportsmanship", "tags": ["emotion", "disappointment", "sportsmanship", "maturity", "learning"]},
    {"id": "act_020", "style": "realistic", "prompt": "A child flying a kite on a windy hill, freedom and joy", "name": "Flying Kite Freedom", "tags": ["action", "kite", "wind", "freedom", "joy"]},
    {"id": "act_021", "style": "realistic", "prompt": "A child feeling amazed seeing fireworks for the first time, wonder", "name": "Fireworks Amazement", "tags": ["emotion", "wonder", "fireworks", "celebration", "amazement"]},
    {"id": "act_022", "style": "realistic", "prompt": "A child rescuing a butterfly from a spider web, gentle hero moment", "name": "Butterfly Rescue", "tags": ["action", "rescue", "kindness", "nature", "gentle"]},
    {"id": "act_023", "style": "realistic", "prompt": "A child feeling grateful receiving a homemade gift from grandparent", "name": "Grateful Heart", "tags": ["emotion", "gratitude", "family", "love", "gift"]},
    {"id": "act_024", "style": "realistic", "prompt": "A child learning to ride a bike, wobbly but determined, perseverance", "name": "First Bike Ride", "tags": ["action", "learning", "bike", "determination", "milestone"]},
    {"id": "act_025", "style": "realistic", "prompt": "A child feeling excited waiting for Santa, Christmas anticipation", "name": "Christmas Excitement", "tags": ["emotion", "excitement", "christmas", "anticipation", "wonder"]},
    {"id": "act_026", "style": "realistic", "prompt": "Children playing hide and seek, one child peeking around a tree", "name": "Hide and Seek", "tags": ["action", "play", "game", "friends", "fun"]},

    # === COMIC BOOK STYLE (12 images) ===
    {"id": "act_027", "style": "comic", "prompt": "A superhero child flying through clouds, cape flowing, heroic pose", "name": "Hero Flying High", "tags": ["action", "superhero", "flying", "heroic", "adventure"]},
    {"id": "act_028", "style": "comic", "prompt": "A child feeling super confident before a big challenge, power pose", "name": "Power Pose Confidence", "tags": ["emotion", "confidence", "brave", "powerful", "ready"]},
    {"id": "act_029", "style": "comic", "prompt": "Children working together to build a giant sandcastle, teamwork", "name": "Teamwork Castle", "tags": ["action", "teamwork", "building", "beach", "cooperation"]},
    {"id": "act_030", "style": "comic", "prompt": "A child feeling fierce determination facing a challenge, intense focus", "name": "Fierce Determination", "tags": ["emotion", "determination", "focus", "challenge", "brave"]},
    {"id": "act_031", "style": "comic", "prompt": "A child on a rope swing over a river, thrilling adventure moment", "name": "Rope Swing Adventure", "tags": ["action", "adventure", "swing", "thrill", "brave"]},
    {"id": "act_032", "style": "comic", "prompt": "A child feeling triumphant after solving a difficult puzzle, eureka", "name": "Eureka Moment", "tags": ["emotion", "triumph", "smart", "puzzle", "achievement"]},
    {"id": "act_033", "style": "comic", "prompt": "A child racing on a go-kart, speed lines, competitive spirit", "name": "Go-Kart Racing", "tags": ["action", "racing", "speed", "competition", "exciting"]},
    {"id": "act_034", "style": "comic", "prompt": "A child feeling surprised by a surprise party, shock and joy", "name": "Surprise Party", "tags": ["emotion", "surprise", "joy", "party", "celebration"]},
    {"id": "act_035", "style": "comic", "prompt": "A child doing a spectacular skateboard trick, action sports", "name": "Skateboard Trick", "tags": ["action", "skateboard", "trick", "cool", "sports"]},
    {"id": "act_036", "style": "comic", "prompt": "A child feeling mischievous planning a harmless prank, playful", "name": "Mischievous Grin", "tags": ["emotion", "mischief", "playful", "fun", "sneaky"]},
    {"id": "act_037", "style": "comic", "prompt": "Children having an epic snowball fight, winter action battle", "name": "Snowball Battle", "tags": ["action", "snowball", "winter", "battle", "fun"]},
    {"id": "act_038", "style": "comic", "prompt": "A child feeling victorious holding a trophy high, champion moment", "name": "Trophy Champion", "tags": ["emotion", "victory", "champion", "trophy", "pride"]},

    # === PENCIL SKETCH STYLE (12 images) ===
    {"id": "act_039", "style": "sketch", "prompt": "A child quietly reading a book under a tree, peaceful contentment", "name": "Peaceful Reading", "tags": ["action", "reading", "peaceful", "nature", "quiet"]},
    {"id": "act_040", "style": "sketch", "prompt": "A child feeling shy meeting new friends at school, first day", "name": "Shy First Day", "tags": ["emotion", "shy", "school", "new", "nervous"]},
    {"id": "act_041", "style": "sketch", "prompt": "A child carefully planting a seed in soil, nurturing moment", "name": "Planting Seeds", "tags": ["action", "planting", "garden", "nurturing", "growth"]},
    {"id": "act_042", "style": "sketch", "prompt": "A child feeling deep love hugging their pet dog, bond moment", "name": "Pet Love Hug", "tags": ["emotion", "love", "pet", "bond", "comfort"]},
    {"id": "act_043", "style": "sketch", "prompt": "A child drawing in a sketchbook, lost in creative concentration", "name": "Creative Drawing", "tags": ["action", "art", "drawing", "creative", "focus"]},
    {"id": "act_044", "style": "sketch", "prompt": "A child feeling sleepy being carried by parent after long day", "name": "Sleepy Time", "tags": ["emotion", "sleepy", "love", "parent", "comfort"]},
    {"id": "act_045", "style": "sketch", "prompt": "A child tiptoeing quietly to not wake the baby, gentle care", "name": "Quiet Tiptoeing", "tags": ["action", "quiet", "gentle", "caring", "sibling"]},
    {"id": "act_046", "style": "sketch", "prompt": "A child feeling nostalgic looking at old photos with grandma", "name": "Memory Sharing", "tags": ["emotion", "nostalgia", "family", "memories", "love"]},
    {"id": "act_047", "style": "sketch", "prompt": "A child building a blanket fort, imagination and creativity", "name": "Blanket Fort", "tags": ["action", "building", "imagination", "play", "creative"]},
    {"id": "act_048", "style": "sketch", "prompt": "A child feeling curious peeking around a door, wonder", "name": "Curious Peek", "tags": ["emotion", "curious", "wonder", "peek", "discovery"]},
    {"id": "act_049", "style": "sketch", "prompt": "A child blowing dandelion seeds making a wish, hopeful moment", "name": "Dandelion Wishes", "tags": ["action", "wish", "dandelion", "hope", "magical"]},
    {"id": "act_050", "style": "sketch", "prompt": "A child feeling content falling asleep with favorite stuffed toy", "name": "Sweet Dreams", "tags": ["emotion", "content", "sleep", "comfort", "peaceful"]},
]

STYLE_SUFFIXES = {
    "watercolour": "soft watercolor children's book illustration style, gentle colors, artistic brushstrokes, warm and friendly, professional quality",
    "realistic": "detailed realistic children's book illustration, soft lighting, professional quality, warm tones, expressive",
    "comic": "vibrant comic book style illustration for children, bold colors, dynamic lines, expressive faces, action-oriented",
    "sketch": "charming pencil sketch illustration style, soft shading, delicate lines, warm and gentle, storybook quality"
}

async def generate_batch_4():
    """Generate all 50 images for Batch 4"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
    results = []
    
    for i, item in enumerate(BATCH_4_PROMPTS):
        filename = f"batch4_act_{item['id'].split('_')[1]}_{item['style']}.png"
        filepath = OUTPUT_DIR / filename
        
        # Skip if already exists
        if filepath.exists():
            print(f"[{i+1}/50] Skipping {filename} (already exists)")
            results.append({"id": item["id"], "file": filename, "status": "skipped"})
            continue
        
        # Build full prompt with style
        style_suffix = STYLE_SUFFIXES[item["style"]]
        full_prompt = f"{item['prompt']}, {style_suffix}"
        
        print(f"[{i+1}/50] Generating {item['name']} ({item['style']})...")
        
        try:
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model="gpt-image-1",
                number_of_images=1,
                size="1024x1024",
                quality="high"
            )
            
            if images and len(images) > 0:
                # Save the image
                with open(filepath, 'wb') as f:
                    f.write(images[0])
                print(f"    Saved: {filename}")
                results.append({"id": item["id"], "file": filename, "status": "success"})
            else:
                print(f"    ERROR: No image returned")
                results.append({"id": item["id"], "file": filename, "status": "error", "error": "No image"})
                
        except Exception as e:
            print(f"    ERROR: {str(e)[:100]}")
            results.append({"id": item["id"], "file": filename, "status": "error", "error": str(e)[:100]})
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    # Summary
    success = sum(1 for r in results if r["status"] in ["success", "skipped"])
    print(f"\n=== BATCH 4 COMPLETE ===")
    print(f"Success: {success}/50")
    print(f"Errors: {50 - success}")
    
    return results

if __name__ == "__main__":
    asyncio.run(generate_batch_4())
