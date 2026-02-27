#!/usr/bin/env python3
"""
Generate images for books using fal.ai flux model
"""

import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import fal_client

load_dotenv('/app/backend/.env')

# Books needing images
BOOKS_NEEDING_IMAGES = [
    {"id": "5ebe3908-18f9-4947-b049-7248c2700fa4", "title": "The Unicorn's Rainbow Bridge", "genre": "Fantasy"},
    {"id": "67b40688-b6cb-431b-a0c6-8baa1c28542c", "title": "The Wizard's Apprentice", "genre": "Fantasy"},
    {"id": "51c242bc-99a4-4456-b4dc-1821c2a75138", "title": "The Giant's Gentle Heart", "genre": "Fantasy"},
    {"id": "efdc724b-18b0-4901-a22f-e211836d76c2", "title": "The Enchanted Carousel", "genre": "Fantasy"},
    {"id": "730f7b9b-d2bb-47f4-a797-1337bc0d6980", "title": "The Jungle Explorers Club", "genre": "Adventure"},
    {"id": "f6e35965-f823-4ed5-8b96-658a832daedd", "title": "Mountain Climbing Mice", "genre": "Adventure"},
    {"id": "61dced03-0e50-4d76-826a-640b9ffa0f19", "title": "The Underground City", "genre": "Adventure"},
    {"id": "af46591e-445e-4190-9e02-b68e895c6403", "title": "Sky Pirates of Cloudland", "genre": "Adventure"},
    {"id": "f10ecfac-d2e8-4725-b28e-fee429e5c8ab", "title": "The Lighthouse Keeper's Secret", "genre": "Adventure"},
    {"id": "875cb08c-5634-4304-ae34-07fb0c446afe", "title": "The Arctic Expedition", "genre": "Adventure"},
    {"id": "134d15cb-7824-4e33-a5d8-31f81e8b185f", "title": "The Time Machine Treehouse", "genre": "Science Fiction"},
    {"id": "10b82c6e-6ccb-4466-a97a-ed0fa997196e", "title": "Space Station School", "genre": "Science Fiction"},
    {"id": "d76924a2-eb27-4f7f-b9ae-5a7f9c922dad", "title": "The Friendly Martians", "genre": "Science Fiction"},
    {"id": "967761b8-0efe-4b06-b80b-56102fe02255", "title": "Gadget Girl and the Invention Fair", "genre": "Science Fiction"},
    {"id": "bc4794ea-f46f-4e15-8d13-4f64ad413f93", "title": "The Secret Code Club", "genre": "Mystery"},
    {"id": "4603101f-bfff-4254-ac0a-8c80a6bcd11f", "title": "Detective Daisy's First Case", "genre": "Mystery"},
    {"id": "b5cf1707-7930-4e72-a01c-8d21d052b693", "title": "The Burping Dragon", "genre": "Humour"},
    {"id": "cf359d5f-473d-44de-8b7b-db2ccaba95a1", "title": "The Backwards Day", "genre": "Humour"},
    {"id": "02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a", "title": "Pirate Pete's Bad Hair Day", "genre": "Humour"},
    {"id": "d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f", "title": "Dinosaur Dentist", "genre": "Humour"},
    {"id": "1eb994a4-e00c-4ac6-a47f-d22544493608", "title": "The Alphabet Zoo", "genre": "General"},
    {"id": "5826db64-5029-4729-9eed-8da4fae959d3", "title": "Kindness Kingdom", "genre": "General"},
    {"id": "40fde406-1757-4185-ab62-eb97264784e9", "title": "The Feelings Garden", "genre": "General"},
]

def create_image_prompt(title, genre, page_text, page_num):
    """Create an image prompt based on the page content"""
    # Extract key scene elements from text (first 200 chars)
    scene = page_text[:200] if page_text else title
    
    style_map = {
        "Fantasy": "whimsical watercolor illustration, magical atmosphere, soft pastel colors",
        "Adventure": "vibrant digital illustration, dynamic composition, rich colors",
        "Science Fiction": "colorful sci-fi illustration, futuristic setting, bright and cheerful",
        "Mystery": "atmospheric illustration, intriguing mood, warm earth tones",
        "Humour": "playful cartoon style illustration, bright cheerful colors, fun expressions",
        "General": "warm friendly illustration, soft colors, inviting atmosphere"
    }
    
    style = style_map.get(genre, style_map["General"])
    
    prompt = f"Children's book illustration for '{title}', page {page_num}. Scene: {scene}. Style: {style}, child-friendly, no text, detailed background, professional quality"
    
    return prompt[:500]  # Limit prompt length

async def generate_image(prompt):
    """Generate image using fal.ai flux"""
    try:
        handler = await fal_client.submit_async(
            "fal-ai/flux/schnell",  # Using schnell for faster/cheaper generation
            arguments={
                "prompt": prompt,
                "image_size": "landscape_4_3",
                "num_images": 1
            }
        )
        result = await handler.get()
        
        if result and result.get('images') and len(result['images']) > 0:
            return result['images'][0].get('url')
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None

async def process_book(db, book_info, book_index, total_books):
    """Generate images for all pages of a book"""
    book_id = book_info['id']
    title = book_info['title']
    genre = book_info['genre']
    
    print(f"\n[{book_index}/{total_books}] {title}")
    
    # Get book pages
    book = await db.books.find_one({'id': book_id})
    if not book:
        print(f"  Book not found!")
        return 0
    
    pages = book.get('pages', [])
    if not pages:
        print(f"  No pages!")
        return 0
    
    images_generated = 0
    
    for page in pages:
        page_num = page.get('page_number', 0)
        page_id = page.get('id')
        
        # Skip if already has image
        if page.get('image_url') and len(page.get('image_url', '')) > 10:
            continue
        
        text = page.get('text_content', '')
        prompt = create_image_prompt(title, genre, text, page_num)
        
        print(f"  Page {page_num}...", end=" ", flush=True)
        
        image_url = await generate_image(prompt)
        
        if image_url:
            # Update pages collection
            await db.pages.update_one(
                {'id': page_id, 'book_id': book_id},
                {'$set': {'image_url': image_url, 'updated_at': datetime.now(timezone.utc).isoformat()}}
            )
            
            # Update embedded page in book
            await db.books.update_one(
                {'id': book_id, 'pages.id': page_id},
                {'$set': {'pages.$.image_url': image_url}}
            )
            
            print(f"✅")
            images_generated += 1
        else:
            print(f"❌")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)
    
    print(f"  Generated {images_generated}/{len(pages)} images")
    return images_generated

async def main():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    print("=" * 60)
    print(" Generating Images with fal.ai")
    print("=" * 60)
    
    total_images = 0
    
    for i, book in enumerate(BOOKS_NEEDING_IMAGES, 1):
        try:
            images = await process_book(db, book, i, len(BOOKS_NEEDING_IMAGES))
            total_images += images
        except Exception as e:
            print(f"  Error processing book: {e}")
    
    print("\n" + "=" * 60)
    print(f" Complete! Generated {total_images} images")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
