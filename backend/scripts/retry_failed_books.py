#!/usr/bin/env python3
"""
Retry failed books image regeneration - Pirate Pete and Dinosaur Dentist
"""

import os
import sys
import json
import time
from datetime import datetime
import fal_client
import cloudinary
import cloudinary.uploader
import requests
from pymongo import MongoClient

# Configuration
API_URL = "https://ai-book-updates.preview.emergentagent.com"
FAL_KEY = "ab490710-1d52-45a3-9d2e-3fc9c1a2a995:671ae92454b3d014b5ceced926943e9b"
os.environ['FAL_KEY'] = FAL_KEY

# Cloudinary config
cloudinary.config(
    cloud_name="dlbmjqmoy",
    api_key="623841689882156",
    api_secret="FUp37HECcXY77gAuaVJ1q8HL5CQ"
)

# Failed books to retry
FAILED_BOOKS = [
    ("02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a", "Pirate Pete's Bad Hair Day"),
    ("d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f", "Dinosaur Dentist"),
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def get_auth_token():
    resp = requests.post(f"{API_URL}/api/auth/login", json={
        "email": "jamesstephenbrooks@outlook.com",
        "password": "test123"
    })
    return resp.json().get('access_token')

def get_book_data(book_id, token):
    resp = requests.get(
        f"{API_URL}/api/books/{book_id}/full",
        headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()

def create_book_slug(title):
    slug = title.lower().replace("'s", "_s").replace("'", "_").replace(" ", "_").replace("-", "_")
    return ''.join(c for c in slug if c.isalnum() or c == '_')

def generate_image(prompt, retries=3):
    for attempt in range(retries):
        try:
            result = fal_client.subscribe(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": {"width": 768, "height": 1024},
                    "num_images": 1,
                    "enable_safety_checker": True
                }
            )
            if result and result.get('images'):
                return result['images'][0]['url']
        except Exception as e:
            log(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None

def upload_to_cloudinary(image_url, book_slug, page_num):
    try:
        public_id = f"azories/books/{book_slug}/page_{page_num:02d}_v2"
        result = cloudinary.uploader.upload(image_url, public_id=public_id, overwrite=True)
        return result.get('secure_url')
    except Exception as e:
        log(f"  Cloudinary error: {e}")
        return None

def main():
    log("="*50)
    log("RETRYING FAILED BOOKS")
    log("="*50)
    
    token = get_auth_token()
    
    # MongoDB connection
    with open('/app/backend/.env') as f:
        for line in f:
            if line.startswith('MONGO_URL='):
                mongo_url = line.split('=', 1)[1].strip().strip('"')
                break
    client = MongoClient(mongo_url)
    db = client['azories_db']
    
    total_success = 0
    total_failed = 0
    
    for book_id, book_title in FAILED_BOOKS:
        log(f"\n{'='*50}")
        log(f"Processing: {book_title}")
        log(f"{'='*50}")
        
        book_data = get_book_data(book_id, token)
        book_slug = create_book_slug(book_title)
        
        chapters = book_data.get('chapters', [])
        pages = book_data.get('pages', [])
        
        pages_list = []
        if chapters:
            for ci, ch in enumerate(chapters):
                for pi, page in enumerate(ch.get('pages', [])):
                    pages_list.append({'ci': ci, 'pi': pi, 'page': page, 'num': len(pages_list)+1})
        elif pages:
            for pi, page in enumerate(pages):
                pages_list.append({'ci': 0, 'pi': pi, 'page': page, 'num': pi+1})
        
        log(f"Found {len(pages_list)} pages")
        
        new_urls = {}
        for item in pages_list:
            page = item['page']
            page_num = item['num']
            text = page.get('text_content', '')[:300]
            
            log(f"\n  Page {page_num}/{len(pages_list)}")
            
            prompt = f"""A warm, whimsical children's book illustration in a charming storybook style.
Book: {book_title}
Scene: {text}
Style: Digital illustration, Pixar-inspired, soft lighting, magical atmosphere, vibrant colors, suitable for children ages 4-8.
IMPORTANT: no text, no words, no letters, no captions, no writing, no typography anywhere in the image. Pure illustration only."""
            
            log(f"    Generating...")
            fal_url = generate_image(prompt)
            
            if not fal_url:
                log(f"    FAILED generation")
                total_failed += 1
                continue
            
            log(f"    Uploading to Cloudinary...")
            cloud_url = upload_to_cloudinary(fal_url, book_slug, page_num)
            
            if not cloud_url:
                log(f"    FAILED upload")
                total_failed += 1
                continue
            
            log(f"    SUCCESS: {cloud_url[:60]}...")
            new_urls[(item['ci'], item['pi'])] = cloud_url
            total_success += 1
            time.sleep(1)
        
        # Update database
        log(f"\n  Updating database...")
        book = db.books.find_one({"id": book_id})
        if book:
            chapters_db = book.get('chapters', [])
            pages_db = book.get('pages', [])
            
            for (ci, pi), url in new_urls.items():
                if chapters_db and ci < len(chapters_db):
                    if pi < len(chapters_db[ci].get('pages', [])):
                        chapters_db[ci]['pages'][pi]['image_url'] = url
                elif pages_db and pi < len(pages_db):
                    pages_db[pi]['image_url'] = url
            
            update = {"updated_at": datetime.utcnow().isoformat()}
            if chapters_db:
                update['chapters'] = chapters_db
            if pages_db:
                update['pages'] = pages_db
            
            db.books.update_one({"id": book_id}, {"$set": update})
            log(f"    Database updated!")
    
    client.close()
    
    log(f"\n{'='*50}")
    log(f"RETRY COMPLETE")
    log(f"  Success: {total_success}")
    log(f"  Failed: {total_failed}")
    log(f"{'='*50}")

if __name__ == "__main__":
    main()
