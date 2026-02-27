#!/usr/bin/env python3
"""
Generate images for Captain Compass and Pixie Dust Adventures using OpenAI GPT-Image-1
Uses Emergent LLM key as fal.ai key is invalid
"""

import asyncio
import os
import sys
import base64
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, '/app/backend')

# Import emergent integrations for OpenAI image generation
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

# Get Emergent LLM key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Image prompts for each book
BOOKS_DATA = {
    "ed34dc96-9c78-4eb7-8707-90245371bea4": {
        "title": "Captain Compass and the Treasure Map",
        "style": "realistic",
        "style_prompt": "Realistic painterly children's book illustration, nautical adventure theme, warm golden lighting",
        "page_prompts": [
            "A weathered female sea captain in her 40s on a wooden sailing ship deck, holding a glowing antique brass compass, grey morning sky",
            "A tiny cramped antique shop filled with nautical treasures, brass instruments, old maps, elderly bearded sailor behind counter",
            "Hands unrolling an ancient treasure map showing a turtle-shaped island with red X, candlelight on wooden table",
            "Ship's cabin with maps spread on table, female captain studying charts with compass and navigation tools",
            "A sailing ship on the ocean at sunrise, turtle-shaped island on distant horizon, sailor pointing from crow's nest",
            "Woman rowing small boat toward pristine white sand beach, dense tropical vegetation, enormous ancient tree",
            "Muddy treasure chest being opened in jungle clearing, revealing dozens of rolled maps inside, dappled sunlight",
            "Female captain sitting on white beach surrounded by unrolled maps, sunset, brass compass beside her",
            "Captain climbing aboard ship at sunset carrying treasure chest, first mate helping, warm orange sky",
            "Dawn light in captain's cabin, maps sorted on table, brass compass pointing steadily, captain looking at horizon",
        ]
    },
    "56c45425-ba3b-421d-b17f-f13321c32f65": {
        "title": "Pixie Dust Adventures",
        "style": "watercolor",
        "style_prompt": "Soft watercolor children's book illustration, magical fantasy, gentle pastel colors with sparkles",
        "page_prompts": [
            "Magical fairy village with mushroom houses, pixies flying with colorful sparkling dust, young pixie with amber wings",
            "Young pixie girl sitting cross-legged in dewy morning meadow, amber light from fingertips, woodland creatures approaching",
            "Glowing crystal vessel in pixie village square, pixies with different colored dusts, autumn leaves falling",
            "Small pixie girl crouching beside distressed barn owl in moonlit grass, gentle concerned expression",
            "Pixie with amber light radiating from palms near a barn owl, healing glow, peaceful night scene",
            "Pixie and barn owl sitting peacefully in meadow at night, grass growing greener where amber light touches",
            "Pixie helping woodland creatures at night - hedgehog, fox, mouse - hands glowing bright amber, forest lane lit up",
            "Great crystal vessel singing with warm amber light, pixies watching in amazement, elderly dust-master surprised",
            "Wise elderly pixie addressing crowd around glowing crystal vessel, young pixie standing humbly nearby",
            "Pixie sitting in snowy winter meadow, amber glow from hands, woodland creatures gathered, cozy magical scene",
        ]
    }
}


async def upload_image_to_storage(image_bytes: bytes) -> str:
    """
    Upload image bytes to Cloudinary and return URL.
    """
    try:
        import cloudinary
        import cloudinary.uploader
        import io
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET')
        )
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            io.BytesIO(image_bytes),
            folder="azories/book-pages",
            resource_type="image"
        )
        
        if result and result.get("secure_url"):
            return result["secure_url"]
        
    except Exception as e:
        logger.error(f"Failed to upload to Cloudinary: {e}")
    
    return None


async def generate_images_for_book(db, book_id: str, book_data: dict, dry_run: bool = True):
    """Generate images for a book's pages"""
    
    title = book_data["title"]
    style = book_data["style"]
    style_prompt = book_data["style_prompt"]
    page_prompts = book_data["page_prompts"]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📚 {title}")
    logger.info(f"   Style: {style}")
    logger.info(f"{'='*60}")
    
    # Get existing pages
    pages = await db.pages.find({"book_id": book_id}).sort("page_number", 1).to_list(None)
    
    if not pages:
        logger.error(f"   ❌ No pages found for book")
        return 0
    
    if dry_run:
        for i, page in enumerate(pages):
            has_image = "✅" if page.get("image_url") else "❌"
            logger.info(f"   Page {page['page_number']}: {has_image} image")
        return len(pages)
    
    # Generate images
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
    updated = 0
    
    for i, page in enumerate(pages):
        page_num = page["page_number"]
        
        # Skip if already has image
        if page.get("image_url") and not page["image_url"].startswith("data:"):
            logger.info(f"   Page {page_num}: Already has image - skipping")
            continue
        
        prompt_idx = min(i, len(page_prompts) - 1)
        prompt = f"{page_prompts[prompt_idx]}. Style: {style_prompt}"
        
        logger.info(f"   Page {page_num}: Generating image...")
        
        try:
            images = await image_gen.generate_images(
                prompt=prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            
            if images and len(images) > 0:
                # Upload image and get URL
                image_url = await upload_image_to_storage(images[0])
                
                # Update page in database
                await db.pages.update_one(
                    {"id": page["id"]},
                    {"$set": {"image_url": image_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # Update embedded page
                book = await db.books.find_one({"id": book_id})
                if book and book.get("pages"):
                    for ep in book["pages"]:
                        if ep.get("id") == page["id"]:
                            ep["image_url"] = image_url
                    await db.books.update_one(
                        {"id": book_id},
                        {"$set": {"pages": book["pages"]}}
                    )
                
                logger.info(f"   ✅ Page {page_num}: Image generated and saved")
                updated += 1
            else:
                logger.warning(f"   ⚠️ Page {page_num}: No image returned")
                
        except Exception as e:
            logger.error(f"   ❌ Page {page_num}: Error - {e}")
        
        # Small delay between generations
        await asyncio.sleep(2)
    
    logger.info(f"\n   ✅ {title}: {updated} images generated")
    return updated


async def main(dry_run: bool = True):
    """Main function"""
    
    if not EMERGENT_LLM_KEY:
        logger.error("EMERGENT_LLM_KEY not set!")
        return
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    mode = "DRY RUN" if dry_run else "GENERATING IMAGES"
    logger.info(f"\n{'#'*60}")
    logger.info(f" {mode} - Using OpenAI GPT-Image-1")
    logger.info(f" Books: Captain Compass, Pixie Dust Adventures")
    logger.info(f"{'#'*60}")
    
    total_updated = 0
    
    for book_id, book_data in BOOKS_DATA.items():
        updated = await generate_images_for_book(db, book_id, book_data, dry_run)
        total_updated += updated
    
    logger.info(f"\n{'#'*60}")
    logger.info(f" {mode} COMPLETE")
    logger.info(f" Images processed: {total_updated}")
    logger.info(f"{'#'*60}\n")
    
    client.close()


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    asyncio.run(main(dry_run))
