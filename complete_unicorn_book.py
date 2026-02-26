#!/usr/bin/env python3
"""
Book Completion Script - The Unicorn's Rainbow Bridge
Picture Book (Ages 3-6) - Watercolour Style
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId

APP_DIR = Path(__file__).parent
BACKEND_DIR = APP_DIR / 'backend'

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / '.env')

sys.path.insert(0, str(BACKEND_DIR))
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Book Configuration
BOOK_ID = "699adbe6176ebca750087f15"
BOOK_TITLE = "The Unicorn's Rainbow Bridge"

# Character Bible
CHARACTER_BIBLE = {
    "stardust": {
        "name": "Stardust",
        "type": "unicorn",
        "description": "A graceful white unicorn with a flowing silver mane that sparkles like starlight, a spiral golden horn on her forehead, large gentle violet eyes with long lashes, a soft pink nose, and a tail that shimmers with all the colors of the rainbow. Her hooves leave tiny stars wherever she walks.",
        "personality": "gentle, magical, nurturing, wise"
    },
    "lily": {
        "name": "Lily",
        "type": "main character",
        "age": "5 years old",
        "description": "A sweet little girl with curly golden-blonde hair tied with a purple ribbon, big blue eyes full of wonder, rosy cheeks, fair skin, wearing a soft lavender nightgown with tiny stars on it and fluffy bunny slippers",
        "personality": "curious, brave, kind, imaginative"
    }
}

# Art Style
ART_STYLE = {
    "style": "soft watercolour children's book illustration",
    "mood": "dreamy, magical, peaceful, bedtime",
    "colors": "soft pastels, lavender, silver, rainbow hues, starlight gold, moonlit blue",
    "quality": "professional children's book quality, gentle watercolor washes, magical sparkles"
}

# Story Pages
STORY_PAGES = [
    {
        "page_num": 1,
        "type": "title",
        "text": "The Unicorn's Rainbow Bridge\n\nA Magical Bedtime Story",
        "image_prompt": "A majestic white unicorn with silver mane and golden horn standing on a glowing rainbow bridge in the night sky, stars twinkling all around, dreamy clouds below, magical sparkles",
        "starter_match": None
    },
    {
        "page_num": 2,
        "text": "Every night when the stars come out and the moon rises high, a magical unicorn named Stardust appears in the sky.",
        "image_prompt": "Stardust the white unicorn with silver sparkly mane and golden horn emerging from behind fluffy clouds, full moon behind her, starlit night sky, magical glow",
        "starter_match": None
    },
    {
        "page_num": 3,
        "text": "Little Lily couldn't sleep. She tossed and turned in her cozy bed, watching the moonlight dance on her ceiling.",
        "image_prompt": "Lily a 5-year-old girl with curly golden-blonde hair and purple ribbon in lavender nightgown lying awake in her cozy bed, moonlight streaming through window, soft bedroom with stuffed animals",
        "starter_match": None
    },
    {
        "page_num": 4,
        "text": "\"I wish I could visit the land of dreams,\" Lily whispered to the stars. And that's when she saw it—a beautiful rainbow glowing outside her window!",
        "image_prompt": "Lily at her bedroom window in wonder, gazing at a magical glowing rainbow appearing in the night sky, stars twinkling, her face lit with amazement",
        "starter_match": "Rainbow After Rain"
    },
    {
        "page_num": 5,
        "text": "At the end of the rainbow stood Stardust, her mane flowing like silver starlight. \"Hello, little one,\" the unicorn said softly. \"Would you like to cross the Rainbow Bridge to Dreamland?\"",
        "image_prompt": "Stardust the white unicorn with silver mane standing at the start of a glowing rainbow bridge, speaking gently to Lily who stands in wonder, magical sparkles everywhere",
        "starter_match": None
    },
    {
        "page_num": 6,
        "text": "Lily nodded excitedly. She climbed onto Stardust's soft back, and together they began to walk across the Rainbow Bridge.",
        "image_prompt": "Lily riding on Stardust the unicorn's back, both walking onto the rainbow bridge, magical night sky with stars, Lily holding unicorn's mane gently, joyful expression",
        "starter_match": None
    },
    {
        "page_num": 7,
        "text": "Each color of the rainbow felt different under Stardust's hooves. Red was warm like sunshine. Orange tickled like giggles. Yellow bounced like joy!",
        "image_prompt": "Stardust and Lily walking across the red, orange and yellow sections of the rainbow bridge, each color glowing, magical particles floating up, warm happy feeling",
        "starter_match": None
    },
    {
        "page_num": 8,
        "text": "Green felt soft like grass. Blue was cool like a gentle breeze. And purple... purple felt like the coziest hug.",
        "image_prompt": "Stardust and Lily continuing across green, blue and purple sections of rainbow bridge, dreamy clouds below, stars above, peaceful sleepy expressions",
        "starter_match": None
    },
    {
        "page_num": 9,
        "text": "At the end of the bridge, they found Dreamland—a magical place where cotton candy clouds floated past castles made of moonbeams.",
        "image_prompt": "Lily and Stardust arriving in Dreamland, fluffy pink cotton candy clouds, silver castle made of moonbeams in distance, floating stars, magical landscape",
        "starter_match": "Fairy Tale Castle"
    },
    {
        "page_num": 10,
        "text": "\"You can dream of anything here,\" Stardust whispered. Lily closed her eyes and dreamed of flying through fields of flowers.",
        "image_prompt": "Lily with eyes closed peacefully on Stardust's back, dream clouds forming showing Lily flying through colorful flower fields, magical and whimsical",
        "starter_match": "Peaceful Meadow"
    },
    {
        "page_num": 11,
        "text": "When it was time to go home, Stardust carried Lily gently back across the Rainbow Bridge. The colors now shimmered with sleepy magic.",
        "image_prompt": "Stardust carrying sleepy Lily back across the rainbow bridge, Lily's eyes half-closed, gentle peaceful journey, soft moonlight",
        "starter_match": None
    },
    {
        "page_num": 12,
        "text": "\"Will you come back tomorrow?\" Lily yawned. \"I'll be here whenever you need me,\" Stardust promised. \"Just look for the rainbow.\"",
        "image_prompt": "Stardust nuzzling sleepy Lily goodbye near her window, soft tender moment, unicorn and child connection, starlight around them",
        "starter_match": None
    },
    {
        "page_num": 13,
        "text": "Lily climbed back into her cozy bed, feeling warm and safe. She hugged her pillow and smiled.",
        "image_prompt": "Lily back in her cozy bed, snuggled under blankets, content peaceful smile, moonlight through window, safe and loved feeling",
        "starter_match": None
    },
    {
        "page_num": 14,
        "text": "And as she drifted off to sleep, she could still see the soft glow of the Rainbow Bridge... and a unicorn dancing among the stars.\n\nThe End",
        "image_prompt": "Final scene showing sleeping Lily in foreground, window showing Stardust the unicorn dancing on rainbow bridge in starry sky, magical farewell, dreamy ending",
        "starter_match": None
    }
]

# Starter Library URLs (watercolour style)
STARTER_LIBRARY = {
    "Rainbow After Rain": "/starter-library/scenes/batch2_scene_009_watercolour.png",
    "Fairy Tale Castle": "/starter-library/scenes/batch2_scene_002_watercolour.png", 
    "Peaceful Meadow": "/starter-library/scenes/batch2_scene_004_watercolour.png"
}

async def generate_image(prompt: str, filename: str):
    """Generate an image using GPT-Image-1"""
    full_prompt = f"{ART_STYLE['style']}, {ART_STYLE['mood']} mood, {prompt}. Color palette: {ART_STYLE['colors']}. {ART_STYLE['quality']}."
    
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)
    images = await image_gen.generate_images(
        prompt=full_prompt,
        model="gpt-image-1",
        number_of_images=1,
        quality="medium"
    )
    
    if images and len(images) > 0:
        output_dir = APP_DIR / 'content/books/completed/unicorn_rainbow_bridge'
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        with open(filepath, 'wb') as f:
            f.write(images[0])
        return str(filepath)
    return None

async def complete_book():
    """Complete the book with content and images"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"Completing: {BOOK_TITLE}")
    print("=" * 60)
    
    # Generate cover
    print("\n[1/15] Generating cover...")
    cover_prompt = f"Children's book cover for '{BOOK_TITLE}'. {CHARACTER_BIBLE['stardust']['description']} standing majestically on a glowing rainbow bridge in a starlit night sky, magical and dreamy, title space at top"
    cover_path = await generate_image(cover_prompt, "cover.png")
    print(f"  Cover saved: {cover_path}")
    
    # Process pages
    pages = []
    for i, page_data in enumerate(STORY_PAGES):
        page_num = page_data["page_num"]
        print(f"\n[{i+2}/15] Processing page {page_num}...")
        
        # Check if we can use starter library
        if page_data.get("starter_match") and page_data["starter_match"] in STARTER_LIBRARY:
            image_url = STARTER_LIBRARY[page_data["starter_match"]]
            print(f"  Using starter library: {page_data['starter_match']}")
        else:
            # Generate new image
            image_path = await generate_image(page_data["image_prompt"], f"page_{page_num:02d}.png")
            # For database, we'll use relative URL
            image_url = f"/book-assets/unicorn_rainbow_bridge/page_{page_num:02d}.png"
            print(f"  Generated: page_{page_num:02d}.png")
        
        pages.append({
            "page_number": page_num,
            "content": page_data["text"],
            "text": page_data["text"],
            "image_url": image_url,
            "layout": "full_spread" if page_num == 1 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Generate back cover
    print("\n[15/15] Generating back cover...")
    back_cover_prompt = f"Back cover for children's book. {CHARACTER_BIBLE['stardust']['description']} and {CHARACTER_BIBLE['lily']['description']} together on rainbow bridge looking at distant Dreamland castle, peaceful magical scene"
    back_cover_path = await generate_image(back_cover_prompt, "back_cover.png")
    print(f"  Back cover saved: {back_cover_path}")
    
    # Update database
    print("\n" + "=" * 60)
    print("Updating database...")
    
    # Use relative URL for cover in database
    cover_url = "/book-assets/unicorn_rainbow_bridge/cover.png"
    
    result = await db.books.update_one(
        {"_id": ObjectId(BOOK_ID)},
        {
            "$set": {
                "pages": pages,
                "cover_image_url": cover_url,
                "back_cover_url": "/book-assets/unicorn_rainbow_bridge/back_cover.png",
                "page_count": len(pages),
                "status": "published",
                "age_range": "3-6",
                "art_style": "watercolour",
                "updated_at": datetime.utcnow().isoformat(),
                "character_bible": CHARACTER_BIBLE,
                "completed_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    print(f"Database updated: {result.modified_count} document(s)")
    print("\n✅ Book completion successful!")
    print(f"   Title: {BOOK_TITLE}")
    print(f"   Pages: {len(pages)}")
    print(f"   Images generated: {len(pages) - 3 + 2}")  # Minus starter images, plus covers
    print(f"   Starter library used: 3 images")

if __name__ == "__main__":
    asyncio.run(complete_book())
