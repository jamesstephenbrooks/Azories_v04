#!/usr/bin/env python3
"""
Batch Regeneration Script - All 249 Remaining Images
Generates Pixar-style portrait images using fal.ai and uploads to Cloudinary.
Uses unique filenames (_clean suffix) to avoid overwriting existing images.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from io import BytesIO
import fal_client
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient

# Load environment from .env
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
FAL_KEY = os.environ.get('FAL_KEY')
os.environ['FAL_KEY'] = FAL_KEY

# Cloudinary config
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# 25 books to regenerate (all pages except page 1 of The Wizard's Apprentice which is done)
OLD_BATCH_BOOK_IDS = [
    "5ebe3908-18f9-4947-b049-7248c2700fa4",  # The Unicorn's Rainbow Bridge
    "67b40688-b6cb-431b-a0c6-8baa1c28542c",  # The Wizard's Apprentice (skip page 1)
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

# Progress file
PROGRESS_FILE = '/tmp/batch_regen_progress.json'
LOG_FILE = '/tmp/batch_regen.log'

def log(message):
    """Log with timestamp to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    sys.stdout.flush()
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "started_at": datetime.now().isoformat(),
        "completed_images": 0,
        "failed_images": 0,
        "total_images": 249,
        "processed_pages": [],  # List of "book_id:page_num" that are done
        "failed_list": [],
        "current_book": None,
        "last_update": None
    }

def save_progress(progress):
    """Save progress to file"""
    progress['last_update'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def slugify(title):
    """Convert title to URL-friendly slug"""
    import re
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '_', slug)
    return slug.strip('_')

def generate_image_prompt(book_title, page_text, page_num):
    """Generate an appropriate prompt for the page"""
    # Create a scene description based on the text
    text_preview = page_text[:500] if page_text else ""
    
    prompt = f"""Pixar-style 3D animated illustration for a children's book titled "{book_title}".
Scene for page {page_num}: {text_preview}
Style: Pixar/Disney 3D animation style, vibrant colors, warm lighting, cinematic composition, highly detailed, whimsical and magical atmosphere, suitable for children ages 5-10.
CRITICAL: Absolutely NO text, NO words, NO letters, NO writing of any kind in the image. Pure illustration only."""
    
    return prompt

def generate_image(prompt):
    """Generate an image using fal.ai flux model"""
    try:
        result = fal_client.subscribe(
            "fal-ai/flux-pro/v1.1",
            arguments={
                "prompt": prompt,
                "image_size": {
                    "width": 768,
                    "height": 1024  # Portrait orientation
                },
                "num_images": 1,
                "enable_safety_checker": True,
                "safety_tolerance": "2"
            }
        )
        
        if result and 'images' in result and len(result['images']) > 0:
            return result['images'][0]['url']
        return None
    except Exception as e:
        log(f"    FAL ERROR: {e}")
        return None

def upload_to_cloudinary(image_url, public_id):
    """Upload image to Cloudinary"""
    try:
        # Download the image first
        response = requests.get(image_url, timeout=30)
        if response.status_code != 200:
            return None
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            BytesIO(response.content),
            public_id=public_id,
            overwrite=False,
            resource_type="image"
        )
        
        return result['secure_url']
    except Exception as e:
        log(f"    CLOUDINARY ERROR: {e}")
        return None

def update_database(book_id, page_index, new_url):
    """Update the page image URL in the database"""
    try:
        book = db.books.find_one({"id": book_id})
        if not book:
            return False
        
        pages = book.get('pages', [])
        if page_index < len(pages):
            pages[page_index]['image_url'] = new_url
            
            db.books.update_one(
                {"id": book_id},
                {"$set": {
                    "pages": pages,
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            return True
        return False
    except Exception as e:
        log(f"    DB ERROR: {e}")
        return False

def process_book(book_id, progress):
    """Process all pages of a book"""
    book = db.books.find_one({"id": book_id})
    if not book:
        log(f"  Book not found: {book_id}")
        return 0, 0
    
    title = book.get('title', 'Unknown')
    slug = slugify(title)
    pages = book.get('pages', [])
    
    progress['current_book'] = title
    save_progress(progress)
    
    log(f"\n{'='*60}")
    log(f"Processing: {title}")
    log(f"Pages: {len(pages)}")
    log(f"{'='*60}")
    
    success_count = 0
    fail_count = 0
    
    for i, page in enumerate(pages):
        page_num = i + 1
        page_key = f"{book_id}:{page_num}"
        
        # Skip if already processed
        if page_key in progress['processed_pages']:
            log(f"  Page {page_num}: Already done, skipping")
            continue
        
        # Skip The Wizard's Apprentice page 1 (already done as test)
        if book_id == "67b40688-b6cb-431b-a0c6-8baa1c28542c" and page_num == 1:
            log(f"  Page {page_num}: Test image already done, skipping")
            progress['processed_pages'].append(page_key)
            save_progress(progress)
            continue
        
        log(f"  Page {page_num}/{len(pages)}:")
        
        # Get page text for prompt
        page_text = page.get('text_content', page.get('text', ''))
        
        # Generate prompt
        prompt = generate_image_prompt(title, page_text, page_num)
        
        # Generate image
        log(f"    Generating image...")
        fal_url = generate_image(prompt)
        
        if not fal_url:
            log(f"    FAILED: Image generation failed")
            progress['failed_images'] += 1
            progress['failed_list'].append({
                'book': title,
                'page': page_num,
                'error': 'Generation failed'
            })
            fail_count += 1
            save_progress(progress)
            time.sleep(2)  # Wait before retry
            continue
        
        log(f"    Generated: {fal_url[:50]}...")
        
        # Upload to Cloudinary with _clean suffix
        public_id = f"azories/books/{slug}/page_{page_num:02d}_clean"
        log(f"    Uploading to Cloudinary...")
        cloudinary_url = upload_to_cloudinary(fal_url, public_id)
        
        if not cloudinary_url:
            log(f"    FAILED: Cloudinary upload failed")
            progress['failed_images'] += 1
            progress['failed_list'].append({
                'book': title,
                'page': page_num,
                'error': 'Upload failed',
                'fal_url': fal_url
            })
            fail_count += 1
            save_progress(progress)
            time.sleep(2)
            continue
        
        log(f"    Uploaded: {cloudinary_url[:60]}...")
        
        # Update database
        log(f"    Updating database...")
        if update_database(book_id, i, cloudinary_url):
            log(f"    SUCCESS!")
            progress['completed_images'] += 1
            progress['processed_pages'].append(page_key)
            success_count += 1
        else:
            log(f"    FAILED: Database update failed")
            progress['failed_images'] += 1
            progress['failed_list'].append({
                'book': title,
                'page': page_num,
                'error': 'DB update failed',
                'new_url': cloudinary_url
            })
            fail_count += 1
        
        save_progress(progress)
        
        # Rate limiting - wait between images
        time.sleep(1.5)
    
    return success_count, fail_count

def main():
    """Main entry point"""
    log("\n" + "="*60)
    log("BATCH IMAGE REGENERATION - ALL 249 IMAGES")
    log("="*60)
    log(f"Started at: {datetime.now().isoformat()}")
    log(f"Books to process: {len(OLD_BATCH_BOOK_IDS)}")
    
    # Load or initialize progress
    progress = load_progress()
    
    # Count total images to process
    total_to_process = 0
    for book_id in OLD_BATCH_BOOK_IDS:
        book = db.books.find_one({"id": book_id})
        if book:
            pages = book.get('pages', [])
            for i, _ in enumerate(pages):
                page_key = f"{book_id}:{i+1}"
                if page_key not in progress['processed_pages']:
                    # Skip wizard page 1
                    if not (book_id == "67b40688-b6cb-431b-a0c6-8baa1c28542c" and i == 0):
                        total_to_process += 1
    
    log(f"Images remaining to process: {total_to_process}")
    log(f"Already completed: {progress['completed_images']}")
    
    if total_to_process == 0:
        log("All images already processed!")
        return
    
    progress['total_images'] = total_to_process + progress['completed_images']
    save_progress(progress)
    
    total_success = 0
    total_fail = 0
    
    for i, book_id in enumerate(OLD_BATCH_BOOK_IDS):
        log(f"\n[Book {i+1}/{len(OLD_BATCH_BOOK_IDS)}]")
        
        try:
            success, fail = process_book(book_id, progress)
            total_success += success
            total_fail += fail
        except Exception as e:
            log(f"ERROR processing book {book_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    log("\n" + "="*60)
    log("BATCH REGENERATION COMPLETE!")
    log("="*60)
    log(f"Finished at: {datetime.now().isoformat()}")
    log(f"Total successful: {progress['completed_images']}")
    log(f"Total failed: {progress['failed_images']}")
    
    if progress['failed_list']:
        log(f"\nFailed images ({len(progress['failed_list'])}):")
        for fail in progress['failed_list'][:20]:  # Show first 20
            log(f"  - {fail['book']} Page {fail['page']}: {fail['error']}")
    
    save_progress(progress)
    log(f"\nProgress saved to: {PROGRESS_FILE}")
    log(f"Full log saved to: {LOG_FILE}")

if __name__ == "__main__":
    main()
