#!/usr/bin/env python3
"""
Resume Script - The Unicorn's Rainbow Bridge
Continues from page 8 where we left off
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

BOOK_ID = "699adbe6176ebca750087f15"
OUTPUT_DIR = APP_DIR / 'content/books/completed/unicorn_rainbow_bridge'

# Art Style (same as original)
ART_STYLE = "soft watercolour children's book illustration, dreamy magical peaceful bedtime mood, soft pastels lavender silver rainbow hues starlight gold moonlit blue, professional children's book quality gentle watercolor washes magical sparkles"

# Character descriptions for consistency
STARDUST = "Stardust, a graceful white unicorn with flowing silver sparkly mane, spiral golden horn, large gentle violet eyes with long lashes, soft pink nose, rainbow-shimmer tail"
LILY = "Lily, a 5-year-old girl with curly golden-blonde hair tied with purple ribbon, big blue eyes, rosy cheeks, fair skin, wearing soft lavender nightgown with tiny stars, fluffy bunny slippers"

# Remaining pages to generate
REMAINING_PAGES = [
    {
        "page": 8,
        "text": "Green felt soft like grass. Blue was cool like a gentle breeze. And purple... purple felt like the coziest hug.",
        "prompt": f"{STARDUST} and {LILY} continuing across green, blue and purple sections of rainbow bridge, dreamy clouds below, stars above, peaceful sleepy expressions"
    },
    {
        "page": 9,
        "text": "At the end of the bridge, they found Dreamland—a magical place where cotton candy clouds floated past castles made of moonbeams.",
        "prompt": f"{LILY} and {STARDUST} arriving in Dreamland, fluffy pink cotton candy clouds, silver castle made of moonbeams in distance, floating stars, magical landscape",
        "starter_match": "/starter-library/scenes/batch2_scene_002_watercolour.png"
    },
    {
        "page": 10,
        "text": "\"You can dream of anything here,\" Stardust whispered. Lily closed her eyes and dreamed of flying through fields of flowers.",
        "prompt": f"{LILY} with eyes closed peacefully on {STARDUST}'s back, dream clouds forming showing Lily flying through colorful flower fields, magical and whimsical",
        "starter_match": "/starter-library/scenes/batch2_scene_004_watercolour.png"
    },
    {
        "page": 11,
        "text": "When it was time to go home, Stardust carried Lily gently back across the Rainbow Bridge. The colors now shimmered with sleepy magic.",
        "prompt": f"{STARDUST} carrying sleepy {LILY} back across the rainbow bridge, Lily's eyes half-closed, gentle peaceful journey, soft moonlight"
    },
    {
        "page": 12,
        "text": "\"Will you come back tomorrow?\" Lily yawned. \"I'll be here whenever you need me,\" Stardust promised. \"Just look for the rainbow.\"",
        "prompt": f"{STARDUST} nuzzling sleepy {LILY} goodbye near her window, soft tender moment, unicorn and child connection, starlight around them"
    },
    {
        "page": 13,
        "text": "Lily climbed back into her cozy bed, feeling warm and safe. She hugged her pillow and smiled.",
        "prompt": f"{LILY} back in her cozy bed, snuggled under blankets, content peaceful smile, moonlight through window, safe and loved feeling"
    },
    {
        "page": 14,
        "text": "And as she drifted off to sleep, she could still see the soft glow of the Rainbow Bridge... and a unicorn dancing among the stars.\n\nThe End",
        "prompt": f"Final scene showing sleeping {LILY} in foreground, window showing {STARDUST} dancing on rainbow bridge in starry sky, magical farewell, dreamy ending"
    }
]

BACK_COVER = {
    "prompt": f"Back cover for children's book. {STARDUST} and {LILY} together on rainbow bridge looking at distant Dreamland castle, peaceful magical scene, soft watercolour style"
}

async def generate_image(prompt: str, filename: str):
    """Generate an image using GPT-Image-1"""
    full_prompt = f"{ART_STYLE}. {prompt}"
    
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)
    images = await image_gen.generate_images(
        prompt=full_prompt,
        model="gpt-image-1",
        number_of_images=1,
        quality="medium"
    )
    
    if images and len(images) > 0:
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(images[0])
        print(f"    ✓ Saved: {filename}")
        return str(filepath)
    return None

async def resume_book():
    """Resume book completion from page 8"""
    print("=" * 60)
    print("RESUMING: The Unicorn's Rainbow Bridge")
    print("=" * 60)
    print(f"Starting from page 8 (7 pages + back cover remaining)")
    print()
    
    # Load existing state
    state_file = OUTPUT_DIR / "RESUME_STATE.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        print(f"Loaded state: {state['progress']['completed_pages']}/14 pages done")
    
    generated_images = []
    
    # Generate remaining pages
    for i, page_data in enumerate(REMAINING_PAGES):
        page_num = page_data["page"]
        print(f"\n[{i+1}/8] Page {page_num}...")
        
        # Check if using starter library
        if page_data.get("starter_match"):
            print(f"    → Using starter library image")
            generated_images.append({
                "page": page_num,
                "image_url": page_data["starter_match"],
                "text": page_data["text"],
                "source": "starter_library"
            })
        else:
            # Generate new image
            filepath = await generate_image(page_data["prompt"], f"page_{page_num:02d}.png")
            if filepath:
                generated_images.append({
                    "page": page_num,
                    "image_url": f"/book-assets/unicorn_rainbow_bridge/page_{page_num:02d}.png",
                    "text": page_data["text"],
                    "source": "generated"
                })
        
        await asyncio.sleep(0.5)
    
    # Generate back cover
    print(f"\n[8/8] Back cover...")
    back_cover_path = await generate_image(BACK_COVER["prompt"], "back_cover.png")
    
    # Update database with complete book
    print("\n" + "=" * 60)
    print("Updating database...")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Build complete pages array
    pages = []
    
    # Add previously completed pages (1-7)
    existing_pages = [
        {"page_number": 1, "text": "The Unicorn's Rainbow Bridge\n\nA Magical Bedtime Story", "image_url": "/book-assets/unicorn_rainbow_bridge/page_01.png"},
        {"page_number": 2, "text": "Every night when the stars come out and the moon rises high, a magical unicorn named Stardust appears in the sky.", "image_url": "/book-assets/unicorn_rainbow_bridge/page_02.png"},
        {"page_number": 3, "text": "Little Lily couldn't sleep. She tossed and turned in her cozy bed, watching the moonlight dance on her ceiling.", "image_url": "/book-assets/unicorn_rainbow_bridge/page_03.png"},
        {"page_number": 4, "text": "\"I wish I could visit the land of dreams,\" Lily whispered to the stars. And that's when she saw it—a beautiful rainbow glowing outside her window!", "image_url": "/starter-library/scenes/batch2_scene_009_watercolour.png"},
        {"page_number": 5, "text": "At the end of the rainbow stood Stardust, her mane flowing like silver starlight. \"Hello, little one,\" the unicorn said softly. \"Would you like to cross the Rainbow Bridge to Dreamland?\"", "image_url": "/book-assets/unicorn_rainbow_bridge/page_05.png"},
        {"page_number": 6, "text": "Lily nodded excitedly. She climbed onto Stardust's soft back, and together they began to walk across the Rainbow Bridge.", "image_url": "/book-assets/unicorn_rainbow_bridge/page_06.png"},
        {"page_number": 7, "text": "Each color of the rainbow felt different under Stardust's hooves. Red was warm like sunshine. Orange tickled like giggles. Yellow bounced like joy!", "image_url": "/book-assets/unicorn_rainbow_bridge/page_07.png"},
    ]
    pages.extend(existing_pages)
    
    # Add newly generated pages (8-14)
    for img in generated_images:
        pages.append({
            "page_number": img["page"],
            "text": img["text"],
            "content": img["text"],
            "image_url": img["image_url"],
            "layout": "text_left_image_right"
        })
    
    # Update database
    result = await db.books.update_one(
        {"_id": ObjectId(BOOK_ID)},
        {
            "$set": {
                "pages": pages,
                "cover_image_url": "/book-assets/unicorn_rainbow_bridge/cover.png",
                "back_cover_url": "/book-assets/unicorn_rainbow_bridge/back_cover.png",
                "page_count": len(pages),
                "status": "published",
                "age_range": "3-6",
                "art_style": "watercolour",
                "updated_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    print(f"Database updated: {result.modified_count} document(s)")
    
    # Update state file
    state["status"] = "completed"
    state["progress"]["completed_pages"] = 14
    state["progress"]["remaining_pages"] = 0
    state["progress"]["back_cover_generated"] = True
    state["completed_at"] = datetime.utcnow().isoformat()
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ BOOK COMPLETED: The Unicorn's Rainbow Bridge")
    print("=" * 60)
    print(f"   Total pages: 14")
    print(f"   Images generated: 5 (pages 8, 11, 12, 13, 14 + back cover)")
    print(f"   Starter library used: 2 (pages 9, 10)")
    print(f"   Status: Published")

if __name__ == "__main__":
    asyncio.run(resume_book())
