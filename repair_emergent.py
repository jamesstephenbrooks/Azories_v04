#!/usr/bin/env python3
"""
REPAIR SCRIPT - Using Emergent Key (GPT-Image-1)
Fixes 14 books: 5 broken + 9 empty
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

images_generated = 0
estimated_cost = 0.0
COST_PER_IMAGE = 0.04

image_gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)

# All 14 books that need repair/generation
BOOK_TEMPLATES = {
    # === 5 BROKEN BOOKS (partial images) ===
    "Elves and the Magic Tree": {
        "age_range": "3-6", "genre": "Fantasy", "art_style": "watercolour",
        "style_prompt": "Enchanted forest watercolour children's book illustration, elves, rich greens",
        "characters": {"main": "Acorn and Maple, twin elves with pointed ears and green tunics"},
        "pages": [
            {"text": "Elves and the Magic Tree", "scene": "Title page: Two elves before magnificent glowing tree"},
            {"text": "Twin elves lived in the Whispering Woods.", "scene": "Twin elves in cozy treehouse"},
            {"text": "Their job was caring for the Great Magic Tree.", "scene": "Elves tending to enormous magical tree"},
            {"text": "One morning, the tree looked sick!", "scene": "Worried elves looking at wilting tree"},
            {"text": "\"We must find the Golden Acorn!\"", "scene": "Elves looking at old map"},
            {"text": "They searched high where the wise owl lived.", "scene": "Elves climbing branches, talking to owl"},
            {"text": "They searched low where mushrooms grew.", "scene": "Elves among colorful mushrooms"},
            {"text": "They found it in a squirrel's collection!", "scene": "Elves discovering golden acorn"},
            {"text": "Golden light spread as they planted it!", "scene": "Magical golden light healing tree"},
            {"text": "The forest was saved!\n\nThe End", "scene": "Celebratory scene, healthy tree"}
        ]
    },
    
    "Pixie Dust Adventures": {
        "age_range": "3-6", "genre": "Fantasy", "art_style": "watercolour",
        "style_prompt": "Magical sparkly watercolour children's book illustration, pixie theme, pastels",
        "characters": {"main": "Pip, a tiny pixie with sparkling blue wings and purple hair"},
        "pages": [
            {"text": "Pixie Dust Adventures", "scene": "Title page: Tiny pixie flying through magical forest"},
            {"text": "Pip was the smallest pixie with blue wings.", "scene": "Pip in beautiful hollow with dewdrops"},
            {"text": "Every pixie had a job. But Pip didn't know hers.", "scene": "Other pixies working, Pip watching"},
            {"text": "\"I want to find my magic!\"", "scene": "Pip flying into mystical forest"},
            {"text": "She helped a ladybug missing her spots.", "scene": "Pip helping ladybug with pixie dust"},
            {"text": "A wilted flower bloomed with her dust!", "scene": "Pip making flower bloom"},
            {"text": "A grumpy toad's puddle turned sparkling!", "scene": "Pip transforming puddle"},
            {"text": "\"I make things HAPPY!\"", "scene": "Pip flying excitedly"},
            {"text": "The Queen smiled. \"The rarest gift.\"", "scene": "Queen crowning Pip"},
            {"text": "Pip's dust made the forest smile!\n\nThe End", "scene": "Pip over happy magical forest"}
        ]
    },
    
    "The Enchanted Carousel": {
        "age_range": "3-6", "genre": "Fantasy", "art_style": "watercolour",
        "style_prompt": "Whimsical vintage watercolour children's book, carousel, pastels and golden lights",
        "characters": {"main": "Mia, a 5-year-old girl with two dark braids"},
        "pages": [
            {"text": "The Enchanted Carousel", "scene": "Title page: Glowing carousel at twilight"},
            {"text": "Mia found an old carousel in the park.", "scene": "Mia discovering ornate carousel"},
            {"text": "She climbed onto a white horse. It began to spin!", "scene": "Mia on carousel horse, lights glowing"},
            {"text": "The horse winked! \"Hold tight!\"", "scene": "Horse winking, magical sparkles"},
            {"text": "WHOOSH! They flew into the sky!", "scene": "Carousel lifting into starry sky"},
            {"text": "They soared over candy mountains.", "scene": "Flying over magical candy landscape"},
            {"text": "They raced through cloud animals.", "scene": "Flying through cloud animals"},
            {"text": "\"Time to go home,\" the horse said.", "scene": "Horse and Mia descending"},
            {"text": "Mia held a magical flower.", "scene": "Mia holding glowing flower"},
            {"text": "\"Come back anytime.\"\n\nThe End", "scene": "Mia waving at carousel, sunset"}
        ]
    },
    
    "Captain Compass and the Treasure Map": {
        "age_range": "6-8", "genre": "Adventure", "art_style": "realistic",
        "style_prompt": "Detailed adventure children's book illustration, expedition theme, ocean",
        "characters": {"main": "Captain Compass (Emma), young adventurer with compass necklace"},
        "pages": [
            {"text": "Captain Compass and the Treasure Map", "scene": "Title page: Young captain holding map, ocean sunset"},
            {"text": "Emma found a dusty map in the attic.", "scene": "Emma in attic discovering map"},
            {"text": "\"I'm going to find that treasure!\"", "scene": "Emma with parrot, determined"},
            {"text": "She gathered her crew.", "scene": "Four young adventurers preparing"},
            {"text": "They sailed through Whispering Waves.", "scene": "Ship sailing, dolphins alongside"},
            {"text": "\"Storm ahead!\" Emma steered through.", "scene": "Emma steering through storm"},
            {"text": "The island appeared through mist!", "scene": "Ship approaching mysterious island"},
            {"text": "They followed the map through jungle.", "scene": "Kids hiking through jungle"},
            {"text": "The X marked a hidden cave!", "scene": "Kids entering cave"},
            {"text": "The treasure was ancient books!\n\nThe End", "scene": "Kids surrounded by glowing books"}
        ]
    },
    
    "The Jungle Explorers Club": {
        "age_range": "6-8", "genre": "Adventure", "art_style": "realistic",
        "style_prompt": "Detailed jungle expedition children's book illustration, lush greens",
        "characters": {"main": "The Jungle Explorers: Zara, Kai, and Bella"},
        "pages": [
            {"text": "The Jungle Explorers Club", "scene": "Title page: Three kids at jungle entrance"},
            {"text": "The Explorers wanted to discover something new!", "scene": "Kids in treehouse planning"},
            {"text": "Deep in the Amazon, they heard a strange sound.", "scene": "Kids in dense jungle"},
            {"text": "Kai spotted jaguar tracks!", "scene": "Kids examining paw prints"},
            {"text": "Bella found glowing mushrooms!", "scene": "Bioluminescent mushrooms"},
            {"text": "Zara saw a hidden waterfall!", "scene": "Zara pointing at waterfall"},
            {"text": "Behind it was a secret garden!", "scene": "Magical garden, color-changing flowers"},
            {"text": "A baby jaguar played there!", "scene": "Cute jaguar cub in garden"},
            {"text": "They promised to keep the secret.", "scene": "Kids making promise"},
            {"text": "A secret worth keeping.\n\nThe End", "scene": "Kids leaving, waterfall behind"}
        ]
    },
    
    # === 9 EMPTY BOOKS ===
    "Mountain Climbing Mice": {
        "age_range": "6-8", "genre": "Adventure", "art_style": "realistic",
        "style_prompt": "Detailed children's book illustration, tiny adventurous mice, mountains",
        "characters": {"main": "Marco and Mia, two brave mice in climbing gear"},
        "pages": [
            {"text": "Mountain Climbing Mice", "scene": "Title page: Two tiny mice at base of mountain"},
            {"text": "Marco and Mia looked up at Cheese Peak.", "scene": "Mice staring at massive peak"},
            {"text": "\"Mice CAN climb mountains!\"", "scene": "Determined mice beginning climb"},
            {"text": "First: Crumb Canyon rope bridge!", "scene": "Mice crossing rope bridge"},
            {"text": "Through the Forest of Giant Pines.", "scene": "Mice among enormous pine trees"},
            {"text": "A friendly eagle gave them a lift!", "scene": "Mice riding on eagle"},
            {"text": "The ice was slippery! Teamwork!", "scene": "Mice climbing ice together"},
            {"text": "At last, the summit!", "scene": "Mice at peak, triumphant"},
            {"text": "They planted a tiny flag.", "scene": "Mice planting flag at sunrise"},
            {"text": "Size doesn't matter!\n\nThe End", "scene": "Mice sliding down happily"}
        ]
    },
    
    "Space Station School": {
        "age_range": "6-8", "genre": "Science Fiction", "art_style": "realistic",
        "style_prompt": "Futuristic space station children's book illustration, blue and silver",
        "characters": {"main": "Nova, a 7-year-old in silver space suit"},
        "pages": [
            {"text": "Space Station School", "scene": "Title page: Space station orbiting Earth"},
            {"text": "Nova's classroom floated above Earth!", "scene": "Futuristic classroom, kids floating"},
            {"text": "Math: calculating asteroid speeds!", "scene": "Nova doing math with asteroids"},
            {"text": "Science: plants in zero gravity!", "scene": "Plants growing all directions"},
            {"text": "Lunch: catching floating food!", "scene": "Kids catching food spheres"},
            {"text": "PE was zero-G soccer!", "scene": "Zero gravity soccer"},
            {"text": "Art: painting Earth from above!", "scene": "Kids painting at easels"},
            {"text": "Nova's favorite: astronaut training!", "scene": "Nova in simulator"},
            {"text": "Watching shooting stars from bed.", "scene": "Kids watching meteors"},
            {"text": "\"Out of this world!\"\n\nThe End", "scene": "Nova writing in journal"}
        ]
    },
    
    "The Friendly Martians": {
        "age_range": "3-6", "genre": "Science Fiction", "art_style": "watercolour",
        "style_prompt": "Fun space watercolour children's book illustration, Mars, friendly aliens",
        "characters": {"main": "Ziggy and Zara, small green Martians with heart antennae"},
        "pages": [
            {"text": "The Friendly Martians", "scene": "Title page: Cute green Martians waving from Mars"},
            {"text": "Ziggy and Zara had rocks but no friends.", "scene": "Martians looking lonely on Mars"},
            {"text": "A spaceship landed! Out came Luna.", "scene": "Spaceship landing, girl stepping out"},
            {"text": "The Martians were scared at first.", "scene": "Martians hiding behind rocks"},
            {"text": "But Luna waved. \"Want to play?\"", "scene": "Luna waving, Martians curious"},
            {"text": "Hide and seek behind craters!", "scene": "Playing hide and seek on Mars"},
            {"text": "Sandcastles from red dust!", "scene": "Building Mars dust castles"},
            {"text": "Bouncing high in low gravity!", "scene": "All bouncing, laughing"},
            {"text": "\"Will you come back?\"", "scene": "Sad farewell at spaceship"},
            {"text": "\"Friends visit!\"\n\nThe End", "scene": "Luna waving from ship"}
        ]
    },
    
    "Gadget Girl and the Invention Fair": {
        "age_range": "6-8", "genre": "Science Fiction", "art_style": "cartoon",
        "style_prompt": "Bright STEM cartoon children's book illustration, inventions, workshop",
        "characters": {"main": "Gwen, 8-year-old inventor with goggles and tool belt"},
        "pages": [
            {"text": "Gadget Girl and the Invention Fair", "scene": "Title page: Inventor surrounded by gadgets"},
            {"text": "Gwen LOVED inventing!", "scene": "Gwen in messy workshop"},
            {"text": "The Fair was next week!", "scene": "Gwen looking at fair poster"},
            {"text": "Flying toaster? CRASH!", "scene": "Toaster flying chaotically"},
            {"text": "Homework robot? It ate it!", "scene": "Robot eating papers"},
            {"text": "Rocket shoes? UP but no DOWN!", "scene": "Gwen stuck on ceiling"},
            {"text": "She saw her brother struggling.", "scene": "Watching brother with backpack"},
            {"text": "IDEA! The Hover-Pack!", "scene": "Eureka moment"},
            {"text": "Kids LOVED it at the fair!", "scene": "Kids trying Hover-Pack"},
            {"text": "\"Help others.\"\n\nThe End", "scene": "Gwen with trophy"}
        ]
    },
    
    "The Secret Code Club": {
        "age_range": "6-8", "genre": "Mystery", "art_style": "realistic",
        "style_prompt": "Detailed mystery children's book illustration, codes, secret agent theme",
        "characters": {"main": "The Code Breakers: Sam, Lily, and Jake"},
        "pages": [
            {"text": "The Secret Code Club", "scene": "Title page: Kids with coded messages"},
            {"text": "They solved coded mysteries!", "scene": "Kids in tree house with code wheels"},
            {"text": "A strange note: GSRH RH GSV URMOW!", "scene": "Finding coded note in library"},
            {"text": "\"Substitution cipher!\"", "scene": "Kids working at table"},
            {"text": "THIS IS THE FIRST!", "scene": "Reading decoded message"},
            {"text": "Codes all over town!", "scene": "Kids finding notes everywhere"},
            {"text": "Five clues led to clock tower!", "scene": "Approaching clock tower"},
            {"text": "Inside: a time capsule!", "scene": "Opening old capsule"},
            {"text": "Same club - 50 years ago!", "scene": "Old photos inside"},
            {"text": "Their club's history!\n\nThe End", "scene": "Old photo next to new one"}
        ]
    },
    
    "Detective Daisy's First Case": {
        "age_range": "6-8", "genre": "Mystery", "art_style": "realistic",
        "style_prompt": "Cozy mystery children's book illustration, detective theme, warm home",
        "characters": {"main": "Daisy, 8-year-old with curly red hair and magnifying glass"},
        "pages": [
            {"text": "Detective Daisy's First Case", "scene": "Title page: Girl detective with magnifying glass"},
            {"text": "Daisy dreamed of being a detective.", "scene": "Daisy writing in notebook"},
            {"text": "Grandma's cookies vanished!", "scene": "Empty cookie jar"},
            {"text": "\"I'll take the case!\"", "scene": "Daisy putting on detective coat"},
            {"text": "Clue #1: Chocolate smudges!", "scene": "Following chocolate trail"},
            {"text": "Clue #2: Paw print on couch!", "scene": "Examining paw print"},
            {"text": "But the dog was outside!", "scene": "Daisy thinking"},
            {"text": "Clue #3: Giggling behind curtains!", "scene": "Approaching curtains"},
            {"text": "Little brother - chocolate everywhere!", "scene": "Brother caught"},
            {"text": "Case closed!\n\nThe End", "scene": "Family eating cookies"}
        ]
    },
    
    "The Backwards Day": {
        "age_range": "4-7", "genre": "Humour", "art_style": "cartoon",
        "style_prompt": "Bright silly cartoon children's book illustration, backwards theme",
        "characters": {"main": "Tommy, 6-year-old with spiky hair and goofy grin"},
        "pages": [
            {"text": "The Backwards Day", "scene": "Title page: Boy walking backwards"},
            {"text": "Tommy woke up. Pillow at his feet!", "scene": "Tommy upside down in bed"},
            {"text": "\"Good night!\" said Mom at breakfast.", "scene": "Mom at breakfast backwards"},
            {"text": "Tommy put everything on backwards!", "scene": "Tommy dressed backwards"},
            {"text": "At school, everyone walked backwards!", "scene": "Backwards classroom"},
            {"text": "Dessert first, THEN vegetables!", "scene": "Eating cake before broccoli"},
            {"text": "Running the race backwards!", "scene": "Kids running backwards"},
            {"text": "Bell rang at START of school!", "scene": "Kids cheering at bell"},
            {"text": "\"Hello\" when leaving!", "scene": "Tommy confusing family"},
            {"text": "Upside-Down Day tomorrow?\n\nThe End", "scene": "Tommy dreaming"}
        ]
    },
    
    "Pirate Pete's Bad Hair Day": {
        "age_range": "4-7", "genre": "Humour", "art_style": "cartoon",
        "style_prompt": "Bright pirate cartoon children's book illustration, ocean, silly",
        "characters": {"main": "Pirate Pete with eye patch and wild uncontrollable hair"},
        "pages": [
            {"text": "Pirate Pete's Bad Hair Day", "scene": "Title page: Pirate with wild hair"},
            {"text": "Pete was tough. But his hair was WILD!", "scene": "Pete looking at crazy hair"},
            {"text": "Brush it? BOING! It popped back!", "scene": "Hair springing back"},
            {"text": "Bandana? Hair ATE it!", "scene": "Hair swallowing bandana"},
            {"text": "Hat? POP! Into the ocean!", "scene": "Hat flying off"},
            {"text": "\"Captain! We can't see the map!\"", "scene": "Crew blocked by hair"},
            {"text": "Seagulls got stuck!", "scene": "Seagulls trapped in hair"},
            {"text": "A girl offered a scrunchie.", "scene": "Girl with pink scrunchie"},
            {"text": "PERFECT! Magnificent ponytail!", "scene": "Pete with fabulous ponytail"},
            {"text": "Fanciest pirate ever!\n\nThe End", "scene": "Pete sailing away"}
        ]
    },
    
    "Dinosaur Dentist": {
        "age_range": "3-6", "genre": "Humour", "art_style": "cartoon",
        "style_prompt": "Funny dinosaur cartoon children's book illustration, prehistoric modern",
        "characters": {"main": "Dr. Dino, small friendly dinosaur in white coat"},
        "pages": [
            {"text": "Dinosaur Dentist", "scene": "Title page: Small dentist with big toothbrush"},
            {"text": "Dr. Dino was the only dentist!", "scene": "Tiny office, huge patients"},
            {"text": "T-Rex first! LOT of teeth!", "scene": "Dr. Dino in T-Rex mouth"},
            {"text": "\"No more eating rocks!\"", "scene": "T-Rex looking guilty"},
            {"text": "Triceratops - wrong end!", "scene": "Checking horns by mistake"},
            {"text": "Brontosaurus needed a TALL ladder!", "scene": "Super tall ladder"},
            {"text": "Stegosaurus kept wiggling!", "scene": "Stegosaurus laughing"},
            {"text": "Pterodactyl: \"No cavities!\"", "scene": "Pterodactyl in chair"},
            {"text": "Everyone had sparkly teeth!", "scene": "Dinosaurs smiling"},
            {"text": "\"Same time next millennium?\"\n\nThe End", "scene": "Dr. Dino waving goodbye"}
        ]
    },
}


async def generate_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality, no text."
    
    try:
        print(f".", end="", flush=True)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            with open(output_path, 'wb') as f:
                f.write(images[0])
            images_generated += 1
            estimated_cost += COST_PER_IMAGE
            return True
        return False
    except Exception as e:
        error = str(e).lower()
        if "balance" in error or "budget" in error or "insufficient" in error:
            raise Exception("BUDGET_EXHAUSTED")
        print(f"!", end="", flush=True)
        return False


async def repair_book(book_id: str, title: str, template: dict, db):
    global estimated_cost
    
    print(f"\n[{title}] ", end="")
    
    safe_title = title.lower().replace("'", "").replace(" ", "_").replace(":", "").strip()
    output_dir = CONTENT_DIR / safe_title
    output_dir.mkdir(parents=True, exist_ok=True)
    
    public_dir = PUBLIC_DIR / safe_title
    if public_dir.exists():
        shutil.rmtree(public_dir)
    public_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    
    # Cover
    cover_path = output_dir / "cover.png"
    cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}."
    await generate_image(cover_prompt, template["style_prompt"], cover_path)
    if cover_path.exists():
        shutil.copy(cover_path, public_dir / "cover.png")
    
    # Pages
    for i, page in enumerate(template["pages"]):
        page_path = output_dir / f"page_{i+1:02d}.png"
        scene = f"{page['scene']}. Character: {template['characters']['main']}"
        await generate_image(scene, template["style_prompt"], page_path)
        if page_path.exists():
            shutil.copy(page_path, public_dir / f"page_{i+1:02d}.png")
        
        pages.append({
            "page_number": i + 1,
            "text": page["text"],
            "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.3)
    
    # Back cover
    back_path = output_dir / "back_cover.png"
    await generate_image(f"Back cover: {template['characters']['main']} peaceful scene", 
                        template["style_prompt"], back_path)
    if back_path.exists():
        shutil.copy(back_path, public_dir / "back_cover.png")
    
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
            "genre": template["genre"],
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    print(f" ✓ (${estimated_cost:.2f})")
    return True


async def main():
    global estimated_cost
    
    print("="*60)
    print("REPAIR: 14 books using Emergent Key (GPT-Image-1)")
    print("Estimated cost: ~$6.72")
    print("="*60)
    
    if not EMERGENT_KEY:
        print("ERROR: EMERGENT_LLM_KEY not found!")
        return
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # First reset the 5 broken books that have bad DB entries
    broken_titles = [
        "Elves and the Magic Tree",
        "Pixie Dust Adventures", 
        "The Enchanted Carousel",
        "Captain Compass and the Treasure Map",
        "The Jungle Explorers Club"
    ]
    
    for title in broken_titles:
        await db.books.update_one(
            {"title": title},
            {"$set": {"pages": [], "cover_image_url": None}}
        )
    
    # Get all books needing repair
    cursor = db.books.find({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}],
        "title": {"$in": list(BOOK_TEMPLATES.keys())}
    }, {"title": 1, "_id": 1})
    
    books = []
    async for book in cursor:
        if book.get("title") in BOOK_TEMPLATES:
            books.append({"id": str(book["_id"]), "title": book["title"]})
    
    print(f"\nBooks to repair: {len(books)}")
    
    repaired = 0
    for book in books:
        try:
            await repair_book(book["id"], book["title"], BOOK_TEMPLATES[book["title"]], db)
            repaired += 1
        except Exception as e:
            if "BUDGET" in str(e):
                print(f"\n⚠️ BUDGET EXHAUSTED at ${estimated_cost:.2f}")
                break
            print(f" ERROR: {e}")
    
    print("\n" + "="*60)
    print(f"COMPLETE: {repaired}/{len(books)} books repaired")
    print(f"Images: {images_generated} | Cost: ${estimated_cost:.2f}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
