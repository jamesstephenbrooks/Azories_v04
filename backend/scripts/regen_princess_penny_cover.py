"""
Regenerate Princess Penny's Pet Dragon cover to match cartoon interior style
"""
import asyncio
import os
import cloudinary
import cloudinary.uploader
import aiohttp
from datetime import datetime
from pymongo import MongoClient
from pathlib import Path

# Load environment manually
env_path = Path('/app/backend/.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

# Import fal.ai service
import sys
sys.path.insert(0, '/app/backend')
from fal_service import generate_image_flux

# MongoDB setup
client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client[os.environ.get('DB_NAME', 'test_database')]

# Cloudinary setup
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            raise Exception(f"Failed to download: {response.status}")

async def main():
    print("=" * 60)
    print("Regenerating Princess Penny's Pet Dragon Cover")
    print("Matching digital cartoon interior style")
    print("=" * 60)
    
    # Prompt matches the interior style: digital cartoon, red-haired princess, cute dragons
    prompt = """Children's book cover illustration, digital cartoon style matching interior pages, 
    cute red-haired princess with crown wearing pink dress, friendly small dragon companion, 
    castle in background, bright cheerful colors, clean white background elements, 
    whimsical cartoon aesthetic, no text, professional children's book art, 
    matching style of interior illustrations with the same character design"""
    
    print("\nGenerating cover with fal.ai FLUX...")
    result = await generate_image_flux(
        prompt=prompt,
        model="flux-dev",
        image_size="portrait_4_3",
        num_images=1,
        guidance_scale=4.0,
        num_inference_steps=30
    )
    
    if not result or 'images' not in result:
        print("ERROR: No image generated")
        return
    
    image_url = result['images'][0].get('url')
    print(f"Image generated: {image_url[:60]}...")
    
    # Download and upload to Cloudinary
    print("Downloading and uploading to Cloudinary...")
    image_bytes = await download_image(image_url)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    public_id = f"azories/books/princess_pennys_pet_dragon_cover_cartoon_{timestamp}"
    
    upload_result = cloudinary.uploader.upload(
        image_bytes,
        public_id=public_id,
        overwrite=True,
        resource_type="image"
    )
    
    new_cover_url = upload_result['secure_url']
    print(f"Uploaded: {new_cover_url}")
    
    # Update database
    db.books.update_one(
        {"title": "Princess Penny's Pet Dragon"},
        {"$set": {
            "cover_image": new_cover_url,
            "_cover_style": "cartoon_matched_interior",
            "_cover_regenerated": datetime.now().isoformat()
        }}
    )
    print("\n✓ Database updated!")
    print(f"\nNEW COVER URL:\n{new_cover_url}")

if __name__ == "__main__":
    asyncio.run(main())
