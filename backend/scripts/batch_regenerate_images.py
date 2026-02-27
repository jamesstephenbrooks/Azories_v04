#!/usr/bin/env python3
"""
Batch Image Regeneration Script for Azories Books
Regenerates all page images for books with text-baked issues.
- Generates portrait images (768x1024) using fal.ai
- Uploads to Cloudinary for permanent storage
- Updates database with new URLs
"""

import os
import sys
import json
import time
import asyncio
import requests
from datetime import datetime
import fal_client
import cloudinary
import cloudinary.uploader

# Configuration
API_URL = "https://image-integrity-1.preview.emergentagent.com"
FAL_KEY = "ab490710-1d52-45a3-9d2e-3fc9c1a2a995:671ae92454b3d014b5ceced926943e9b"

# Set environment variables
os.environ['FAL_KEY'] = FAL_KEY

# Cloudinary config (from .env)
cloudinary.config(
    cloud_name="dlbmjqmoy",
    api_key="623841689882156",
    api_secret="FUp37HECcXY77gAuaVJ1q8HL5CQ"
)

# Book IDs to regenerate (25 OLD batch books)
OLD_BATCH_BOOK_IDS = [
    "5ebe3908-18f9-4947-b049-7248c2700fa4",  # The Unicorn's Rainbow Bridge
    "67b40688-b6cb-431b-a0c6-8baa1c28542c",  # The Wizard's Apprentice
    "51c242bc-99a4-4456-b4dc-1821c2a75138",  # The Giant's Gentle Heart
    "56c45425-ba3b-421d-b17f-f13321c32f65",  # Pixie Dust Adventures
    "efdc724b-18b0-4901-a22f-e211836d76c2",  # The Enchanted Carousel
    "ed34dc96-9c78-4eb7-8707-90245371bea4",  # Captain Compass and the Treasure Map
    "730f7b9b-d2bb-47f4-a797-1337bc0d6980",  # The Jungle Explorers Club
    "f6e35965-f823-4ed5-8b96-658a832daedd",  # Mountain Climbing Mice
    "61dced03-0e50-4d76-826a-640b9ffa0f19",  # The Underground City
    "af46591e-445e-4190-9e02-b68e895c6403",  # Sky Pirates of Cloudland
    "f10ecfac-d2e8-4725-b28e-fee429e5c8ab",  # The Lighthouse Keeper's Secret
    "875cb08c-5634-4304-ae34-07fb0c446afe",  # The Arctic Expedition
    "134d15cb-7824-4e33-a5d8-31f81e8b185f",  # The Time Machine Treehouse
    "10b82c6e-6ccb-4466-a97a-ed0fa997196e",  # Space Station School
    "d76924a2-eb27-4f7f-b9ae-5a7f9c922dad",  # The Friendly Martians
    "967761b8-0efe-4b06-b80b-56102fe02255",  # Gadget Girl and the Invention Fair
    "bc4794ea-f46f-4e15-8d13-4f64ad413f93",  # The Secret Code Club
    "4603101f-bfff-4254-ac0a-8c80a6bcd11f",  # Detective Daisy's First Case
    "b5cf1707-7930-4e72-a01c-8d21d052b693",  # The Burping Dragon
    "cf359d5f-473d-44de-8b7b-db2ccaba95a1",  # The Backwards Day
    "02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a",  # Pirate Pete's Bad Hair Day
    "d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f",  # Dinosaur Dentist
    "1eb994a4-e00c-4ac6-a47f-d22544493608",  # The Alphabet Zoo
    "5826db64-5029-4729-9eed-8da4fae959d3",  # Kindness Kingdom
    "40fde406-1757-4185-ab62-eb97264784e9",  # The Feelings Garden
]

# Progress tracking
progress = {
    "total_books": len(OLD_BATCH_BOOK_IDS),
    "completed_books": 0,
    "total_images": 0,
    "generated_images": 0,
    "uploaded_images": 0,
    "failed_images": [],
    "start_time": None,
    "current_book": None
}

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def save_progress():
    """Save progress to file"""
    with open('/tmp/regeneration_progress.json', 'w') as f:
        json.dump(progress, f, indent=2, default=str)

def get_auth_token():
    """Get authentication token"""
    resp = requests.post(f"{API_URL}/api/auth/login", json={
        "email": "jamesstephenbrooks@outlook.com",
        "password": "test123"
    })
    return resp.json().get('access_token')

def get_book_data(book_id, token):
    """Get full book data including pages"""
    resp = requests.get(
        f"{API_URL}/api/books/{book_id}/full",
        headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()

def generate_image_prompt(book_title, book_description, page_text, page_number):
    """Generate a prompt for the image based on page content"""
    # Create scene description from page text
    scene = page_text[:300] if page_text else f"A scene from {book_title}"
    
    prompt = f"""A warm, whimsical children's book illustration in a charming storybook style.
Book: {book_title}
Scene: {scene}
Style: Digital illustration, Pixar-inspired, soft lighting, magical atmosphere, vibrant colors, suitable for children ages 4-8. Professional children's book quality illustration.
IMPORTANT: no text, no words, no letters, no captions, no writing, no typography anywhere in the image. Pure illustration only."""
    
    return prompt

def generate_image(prompt, retries=3):
    """Generate image using fal.ai with retries"""
    for attempt in range(retries):
        try:
            result = fal_client.subscribe(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": {
                        "width": 768,
                        "height": 1024
                    },
                    "num_images": 1,
                    "enable_safety_checker": True
                }
            )
            
            if result and result.get('images'):
                return result['images'][0]['url']
            else:
                log(f"  No images returned on attempt {attempt + 1}")
                
        except Exception as e:
            log(f"  Generation error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(5)  # Wait before retry
    
    return None

def upload_to_cloudinary(image_url, book_slug, page_number):
    """Upload image to Cloudinary and return permanent URL"""
    try:
        # Create public_id for organized storage
        public_id = f"azories/books/{book_slug}/page_{page_number:02d}_v2"
        
        result = cloudinary.uploader.upload(
            image_url,
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )
        
        return result.get('secure_url')
        
    except Exception as e:
        log(f"  Cloudinary upload error: {e}")
        return None

def update_page_image_url(book_id, chapter_index, page_index, new_url, token):
    """Update the page image URL in the database via API"""
    try:
        # Use the update endpoint
        resp = requests.put(
            f"{API_URL}/api/books/{book_id}/pages/{chapter_index}/{page_index}/image",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"image_url": new_url}
        )
        return resp.status_code == 200
    except Exception as e:
        log(f"  DB update error: {e}")
        return False

def create_book_slug(title):
    """Create URL-safe slug from book title"""
    slug = title.lower()
    slug = slug.replace("'s", "_s").replace("'", "_")
    slug = slug.replace(" ", "_").replace("-", "_")
    slug = ''.join(c for c in slug if c.isalnum() or c == '_')
    return slug

def process_book(book_id, token):
    """Process a single book - regenerate all page images"""
    book_data = get_book_data(book_id, token)
    book_title = book_data.get('title', 'Unknown')
    book_description = book_data.get('description', '')
    book_slug = create_book_slug(book_title)
    
    progress['current_book'] = book_title
    log(f"\n{'='*60}")
    log(f"Processing: {book_title}")
    log(f"{'='*60}")
    
    # Get pages from chapters or direct pages array
    chapters = book_data.get('chapters', [])
    direct_pages = book_data.get('pages', [])
    
    pages_to_process = []
    if chapters:
        for ci, chapter in enumerate(chapters):
            for pi, page in enumerate(chapter.get('pages', [])):
                pages_to_process.append({
                    'chapter_index': ci,
                    'page_index': pi,
                    'page': page,
                    'page_number': len(pages_to_process) + 1
                })
    elif direct_pages:
        for pi, page in enumerate(direct_pages):
            pages_to_process.append({
                'chapter_index': 0,
                'page_index': pi,
                'page': page,
                'page_number': pi + 1
            })
    
    log(f"Found {len(pages_to_process)} pages to regenerate")
    progress['total_images'] += len(pages_to_process)
    save_progress()
    
    book_success = 0
    book_failed = 0
    
    for page_info in pages_to_process:
        page = page_info['page']
        page_num = page_info['page_number']
        page_text = page.get('text_content', '')
        
        log(f"\n  Page {page_num}/{len(pages_to_process)}")
        
        # Generate prompt
        prompt = generate_image_prompt(book_title, book_description, page_text, page_num)
        
        # Generate image
        log(f"    Generating image...")
        fal_url = generate_image(prompt)
        
        if not fal_url:
            log(f"    FAILED: Could not generate image")
            progress['failed_images'].append({
                'book': book_title,
                'page': page_num,
                'error': 'Generation failed'
            })
            book_failed += 1
            save_progress()
            continue
        
        progress['generated_images'] += 1
        log(f"    Generated: {fal_url[:60]}...")
        
        # Upload to Cloudinary
        log(f"    Uploading to Cloudinary...")
        cloudinary_url = upload_to_cloudinary(fal_url, book_slug, page_num)
        
        if not cloudinary_url:
            log(f"    FAILED: Could not upload to Cloudinary")
            progress['failed_images'].append({
                'book': book_title,
                'page': page_num,
                'error': 'Cloudinary upload failed',
                'fal_url': fal_url
            })
            book_failed += 1
            save_progress()
            continue
        
        progress['uploaded_images'] += 1
        log(f"    Uploaded: {cloudinary_url[:60]}...")
        
        # Update database - we'll do this via direct MongoDB since API endpoint might not exist
        book_success += 1
        
        # Store the new URL for batch update
        page_info['new_url'] = cloudinary_url
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    # Batch update all page URLs for this book
    log(f"\n  Updating database for {book_title}...")
    update_book_images_in_db(book_id, book_slug, pages_to_process)
    
    progress['completed_books'] += 1
    log(f"\n  Book complete: {book_success} succeeded, {book_failed} failed")
    save_progress()
    
    return book_success, book_failed

def update_book_images_in_db(book_id, book_slug, pages_info):
    """Update all page images in MongoDB directly"""
    from pymongo import MongoClient
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    # Use the production DB URL from .env
    with open('/app/backend/.env') as f:
        for line in f:
            if line.startswith('MONGO_URL='):
                mongo_url = line.split('=', 1)[1].strip().strip('"')
                break
    
    client = MongoClient(mongo_url)
    db = client['azories_db']
    
    # Get the book
    book = db.books.find_one({"id": book_id})
    if not book:
        log(f"    Book not found in database: {book_id}")
        return
    
    # Update pages
    chapters = book.get('chapters', [])
    pages = book.get('pages', [])
    
    updated = False
    for page_info in pages_info:
        new_url = page_info.get('new_url')
        if not new_url:
            continue
            
        if chapters:
            ci = page_info['chapter_index']
            pi = page_info['page_index']
            if ci < len(chapters) and pi < len(chapters[ci].get('pages', [])):
                chapters[ci]['pages'][pi]['image_url'] = new_url
                updated = True
        elif pages:
            pi = page_info['page_index']
            if pi < len(pages):
                pages[pi]['image_url'] = new_url
                updated = True
    
    if updated:
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if chapters:
            update_data['chapters'] = chapters
        if pages:
            update_data['pages'] = pages
            
        db.books.update_one(
            {"id": book_id},
            {"$set": update_data}
        )
        log(f"    Database updated successfully")
    
    client.close()

def main():
    """Main entry point"""
    log("="*60)
    log("BATCH IMAGE REGENERATION STARTED")
    log("="*60)
    
    progress['start_time'] = datetime.now().isoformat()
    save_progress()
    
    # Get auth token
    log("Getting authentication token...")
    token = get_auth_token()
    if not token:
        log("ERROR: Could not get auth token")
        return
    
    log(f"Processing {len(OLD_BATCH_BOOK_IDS)} books...")
    
    total_success = 0
    total_failed = 0
    
    for i, book_id in enumerate(OLD_BATCH_BOOK_IDS):
        log(f"\n[Book {i+1}/{len(OLD_BATCH_BOOK_IDS)}]")
        
        try:
            success, failed = process_book(book_id, token)
            total_success += success
            total_failed += failed
        except Exception as e:
            log(f"ERROR processing book {book_id}: {e}")
            import traceback
            traceback.print_exc()
        
        # Refresh token periodically
        if (i + 1) % 5 == 0:
            log("Refreshing auth token...")
            token = get_auth_token()
    
    # Final summary
    log("\n" + "="*60)
    log("BATCH REGENERATION COMPLETE")
    log("="*60)
    log(f"Total books processed: {progress['completed_books']}/{progress['total_books']}")
    log(f"Total images generated: {progress['generated_images']}")
    log(f"Total images uploaded to Cloudinary: {progress['uploaded_images']}")
    log(f"Total failures: {len(progress['failed_images'])}")
    
    if progress['failed_images']:
        log("\nFailed images:")
        for fail in progress['failed_images']:
            log(f"  - {fail['book']} Page {fail['page']}: {fail['error']}")
    
    save_progress()
    log("\nProgress saved to /tmp/regeneration_progress.json")

if __name__ == "__main__":
    main()
