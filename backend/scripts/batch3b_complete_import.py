#!/usr/bin/env python3
"""
Batch 3B Complete Import Script
- Syncs existing embedded pages to pages collection with new text
- Creates new pages for books without embedded pages
- Generates images for books that need them using fal.ai
"""

import asyncio
import os
import sys
import uuid
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import fal service for image generation
sys.path.insert(0, '/app/backend')
from fal_service import generate_image_flux

# Book data extracted from the document (text content)
# Due to size, this will be populated from the import JSON file


async def sync_embedded_to_pages(db, book_id: str, new_text_map: dict) -> int:
    """
    Sync embedded pages to pages collection, updating text content.
    new_text_map: {page_number: new_text_content}
    Returns number of pages synced.
    """
    book = await db.books.find_one({"id": book_id})
    if not book:
        return 0
    
    embedded_pages = book.get("pages", [])
    if not embedded_pages:
        return 0
    
    synced = 0
    for page in embedded_pages:
        page_num = page.get("page_number", 0)
        page_id = page.get("id") or str(uuid.uuid4())
        
        # Get new text or keep existing
        new_text = new_text_map.get(page_num, page.get("text_content", ""))
        
        # Check if page exists in pages collection
        existing = await db.pages.find_one({"id": page_id})
        
        if existing:
            # Update existing
            await db.pages.update_one(
                {"id": page_id},
                {"$set": {"text_content": new_text, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        else:
            # Create new
            new_page = {
                "id": page_id,
                "book_id": book_id,
                "page_number": page_num,
                "text_content": new_text,
                "image_url": page.get("image_url"),
                "audio_url": page.get("audio_url"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.pages.insert_one(new_page)
        
        synced += 1
    
    # Also update the embedded pages with new text
    for i, page in enumerate(embedded_pages):
        page_num = page.get("page_number", i + 1)
        if page_num in new_text_map:
            embedded_pages[i]["text_content"] = new_text_map[page_num]
    
    await db.books.update_one(
        {"id": book_id},
        {"$set": {"pages": embedded_pages}}
    )
    
    return synced


async def create_pages_with_images(db, book_id: str, pages_data: list, art_style: str = "illustrated") -> int:
    """
    Create new pages for a book that has no embedded pages.
    Also generates images using fal.ai.
    pages_data: list of {"page_number": int, "text": str}
    Returns number of pages created.
    """
    book = await db.books.find_one({"id": book_id})
    if not book:
        return 0
    
    title = book.get("title", "Unknown")
    genre = book.get("genre", "General")
    
    created = 0
    embedded_pages = []
    
    for page_data in pages_data:
        page_num = page_data["page_number"]
        text = page_data["text"]
        page_id = str(uuid.uuid4())
        
        # Generate image using fal.ai
        image_url = None
        try:
            # Create a prompt based on the text content
            prompt = f"{art_style} children's book illustration for '{title}', {genre} style. Scene: {text[:200]}... High quality, vibrant colors, child-friendly."
            
            logger.info(f"  Generating image for page {page_num}...")
            result = await generate_image_flux(
                prompt=prompt,
                model="flux-dev",
                image_size="landscape_16_9",
                num_images=1,
                guidance_scale=3.5,
                num_inference_steps=28
            )
            
            if result.get("success") and result.get("images"):
                image_url = result["images"][0].get("url")
                logger.info(f"  ✅ Page {page_num} image generated")
            else:
                logger.warning(f"  ⚠️ Page {page_num} image generation failed")
        except Exception as e:
            logger.error(f"  ❌ Page {page_num} image error: {e}")
        
        # Create page in pages collection
        new_page = {
            "id": page_id,
            "book_id": book_id,
            "page_number": page_num,
            "text_content": text,
            "image_url": image_url,
            "audio_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.pages.insert_one(new_page)
        
        # Add to embedded pages
        embedded_pages.append({
            "id": page_id,
            "page_number": page_num,
            "text_content": text,
            "image_url": image_url,
            "audio_url": None
        })
        
        created += 1
    
    # Update book with embedded pages
    await db.books.update_one(
        {"id": book_id},
        {"$set": {"pages": embedded_pages}}
    )
    
    return created


async def main(dry_run: bool = True):
    """Main import function"""
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    mode = "DRY RUN" if dry_run else "APPLYING"
    print(f"\n{'='*60}")
    print(f" {mode} - Batch 3B Complete Import")
    print(f"{'='*60}")
    
    # Books with embedded pages (need sync + text update)
    books_with_pages = [
        'ab0fe05e-1e98-4106-9334-66577fead8c3',  # Aliens at My School
        '32c78d01-b21c-4496-9bf5-476bfb92818b',  # Astronaut Alex's Moon Mission
        '1feebc6d-6bb7-4e35-9602-8fccdc5a918b',  # Bedtime in the Animal World
        'f0a6f967-0b03-4a5e-b9a5-fa7141dc8a25',  # Desert Treasure Hunt
        'c83e67ba-2fa4-421a-85a4-1f9e1f7384de',  # Elves and the Magic Tree
        '3a413305-8f24-41b0-adec-02164007e1d9',  # Fairies of Moonlight Meadow
        '92a762e4-3719-4c1d-bfbb-76aa21eceb92',  # Guardians of Tomorrow
        '5826db64-5029-4729-9eed-8da4fae959d3',  # Kindness Kingdom
        '57ddb1d3-1d67-496a-a50b-b6b3cc95dc26',  # Mystery at the Zoo
        '995e0963-3ebe-472b-9db6-8a8f43794f4d',  # Princess Penny's Pet Dragon
        'f7d9d8d6-20aa-495d-be23-382ac11a0927',  # Puzzle Palace Adventures
        'e619937d-d90e-4c64-9cb4-795a00c4696b',  # River Rafting Raccoons
        '185b7566-d59e-42fa-90ab-55a8ea5f169f',  # Safari Sam's Big Day
        'e448e6d7-7c88-457e-80f4-01439d2b416f',  # Shapes in the City
        '02207156-79bc-4089-9512-86ec8cd43a78',  # Seasons of the Magic Forest
    ]
    
    # Books WITHOUT embedded pages (need full creation + images)
    books_need_images = [
        'ed34dc96-9c78-4eb7-8707-90245371bea4',  # Captain Compass (realistic, Adventure)
        '56c45425-ba3b-421d-b17f-f13321c32f65',  # Pixie Dust Adventures (watercolour, Fantasy)
    ]
    
    if dry_run:
        print(f"\n📚 Books with existing pages (sync + text update): {len(books_with_pages)}")
        for bid in books_with_pages:
            book = await db.books.find_one({"id": bid})
            if book:
                print(f"   ✅ {book.get('title')}: will sync {len(book.get('pages', []))} pages")
        
        print(f"\n🎨 Books needing full creation + images: {len(books_need_images)}")
        for bid in books_need_images:
            book = await db.books.find_one({"id": bid})
            if book:
                print(f"   🆕 {book.get('title')}: will create 10 pages + generate images")
                print(f"       Art style: {book.get('art_style', 'illustrated')}, Genre: {book.get('genre', 'General')}")
        
        print(f"\n{'='*60}")
        print(f" DRY RUN Summary:")
        print(f"   Pages to sync: {len(books_with_pages) * 10}")
        print(f"   Pages to create: {len(books_need_images) * 10}")
        print(f"   Images to generate: {len(books_need_images) * 10}")
        print(f"{'='*60}")
    else:
        print("APPLYING changes... (not implemented in this test)")
    
    client.close()


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    asyncio.run(main(dry_run))
