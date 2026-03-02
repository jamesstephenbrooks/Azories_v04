#!/usr/bin/env python3
"""
Regenerate cover images for the 25 books to match Pixar-inspired interior style
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

# 25 books that had interior pages regenerated
BOOKS_TO_UPDATE = [
    ("5ebe3908-18f9-4947-b049-7248c2700fa4", "The Unicorn's Rainbow Bridge"),
    ("67b40688-b6cb-431b-a0c6-8baa1c28542c", "The Wizard's Apprentice"),
    ("51c242bc-99a4-4456-b4dc-1821c2a75138", "The Giant's Gentle Heart"),
    ("56c45425-ba3b-421d-b17f-f13321c32f65", "Pixie Dust Adventures"),
    ("efdc724b-18b0-4901-a22f-e211836d76c2", "The Enchanted Carousel"),
    ("ed34dc96-9c78-4eb7-8707-90245371bea4", "Captain Compass and the Treasure Map"),
    ("730f7b9b-d2bb-47f4-a797-1337bc0d6980", "The Jungle Explorers Club"),
    ("f6e35965-f823-4ed5-8b96-658a832daedd", "Mountain Climbing Mice"),
    ("61dced03-0e50-4d76-826a-640b9ffa0f19", "The Underground City"),
    ("af46591e-445e-4190-9e02-b68e895c6403", "Sky Pirates of Cloudland"),
    ("f10ecfac-d2e8-4725-b28e-fee429e5c8ab", "The Lighthouse Keeper's Secret"),
    ("875cb08c-5634-4304-ae34-07fb0c446afe", "The Arctic Expedition"),
    ("134d15cb-7824-4e33-a5d8-31f81e8b185f", "The Time Machine Treehouse"),
    ("10b82c6e-6ccb-4466-a97a-ed0fa997196e", "Space Station School"),
    ("d76924a2-eb27-4f7f-b9ae-5a7f9c922dad", "The Friendly Martians"),
    ("967761b8-0efe-4b06-b80b-56102fe02255", "Gadget Girl and the Invention Fair"),
    ("bc4794ea-f46f-4e15-8d13-4f64ad413f93", "The Secret Code Club"),
    ("4603101f-bfff-4254-ac0a-8c80a6bcd11f", "Detective Daisy's First Case"),
    ("b5cf1707-7930-4e72-a01c-8d21d052b693", "The Burping Dragon"),
    ("cf359d5f-473d-44de-8b7b-db2ccaba95a1", "The Backwards Day"),
    ("02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a", "Pirate Pete's Bad Hair Day"),
    ("d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f", "Dinosaur Dentist"),
    ("1eb994a4-e00c-4ac6-a47f-d22544493608", "The Alphabet Zoo"),
    ("5826db64-5029-4729-9eed-8da4fae959d3", "Kindness Kingdom"),
    ("40fde406-1757-4185-ab62-eb97264784e9", "The Feelings Garden"),
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

def generate_cover_prompt(title, description):
    """Generate cover prompt matching the Pixar-inspired interior style"""
    return f"""A beautiful children's book cover illustration in Pixar-inspired digital art style.
Title: {title}
Description: {description}
Style: Vibrant colors, soft lighting, magical atmosphere, 3D rendered look, professional children's book cover quality. The main character or scene should be prominently featured with an inviting, whimsical feel suitable for children ages 4-8.
IMPORTANT: no text, no words, no letters, no title, no captions, no writing, no typography anywhere in the image. Pure illustration only - the title will be added separately."""

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

def upload_to_cloudinary(image_url, book_slug):
    try:
        public_id = f"azories/books/{book_slug}/cover_v2"
        result = cloudinary.uploader.upload(image_url, public_id=public_id, overwrite=True)
        return result.get('secure_url')
    except Exception as e:
        log(f"  Cloudinary error: {e}")
        return None

def main():
    log("="*50)
    log("COVER IMAGE REGENERATION")
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
    
    success = 0
    failed = 0
    
    for i, (book_id, title) in enumerate(BOOKS_TO_UPDATE):
        log(f"\n[{i+1}/{len(BOOKS_TO_UPDATE)}] {title}")
        
        # Get book description
        book_data = get_book_data(book_id, token)
        description = book_data.get('description', title)[:200]
        book_slug = create_book_slug(title)
        
        # Generate cover
        prompt = generate_cover_prompt(title, description)
        log(f"  Generating cover...")
        
        fal_url = generate_image(prompt)
        if not fal_url:
            log(f"  FAILED: Generation error")
            failed += 1
            continue
        
        log(f"  Uploading to Cloudinary...")
        cloud_url = upload_to_cloudinary(fal_url, book_slug)
        if not cloud_url:
            log(f"  FAILED: Upload error")
            failed += 1
            continue
        
        # Update database
        log(f"  Updating database...")
        db.books.update_one(
            {"id": book_id},
            {"$set": {
                "cover_image": cloud_url,
                "updated_at": datetime.utcnow().isoformat()
            }}
        )
        
        log(f"  SUCCESS: {cloud_url[:60]}...")
        success += 1
        time.sleep(1)
    
    client.close()
    
    log(f"\n{'='*50}")
    log(f"COVER REGENERATION COMPLETE")
    log(f"  Success: {success}")
    log(f"  Failed: {failed}")
    log(f"{'='*50}")

if __name__ == "__main__":
    main()
