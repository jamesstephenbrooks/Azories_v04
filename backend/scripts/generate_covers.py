#!/usr/bin/env python3
"""
Generate cover images for existing books using AI.
Run this script in the background as it takes time.
"""

import asyncio
import os
import sys
import base64
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Cover prompts for each book
BOOK_COVERS = {
    "The Dragon's Secret Garden": "children's book cover illustration, young girl with autumn hair discovering a magical hidden garden with a friendly baby dragon, glowing flowers, enchanted atmosphere, warm colors, whimsical fantasy art style",
    "Robot Best Friend": "children's book cover illustration, young girl with glasses hugging a cute friendly robot with blue glowing eyes, science fair ribbons in background, heartwarming, colorful, futuristic but friendly style",
    "The Case of the Missing Cookies": "children's book cover illustration, two kid detectives with magnifying glasses following cookie crumbs, school cafeteria setting, mystery theme, playful and fun style",
    "Super Silly Superhero": "children's book cover illustration, funny boy superhero flying sideways with a cape, comic book style, bright colors, humorous expression, action pose with sparkles",
    "Colors of the World": "children's book cover illustration, magical girl named Rainbow touching a colorful rainbow arc, gray world becoming colorful around her, beautiful transformation, vibrant and inspiring"
}

async def generate_cover_image(prompt, api_key):
    """Generate a cover image using AI"""
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        if not api_key:
            print("  [SKIP] No API key")
            return None
        
        image_gen = OpenAIImageGeneration(api_key=api_key)
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1,
            quality="medium",
            size="1024x1536"  # Portrait for book covers
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
        return None
    except Exception as e:
        print(f"  [ERROR] Image generation failed: {e}")
        return None

async def main():
    print("=" * 60)
    print("GENERATING COVER IMAGES FOR BOOKS")
    print("=" * 60)
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME required")
        return
    
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY required for image generation")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Get all books without cover images
    books = await db.books.find(
        {"$or": [{"cover_image": ""}, {"cover_image": None}]},
        {"_id": 0, "id": 1, "title": 1}
    ).to_list(100)
    
    print(f"\nFound {len(books)} books needing covers")
    
    for i, book in enumerate(books):
        title = book.get("title", "")
        book_id = book.get("id")
        
        if title not in BOOK_COVERS:
            print(f"\n[{i+1}/{len(books)}] Skipping '{title}' - no cover prompt defined")
            continue
        
        print(f"\n[{i+1}/{len(books)}] Generating cover for: {title}")
        
        prompt = BOOK_COVERS[title]
        cover_image = await generate_cover_image(prompt, api_key)
        
        if cover_image:
            # Update book with cover image
            await db.books.update_one(
                {"id": book_id},
                {"$set": {
                    "cover_image": cover_image,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            print(f"  [SUCCESS] Cover generated and saved")
        else:
            print(f"  [FAILED] Could not generate cover")
        
        # Small delay between generations
        await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("COVER GENERATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
