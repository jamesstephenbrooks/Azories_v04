"""
Generate sample interior pages for 3 books in Pixar style
Shows 2-3 samples per book for approval before full regeneration
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

import cloudinary
import cloudinary.uploader
import aiohttp
from datetime import datetime

# Cloudinary setup
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Sample prompts for each book (2-3 pages each)
SAMPLE_PAGES = [
    # Cooking Adventures with Chef Cat
    {
        "book": "Cooking Adventures with Chef Cat",
        "page": 1,
        "prompt": "Children's book interior illustration, Pixar 3D animated style, charming orange tabby cat wearing white chef hat and red apron in a cozy colorful kitchen, warm lighting, pots and pans on shelves, whimsical atmosphere, no text, clean professional illustration, high quality"
    },
    {
        "book": "Cooking Adventures with Chef Cat", 
        "page": 4,
        "prompt": "Children's book interior illustration, Pixar 3D animated style, orange tabby chef cat teaching group of adorable kittens how to bake cookies, flour on table, mixing bowls, kittens watching with wide curious eyes, warm kitchen setting, no text, clean professional illustration, high quality"
    },
    # Friendship Island
    {
        "book": "Friendship Island",
        "page": 1,
        "prompt": "Children's book interior illustration, Pixar 3D animated style, five diverse children standing on beautiful tropical island beach, palm trees, crystal blue water, colorful swimwear, adventure excitement on faces, sunny day, no text, clean professional illustration, high quality"
    },
    {
        "book": "Friendship Island",
        "page": 5,
        "prompt": "Children's book interior illustration, Pixar 3D animated style, five children building a treehouse together on tropical island, teamwork, lush jungle background, rope ladder, wooden planks, cooperation and friendship theme, no text, clean professional illustration, high quality"
    },
    # Galaxy Racers
    {
        "book": "Galaxy Racers",
        "page": 1,
        "prompt": "Children's book interior illustration, Pixar 3D animated style, exciting space race starting line with colorful futuristic spaceships, diverse alien kid pilots in cockpits, planets and stars in background, vibrant cosmic colors, dynamic composition, no text, clean professional illustration, high quality"
    },
    {
        "book": "Galaxy Racers",
        "page": 7,
        "prompt": "Children's book interior illustration, Pixar 3D animated style, spaceships racing through asteroid field in deep space, multiple colorful ships dodging rocks, exciting action scene, purple and blue nebula background, speed lines, no text, clean professional illustration, high quality"
    },
]

async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            raise Exception(f"Failed to download: {response.status}")

async def generate_sample(sample):
    book = sample["book"]
    page = sample["page"]
    prompt = sample["prompt"]
    
    print(f"\n  Generating {book} - Page {page}...")
    
    try:
        result = await generate_image_flux(
            prompt=prompt,
            model="flux-dev",
            image_size="landscape_16_9",  # Good for interior pages
            num_images=1,
            guidance_scale=4.0,
            num_inference_steps=30
        )
        
        if result and 'images' in result and result['images']:
            image_url = result['images'][0].get('url')
            print(f"    Generated: {image_url[:50]}...")
            
            # Download and upload to Cloudinary
            image_bytes = await download_image(image_url)
            
            safe_book = book.lower().replace(" ", "_").replace("'", "")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            public_id = f"azories/samples/{safe_book}_page{page}_pixar_{timestamp}"
            
            upload_result = cloudinary.uploader.upload(
                image_bytes,
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            
            cloudinary_url = upload_result['secure_url']
            print(f"    Uploaded to Cloudinary: {cloudinary_url}")
            
            return {
                "book": book,
                "page": page,
                "url": cloudinary_url,
                "success": True
            }
        else:
            return {"book": book, "page": page, "success": False, "error": "No image generated"}
            
    except Exception as e:
        print(f"    ERROR: {e}")
        return {"book": book, "page": page, "success": False, "error": str(e)}

async def main():
    print("=" * 70)
    print("GENERATING SAMPLE INTERIOR PAGES IN PIXAR STYLE")
    print("=" * 70)
    
    results = []
    for sample in SAMPLE_PAGES:
        result = await generate_sample(sample)
        results.append(result)
        await asyncio.sleep(1)  # Small delay between requests
    
    print("\n" + "=" * 70)
    print("SAMPLE GENERATION COMPLETE")
    print("=" * 70)
    
    # Group by book
    by_book = {}
    for r in results:
        book = r["book"]
        if book not in by_book:
            by_book[book] = []
        by_book[book].append(r)
    
    for book, pages in by_book.items():
        print(f"\n📖 {book}:")
        for p in pages:
            if p["success"]:
                print(f"  Page {p['page']}: {p['url']}")
            else:
                print(f"  Page {p['page']}: FAILED - {p.get('error', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
