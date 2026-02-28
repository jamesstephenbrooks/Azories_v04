"""
Regenerate ALL interior pages for 3 books in Pixar style
With consistent character design throughout each book
"""
import asyncio
import os
import sys
from pathlib import Path

# Load environment
env_path = Path('/app/backend/.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

sys.path.insert(0, '/app/backend')
from fal_service import generate_image_flux
from pymongo import MongoClient

import cloudinary
import cloudinary.uploader
import aiohttp
from datetime import datetime

# Setup
client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client[os.environ.get('DB_NAME', 'test_database')]

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Character descriptions for consistency
BOOK_CHARACTERS = {
    "Cooking Adventures with Chef Cat": {
        "style": "Pixar 3D animated style, children's book illustration",
        "main_char": "Chef Clementine, a charming orange tabby cat with bright green eyes, wearing a tall white chef's hat and red apron with a heart on the pocket",
        "supporting": "group of adorable kittens: Little Mittens (small white kitten with gray patches), Whiskers (fluffy gray kitten with long whiskers), and other colorful kittens",
        "setting": "warm cozy kitchen with wooden counters, copper pots, colorful ingredients"
    },
    "Friendship Island": {
        "style": "Pixar 3D animated style, children's book illustration",
        "main_char": "five diverse children ages 8-10: Maya (Asian girl with black pigtails, pink shirt), Leo (Black boy with curly hair, blue shorts), Sofia (Hispanic girl with brown braids, yellow dress), Jake (Caucasian boy with red hair, green shirt), and Aisha (Middle Eastern girl with hijab, purple outfit)",
        "supporting": "tropical island wildlife, colorful parrots, friendly monkeys",
        "setting": "beautiful tropical island with palm trees, crystal blue water, sandy beaches, lush jungle"
    },
    "Galaxy Racers": {
        "style": "Pixar 3D animated style, children's book illustration, sci-fi adventure",
        "main_char": "diverse team of young space racers: Zara (brave pilot with purple hair and silver flight suit), Max (clever mechanic with goggles and orange jumpsuit), Kira (alien friend with blue skin and antennae), and their robot companion Bolt (small friendly robot with big eyes)",
        "supporting": "rival racers in various colorful ships",
        "setting": "vibrant outer space with colorful nebulae, planets, asteroid fields, futuristic space stations"
    }
}

# Page prompts for each book
BOOK_PAGES = {
    "Cooking Adventures with Chef Cat": [
        "Chef Clementine in her kitchen preparing for the day, warm morning light through window, pots and pans ready",
        "Chef Clementine greeting excited young kittens at the restaurant door, welcoming gesture",
        "kittens gathered around Chef Clementine at cooking table, ingredients spread out, everyone eager to learn",
        "Chef Clementine demonstrating how to crack eggs, kittens watching with wide curious eyes",
        "Little Mittens covered in flour, laughing, other kittens giggling, flour cloud in air",
        "kittens mixing cookie dough together in big bowl, teamwork, colorful aprons",
        "Chef Clementine showing proper stirring technique, gentle circular motions",
        "golden cookies coming out of oven, magical warm glow, kittens amazed",
        "kittens decorating cookies with colorful frosting, creative expressions",
        "Chef Clementine and all kittens sharing cookies together, warm family feeling",
        "cleanup time, kittens washing dishes together, bubbles floating",
        "kittens leaving restaurant waving goodbye, sunset, carrying cookie boxes",
        "Chef Clementine alone in kitchen, satisfied smile, looking at photos of cooking class",
        "nighttime exterior of cozy restaurant, warm lights glowing from windows",
        "Chef Clementine writing in recipe book by candlelight",
        "dawn, Chef Clementine opening curtains, ready for new day",
        "final page, group photo of Chef Clementine with all her kitten students"
    ],
    "Friendship Island": [
        "five diverse children arriving on island by boat, excited faces, tropical paradise ahead",
        "children exploring beach together, finding seashells, palm trees overhead",
        "children discovering mysterious cave entrance covered in vines",
        "inside cave, children finding ancient map on wall, flashlight beams",
        "children building treehouse together, teamwork, jungle setting",
        "Maya teaching others to make flower crowns, sitting in meadow",
        "Leo leading group across rope bridge over river, encouraging friends",
        "Sofia sharing food she prepared, picnic on beach at sunset",
        "Jake helping Aisha climb tall tree to see view, supportive friendship",
        "children swimming in lagoon with friendly dolphins",
        "rainstorm, children huddled in treehouse, telling stories",
        "rainbow after storm, children cheering on beach",
        "children finding treasure chest with friendship bracelets inside",
        "each child tying bracelet on another's wrist, circle of friendship",
        "bonfire on beach at night, children roasting marshmallows, stars above",
        "children saying goodbye, hugging, promising to return",
        "final page, children waving from boat, island in background, friendship forever"
    ],
    "Galaxy Racers": [
        "Zara and team at space station, preparing colorful spaceship for big race",
        "race starting line in space, dozens of ships, excitement, countdown",
        "ships blasting off, colorful engine trails, space backdrop",
        "Zara piloting through asteroid field, intense focus, rocks flying past",
        "Max fixing engine mid-race, sparks flying, determined expression",
        "Kira using alien abilities to navigate, glowing antennae",
        "rival racer trying to push them off course, tense moment",
        "team working together through nebula cloud, beautiful purple and pink gases",
        "pit stop on small moon, robot Bolt refueling ship quickly",
        "second half of race begins, ships even closer together",
        "dangerous shortcut through ring of ice crystals",
        "one team member almost gives up, others encourage them",
        "final stretch, three ships neck and neck",
        "photo finish, crowd cheering on viewing screens",
        "victory celebration, confetti in zero gravity, floating",
        "team receiving trophy together, proud moment, diverse crowd cheering",
        "final page, team flying into sunset toward new adventures, friendship bonds"
    ]
}

async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            raise Exception(f"Failed: {response.status}")

async def generate_page(book_title, page_num, page_desc):
    chars = BOOK_CHARACTERS[book_title]
    
    # Build consistent prompt
    prompt = f"""{chars['style']}, {page_desc}, featuring {chars['main_char']}, 
    {chars['setting']}, vibrant colors, no text, clean professional illustration, 
    high quality, consistent character design"""
    
    try:
        result = await generate_image_flux(
            prompt=prompt,
            model="flux-dev",
            image_size="landscape_16_9",
            num_images=1,
            guidance_scale=4.0,
            num_inference_steps=28
        )
        
        if result and 'images' in result and result['images']:
            return result['images'][0].get('url')
    except Exception as e:
        print(f"    Error: {e}")
    return None

async def process_book(book_title):
    print(f"\n{'='*60}")
    print(f"Processing: {book_title}")
    print(f"{'='*60}")
    
    pages = BOOK_PAGES[book_title]
    book = db.books.find_one({"title": book_title})
    
    if not book:
        print(f"ERROR: Book not found in database")
        return 0
    
    db_pages = book.get('pages', [])
    regenerated = 0
    
    for i, page_desc in enumerate(pages):
        if i >= len(db_pages):
            print(f"  Page {i+1}: Skipping (no DB entry)")
            continue
            
        print(f"  Page {i+1}/{len(pages)}: Generating...")
        
        image_url = await generate_page(book_title, i+1, page_desc)
        
        if image_url:
            # Download and upload to Cloudinary
            try:
                image_bytes = await download_image(image_url)
                
                safe_title = book_title.lower().replace(" ", "_").replace("'", "")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                public_id = f"azories/books/{safe_title}/page_{i+1:02d}_pixar_{timestamp}"
                
                upload_result = cloudinary.uploader.upload(
                    image_bytes,
                    public_id=public_id,
                    overwrite=True,
                    resource_type="image"
                )
                
                new_url = upload_result['secure_url']
                
                # Update database
                db_pages[i]['image_url'] = new_url
                regenerated += 1
                print(f"    ✓ Done")
                
            except Exception as e:
                print(f"    ✗ Upload failed: {e}")
        else:
            print(f"    ✗ Generation failed")
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Save all updates to database
    db.books.update_one(
        {"title": book_title},
        {"$set": {
            "pages": db_pages,
            "_interior_regenerated": datetime.now().isoformat(),
            "_interior_style": "pixar_3d"
        }}
    )
    
    return regenerated

async def main():
    print("="*70)
    print("REGENERATING ALL INTERIOR PAGES - PIXAR STYLE")
    print("="*70)
    
    books = [
        "Cooking Adventures with Chef Cat",
        "Friendship Island",
        "Galaxy Racers"
    ]
    
    results = {}
    for book in books:
        count = await process_book(book)
        results[book] = count
    
    print("\n" + "="*70)
    print("REGENERATION COMPLETE")
    print("="*70)
    
    total = 0
    for book, count in results.items():
        print(f"  {book}: {count} pages regenerated")
        total += count
    
    print(f"\nTOTAL: {total} pages regenerated across {len(books)} books")

if __name__ == "__main__":
    asyncio.run(main())
