#!/usr/bin/env python3
"""
Book Generation Script using OpenAI GPT-Image-1 via Emergent Key
"""

import asyncio
import os
import sys
import base64
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

# Book templates
BOOK_TEMPLATES = {
    "The Wizard's Apprentice": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, magical wizard theme, warm purples and golds, sparkly magical effects",
        "characters": {
            "main": "Finn, a young boy with messy red hair, big curious green eyes, wearing an oversized purple wizard robe and a crooked pointy hat"
        },
        "pages": [
            {"text": "The Wizard's Apprentice\n\nA Magical Story", "scene": "Title page: A young wizard apprentice in a magical tower surrounded by floating spell books"},
            {"text": "Finn was the wizard's new helper. Everything was new and magical!", "scene": "Finn arriving at a magical tower, eyes wide with wonder, spell books floating around"},
            {"text": "His first task: sort the spell ingredients. But the jars were talking!", "scene": "Finn surrounded by talking magical jars with faces, looking surprised"},
            {"text": "\"Careful with the moon dust!\" squeaked a tiny jar. POOF! Too late.", "scene": "Finn accidentally spilling sparkly moon dust everywhere, creating a mini galaxy"},
            {"text": "The broom started dancing! The cauldron began singing!", "scene": "Magical chaos with a dancing broom and singing cauldron, Finn laughing"},
            {"text": "\"Oh dear,\" said the wizard, but he was smiling. \"Magic is messy at first.\"", "scene": "Kind old wizard with long white beard smiling at the chaos, arm around Finn"},
            {"text": "Together they cleaned up, and Finn learned his first spell: Tidius Uppicus!", "scene": "Finn casting a cleaning spell, items floating back to their places"},
            {"text": "\"Every great wizard started just like you,\" the wizard said kindly.", "scene": "Wizard showing Finn old photos of himself making the same mistakes"},
            {"text": "Finn practiced every day. Some spells worked, some went SPLAT!", "scene": "Montage of Finn practicing, some successes and funny failures"},
            {"text": "And that's how the smallest apprentice became the bravest little wizard.\n\nThe End", "scene": "Finn proudly casting a beautiful spell, wizard clapping, magical celebration"}
        ]
    },
    
    "Fairies of Moonlight Meadow": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, ethereal fairy mood, silver moonlight with pastel flowers",
        "characters": {
            "main": "Luna, Dewdrop, and Sparkle - three tiny fairies with delicate wings"
        },
        "pages": [
            {"text": "Fairies of Moonlight Meadow\n\nA Bedtime Adventure", "scene": "Title page: Three tiny fairies dancing in a moonlit meadow with glowing flowers"},
            {"text": "When the moon rises high, the fairies come out to play in Moonlight Meadow.", "scene": "Beautiful meadow at night, fairies emerging from flower homes"},
            {"text": "Luna lights the path with her silver glow. She's the oldest and wisest.", "scene": "Luna fairy with silver wings creating a path of light"},
            {"text": "Dewdrop makes the flowers sparkle with morning dew, even at night!", "scene": "Dewdrop fairy touching flowers, making them shimmer with dew drops"},
            {"text": "Sparkle, the youngest, loves to play with fireflies and giggle!", "scene": "Sparkle fairy playing tag with fireflies, laughing"},
            {"text": "Tonight was special - they found a lost baby bunny!", "scene": "Fairies discovering a tiny lost bunny looking scared"},
            {"text": "\"Don't worry, little one,\" Luna whispered. \"We'll help you find home.\"", "scene": "Luna comforting the bunny while other fairies gather around"},
            {"text": "They followed the moonbeams through the meadow, past the sleepy owls.", "scene": "Fairies leading bunny through meadow, friendly owls watching"},
            {"text": "At last! The bunny's family was waiting by the old oak tree!", "scene": "Joyful reunion with bunny family, fairies watching happily"},
            {"text": "The fairies flew home as the sun peeked over the hills. Sweet dreams!\n\nThe End", "scene": "Fairies returning to flower homes as dawn breaks, peaceful ending"}
        ]
    },
    
    "Elves and the Magic Tree": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, enchanted forest mood, rich greens and autumn colors",
        "characters": {
            "main": "Acorn and Maple, twin elves with pointed ears and matching green tunics"
        },
        "pages": [
            {"text": "Elves and the Magic Tree\n\nA Tale of the Forest", "scene": "Title page: Two small elves standing before a magnificent glowing tree"},
            {"text": "Deep in the Whispering Woods lived two elf twins named Acorn and Maple.", "scene": "Twin elves in cozy treehouse home, forest morning"},
            {"text": "Their job was to care for the Great Magic Tree - the heart of the forest.", "scene": "Elves tending to enormous magical tree with glowing leaves"},
            {"text": "One morning, the tree looked sick. Its leaves were falling too soon!", "scene": "Worried elves looking at wilting magical tree, leaves dropping"},
            {"text": "\"We must find the Golden Acorn,\" said Maple. \"It will heal the tree!\"", "scene": "Elves looking at old map showing location of golden acorn"},
            {"text": "They searched high in the branches where the wise owl lived.", "scene": "Elves climbing high tree branches, talking to wise old owl"},
            {"text": "They searched low where the friendly mushrooms grew in circles.", "scene": "Elves among large colorful mushrooms, searching"},
            {"text": "Finally, they found it hidden in a squirrel's treasure collection!", "scene": "Elves discovering golden glowing acorn among squirrel's treasures"},
            {"text": "They planted it at the tree's roots. Golden light spread everywhere!", "scene": "Magical moment as golden light heals the tree, leaves regrow"},
            {"text": "The Great Tree bloomed brighter than ever. The forest was saved!\n\nThe End", "scene": "Celebratory scene with happy elves, healthy magical tree, forest creatures cheering"}
        ]
    },
    
    "The Backwards Day": {
        "age_range": "4-7",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, silly humorous mood, bold colors and exaggerated expressions",
        "characters": {
            "main": "Tommy, a 6-year-old boy with spiky brown hair, big goofy grin"
        },
        "pages": [
            {"text": "The Backwards Day\n\nA Silly Story", "scene": "Title page: Boy walking backwards with everything around him reversed, funny expressions"},
            {"text": "Tommy woke up and something felt strange. His pillow was at his feet!", "scene": "Tommy waking up upside down in bed, confused expression"},
            {"text": "\"Good night, Tommy!\" said Mom at breakfast. Wait, that's not right!", "scene": "Mom serving breakfast but saying goodnight, Tommy looking confused"},
            {"text": "Tommy put on his shirt backwards, his pants backwards, even his socks backwards!", "scene": "Tommy dressed completely backwards, looking pleased with himself"},
            {"text": "At school, everyone walked backwards. The teacher wrote on the board from right to left!", "scene": "Funny classroom scene with everyone walking backwards"},
            {"text": "They had dessert first, THEN vegetables! Tommy didn't mind that part.", "scene": "Tommy happily eating cake before broccoli, lunchroom chaos"},
            {"text": "During P.E., they ran the race backwards! Tommy won by coming last!", "scene": "Kids running backwards on track, Tommy celebrating"},
            {"text": "The end-of-day bell rang at the START of school. Everyone cheered!", "scene": "Kids cheering at morning bell, school in background"},
            {"text": "At home, Tommy said \"Hello!\" when leaving and \"Goodbye!\" when arriving.", "scene": "Tommy at front door confusing his family with reversed greetings"},
            {"text": "As Tommy fell asleep, he wondered: would tomorrow be Upside-Down Day?\n\nThe End", "scene": "Tommy in bed dreaming of upside-down world, silly smile"}
        ]
    },
    
    "Pirate Pete's Bad Hair Day": {
        "age_range": "4-7",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, pirate adventure mood, ocean blues with silly expressions",
        "characters": {
            "main": "Pirate Pete, a small pirate with an eye patch, big bushy beard, outrageous wild curly hair"
        },
        "pages": [
            {"text": "Pirate Pete's Bad Hair Day\n\nA Hairy Adventure", "scene": "Title page: Pirate with hilariously wild hair on a ship, crew laughing"},
            {"text": "Pirate Pete was the toughest pirate on the seven seas. But today, his hair was WILD!", "scene": "Pete looking in mirror at his crazy hair, looking distressed"},
            {"text": "He tried to brush it down. BOING! It popped right back up!", "scene": "Pete's hair springing back up after brushing, brush flying away"},
            {"text": "He tried a bandana. His hair ate it! Gulp!", "scene": "Hair seemingly swallowing the bandana, Pete shocked"},
            {"text": "He tried his best pirate hat. POP! The hair pushed it off into the ocean!", "scene": "Hat flying off Pete's head into ocean, shark catching it"},
            {"text": "\"Captain! We can't see the map!\" cried the crew. His hair covered everything!", "scene": "Crew trying to read map but Pete's hair is in the way"},
            {"text": "A seagull got stuck in his hair! Then another! Then three more!", "scene": "Multiple seagulls trapped in Pete's huge hair, chaos"},
            {"text": "Finally, a little girl on an island said, \"Have you tried... a scrunchie?\"", "scene": "Small girl on island beach offering a pink scrunchie"},
            {"text": "PERFECT! The scrunchie tamed the wild hair into a magnificent ponytail!", "scene": "Pete's hair in a neat ponytail, looking proud and fabulous"},
            {"text": "\"Thank ye, tiny landlubber!\" Pete sailed away, the fanciest pirate ever.\n\nThe End", "scene": "Pete sailing away with fabulous hair, crew admiring, little girl waving"}
        ]
    },
    
    "Dinosaur Dentist": {
        "age_range": "3-6",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, funny dinosaur theme, prehistoric setting with modern twist",
        "characters": {
            "main": "Dr. Dino, a small friendly dinosaur wearing a white coat and tiny glasses"
        },
        "pages": [
            {"text": "Dinosaur Dentist\n\nA Prehistoric Smile", "scene": "Title page: Small dinosaur dentist with big toothbrush next to T-Rex with toothache"},
            {"text": "Dr. Dino was the only dentist in all of Prehistoric Valley. And boy, was he busy!", "scene": "Tiny dinosaur dentist office with huge dinosaur patients waiting"},
            {"text": "First patient: T-Rex! \"Open wide!\" That's a LOT of teeth to clean!", "scene": "Tiny Dr. Dino climbing into giant T-Rex mouth with toothbrush"},
            {"text": "\"No more eating rocks, Rex. That's bad for your enamel!\"", "scene": "T-Rex looking guilty, pile of rocks nearby"},
            {"text": "Next: Triceratops! She had spinach stuck between her horns. Wait, wrong end!", "scene": "Dr. Dino accidentally checking Triceratops horns, both laughing"},
            {"text": "Brontosaurus had the longest neck. Dr. Dino needed a ladder!", "scene": "Dr. Dino on super tall ladder reaching Brontosaurus mouth"},
            {"text": "Stegosaurus kept wiggling! \"Hold still, you're ticklish!\"", "scene": "Stegosaurus laughing and wiggling, Dr. Dino bouncing around"},
            {"text": "The Pterodactyl flew in for a checkup. \"No cavities! You may fly!\"", "scene": "Pterodactyl in dental chair getting checked, happy result"},
            {"text": "By sunset, everyone had sparkly clean teeth. Even the volcano smiled!", "scene": "All dinosaurs smiling with sparkly teeth, happy volcano in background"},
            {"text": "\"Same time next millennium?\" asked Dr. Dino with a wink.\n\nThe End", "scene": "Dr. Dino waving goodbye to happy dinosaur patients at sunset"}
        ]
    },
}


async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    """Generate a single image using OpenAI GPT-Image-1"""
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality, high detail, kid-friendly."
    
    try:
        print(f"    Generating image...", end=" ", flush=True)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            with open(output_path, 'wb') as f:
                f.write(images[0])
            images_generated += 1
            estimated_cost += 0.04  # GPT-Image-1 approximate cost
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
    
    safe_title = title.lower().replace("'", "").replace(" ", "_").replace(":", "")
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
            import shutil
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
                import shutil
                shutil.copy(page_path, public_dir / f"page_{i+1:02d}.png")
        else:
            print(f"[Page {i+1}/{total}] Already exists")
        
        pages.append({
            "page_number": i + 1,
            "text": page["text"],
            "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.5)  # Delay between images
    
    # Generate back cover
    back_path = output_dir / "back_cover.png"
    if not back_path.exists():
        print("[Back]", end=" ")
        back_prompt = f"Back cover for children's book. {template['characters']['main']} in peaceful scene."
        if await generate_book_image(back_prompt, template["style_prompt"], back_path):
            import shutil
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
        print("ERROR: EMERGENT_LLM_KEY not found in environment!")
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
        if title in BOOK_TEMPLATES:
            books_to_generate.append({
                "id": str(book["_id"]),
                "title": title
            })
    
    print(f"Found {len(books_to_generate)} books with templates ready to generate:")
    for b in books_to_generate:
        print(f"  - {b['title']}")
    
    if not books_to_generate:
        print("\nNo books to generate!")
        return
    
    # Generate books
    print("\n--- GENERATING BOOKS ---")
    
    completed = 0
    BUDGET_LIMIT = 6.0  # Stop before exhausting budget
    
    for book_info in books_to_generate:
        if estimated_cost > BUDGET_LIMIT:
            print(f"\n BUDGET LIMIT: ${estimated_cost:.2f} spent. Stopping to preserve budget.")
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
            print(f"Error with {book_info['title']}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print(f"Books completed: {completed}")
    print(f"Images generated: {images_generated}")
    print(f"Estimated cost: ${estimated_cost:.2f}")
    
    # Count remaining
    remaining = await db.books.count_documents({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}]
    })
    print(f"Books still empty: {remaining}")


if __name__ == "__main__":
    asyncio.run(main())
