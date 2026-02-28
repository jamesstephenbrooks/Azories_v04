#!/usr/bin/env python3
"""
Batch Cover Regeneration - All 25 Books
Generates Pixar-style cover images using fal.ai and uploads to Cloudinary.
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
import re

from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
os.environ['FAL_KEY'] = os.environ.get('FAL_KEY')

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# 25 books - The Wizard's Apprentice already done as test
BOOKS = [
    ("5ebe3908-18f9-4947-b049-7248c2700fa4", "The Unicorn's Rainbow Bridge", "A magical unicorn crossing a rainbow bridge between mountains, with colorful sparkles trailing behind. Enchanted forest setting with floating crystals."),
    ("67b40688-b6cb-431b-a0c6-8baa1c28542c", "The Wizard's Apprentice", "SKIP - Already done"),
    ("51c242bc-99a4-4456-b4dc-1821c2a75138", "The Giant's Gentle Heart", "A friendly giant with kind eyes sitting in a meadow, gently holding tiny woodland creatures in his huge palm. Flowers and butterflies around him."),
    ("56c45425-ba3b-421d-b17f-f13321c32f65", "Pixie Dust Adventures", "Tiny glowing pixies with translucent wings flying through an enchanted forest, leaving trails of sparkling golden dust. Mushroom houses below."),
    ("efdc724b-18b0-4901-a22f-e211836d76c2", "The Enchanted Carousel", "A magical glowing carousel with fantastical creatures instead of horses - dragons, unicorns, and phoenixes. Starry night sky with aurora lights."),
    ("ed34dc96-9c78-4eb7-8707-90245371bea4", "Captain Compass and the Treasure Map", "A young pirate captain with a compass and treasure map, standing on a ship's deck with a parrot on shoulder. Tropical island visible in distance."),
    ("730f7b9b-d2bb-47f4-a797-1337bc0d6980", "The Jungle Explorers Club", "A group of diverse young explorers with binoculars and backpacks in a lush jungle, surrounded by friendly exotic animals peeking from foliage."),
    ("f6e35965-f823-4ed5-8b96-658a832daedd", "Mountain Climbing Mice", "Adorable mice in tiny climbing gear scaling a mountain peak, with ropes and pickaxes. Dramatic mountain vista with clouds below."),
    ("61dced03-0e50-4d76-826a-640b9ffa0f19", "The Underground City", "A vast glowing underground city carved into crystal caves, with tiny houses, bridges, and friendly mole and rabbit citizens."),
    ("af46591e-445e-4190-9e02-b68e895c6403", "Sky Pirates of Cloudland", "Flying ships sailing through clouds, with young sky pirates on deck. Floating islands and castles visible in a sunset sky."),
    ("f10ecfac-d2e8-4725-b28e-fee429e5c8ab", "The Lighthouse Keeper's Secret", "A cozy lighthouse on rocky cliffs at sunset, with a mysterious golden glow from the top. A child looking up at it with wonder."),
    ("875cb08c-5634-4304-ae34-07fb0c446afe", "The Arctic Expedition", "Young explorers in warm winter gear with huskies, standing before magnificent ice formations and northern lights in the sky."),
    ("134d15cb-7824-4e33-a5d8-31f81e8b185f", "The Time Machine Treehouse", "A fantastic treehouse with glowing portals and clockwork gears, showing glimpses of different time periods. A child at the entrance."),
    ("10b82c6e-6ccb-4466-a97a-ed0fa997196e", "Space Station School", "A futuristic space station classroom with diverse young astronauts floating, Earth visible through large windows. Friendly robots teaching."),
    ("d76924a2-eb27-4f7f-b9ae-5a7f9c922dad", "The Friendly Martians", "Cute green Martians with big eyes welcoming a young astronaut on Mars surface. Red landscape with domed habitats and two moons."),
    ("967761b8-0efe-4b06-b80b-56102fe02255", "Gadget Girl and the Invention Fair", "A clever young girl inventor with goggles surrounded by whimsical inventions - flying machines, robots, and glowing gadgets."),
    ("bc4794ea-f46f-4e15-8d13-4f64ad413f93", "The Secret Code Club", "Children huddled together with magnifying glasses and notebooks, deciphering mysterious symbols on an old map in a cozy clubhouse."),
    ("4603101f-bfff-4254-ac0a-8c80a6bcd11f", "Detective Daisy's First Case", "A young girl detective with a magnifying glass and notepad, examining clues with her loyal dog sidekick. Mystery mansion behind."),
    ("b5cf1707-7930-4e72-a01c-8d21d052b693", "The Burping Dragon", "A small embarrassed dragon with puffed cheeks accidentally burping colorful flames, surrounded by laughing friendly woodland creatures."),
    ("cf359d5f-473d-44de-8b7b-db2ccaba95a1", "The Backwards Day", "A topsy-turvy scene with everything hilariously reversed - birds walking, fish flying, sun wearing pajamas. A confused but amused child."),
    ("02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a", "Pirate Pete's Bad Hair Day", "A young pirate looking dismayed in a mirror at his wild, tangled hair sticking out everywhere. His parrot trying to help with a comb."),
    ("d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f", "Dinosaur Dentist", "A friendly dinosaur patient in a giant dental chair with a tiny brave dentist on a ladder. Comically oversized toothbrush nearby."),
    ("1eb994a4-e00c-4ac6-a47f-d22544493608", "The Alphabet Zoo", "A whimsical zoo where each animal represents a letter - an Alligator, Bear, Cat arranged playfully. Colorful and educational."),
    ("5826db64-5029-4729-9eed-8da4fae959d3", "Kindness Kingdom", "A magical kingdom where acts of kindness create glowing hearts that float up. Diverse children helping each other, castle in background."),
    ("40fde406-1757-4185-ab62-eb97264784e9", "The Feelings Garden", "A magical garden where emotions grow as flowers - happy sunflowers, calm blue roses, excited orange blooms. A child tending to them."),
]

LOG_FILE = '/tmp/cover_regen.log'
PROGRESS_FILE = '/tmp/cover_regen_progress.json'

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    sys.stdout.flush()
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def slugify(title):
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '_', slug)
    return slug.strip('_')

def save_progress(progress):
    progress['last_update'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def generate_cover(title, scene_description):
    prompt = f"""Pixar-style 3D animated book cover illustration for a children's book called "{title}".

Scene: {scene_description}

Style: Pixar/Disney 3D animation style, vibrant colors, warm magical lighting, cinematic composition, highly detailed, whimsical and enchanting atmosphere, suitable for children ages 5-10.

CRITICAL: Absolutely NO text, NO title, NO words, NO letters, NO writing of any kind in the image. Pure illustration only."""

    result = fal_client.subscribe(
        "fal-ai/flux-pro/v1.1",
        arguments={
            "prompt": prompt,
            "image_size": {"width": 768, "height": 1024},
            "num_images": 1,
            "enable_safety_checker": True,
            "safety_tolerance": "2"
        }
    )
    
    if result and 'images' in result and len(result['images']) > 0:
        return result['images'][0]['url']
    return None

def upload_to_cloudinary(image_url, public_id):
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code != 200:
            return None
        
        result = cloudinary.uploader.upload(
            BytesIO(response.content),
            public_id=public_id,
            overwrite=False,
            resource_type="image"
        )
        return result['secure_url']
    except Exception as e:
        log(f"  Cloudinary error: {e}")
        return None

def update_database(book_id, new_cover_url):
    try:
        result = db.books.update_one(
            {"id": book_id},
            {"$set": {
                "cover_image": new_cover_url,
                "updated_at": datetime.utcnow().isoformat()
            }}
        )
        return result.modified_count > 0
    except Exception as e:
        log(f"  DB error: {e}")
        return False

def main():
    log("=" * 60)
    log("BATCH COVER REGENERATION - 25 BOOKS")
    log("=" * 60)
    
    progress = {
        "started_at": datetime.now().isoformat(),
        "completed": 0,
        "failed": 0,
        "total": 24,  # Excluding Wizard's Apprentice (already done)
        "done_list": [],
        "failed_list": []
    }
    save_progress(progress)
    
    for i, (book_id, title, scene) in enumerate(BOOKS):
        if scene == "SKIP - Already done":
            log(f"\n[{i+1}/25] {title} - SKIPPED (test cover already done)")
            continue
        
        log(f"\n[{i+1}/25] {title}")
        log("-" * 40)
        
        # Generate
        log("  Generating cover...")
        fal_url = generate_cover(title, scene)
        
        if not fal_url:
            log("  FAILED: Generation error")
            progress['failed'] += 1
            progress['failed_list'].append(title)
            save_progress(progress)
            time.sleep(2)
            continue
        
        log(f"  Generated: {fal_url[:50]}...")
        
        # Upload
        slug = slugify(title)
        public_id = f"azories/books/{slug}/cover_clean"
        log("  Uploading to Cloudinary...")
        
        cloudinary_url = upload_to_cloudinary(fal_url, public_id)
        
        if not cloudinary_url:
            log("  FAILED: Upload error")
            progress['failed'] += 1
            progress['failed_list'].append(title)
            save_progress(progress)
            time.sleep(2)
            continue
        
        log(f"  Uploaded: {cloudinary_url[:60]}...")
        
        # Update DB
        log("  Updating database...")
        if update_database(book_id, cloudinary_url):
            log("  SUCCESS!")
            progress['completed'] += 1
            progress['done_list'].append(title)
        else:
            log("  FAILED: DB update error")
            progress['failed'] += 1
            progress['failed_list'].append(title)
        
        save_progress(progress)
        time.sleep(1.5)
    
    # Also update Wizard's Apprentice DB with the test cover
    log("\nUpdating The Wizard's Apprentice with test cover URL...")
    wizard_url = "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772261904/azories/books/the_wizards_apprentice/cover_clean.jpg"
    if update_database("67b40688-b6cb-431b-a0c6-8baa1c28542c", wizard_url):
        log("  SUCCESS!")
        progress['completed'] += 1
    
    log("\n" + "=" * 60)
    log("BATCH COMPLETE!")
    log("=" * 60)
    log(f"Completed: {progress['completed']}/25")
    log(f"Failed: {progress['failed']}")
    
    if progress['failed_list']:
        log(f"\nFailed books: {', '.join(progress['failed_list'])}")
    
    save_progress(progress)

if __name__ == "__main__":
    main()
