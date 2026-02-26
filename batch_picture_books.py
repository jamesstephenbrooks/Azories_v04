#!/usr/bin/env python3
"""
Batch Picture Book Completion Script
Uses fal.ai FLUX for cost efficiency
Processes books one at a time with progress tracking
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId

APP_DIR = Path(__file__).parent
BACKEND_DIR = APP_DIR / 'backend'

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / '.env')

sys.path.insert(0, str(BACKEND_DIR))
from motor.motor_asyncio import AsyncIOMotorClient
from fal_service import generate_image_flux

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Track costs
images_generated = 0
estimated_cost = 0.0

# Book templates with character bibles and stories
BOOK_TEMPLATES = {
    "The Dragon's Secret Garden": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, magical whimsical mood, warm greens and soft pinks, gentle brushstrokes",
        "characters": {
            "main": "Lily, a curious 6-year-old girl with long brown braids, bright green eyes, freckles, wearing a yellow sundress and brown boots",
            "dragon": "Ember, a small friendly dragon the size of a cat, with shimmery green scales, big golden eyes, tiny wings, and a flower tucked behind one ear"
        },
        "pages": [
            {"text": "The Dragon's Secret Garden\n\nA Magical Tale", "scene": "Title page: A hidden garden gate covered in vines with a glimpse of magical flowers and a tiny dragon peeking through"},
            {"text": "Lily loved exploring the old forest behind her grandmother's cottage. One day, she found a gate she had never seen before.", "scene": "Lily discovering an ancient stone gate covered in flowering vines in a misty forest"},
            {"text": "Behind the gate was the most beautiful garden Lily had ever seen. Flowers of every color sparkled like jewels!", "scene": "A magical garden with glowing flowers in rainbow colors, sparkling dewdrops, winding paths"},
            {"text": "\"Hello there!\" said a small voice. A tiny green dragon sat on a rose bush, watering flowers with little puffs of steam.", "scene": "Ember the small green dragon sitting on a rose bush, puffing gentle steam onto flowers, looking friendly"},
            {"text": "\"I'm Ember,\" said the dragon. \"I take care of these magic flowers. Would you like to help?\"", "scene": "Lily and Ember meeting, Ember offering a tiny watering can, garden background"},
            {"text": "Lily and Ember planted seeds that grew into flowers shaped like stars and moons. Some even giggled when you tickled them!", "scene": "Lily and Ember planting together, whimsical star and moon shaped flowers growing, magical sparkles"},
            {"text": "\"These flowers grant wishes,\" Ember whispered. \"But only kind wishes work.\"", "scene": "Ember whispering to Lily near a glowing wish flower, magical atmosphere"},
            {"text": "Lily wished for her grandmother to feel better. A golden flower bloomed and sent sparkles toward the cottage.", "scene": "Lily making a wish, golden sparkles flowing from a special flower toward a distant cottage"},
            {"text": "From that day on, Lily visited the secret garden every week. She and Ember became the best of friends.", "scene": "Lily and Ember having a tea party in the garden surrounded by magical flowers"},
            {"text": "And if you ever find a hidden gate in the forest, look carefully—you might just meet a friendly dragon too.\n\nThe End", "scene": "Final spread: Lily waving goodbye at the garden gate, Ember on her shoulder, magical sunset"}
        ]
    },
    "Princess Penny's Pet Dragon": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, playful royal mood, pinks purples and golds, castle setting",
        "characters": {
            "main": "Princess Penny, a 5-year-old princess with curly red hair in a messy bun with a tiny crown, freckles, wearing a pink dress with muddy hem",
            "dragon": "Spark, a clumsy baby dragon the size of a puppy, bright purple scales, big innocent blue eyes, tiny wings too small to fly"
        },
        "pages": [
            {"text": "Princess Penny's Pet Dragon\n\nA Royal Adventure", "scene": "Title page: A castle with a small purple dragon causing chaos in the window"},
            {"text": "Princess Penny didn't want a pony or a kitten. She wanted something special. So when a tiny purple dragon hatched in the royal garden, she knew he was meant to be hers.", "scene": "Princess Penny finding a cracking dragon egg in the royal garden, her face full of wonder"},
            {"text": "\"I'll call you Spark!\" Penny giggled as the baby dragon sneezed and accidentally set the royal curtains on fire.", "scene": "Spark sneezing a small flame at curtains while Penny giggles, servants looking worried"},
            {"text": "Spark tried to be a good dragon, but everything went wrong. He knocked over the king's soup at dinner.", "scene": "Spark's tail knocking over soup bowl at royal dinner table, the king surprised, Penny covering her smile"},
            {"text": "He chased the royal cats through the throne room and got tangled in the queen's knitting.", "scene": "Spark tangled in colorful yarn, cats running, queen looking amused, throne room chaos"},
            {"text": "\"Perhaps,\" said the queen gently, \"Spark needs dragon training.\"", "scene": "The queen talking kindly to sad-looking Penny and Spark"},
            {"text": "Penny and Spark practiced together every day. Sitting. Staying. NOT setting things on fire.", "scene": "Penny training Spark in the garden, Spark trying very hard to behave, training treats visible"},
            {"text": "Slowly, Spark got better. He only burned small things. Mostly by accident.", "scene": "Spark successfully doing a trick, small proud flame, Penny clapping, tiny scorch mark on ground"},
            {"text": "When a mean cat scared the princess, Spark stood bravely in front of her and gave his biggest, most protective little roar.", "scene": "Spark standing protectively in front of Penny, puffing up at a hissing cat, being brave"},
            {"text": "\"You're the best dragon ever,\" Penny whispered, hugging Spark. And Spark knew he finally belonged.\n\nThe End", "scene": "Penny hugging Spark in the castle garden at sunset, both looking happy and loved"}
        ]
    },
    "The Mermaid's Lost Pearl": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, underwater magical mood, teals blues and iridescent colors, ocean setting",
        "characters": {
            "main": "Marina, a young mermaid with long flowing turquoise hair, big violet eyes, shimmering pink tail, wearing a coral crown",
            "friend": "Bubbles, a friendly orange clownfish with big eyes and a cheerful smile"
        },
        "pages": [
            {"text": "The Mermaid's Lost Pearl\n\nAn Ocean Adventure", "scene": "Title page: A glowing pearl in an oyster shell with underwater coral and a mermaid silhouette"},
            {"text": "Marina the mermaid lived in a beautiful coral palace. Her most treasured possession was her grandmother's magical pearl.", "scene": "Marina in her coral bedroom holding a glowing pearl, underwater palace visible"},
            {"text": "But one morning, the pearl was gone! Marina searched everywhere in her room but couldn't find it.", "scene": "Marina looking worried, searching through shells and coral, empty pearl box"},
            {"text": "\"Don't worry!\" said Bubbles the clownfish. \"I'll help you find it!\"", "scene": "Bubbles the clownfish swimming up to comfort worried Marina"},
            {"text": "They searched the kelp forest, but found only a family of shy seahorses.", "scene": "Marina and Bubbles swimming through tall green kelp, cute seahorses peeking out"},
            {"text": "They explored the sunken ship, but found only a cranky old crab.", "scene": "Marina and Bubbles peeking into a sunken ship, a grumpy crab waving claws"},
            {"text": "They swam to the deep caves, but found only glowing jellyfish dancing in the dark.", "scene": "Marina and Bubbles in a dark cave with beautiful bioluminescent jellyfish"},
            {"text": "Marina was ready to give up when Bubbles shouted, \"Look! It's glowing!\"", "scene": "Bubbles pointing excitedly, a soft glow visible in the distance"},
            {"text": "The pearl had rolled into a little hermit crab's shell. \"I thought it was the moon,\" the crab said shyly.", "scene": "A cute hermit crab with the glowing pearl in its shell, looking apologetic"},
            {"text": "Marina thanked the hermit crab and gave him a small shell of his own. \"Now we both have treasures,\" she smiled.\n\nThe End", "scene": "Marina, Bubbles, and the hermit crab all happy together, pearl back where it belongs"}
        ]
    }
}

async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    """Generate a single image using fal.ai FLUX"""
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality."
    
    try:
        result = await generate_image_flux(
            prompt=full_prompt,
            model="flux-dev",
            image_size="landscape_4_3",
            num_images=1
        )
        
        if result.get("success") and result.get("images"):
            image_info = result["images"][0]
            image_url = image_info["url"] if isinstance(image_info, dict) else image_info
            
            # Download and save
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        with open(output_path, 'wb') as f:
                            f.write(image_bytes)
                        images_generated += 1
                        estimated_cost += 0.03  # fal.ai cost per image
                        return True
        return False
    except Exception as e:
        print(f"    ERROR: {str(e)[:100]}")
        return False

async def complete_single_book(book_id: str, title: str, template: dict):
    """Complete a single book with full content"""
    global images_generated, estimated_cost
    
    print(f"\n{'='*60}")
    print(f"COMPLETING: {title}")
    print(f"{'='*60}")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Create output directory
    safe_title = title.lower().replace("'", "").replace(" ", "_")
    output_dir = APP_DIR / f"content/books/completed/{safe_title}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    total_pages = len(template["pages"])
    
    # Generate cover
    print(f"\n[Cover] Generating...")
    cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}. Engaging scene showing main character, space for title at top"
    cover_path = output_dir / "cover.png"
    if await generate_book_image(cover_prompt, template["style_prompt"], cover_path):
        print(f"    ✓ Cover saved")
    
    # Generate interior pages
    for i, page_data in enumerate(template["pages"]):
        print(f"\n[Page {i+1}/{total_pages}] Generating...")
        
        # Build scene prompt with character descriptions
        scene_prompt = page_data["scene"]
        for char_key, char_desc in template["characters"].items():
            if char_key in scene_prompt.lower() or char_key == "main":
                scene_prompt = f"{scene_prompt}. Character: {char_desc}"
                break
        
        page_path = output_dir / f"page_{i+1:02d}.png"
        
        if await generate_book_image(scene_prompt, template["style_prompt"], page_path):
            print(f"    ✓ Page {i+1} saved")
            pages.append({
                "page_number": i + 1,
                "text": page_data["text"],
                "content": page_data["text"],
                "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
                "layout": "full_spread" if i == 0 else "text_left_image_right"
            })
        else:
            print(f"    ✗ Page {i+1} failed")
            pages.append({
                "page_number": i + 1,
                "text": page_data["text"],
                "content": page_data["text"],
                "image_url": None,
                "layout": "text_only"
            })
        
        await asyncio.sleep(0.5)
    
    # Generate back cover
    print(f"\n[Back Cover] Generating...")
    back_cover_prompt = f"Back cover for '{title}'. Peaceful scene with {template['characters']['main']}, soft colors"
    back_cover_path = output_dir / "back_cover.png"
    await generate_book_image(back_cover_prompt, template["style_prompt"], back_cover_path)
    
    # Update database
    print(f"\nUpdating database...")
    result = await db.books.update_one(
        {"_id": ObjectId(book_id)},
        {
            "$set": {
                "pages": pages,
                "cover_image_url": f"/book-assets/{safe_title}/cover.png",
                "back_cover_url": f"/book-assets/{safe_title}/back_cover.png",
                "page_count": len(pages),
                "status": "published",
                "age_range": template["age_range"],
                "art_style": template["art_style"],
                "character_bible": template["characters"],
                "updated_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    # Copy to public folder
    public_dir = APP_DIR / f"frontend/public/book-assets/{safe_title}"
    public_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    for img_file in output_dir.glob("*.png"):
        shutil.copy(img_file, public_dir / img_file.name)
    
    print(f"\n✓ {title} COMPLETED")
    print(f"  Pages: {len(pages)}")
    print(f"  Cost so far: ${estimated_cost:.2f}")
    
    return True

async def run_batch():
    """Run batch completion for available books"""
    global images_generated, estimated_cost
    
    print("="*60)
    print("PICTURE BOOK BATCH COMPLETION")
    print("="*60)
    print(f"Estimated cost per book: ~$0.36 (12 images × $0.03)")
    print()
    
    # Books to complete (with templates defined)
    books_to_complete = [
        ("699a451bf2f82cc029a248c8", "The Dragon's Secret Garden"),
        ("699adbe6176ebca750087f16", "Princess Penny's Pet Dragon"),
        ("699adbe6176ebca750087f19", "The Mermaid's Lost Pearl"),
    ]
    
    completed = 0
    for book_id, title in books_to_complete:
        if title in BOOK_TEMPLATES:
            try:
                await complete_single_book(book_id, title, BOOK_TEMPLATES[title])
                completed += 1
                
                # Check budget warning
                if estimated_cost > 8.0:
                    print("\n⚠️ BUDGET WARNING: Approaching $10 limit")
                    print(f"   Estimated cost: ${estimated_cost:.2f}")
                    print("   Pausing to preserve budget.")
                    break
                    
            except Exception as e:
                print(f"\n✗ Error completing {title}: {e}")
                if "budget" in str(e).lower() or "exceeded" in str(e).lower():
                    print("\n🚨 BUDGET EXHAUSTED - Stopping batch")
                    break
    
    print("\n" + "="*60)
    print("BATCH SUMMARY")
    print("="*60)
    print(f"Books completed: {completed}")
    print(f"Images generated: {images_generated}")
    print(f"Estimated cost: ${estimated_cost:.2f}")

if __name__ == "__main__":
    asyncio.run(run_batch())
