#!/usr/bin/env python3
"""
Batch Picture Book Completion Script - Part 3
More Picture Books - Educational & Adventure
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
    "The Alphabet Zoo": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, fun educational mood, bright zoo colors",
        "characters": {
            "main": "Zoe the zookeeper, a cheerful young woman with a ponytail, wearing khaki uniform and a big smile"
        },
        "pages": [
            {"text": "The Alphabet Zoo\n\nLearn Your ABCs with Animals!", "scene": "Zoo entrance with colorful animal letters above the gate"},
            {"text": "A is for Alligator, with a smile so wide!\nB is for Bear, playing on the slide!", "scene": "Friendly alligator smiling and a bear on a playground slide, letters A and B visible"},
            {"text": "C is for Cat, so fluffy and sweet!\nD is for Dog, with happy dancing feet!", "scene": "Fluffy cat and dancing dog together, letters C and D visible"},
            {"text": "E is for Elephant, spraying water high!\nF is for Flamingo, standing by!", "scene": "Elephant spraying water, flamingo standing on one leg, letters E and F"},
            {"text": "G is for Giraffe, reaching for a treat!\nH is for Hippo, splashing in the heat!", "scene": "Giraffe eating from tall tree, hippo splashing in water, letters G and H"},
            {"text": "I is for Iguana, green and cool!\nJ is for Jaguar, looking like a jewel!", "scene": "Green iguana and spotted jaguar, letters I and J"},
            {"text": "K is for Koala, hugging a tree!\nL is for Lion, roaring with glee!", "scene": "Koala on eucalyptus tree, lion roaring happily, letters K and L"},
            {"text": "M is for Monkey, swinging around!\nN is for Newt, crawling on the ground!", "scene": "Monkey swinging on vines, newt on leaves, letters M and N"},
            {"text": "O is for Owl, wise and bright!\nP is for Penguin, a silly sight!", "scene": "Wise owl on branch, silly penguin waddling, letters O and P"},
            {"text": "Now you know your alphabet friends!\nVisit the zoo where learning never ends!\n\nThe End", "scene": "All animals gathered together waving, full alphabet visible in background"}
        ]
    },
    "Safari Sam's Big Day": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, exciting adventure mood, African savanna colors, warm golden light",
        "characters": {
            "main": "Safari Sam, a 6-year-old boy with dark skin, big curious eyes, wearing a safari hat, khaki vest with many pockets, and binoculars around his neck"
        },
        "pages": [
            {"text": "Safari Sam's Big Day\n\nAn African Adventure", "scene": "Title page: Sam looking through binoculars at African savanna"},
            {"text": "Today was the day! Sam was going on his very first safari with his grandfather.", "scene": "Sam excitedly waking up, safari gear ready, sun rising through window"},
            {"text": "They drove across the golden grassland in an open jeep. Sam held his camera tight.", "scene": "Sam and grandfather in safari jeep driving through savanna, acacia trees"},
            {"text": "\"Look!\" whispered Sam. A family of elephants walked by, the baby holding its mother's tail.", "scene": "Sam photographing elephant family, baby elephant holding mother's tail"},
            {"text": "Giraffes stretched their long necks to eat from the tallest trees. Sam counted five!", "scene": "Sam watching and counting giraffes eating from acacia trees"},
            {"text": "A lion yawned lazily in the shade. \"He's taking a nap,\" Grandfather chuckled.", "scene": "Lion yawning in shade, Sam watching from jeep, grandfather smiling"},
            {"text": "Zebras galloped past in their stripy pajamas. Sam laughed at how silly they looked!", "scene": "Zebras running, Sam laughing at their stripes, dust cloud behind them"},
            {"text": "At the watering hole, hippos and crocodiles shared the cool water peacefully.", "scene": "Hippos and crocodiles at watering hole, birds nearby, Sam watching from safe distance"},
            {"text": "As the sun set orange and pink, Sam took one last photo of a beautiful cheetah.", "scene": "Cheetah silhouette against beautiful sunset, Sam taking photo"},
            {"text": "\"Best day ever,\" Sam smiled, his camera full of memories.\n\nThe End", "scene": "Sam and grandfather driving home at sunset, Sam looking happy with camera"}
        ]
    },
    "Astronaut Alex's Moon Mission": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, wonder and space adventure mood, deep space blues and starlight",
        "characters": {
            "main": "Alex, a 5-year-old astronaut with short black hair, wearing a puffy white spacesuit with a clear helmet, big excited brown eyes"
        },
        "pages": [
            {"text": "Astronaut Alex's Moon Mission\n\nA Space Adventure", "scene": "Title page: Alex in spacesuit floating toward the moon"},
            {"text": "Alex dreamed of going to space. Every night, she counted the stars from her window.", "scene": "Young Alex at window looking at stars, moon glowing, space posters on wall"},
            {"text": "One special morning, Alex put on her spacesuit. Today was the day!", "scene": "Alex putting on cute child-sized spacesuit, excited expression"},
            {"text": "3... 2... 1... BLAST OFF! The rocket zoomed up, up, up into the sky!", "scene": "Rocket launching with big flames, Alex waving from window, dramatic sky"},
            {"text": "Through the window, Alex watched Earth get smaller and smaller. \"Goodbye, home!\"", "scene": "Alex looking out rocket window at Earth getting smaller, stars around"},
            {"text": "The moon got closer and closer. It was grey and bumpy with lots of craters.", "scene": "Moon getting bigger through window, Alex's face full of wonder"},
            {"text": "Alex bounced on the moon. Each jump took her super high! \"Wheee!\"", "scene": "Alex bouncing in low gravity on moon surface, Earth visible in black sky"},
            {"text": "She planted a little flower in moon soil. \"The first flower on the moon!\"", "scene": "Alex planting small flower in moon dirt, proud expression, Earth in background"},
            {"text": "Alex collected sparkly moon rocks to show everyone back home.", "scene": "Alex gathering glowing moon rocks, putting them in sample bag"},
            {"text": "Back on Earth, Alex smiled at the moon. \"I'll visit you again soon!\"\n\nThe End", "scene": "Alex back home looking at moon through window, moon rocks on shelf, dreaming"}
        ]
    },
    "The Feelings Garden": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, gentle emotional mood, soft colors representing different feelings",
        "characters": {
            "main": "Felix, a sensitive 4-year-old boy with curly brown hair, big expressive hazel eyes, wearing overalls with patches"
        },
        "pages": [
            {"text": "The Feelings Garden\n\nWhere Emotions Bloom", "scene": "Title page: A magical garden where flowers represent different emotions"},
            {"text": "Felix had a special garden where his feelings grew as flowers.", "scene": "Felix in magical garden surrounded by emotion-colored flowers"},
            {"text": "When he felt happy, yellow sunflowers bloomed bright and tall!", "scene": "Felix laughing as yellow sunflowers grow around him, sunny scene"},
            {"text": "When he felt sad, soft blue flowers drooped like tears.", "scene": "Felix looking sad, gentle blue drooping flowers around him, soft rain"},
            {"text": "When he felt angry, spiky red flowers popped up everywhere!", "scene": "Felix with angry expression, red spiky flowers sprouting, steam from head"},
            {"text": "When he felt scared, little purple flowers curled up tight.", "scene": "Felix looking nervous, curled up purple flowers, shadows"},
            {"text": "When he felt calm, peaceful green leaves spread across the ground.", "scene": "Felix sitting peacefully, green leaves and calm flowers, peaceful garden"},
            {"text": "Felix learned that ALL his feelings were okay. Every flower belonged in his garden.", "scene": "Felix tending to all different colored flowers, accepting all emotions"},
            {"text": "Sometimes many feelings grew at once, and that was okay too!", "scene": "Felix surrounded by mixed emotion flowers, rainbow of feelings"},
            {"text": "\"My garden is beautiful,\" Felix smiled, \"because every feeling matters.\"\n\nThe End", "scene": "Felix standing proudly in full emotion garden, all colors blooming"}
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
        if "balance" in str(e).lower() or "budget" in str(e).lower():
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
    print("PICTURE BOOK BATCH - PART 3")
    print("="*60)
    
    books = [
        ("699adbe6176ebca750087f21", "The Alphabet Zoo"),
        ("699adbe6176ebca750087f23", "Safari Sam's Big Day"),
        ("699adbe6176ebca750087f2e", "Astronaut Alex's Moon Mission"),
        ("699adbe6176ebca750087f27", "The Feelings Garden"),
    ]
    
    for book_id, title in books:
        if title in BOOK_TEMPLATES:
            try:
                await complete_single_book(book_id, title, BOOK_TEMPLATES[title])
                if estimated_cost > 8.5:
                    print("\n⚠️ BUDGET WARNING")
                    break
            except Exception as e:
                if "BUDGET" in str(e):
                    print("\n🚨 BUDGET EXHAUSTED")
                    break
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {images_generated} images, ${estimated_cost:.2f}")

if __name__ == "__main__":
    asyncio.run(run_batch())
