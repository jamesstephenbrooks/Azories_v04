"""
PHASE 1: Generate missing/stock photo covers for 10 books
Generates Pixar-style illustrated covers and uploads to Cloudinary
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
import cloudinary
import cloudinary.uploader
import base64
from datetime import datetime

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Cloudinary setup
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# API Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Books that need new covers with their cover prompts
BOOKS_TO_REGENERATE = [
    {
        "title": "Cooking Adventures with Chef Cat",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, a charming orange tabby cat wearing a chef's hat and apron, standing in a colorful kitchen with pots and pans, warm lighting, whimsical and fun atmosphere, no text, clean illustration, professional children's book art"
    },
    {
        "title": "Friendship Island",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, five diverse children standing on a beautiful tropical island beach with palm trees, crystal blue water, adventure atmosphere, friendship theme, warm sunset lighting, no text, clean illustration, professional children's book art"
    },
    {
        "title": "Galaxy Racers",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, exciting space race scene with colorful futuristic spaceships zooming through a galaxy with planets and stars, dynamic action pose, vibrant cosmic colors, no text, clean illustration, professional children's book art for ages 10-12"
    },
    {
        "title": "Ocean Wonders",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, magical underwater ocean scene with colorful coral reefs, friendly sea creatures like dolphins, sea turtles, and tropical fish, beautiful blue water with light rays, no text, clean illustration, educational children's book art"
    },
    {
        "title": "Princess and the Enchanted Forest",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, beautiful young princess with flowing dress standing at the entrance of a magical glowing forest, talking woodland animals around her, fairy tale atmosphere, soft magical lighting, no text, clean illustration, professional children's book art"
    },
    {
        "title": "The Dinosaur Time Machine",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, two excited children (boy and girl siblings) standing next to a glowing time machine with friendly dinosaurs in the background, prehistoric jungle setting, adventure atmosphere, no text, clean illustration, professional children's book art for ages 7-9"
    },
    {
        "title": "The Haunted Treehouse",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, three brave children with flashlights looking up at a mysterious old treehouse at dusk, spooky but not scary atmosphere, autumn leaves, mystery theme, soft moonlight, no text, clean illustration, professional children's book art for ages 7-9"
    },
    {
        "title": "The Robot Who Wanted Friends",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, adorable small robot with big expressive eyes looking hopeful, surrounded by children playing in a park, heartwarming friendship theme, bright cheerful colors, no text, clean illustration, professional children's book art"
    },
    {
        "title": "The Superhero School",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, diverse group of kids in colorful superhero costumes standing in front of an amazing superhero academy building, dynamic heroic poses, bright vibrant colors, action atmosphere, no text, clean illustration, professional children's book art for ages 10-12"
    },
    {
        "title": "Flame's Courageous Journey",
        "prompt": "Children's book cover illustration, Pixar 3D animated style, small cute dragon named Flame with orange and red scales, looking determined and brave, fantasy mountain landscape with magical elements, warm fire colors, courage theme, no text, clean illustration, professional children's book art"
    }
]

async def generate_and_upload_cover(book_info):
    """Generate a cover and upload to Cloudinary"""
    title = book_info["title"]
    prompt = book_info["prompt"]
    
    print(f"\n{'='*60}")
    print(f"Generating cover for: {title}")
    print(f"{'='*60}")
    
    try:
        # Initialize image generator
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        # Generate the image
        print(f"  Sending prompt to GPT-Image-1...")
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if not images or len(images) == 0:
            print(f"  ERROR: No image generated for {title}")
            return None
        
        print(f"  Image generated successfully!")
        
        # Convert to base64 for Cloudinary upload
        image_bytes = images[0]
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create a safe filename
        safe_title = title.lower().replace(" ", "_").replace("'", "").replace(":", "")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        public_id = f"azories/books/{safe_title}_cover_clean_{timestamp}"
        
        # Upload to Cloudinary
        print(f"  Uploading to Cloudinary...")
        result = cloudinary.uploader.upload(
            f"data:image/png;base64,{image_base64}",
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )
        
        new_cover_url = result['secure_url']
        print(f"  Uploaded! URL: {new_cover_url}")
        
        # Update database
        update_result = db.books.update_one(
            {"title": title},
            {"$set": {
                "cover_image": new_cover_url,
                "_clean": True,
                "_cover_regenerated": datetime.now().isoformat()
            }}
        )
        
        if update_result.modified_count > 0:
            print(f"  Database updated successfully!")
        else:
            print(f"  WARNING: Database not updated (book may not exist)")
        
        return {
            "title": title,
            "new_cover_url": new_cover_url,
            "success": True
        }
        
    except Exception as e:
        print(f"  ERROR generating cover for {title}: {str(e)}")
        return {
            "title": title,
            "error": str(e),
            "success": False
        }

async def main():
    print("=" * 80)
    print("PHASE 1: Generating missing/stock photo covers")
    print(f"Total books to process: {len(BOOKS_TO_REGENERATE)}")
    print("=" * 80)
    
    results = []
    
    for book_info in BOOKS_TO_REGENERATE:
        result = await generate_and_upload_cover(book_info)
        results.append(result)
        
        # Small delay between generations
        await asyncio.sleep(2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("PHASE 1 SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r and r.get("success")]
    failed = [r for r in results if r and not r.get("success")]
    
    print(f"\nSuccessful: {len(successful)}/{len(BOOKS_TO_REGENERATE)}")
    for r in successful:
        print(f"  ✓ {r['title']}")
        print(f"    URL: {r['new_cover_url']}")
    
    if failed:
        print(f"\nFailed: {len(failed)}")
        for r in failed:
            print(f"  ✗ {r['title']}: {r.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 80)
    print("Phase 1 complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
