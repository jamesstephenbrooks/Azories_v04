#!/usr/bin/env python3
"""
Book Generation Script - Batch 3
Priority: Super Silly Superhero, Colors of the World, then remaining books
Using OpenAI GPT-Image-1 via Emergent Key
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

image_gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)

# Priority 1: Duplicate survivors
# Priority 2: Picture Books
# Priority 3: Others

BOOK_TEMPLATES = {
    # === PRIORITY 1: DUPLICATE SURVIVORS ===
    "Super Silly Superhero": {
        "age_range": "3-6",
        "genre": "Comic",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful comic book style children's illustration, bold lines, action poses, fun superhero theme",
        "characters": {
            "main": "Captain Giggles, a small superhero with a too-big cape, mismatched boots, a crooked mask, and the silliest grin"
        },
        "pages": [
            {"text": "Super Silly Superhero\n\nThe Goofiest Hero Ever!", "scene": "Title page: Silly superhero flying upside down with cape over face"},
            {"text": "Captain Giggles wasn't like other superheroes. His cape was always inside out!", "scene": "Captain Giggles with cape on backwards, looking confused but happy"},
            {"text": "His super power? Making everyone laugh! Even the grumpiest villains!", "scene": "Captain Giggles making a funny face at a grumpy villain who starts smiling"},
            {"text": "One day, the Frown Monster came to town. Nobody could smile!", "scene": "Dark cloud-like Frown Monster hovering over sad-looking town"},
            {"text": "\"I'll save the day!\" shouted Captain Giggles. Then he tripped on his cape.", "scene": "Captain Giggles tripping, cape tangled, arms flailing comedically"},
            {"text": "He tried to fly but went sideways. BONK! Right into a jello truck!", "scene": "Captain Giggles covered in colorful jello, looking surprised"},
            {"text": "The Frown Monster tried not to laugh. But Captain Giggles did a silly dance!", "scene": "Captain Giggles doing ridiculous jello-covered dance, Monster cracking a smile"},
            {"text": "\"Stop it! I can't... hehe... stop... HAHAHA!\" The monster burst out laughing!", "scene": "Frown Monster laughing uncontrollably, turning from dark to colorful"},
            {"text": "When the monster laughed, it turned into a rainbow! The town smiled again!", "scene": "Monster transformed into rainbow, townspeople cheering and laughing"},
            {"text": "Captain Giggles saved the day - the silliest way possible!\n\nThe End", "scene": "Captain Giggles proudly posing (still covered in jello), everyone celebrating"}
        ]
    },
    
    "Colors of the World": {
        "age_range": "3-6",
        "genre": "General",
        "art_style": "watercolour",
        "style_prompt": "Beautiful soft watercolour children's book illustration, vibrant colors, educational yet magical feel",
        "characters": {
            "main": "Rainbow, a magical paintbrush with sparkly bristles who brings color to everything"
        },
        "pages": [
            {"text": "Colors of the World\n\nA Colorful Journey", "scene": "Title page: Magical paintbrush flying over a colorful globe"},
            {"text": "Rainbow the paintbrush loved to travel the world and find beautiful colors!", "scene": "Magical paintbrush with wings flying joyfully over mountains and oceans"},
            {"text": "In Africa, she found the golden YELLOW of the savanna at sunset.", "scene": "African savanna at sunset, golden yellows, giraffes and elephants silhouetted"},
            {"text": "In the ocean, she discovered the deep BLUE where whales sing.", "scene": "Deep blue ocean with friendly whale, magical underwater scene"},
            {"text": "The forests taught her about GREEN - from bright lime to deep emerald.", "scene": "Lush green forest with various shades of green, magical mushrooms"},
            {"text": "Autumn leaves showed her RED and ORANGE dancing in the wind.", "scene": "Beautiful autumn scene with red and orange leaves swirling"},
            {"text": "Snow-capped mountains sparkled with WHITE so bright it glowed!", "scene": "Majestic snowy mountains with sparkling white snow"},
            {"text": "Flowers shared their PURPLE and PINK in gardens around the world.", "scene": "Magical garden with purple and pink flowers from different cultures"},
            {"text": "\"Every color is special,\" Rainbow smiled. \"Just like every person!\"", "scene": "Paintbrush surrounded by all colors forming a beautiful rainbow"},
            {"text": "And when all colors come together, they make our world beautiful!\n\nThe End", "scene": "Children of different cultures holding hands under a rainbow, world map behind"}
        ]
    },
    
    # === PRIORITY 2: PICTURE BOOKS ===
    "Numbers Come Alive": {
        "age_range": "3-6",
        "genre": "General",
        "art_style": "cartoon",
        "style_prompt": "Bright educational cartoon children's book illustration, friendly number characters, fun math theme",
        "characters": {
            "main": "The Number Friends: One (tall and proud), Two (twins), Three (triangle-shaped), and so on"
        },
        "pages": [
            {"text": "Numbers Come Alive\n\nLet's Count!", "scene": "Title page: Friendly numbers 1-10 as cartoon characters waving"},
            {"text": "ONE stood tall and proud. \"I'm the first! I start everything!\"", "scene": "Number 1 character standing tall with a crown, proud pose"},
            {"text": "TWO were twins who did everything together. \"We're a pair!\"", "scene": "Two identical number 2 characters holding hands, smiling"},
            {"text": "THREE loved triangles. \"Three sides, three corners, three is fun!\"", "scene": "Number 3 character juggling triangles, pyramid in background"},
            {"text": "FOUR was strong like a table. \"Four legs keep everything steady!\"", "scene": "Number 4 character as sturdy table, balancing things"},
            {"text": "FIVE gave high-fives! \"Count my fingers - one, two, three, four, FIVE!\"", "scene": "Number 5 character with hand up for high-five, energetic"},
            {"text": "SIX, SEVEN, EIGHT, NINE all joined the party!", "scene": "Numbers 6-9 dancing and playing together at a party"},
            {"text": "And TEN? Ten was the leader! \"Together we make counting fun!\"", "scene": "Number 10 character with cape leading the number parade"},
            {"text": "\"When you see us in the world, say hello!\" they cheered.", "scene": "Numbers appearing in everyday objects - clock, calendar, price tags"},
            {"text": "Now YOU can count too! 1, 2, 3... go!\n\nThe End", "scene": "All numbers together forming a happy group, encouraging kids to count"}
        ]
    },
    
    "Shapes in the City": {
        "age_range": "3-6",
        "genre": "General",
        "art_style": "cartoon",
        "style_prompt": "Modern colorful cartoon children's book illustration, geometric shapes as characters, urban cityscape",
        "characters": {
            "main": "Shelly the Circle, Sammy the Square, and Trixie the Triangle"
        },
        "pages": [
            {"text": "Shapes in the City\n\nFinding Shapes Everywhere!", "scene": "Title page: Friendly shape characters exploring a colorful city"},
            {"text": "Shelly the Circle loved rolling through the city. \"I'm everywhere!\"", "scene": "Circle character rolling past wheels, clocks, and manhole covers"},
            {"text": "\"Look! I'm in the sun, in pizzas, in coins!\" Shelly spun happily.", "scene": "Circle showing off - sun, pizza, coins all highlighted as circles"},
            {"text": "Sammy the Square was proud too. \"Buildings need me!\"", "scene": "Square character pointing at windows, doors, and building blocks"},
            {"text": "\"Windows, boxes, tiles - I make things strong and neat!\"", "scene": "Square shapes highlighted in city architecture"},
            {"text": "Trixie the Triangle climbed high. \"I'm on top of everything!\"", "scene": "Triangle character on rooftops, showing roof peaks and road signs"},
            {"text": "\"Rooftops, pizza slices, mountains - I reach for the sky!\"", "scene": "Triangle shapes in city - yield signs, roof peaks, party hats"},
            {"text": "\"Let's work together!\" they said. And they built amazing things!", "scene": "Shapes combining to build a colorful playground"},
            {"text": "Houses, cars, parks - all made from shapes working as friends.", "scene": "City scene with all shapes highlighted in buildings and objects"},
            {"text": "Now look around YOU! What shapes can you find?\n\nThe End", "scene": "Shapes waving goodbye, encouraging kids to find shapes around them"}
        ]
    },
    
    "Bedtime in the Animal World": {
        "age_range": "3-6",
        "genre": "General",
        "art_style": "watercolour",
        "style_prompt": "Soft dreamy watercolour children's book illustration, peaceful nighttime scenes, cute sleepy animals",
        "characters": {
            "main": "Various baby animals getting ready for bed around the world"
        },
        "pages": [
            {"text": "Bedtime in the Animal World\n\nTime to Sleep", "scene": "Title page: Moon rising over peaceful world, sleepy animals silhouetted"},
            {"text": "When the sun sets, animals everywhere get ready for bed.", "scene": "Beautiful sunset with animals yawning"},
            {"text": "Baby bears snuggle in their warm dens. \"Good night, mama bear.\"", "scene": "Cozy bear den with mama bear and cubs cuddling"},
            {"text": "Little owls wake up! Bedtime for them is when WE wake up!", "scene": "Baby owls opening eyes as moon rises, looking alert"},
            {"text": "Bunnies hop to their burrows. Soft grass makes the best beds!", "scene": "Bunny family settling into cozy underground burrow"},
            {"text": "Fish rest in quiet waters. Even the ocean gets sleepy.", "scene": "Peaceful underwater scene with fish resting among coral"},
            {"text": "Puppies curl up in balls. Their paws twitch - they're dreaming!", "scene": "Adorable puppy curled up, paws twitching in dreams"},
            {"text": "Kittens purr and stretch. They've played hard and now they rest.", "scene": "Sleepy kitten stretched out, peaceful expression"},
            {"text": "Birds tuck heads under wings. The nest is quiet and warm.", "scene": "Bird family in nest, babies tucked under mother's wing"},
            {"text": "And somewhere, a little one like YOU is getting sleepy too. Sweet dreams!\n\nThe End", "scene": "Peaceful nighttime scene with moon, stars, and sleeping animals"}
        ]
    },
    
    # === FANTASY ===
    "The Journey to Merlden": {
        "age_range": "6-8",
        "genre": "Fantasy",
        "art_style": "realistic",
        "style_prompt": "Detailed fantasy children's book illustration, magical kingdom, epic adventure feel",
        "characters": {
            "main": "Finn, a brave young traveler with a magical compass that points to where he's needed most"
        },
        "pages": [
            {"text": "The Journey to Merlden\n\nAn Epic Quest", "scene": "Title page: Young traveler looking at distant magical kingdom on floating islands"},
            {"text": "Finn's compass spun wildly one morning. It pointed to Merlden - the hidden kingdom!", "scene": "Finn holding glowing compass, needle spinning towards distant mountains"},
            {"text": "\"The kingdom needs help,\" the compass whispered. \"Only you can save them.\"", "scene": "Compass glowing with magical light, Finn looking determined"},
            {"text": "The path led through the Whispering Woods where trees told secrets.", "scene": "Finn walking through mystical forest with talking trees"},
            {"text": "He crossed the Bridge of Stars that only appeared at twilight.", "scene": "Finn crossing a bridge made of starlight over a deep canyon"},
            {"text": "The Crystal Caves glittered with a thousand colors. A friendly dragon guided him through.", "scene": "Finn and small friendly dragon in spectacular crystal cave"},
            {"text": "At last, Merlden appeared - a kingdom of towers and waterfalls!", "scene": "Magnificent floating kingdom with waterfalls and towers"},
            {"text": "The queen was trapped in an enchanted sleep. Only kindness could wake her.", "scene": "Queen sleeping in crystal palace, Finn approaching respectfully"},
            {"text": "Finn didn't use magic or strength - he simply played a lullaby his mother taught him.", "scene": "Finn playing small flute, magical notes floating toward sleeping queen"},
            {"text": "The queen awoke smiling. \"True heroes use their hearts.\"\n\nThe End", "scene": "Queen awake, kingdom celebrating, Finn honored as hero"}
        ]
    },
    
    "Flame's Courageous Journey": {
        "age_range": "6-8",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Warm watercolour children's book illustration, baby dragon theme, adventure with heart",
        "characters": {
            "main": "Flame, a small orange dragon who's afraid of fire but learns to be brave"
        },
        "pages": [
            {"text": "Flame's Courageous Journey\n\nA Dragon's Tale", "scene": "Title page: Small cute orange dragon looking nervous but hopeful"},
            {"text": "Flame was a dragon who was afraid of fire. Yes, his OWN fire!", "scene": "Baby dragon hiccuping tiny flame and looking scared"},
            {"text": "Other dragons breathed big flames. But Flame? Only little sparks came out.", "scene": "Other dragons breathing impressive flames while Flame produces tiny spark"},
            {"text": "\"I'm not a real dragon,\" Flame sighed. \"I can't do anything right.\"", "scene": "Sad Flame sitting alone on a rock, other dragons flying in background"},
            {"text": "One day, a village needed help. A flood was coming!", "scene": "Flame seeing village below with rising water threatening it"},
            {"text": "Big dragons couldn't help - their fire made steam that made things worse!", "scene": "Big dragon fire creating steam clouds, villagers worried"},
            {"text": "But Flame had an idea! His tiny sparks could light the warning beacons!", "scene": "Flame carefully lighting small beacon torches with precise tiny flames"},
            {"text": "One by one, Flame lit every beacon. The village was warned in time!", "scene": "Chain of lit beacons across mountains, villagers evacuating safely"},
            {"text": "\"You saved us all!\" the villagers cheered. Flame stood tall with pride.", "scene": "Villagers celebrating Flame, other dragons watching proudly"},
            {"text": "Flame learned that being different isn't bad - it's what makes you special!\n\nThe End", "scene": "Flame confidently producing beautiful small flame, happy ending"}
        ]
    },
    
    # === ADVENTURE ===
    "Guardians of Tomorrow": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Dynamic adventure children's book illustration, diverse young heroes, save-the-planet theme",
        "characters": {
            "main": "The Eco-Squad: Maya (plants), Kai (water), Zara (animals), and Leo (energy)"
        },
        "pages": [
            {"text": "Guardians of Tomorrow\n\nProtecting Our Planet", "scene": "Title page: Four diverse kids with nature powers standing heroically"},
            {"text": "The Eco-Squad were kids with special powers connected to nature.", "scene": "Four kids discovering their powers - plants, water, animals, energy"},
            {"text": "Maya could make plants grow. Kai could clean water. Zara talked to animals. Leo made clean energy!", "scene": "Each kid demonstrating their unique power"},
            {"text": "One day, they saw their town was sick - polluted water, dying trees!", "scene": "Kids looking sadly at polluted river and wilting park"},
            {"text": "\"We have to do something!\" said Maya. The squad made a plan.", "scene": "Kids huddled together, making a plan with a hand-drawn map"},
            {"text": "Maya planted trees everywhere. In days, the air smelled fresh!", "scene": "Maya using powers to grow trees rapidly, air becoming cleaner"},
            {"text": "Kai cleaned the river. Fish came back, and so did the birds!", "scene": "Kai purifying water, fish swimming, birds returning"},
            {"text": "Zara helped animals find new homes. The forest came alive again!", "scene": "Zara communicating with animals, guiding them to restored habitat"},
            {"text": "Leo powered the town with sun and wind. No more smoke!", "scene": "Leo creating solar and wind energy, factory smoke disappearing"},
            {"text": "\"We're ALL guardians,\" they told the town. \"Everyone can help!\"\n\nThe End", "scene": "Whole town joining in to help environment, kids leading the way"}
        ]
    },
    
    "Friendship Island": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "cartoon",
        "style_prompt": "Bright tropical cartoon children's book illustration, island adventure, friendship theme",
        "characters": {
            "main": "Sunny the crab, Splash the dolphin, and Breeze the seagull - unlikely friends"
        },
        "pages": [
            {"text": "Friendship Island\n\nWhere Friends are Found", "scene": "Title page: Tropical island with crab, dolphin, and seagull together"},
            {"text": "On a tiny island lived Sunny the crab. She had lots of shells but no friends.", "scene": "Lonely crab on beach surrounded by beautiful shells"},
            {"text": "Splash the dolphin swam by every day. \"Want to play?\" But Sunny was too shy.", "scene": "Friendly dolphin waving fin, crab hiding in shell"},
            {"text": "Breeze the seagull landed nearby. \"Hello!\" Sunny scuttled away nervously.", "scene": "Seagull landing, crab sideways-walking away"},
            {"text": "One stormy day, Sunny's shell collection washed away!", "scene": "Storm scene with shells being swept out to sea, crab distressed"},
            {"text": "Splash dove deep to find the shells. Breeze flew high to spot them!", "scene": "Dolphin diving, seagull searching from above"},
            {"text": "Together they brought back every single shell!", "scene": "Dolphin and seagull delivering shells to grateful crab"},
            {"text": "\"You did that... for ME?\" Sunny couldn't believe it.", "scene": "Crab looking at pile of recovered shells, friends smiling"},
            {"text": "\"That's what friends do,\" Splash smiled. Sunny smiled back.", "scene": "Three friends together on beach, sunset"},
            {"text": "Now the island isn't lonely anymore. It's Friendship Island!\n\nThe End", "scene": "Three friends playing together, island looking happy and alive"}
        ]
    },
    
    "Desert Treasure Hunt": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed adventure children's book illustration, desert archaeology theme, golden sand colors",
        "characters": {
            "main": "Dr. Sara and her nephew Jake, archaeologist adventurers"
        },
        "pages": [
            {"text": "Desert Treasure Hunt\n\nThe Search Begins", "scene": "Title page: Woman archaeologist and boy with map in desert, pyramids behind"},
            {"text": "Dr. Sara found an old map in her grandfather's journal. X marked a lost tomb!", "scene": "Sara and Jake examining ancient map with X marked"},
            {"text": "\"Let's find it together, Jake!\" They packed their gear and headed to Egypt.", "scene": "Duo preparing equipment, excited expressions"},
            {"text": "The desert was hot and vast. But the map led them to ancient ruins.", "scene": "Two figures approaching half-buried ruins in desert"},
            {"text": "Hidden beneath the sand was a door! Jake spotted the symbols.", "scene": "Jake pointing at hieroglyphics on hidden stone door"},
            {"text": "\"These symbols tell a story,\" Sara explained. \"They're the key!\"", "scene": "Sara translating hieroglyphics while Jake watches"},
            {"text": "Inside, they found chambers filled with amazing artifacts!", "scene": "Amazing tomb interior with gold artifacts, both in awe"},
            {"text": "But the real treasure? A library of ancient scrolls - knowledge!", "scene": "Room full of preserved scrolls, Sara and Jake amazed"},
            {"text": "\"The greatest treasure isn't gold,\" Sara smiled. \"It's learning!\"", "scene": "Sara and Jake carefully handling ancient scrolls"},
            {"text": "They shared their discovery with the world. History came alive!\n\nThe End", "scene": "Museum exhibit of their discovery, children learning"}
        ]
    },
}


async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality, high detail, kid-friendly, no text."
    
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
        print("FAILED - No image")
        return False
    except Exception as e:
        error = str(e).lower()
        if "balance" in error or "budget" in error or "insufficient" in error or "quota" in error:
            raise Exception("BUDGET_EXHAUSTED")
        print(f"FAILED - {str(e)[:60]}")
        return False


async def complete_single_book(book_id: str, title: str, template: dict, db):
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
    
    # Cover
    cover_path = output_dir / "cover.png"
    if not cover_path.exists():
        print(f"[Cover]", end=" ")
        cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}. Title space at top."
        if await generate_book_image(cover_prompt, template["style_prompt"], cover_path):
            shutil.copy(cover_path, public_dir / "cover.png")
    else:
        print(f"[Cover] Exists")
    
    # Pages
    for i, page in enumerate(template["pages"]):
        page_path = output_dir / f"page_{i+1:02d}.png"
        
        if not page_path.exists():
            print(f"[Page {i+1}/{total}]", end=" ")
            scene_prompt = f"{page['scene']}. Character: {template['characters']['main']}"
            if await generate_book_image(scene_prompt, template["style_prompt"], page_path):
                shutil.copy(page_path, public_dir / f"page_{i+1:02d}.png")
        else:
            print(f"[Page {i+1}/{total}] Exists")
        
        pages.append({
            "page_number": i + 1,
            "text": page["text"],
            "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.5)
    
    # Back cover
    back_path = output_dir / "back_cover.png"
    if not back_path.exists():
        print("[Back]", end=" ")
        back_prompt = f"Back cover for children's book. {template['characters']['main']} in peaceful scene."
        if await generate_book_image(back_prompt, template["style_prompt"], back_path):
            shutil.copy(back_path, public_dir / "back_cover.png")
    else:
        print("[Back] Exists")
    
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
    
    print(f"\n✓ Complete! Cost so far: ${estimated_cost:.2f}")
    return True


async def main():
    global estimated_cost
    
    print("="*60)
    print("BOOK GENERATION - BATCH 3")
    print("Using: OpenAI GPT-Image-1 (Emergent Key)")
    print("="*60)
    
    if not EMERGENT_KEY:
        print("ERROR: EMERGENT_LLM_KEY not found!")
        return
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get empty books with templates
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
    
    # Sort by priority (Super Silly Superhero and Colors of the World first)
    priority_order = ["Super Silly Superhero", "Colors of the World"]
    books_to_generate.sort(key=lambda x: (
        priority_order.index(x["title"]) if x["title"] in priority_order else 100
    ))
    
    print(f"\nFound {len(books_to_generate)} books to generate:")
    for i, b in enumerate(books_to_generate):
        priority = "⭐ PRIORITY" if b["title"] in priority_order else ""
        print(f"  {i+1}. {b['title']} {priority}")
    
    if not books_to_generate:
        print("\nNo matching books!")
        return
    
    # Generate
    print("\n--- GENERATING ---")
    
    completed = 0
    BUDGET_LIMIT = 8.0  # ~200 images
    
    for book_info in books_to_generate:
        if estimated_cost > BUDGET_LIMIT:
            print(f"\n⚠️ BUDGET LIMIT: ${estimated_cost:.2f}. Stopping.")
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
                print(f"\n🚨 BUDGET EXHAUSTED")
                break
            print(f"Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("BATCH COMPLETE")
    print("="*60)
    print(f"Books completed: {completed}")
    print(f"Images generated: {images_generated}")
    print(f"Est. cost: ${estimated_cost:.2f}")
    
    remaining = await db.books.count_documents({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}]
    })
    print(f"Books still empty: {remaining}")


if __name__ == "__main__":
    asyncio.run(main())
