#!/usr/bin/env python3
"""
Batch Picture Book Completion Script - Part 4
More Picture Books - Fantasy & Fun
"""

import asyncio
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

images_generated = 0
estimated_cost = 0.0

BOOK_TEMPLATES = {
    "Pixie Dust Adventures": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, magical fairy mood, sparkly pastels and glitter effects",
        "characters": {
            "main": "Pip, a tiny pixie with sparkling blue wings, wild purple hair with flowers in it, wearing a dress made of rose petals, leaving a trail of golden dust"
        },
        "pages": [
            {"text": "Pixie Dust Adventures\n\nA Magical Tale", "scene": "Title page: A tiny pixie flying through a magical forest with sparkles everywhere"},
            {"text": "Pip was the smallest pixie in Dewdrop Hollow. Her wings sparkled blue like morning sky.", "scene": "Pip the tiny pixie in a beautiful hollow with dewdrops and flowers"},
            {"text": "Every pixie had a special job. Some grew flowers. Some painted butterflies. But Pip didn't know her gift yet.", "scene": "Other pixies doing magical jobs while Pip watches, feeling left out"},
            {"text": "\"I want to find my magic!\" Pip declared, and flew off into the Whispering Woods.", "scene": "Pip flying determinedly into a mystical forest with glowing plants"},
            {"text": "She met a sad ladybug who had lost her spots. Pip sprinkled some dust and—POP!—beautiful new spots appeared!", "scene": "Pip sprinkling pixie dust on a ladybug, spots magically appearing"},
            {"text": "A wilted flower begged for help. Pip's dust made it bloom brighter than ever before!", "scene": "Pip making a wilted flower bloom into a magnificent glowing flower"},
            {"text": "Even a grumpy toad smiled when Pip's dust turned his puddle into a sparkling pond!", "scene": "Pip transforming a muddy puddle into a beautiful sparkling pond, toad happy"},
            {"text": "Pip zoomed home. \"I found my gift! I make things HAPPY!\"", "scene": "Pip flying excitedly back home, trail of sparkles behind her"},
            {"text": "The Queen Pixie smiled. \"The rarest gift of all—spreading joy wherever you go.\"", "scene": "Queen Pixie crowning Pip with a tiny flower crown, other pixies cheering"},
            {"text": "And from that day on, Pip's pixie dust made the whole forest smile.\n\nThe End", "scene": "Pip flying over a happy magical forest, everything sparkling and joyful"}
        ]
    },
    "The Enchanted Carousel": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, whimsical carnival mood, vintage pastels with golden lights",
        "characters": {
            "main": "Mia, a 5-year-old girl with two dark braids tied with ribbons, rosy cheeks, wearing a vintage-style dress with a cardigan"
        },
        "pages": [
            {"text": "The Enchanted Carousel\n\nA Magical Ride", "scene": "Title page: A beautiful glowing carousel at twilight with magical horses"},
            {"text": "Mia found an old carousel in the corner of the park. It looked forgotten, but still beautiful.", "scene": "Mia discovering an old ornate carousel covered in vines, evening light"},
            {"text": "She climbed onto a white horse with a golden mane. Suddenly, the carousel began to spin!", "scene": "Mia on a beautiful white carousel horse, lights starting to glow"},
            {"text": "The horse winked at her! \"Hold tight, little one. We're going on an adventure!\"", "scene": "The carousel horse winking at surprised Mia, magical sparkles"},
            {"text": "The carousel spun faster and faster until—WHOOSH! They flew into the sky!", "scene": "Carousel lifting off into starry sky, Mia holding on, amazed expression"},
            {"text": "They soared over candy-colored mountains and rivers made of starlight.", "scene": "Mia riding the horse through a magical landscape of candy mountains and starlight rivers"},
            {"text": "They raced through clouds shaped like animals and picked flowers from floating gardens.", "scene": "Mia and horse flying through cloud animals and floating flower gardens"},
            {"text": "\"Time to go home,\" the horse said gently as the sun began to rise.", "scene": "Horse and Mia descending back toward the carousel, sunrise colors"},
            {"text": "The carousel slowed and Mia stepped off, a magical flower still in her hand.", "scene": "Mia stepping off carousel holding a glowing flower, looking amazed"},
            {"text": "\"Come back anytime,\" the horse whispered. And Mia knew she would.\n\nThe End", "scene": "Mia waving goodbye to the carousel at sunset, magical and warm"}
        ]
    },
    "The Friendly Martians": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, fun space mood, reds and purples of Mars with friendly alien designs",
        "characters": {
            "main": "Ziggy and Zara, two small green Martians with big friendly eyes, antennae with heart shapes on top, wearing space suits with stars"
        },
        "pages": [
            {"text": "The Friendly Martians\n\nA Story About Making Friends", "scene": "Title page: Two cute green Martians waving from Mars with Earth in the sky"},
            {"text": "Ziggy and Zara lived on Mars. They had lots of rocks to play with, but no friends.", "scene": "Two Martians looking lonely on Mars landscape, surrounded by red rocks"},
            {"text": "One day, a spaceship landed nearby! Out came a little girl named Luna.", "scene": "Spaceship landing on Mars, Luna stepping out, Martians hiding and peeking"},
            {"text": "The Martians were scared. Luna looked so different! She had no antennae at all!", "scene": "Martians hiding behind rocks, looking nervously at Luna"},
            {"text": "But Luna smiled and waved. \"Hello! Do you want to play?\"", "scene": "Luna waving friendly, Martians starting to come out curiously"},
            {"text": "They played hide and seek behind craters. Ziggy was really good at hiding!", "scene": "Playing hide and seek on Mars, Ziggy hiding behind a crater"},
            {"text": "They made sand castles from red Mars dust. Zara built the tallest one!", "scene": "All three making Mars dust castles together, having fun"},
            {"text": "They bounced super high in the low gravity and giggled until their tummies hurt.", "scene": "Luna and Martians bouncing high on Mars, all laughing"},
            {"text": "When Luna had to go home, they all felt sad. \"Will you come back?\" asked Ziggy.", "scene": "Sad farewell scene at the spaceship, everyone looking emotional"},
            {"text": "\"Of course!\" Luna smiled. \"Friends visit each other, no matter how far!\"\n\nThe End", "scene": "Luna waving from spaceship window, Martians waving from Mars, Earth and Mars connected by hearts"}
        ]
    },
    "Seasons of the Magic Forest": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, nature mood, changing seasonal colors",
        "characters": {
            "main": "Willow, a young forest sprite with leaf-green hair that changes with seasons, wearing clothes made of natural materials"
        },
        "pages": [
            {"text": "Seasons of the Magic Forest\n\nA Year of Wonder", "scene": "Title page: A magical forest shown in four seasons, sprite in center"},
            {"text": "Willow was a forest sprite. Her hair changed color with every season!", "scene": "Willow the sprite standing in magical forest, hair bright green"},
            {"text": "In SPRING, her hair bloomed with tiny pink flowers. Baby animals woke from their naps!", "scene": "Willow with pink flower hair, surrounded by baby forest animals, spring flowers"},
            {"text": "She helped bunnies find clover and taught birds their first songs.", "scene": "Willow with bunnies in clover field, birds singing on branches"},
            {"text": "In SUMMER, her hair turned sunny yellow. The forest buzzed with life!", "scene": "Willow with golden yellow hair, bright summer forest, butterflies and bees"},
            {"text": "She splashed in cool streams and danced with fireflies at night.", "scene": "Willow playing in stream by day, dancing with fireflies at night"},
            {"text": "In AUTUMN, her hair turned red and orange like falling leaves.", "scene": "Willow with red-orange hair, autumn forest with falling leaves"},
            {"text": "She helped squirrels gather acorns and painted leaves beautiful colors.", "scene": "Willow helping squirrels, magically painting leaves different colors"},
            {"text": "In WINTER, her hair sparkled white like snow. The forest grew quiet and peaceful.", "scene": "Willow with white sparkly hair in snowy forest, peaceful and quiet"},
            {"text": "\"Every season is beautiful,\" Willow smiled, \"because change is magic.\"\n\nThe End", "scene": "Willow shown in all four seasonal forms, celebrating the cycle of nature"}
        ]
    }
}

async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality."
    
    try:
        result = await generate_image_flux(
            prompt=full_prompt, model="flux-dev", image_size="landscape_4_3", num_images=1
        )
        
        if result.get("success") and result.get("images"):
            image_info = result["images"][0]
            image_url = image_info["url"] if isinstance(image_info, dict) else image_info
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        with open(output_path, 'wb') as f:
                            f.write(await resp.read())
                        images_generated += 1
                        estimated_cost += 0.03
                        return True
        return False
    except Exception as e:
        error = str(e).lower()
        if "balance" in error or "budget" in error or "insufficient" in error:
            raise Exception("BUDGET_EXHAUSTED")
        print(f"    ERROR: {str(e)[:80]}")
        return False

async def complete_single_book(book_id: str, title: str, template: dict):
    global estimated_cost
    
    print(f"\n{'='*60}")
    print(f"COMPLETING: {title}")
    print(f"{'='*60}")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    safe_title = title.lower().replace("'", "").replace(" ", "_")
    output_dir = APP_DIR / f"content/books/completed/{safe_title}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    total = len(template["pages"])
    
    # Cover
    cover_path = output_dir / "cover.png"
    print(f"[Cover] Generating...")
    if await generate_book_image(
        f"Children's book cover for '{title}'. {template['characters']['main']}. Title space at top",
        template["style_prompt"], cover_path
    ):
        print(f"    ✓ Cover")
    
    # Pages
    for i, page in enumerate(template["pages"]):
        print(f"[Page {i+1}/{total}]", end=" ")
        page_path = output_dir / f"page_{i+1:02d}.png"
        if await generate_book_image(page["scene"] + f". Character: {template['characters']['main']}", 
                                    template["style_prompt"], page_path):
            print("✓")
            pages.append({
                "page_number": i + 1,
                "text": page["text"],
                "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
                "layout": "full_spread" if i == 0 else "text_left_image_right"
            })
        await asyncio.sleep(0.3)
    
    # Back cover
    print("[Back] ", end="")
    await generate_book_image(f"Back cover, {template['characters']['main']}, peaceful", 
                             template["style_prompt"], output_dir / "back_cover.png")
    print("✓")
    
    # Update DB
    await db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {
            "pages": pages,
            "cover_image_url": f"/book-assets/{safe_title}/cover.png",
            "page_count": len(pages),
            "status": "published",
            "art_style": template["art_style"],
            "age_range": template["age_range"],
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    # Copy to public
    public_dir = APP_DIR / f"frontend/public/book-assets/{safe_title}"
    public_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    for f in output_dir.glob("*.png"):
        shutil.copy(f, public_dir / f.name)
    
    print(f"✓ DONE - Total cost: ${estimated_cost:.2f}")

async def run_batch():
    global estimated_cost
    
    print("="*60)
    print("PICTURE BOOK BATCH - PART 4")
    print("="*60)
    
    books = [
        ("699adbe6176ebca750087f1d", "Pixie Dust Adventures"),
        ("699adbe6176ebca750087f1e", "The Enchanted Carousel"),
        ("699adbe6176ebca750087f1a", "The Friendly Martians"),
        ("699adbe6176ebca750087f24", "Seasons of the Magic Forest"),
    ]
    
    completed = 0
    for book_id, title in books:
        if title in BOOK_TEMPLATES:
            try:
                await complete_single_book(book_id, title, BOOK_TEMPLATES[title])
                completed += 1
                if estimated_cost > 8.5:
                    print("\n⚠️ BUDGET WARNING - Pausing")
                    break
            except Exception as e:
                if "BUDGET" in str(e):
                    print("\n🚨 BUDGET EXHAUSTED")
                    break
                print(f"Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {completed} books, {images_generated} images, ${estimated_cost:.2f}")

if __name__ == "__main__":
    asyncio.run(run_batch())
