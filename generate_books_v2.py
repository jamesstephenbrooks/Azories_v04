#!/usr/bin/env python3
"""
Book Generation Script using OpenAI GPT-Image-1 via Emergent Key
Generates books that exist in the database but have no content
"""

import asyncio
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from bson import ObjectId

APP_DIR = Path(__file__).parent
BACKEND_DIR = APP_DIR / 'backend'
CONTENT_DIR = APP_DIR / 'content' / 'books' / 'completed'
PUBLIC_DIR = APP_DIR / 'frontend' / 'public' / 'book-assets'

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / '.env')

sys.path.insert(0, str(BACKEND_DIR))
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Tracking
images_generated = 0
estimated_cost = 0.0

# Initialize image generator
image_gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)

# Book templates matching actual database titles
BOOK_TEMPLATES = {
    "The Monster Who Was Scared of Kids": {
        "age_range": "3-6",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, funny monster theme, friendly and not scary",
        "characters": {
            "main": "Momo, a big fluffy purple monster with tiny horns, huge scared eyes, and wobbly legs"
        },
        "pages": [
            {"text": "The Monster Who Was Scared of Kids\n\nA Not-So-Scary Story", "scene": "Title page: A big fluffy purple monster hiding behind a tree, peeking nervously at a playground"},
            {"text": "Momo was the biggest monster in Monster Town. But he had a secret...", "scene": "Big fluffy purple monster in a monster village, looking nervous"},
            {"text": "He was TERRIFIED of children! \"They're so loud and fast!\" he whispered.", "scene": "Monster hiding under bed, imagining children running around"},
            {"text": "One day, a little girl named Lily got lost in Monster Town.", "scene": "Small girl looking around curiously in a monster town"},
            {"text": "\"AHHH!\" screamed Momo. \"AHHH!\" screamed Lily. Then they both laughed.", "scene": "Monster and girl both screaming then laughing together"},
            {"text": "\"You're not scary at all!\" said Lily. \"You're fluffy like a teddy bear!\"", "scene": "Lily hugging the fluffy monster, both smiling"},
            {"text": "Momo helped Lily find her way home. She held his big fuzzy paw.", "scene": "Monster and girl walking together, holding hands"},
            {"text": "\"Will you visit me?\" asked Lily. Momo was scared... but also excited.", "scene": "Momo looking nervously but happily at Lily's house"},
            {"text": "Now Momo visits Lily every week for tea and cookies. He's still a little scared...", "scene": "Monster having tea party with Lily, looking happy but nervous"},
            {"text": "But Lily always makes him feel brave. Sometimes friends help us be courageous!\n\nThe End", "scene": "Monster and girl playing happily together, rainbow in background"}
        ]
    },
    
    "Seasons of the Magic Forest": {
        "age_range": "3-6",
        "genre": "General",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, nature mood, changing seasonal colors",
        "characters": {
            "main": "Willow, a young forest sprite with leaf-green hair that changes with seasons"
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
    },
    
    "Robot Best Friend": {
        "age_range": "4-7",
        "genre": "Science Fiction",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, friendly robot theme, futuristic but warm",
        "characters": {
            "main": "Beep, a small round robot with big blue eyes, antenna with a heart, and little wheels"
        },
        "pages": [
            {"text": "Robot Best Friend\n\nA Story About Friendship", "scene": "Title page: Cute small robot holding hands with a young boy, hearts around them"},
            {"text": "Tommy got a robot for his birthday! \"Hello! I am Beep!\" it said.", "scene": "Boy excitedly opening gift box with cute robot inside"},
            {"text": "Beep could do amazing things! He could fly, glow, and even make breakfast!", "scene": "Robot flying, glowing, making pancakes, boy watching amazed"},
            {"text": "But Beep didn't know how to play. \"What is... fun?\" he asked.", "scene": "Robot looking confused at toys, boy thinking"},
            {"text": "Tommy taught Beep to play catch. BONK! The ball hit Beep's head. They both laughed!", "scene": "Ball bouncing off robot's head, both laughing"},
            {"text": "Beep learned to ride bikes, build sandcastles, and even have water balloon fights!", "scene": "Montage of robot and boy doing fun activities together"},
            {"text": "One day, Tommy was sad. His goldfish had gone to fish heaven.", "scene": "Tommy looking sad, empty fishbowl, robot concerned"},
            {"text": "Beep couldn't fix sadness with buttons. So he just sat next to Tommy quietly.", "scene": "Robot sitting quietly next to sad boy, being supportive"},
            {"text": "\"Thanks, Beep,\" Tommy sniffled. \"You're my best friend.\" Beep's heart light glowed bright.", "scene": "Boy hugging robot, robot's heart antenna glowing brightly"},
            {"text": "Beep learned the best thing he could do wasn't flying or glowing—it was just being there.\n\nThe End", "scene": "Boy and robot watching sunset together, friends forever"}
        ]
    },
    
    "Sky Pirates of Cloudland": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration, steampunk sky pirate theme, fluffy clouds and airships",
        "characters": {
            "main": "Captain Cloud and her crew: Misty the navigator and Thunder the lookout"
        },
        "pages": [
            {"text": "Sky Pirates of Cloudland\n\nAn Adventure Above the Clouds", "scene": "Title page: Magnificent airship sailing through clouds, young captain at the wheel"},
            {"text": "High above the world, where clouds are solid enough to walk on, lived the Sky Pirates!", "scene": "Amazing cloudland with floating islands and airships"},
            {"text": "Captain Cloud was the youngest captain ever. Her ship, The Nimbus, was the fastest!", "scene": "Young captain on deck of beautiful airship, clouds streaming past"},
            {"text": "\"Captain! Storm Giants ahead!\" called Thunder from the crow's nest.", "scene": "Lookout spotting massive storm clouds that look like giants"},
            {"text": "\"All hands on deck! We fly THROUGH them!\" Captain Cloud commanded.", "scene": "Crew preparing as ship heads toward storm clouds"},
            {"text": "The Nimbus dove and spun through lightning and thunder. What a ride!", "scene": "Airship dramatically navigating through storm, crew holding on"},
            {"text": "They found what they were looking for—the Rainbow Waterfall, hidden behind the storms!", "scene": "Breathtaking rainbow waterfall pouring from clouds"},
            {"text": "The waterfall's mist made everything sparkle. Even their sails turned rainbow-colored!", "scene": "Ship with rainbow sails, crew amazed by the beauty"},
            {"text": "They collected rainbow water—the most precious treasure in Cloudland.", "scene": "Crew carefully collecting sparkling rainbow water in bottles"},
            {"text": "\"Best adventure yet!\" cheered the crew as they sailed into the sunset.\n\nThe End", "scene": "Rainbow ship sailing into golden sunset clouds, happy crew waving"}
        ]
    },
    
    "The Superhero School": {
        "age_range": "6-8",
        "genre": "Superhero",
        "art_style": "cartoon",
        "style_prompt": "Bold dynamic cartoon children's book illustration, superhero comic style, bright action colors",
        "characters": {
            "main": "Zoe, a new student with wild curly hair and a cape that's too big for her"
        },
        "pages": [
            {"text": "The Superhero School\n\nWhere Heroes Learn to Fly", "scene": "Title page: Exciting school building with kids flying and using powers"},
            {"text": "Zoe's first day at Hero Academy was SCARY. Everyone had cool powers!", "scene": "Nervous girl at school gates, other kids flying and shooting lasers"},
            {"text": "Max could fly. Lily had super strength. Jake could turn invisible!", "scene": "Kids showing off their powers, Zoe watching uncertainly"},
            {"text": "\"What's YOUR power?\" they asked. Zoe didn't know yet. \"I'm still figuring it out...\"", "scene": "Kids crowding around Zoe, who looks embarrassed"},
            {"text": "In Power Class, nothing happened. No flying. No lasers. Nothing.", "scene": "Zoe trying hard but nothing happening, teacher encouraging"},
            {"text": "But during lunch, a bully was being mean to a small kid. Zoe stepped in.", "scene": "Zoe standing up to bigger kid, protecting smaller student"},
            {"text": "\"That's not cool,\" she said bravely. Everyone stopped. The bully walked away.", "scene": "Zoe standing firm, others watching with respect"},
            {"text": "\"Zoe! You have the power of COURAGE!\" said the headmaster. \"The rarest power of all!\"", "scene": "Headmaster announcing Zoe's power, students cheering"},
            {"text": "Zoe learned that being brave doesn't mean you're not scared—it means you do the right thing anyway.", "scene": "Zoe helping others, inspiring classmates"},
            {"text": "She became the hero everyone looked up to—not for what she could do, but for who she was.\n\nThe End", "scene": "Zoe with friends, cape finally fitting, confident pose"}
        ]
    },
    
    "The Case of the Missing Cookies": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration, cozy detective mystery mood, warm kitchen and home setting",
        "characters": {
            "main": "Detective Daisy, a clever girl with a magnifying glass and a notebook full of clues"
        },
        "pages": [
            {"text": "The Case of the Missing Cookies\n\nA Delicious Mystery", "scene": "Title page: Girl detective examining empty cookie jar with magnifying glass"},
            {"text": "Grandma's famous chocolate chip cookies had vanished! Only crumbs remained.", "scene": "Empty cookie jar on counter, crumbs scattered around"},
            {"text": "\"This is a job for Detective Daisy!\" She grabbed her magnifying glass.", "scene": "Daisy putting on detective hat, looking determined"},
            {"text": "Clue #1: Chocolate smudges on the kitchen counter leading to... the living room!", "scene": "Daisy following chocolate trail with magnifying glass"},
            {"text": "Clue #2: A chocolate paw print on the couch! Could it be the dog?", "scene": "Daisy examining paw print on couch cushion"},
            {"text": "But wait—the dog was outside the whole time! Who else could it be?", "scene": "Daisy looking out window at dog in yard, thinking"},
            {"text": "Clue #3: Suspicious giggling coming from behind the curtains!", "scene": "Daisy approaching curtains, hearing giggles"},
            {"text": "\"AHA!\" She found her little brother with chocolate all over his face!", "scene": "Little brother caught with chocolate evidence everywhere"},
            {"text": "\"Case closed!\" But Daisy couldn't be mad—he saved one cookie for her.", "scene": "Little brother offering last cookie, both smiling"},
            {"text": "They shared the cookie and promised to ask next time. Mystery solved!\n\nThe End", "scene": "Both kids eating cookies with Grandma, everyone happy"}
        ]
    },
}


async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    """Generate a single image using OpenAI GPT-Image-1"""
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality, high detail, kid-friendly."
    
    try:
        print(f"    Generating...", end=" ", flush=True)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            with open(output_path, 'wb') as f:
                f.write(images[0])
            images_generated += 1
            estimated_cost += 0.04
            print("OK")
            return True
        print("FAILED - No image returned")
        return False
    except Exception as e:
        error = str(e).lower()
        if "balance" in error or "budget" in error or "insufficient" in error or "quota" in error:
            raise Exception("BUDGET_EXHAUSTED")
        print(f"FAILED - {str(e)[:80]}")
        return False


async def complete_single_book(book_id: str, title: str, template: dict, db):
    """Complete a single book with images and database update"""
    global estimated_cost
    
    print(f"\n{'='*60}")
    print(f"GENERATING: {title}")
    print(f"Style: {template['art_style']}, Age: {template['age_range']}")
    print(f"{'='*60}")
    
    safe_title = title.lower().replace("'", "").replace(" ", "_").replace(":", "").strip()
    output_dir = CONTENT_DIR / safe_title
    output_dir.mkdir(parents=True, exist_ok=True)
    
    public_dir = PUBLIC_DIR / safe_title
    public_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    total = len(template["pages"])
    
    # Generate cover
    cover_path = output_dir / "cover.png"
    if not cover_path.exists():
        print(f"[Cover]", end=" ")
        cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}. Beautiful title space at top."
        if await generate_book_image(cover_prompt, template["style_prompt"], cover_path):
            shutil.copy(cover_path, public_dir / "cover.png")
    else:
        print(f"[Cover] Already exists")
    
    # Generate pages
    for i, page in enumerate(template["pages"]):
        page_path = output_dir / f"page_{i+1:02d}.png"
        
        if not page_path.exists():
            print(f"[Page {i+1}/{total}]", end=" ")
            scene_prompt = f"{page['scene']}. Character: {template['characters']['main']}"
            if await generate_book_image(scene_prompt, template["style_prompt"], page_path):
                shutil.copy(page_path, public_dir / f"page_{i+1:02d}.png")
        else:
            print(f"[Page {i+1}/{total}] Already exists")
        
        pages.append({
            "page_number": i + 1,
            "text": page["text"],
            "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.5)
    
    # Generate back cover
    back_path = output_dir / "back_cover.png"
    if not back_path.exists():
        print("[Back]", end=" ")
        back_prompt = f"Back cover for children's book. {template['characters']['main']} in peaceful scene."
        if await generate_book_image(back_prompt, template["style_prompt"], back_path):
            shutil.copy(back_path, public_dir / "back_cover.png")
    else:
        print("[Back] Already exists")
    
    # Update database
    await db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {
            "pages": pages,
            "cover_image_url": f"/book-assets/{safe_title}/cover.png",
            "page_count": len(pages),
            "status": "published",
            "art_style": template["art_style"],
            "age_range": template["age_range"],
            "genre": template["genre"],
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    print(f"\nBook Complete! Total cost so far: ${estimated_cost:.2f}")
    return True


async def main():
    global estimated_cost
    
    print("="*60)
    print("BOOK GENERATION (OpenAI GPT-Image-1)")
    print("="*60)
    
    if not EMERGENT_KEY:
        print("ERROR: EMERGENT_LLM_KEY not found!")
        return
    
    print(f"Using Emergent Key: {EMERGENT_KEY[:15]}...")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get empty books that have templates
    cursor = db.books.find({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}]
    }, {"title": 1, "_id": 1})
    
    books_to_generate = []
    async for book in cursor:
        title = book.get("title")
        if title and title.strip() in BOOK_TEMPLATES:
            books_to_generate.append({
                "id": str(book["_id"]),
                "title": title.strip()
            })
    
    print(f"Found {len(books_to_generate)} books with templates:")
    for b in books_to_generate:
        print(f"  - {b['title']}")
    
    if not books_to_generate:
        print("\nNo matching books found!")
        print("\nAvailable templates:")
        for t in BOOK_TEMPLATES.keys():
            print(f"  - {t}")
        return
    
    # Generate books
    print("\n--- GENERATING ---")
    
    completed = 0
    BUDGET_LIMIT = 5.0
    
    for book_info in books_to_generate:
        if estimated_cost > BUDGET_LIMIT:
            print(f"\n BUDGET LIMIT: ${estimated_cost:.2f}. Stopping.")
            break
        
        try:
            await complete_single_book(
                book_info["id"],
                book_info["title"],
                BOOK_TEMPLATES[book_info["title"]],
                db
            )
            completed += 1
        except Exception as e:
            if "BUDGET" in str(e):
                print(f"\n BUDGET EXHAUSTED")
                break
            print(f"Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"Books completed: {completed}")
    print(f"Images generated: {images_generated}")
    print(f"Est. cost: ${estimated_cost:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
