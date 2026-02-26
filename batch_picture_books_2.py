#!/usr/bin/env python3
"""
Batch Picture Book Completion Script - Part 2
More Picture Books
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

images_generated = 0
estimated_cost = 0.0

BOOK_TEMPLATES = {
    "The Giant's Gentle Heart": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, warm heartfelt mood, earthy browns and warm colors, gentle giant theme",
        "characters": {
            "main": "Grumble, a huge friendly giant with wild brown hair, kind green eyes, a big bushy beard, wearing patched overalls and no shoes, always looking a bit sad and lonely",
            "children": "A group of village children including a brave girl with pigtails named Emma"
        },
        "pages": [
            {"text": "The Giant's Gentle Heart\n\nA Story of Friendship", "scene": "Title page: A giant sitting alone on a hill, looking at a distant village"},
            {"text": "Grumble the giant lived alone in the mountains. Everyone in the village below was afraid of him.", "scene": "Grumble sitting sadly outside his cave, village visible far below"},
            {"text": "\"Giant! Monster!\" the villagers would shout whenever they saw him. But Grumble had never hurt anyone. He just wanted a friend.", "scene": "Villagers running away scared, Grumble looking sad with his hand reaching out"},
            {"text": "One day, a little girl named Emma got lost in the forest. It started to rain and she was very scared.", "scene": "Emma lost in dark rainy forest, looking scared and wet"},
            {"text": "Grumble found her shivering under a tree. Very gently, he scooped her up and carried her to his warm cave.", "scene": "Grumble carefully and gently picking up small Emma, protective and kind"},
            {"text": "He made her soup in a pot as big as a bathtub and wrapped her in his warmest blanket.", "scene": "Grumble serving soup to Emma in his cozy cave, fire burning, Emma smiling"},
            {"text": "When the rain stopped, Grumble carried Emma safely home. The villagers gasped when they saw them.", "scene": "Grumble walking toward village carrying happy Emma, villagers watching in shock"},
            {"text": "\"He saved me!\" Emma told everyone. \"He's the kindest giant ever!\"", "scene": "Emma speaking to villagers while holding Grumble's big finger, villagers looking ashamed"},
            {"text": "From that day on, the villagers welcomed Grumble. He helped build houses and played with the children.", "scene": "Grumble happily helping build a house while children play around his feet"},
            {"text": "And Grumble finally had what he always wanted—friends who loved him for his gentle heart.\n\nThe End", "scene": "Grumble surrounded by happy villagers and children, finally smiling, sunset"}
        ]
    },
    "The Burping Dragon": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, silly humorous mood, bright fun colors, comedic expressions",
        "characters": {
            "main": "Burp, a small round green dragon with a big belly, silly expression, always looking embarrassed, tiny wings",
            "friend": "Knight Kevin, a small friendly knight with oversized armor, kind face"
        },
        "pages": [
            {"text": "The Burping Dragon\n\nA Silly Story", "scene": "Title page: A dragon mid-burp with a surprised knight nearby, funny style"},
            {"text": "Burp the dragon had a problem. Every time he tried to breathe fire... BURRRP! Out came a big burp instead!", "scene": "Burp the dragon trying to breathe fire but burping instead, embarrassed expression"},
            {"text": "The other dragons laughed at him. \"What kind of dragon can't breathe fire?\" they teased.", "scene": "Other dragons laughing and pointing at sad Burp"},
            {"text": "Burp tried everything. He ate spicy food. BURRRP! He jumped up and down. BURRRP! Nothing worked.", "scene": "Burp trying different things, each resulting in a burp, funny montage style"},
            {"text": "One day, a little knight named Kevin came to the dragon cave. \"Help! A mean ogre is scaring my village!\"", "scene": "Knight Kevin asking dragons for help, the other dragons looking away"},
            {"text": "The big dragons were too scared to help. But Burp wanted to be brave.", "scene": "Burp stepping forward while other dragons hide, determined expression"},
            {"text": "Burp faced the ogre and took a deep breath. The ogre laughed, \"What will YOU do, little dragon?\"", "scene": "Burp facing a big scary ogre, the ogre laughing mockingly"},
            {"text": "BURRRRRRRRRP! The biggest burp ever! It was so stinky the ogre ran away crying!", "scene": "Burp doing massive burp with green clouds, ogre running away holding nose"},
            {"text": "\"You saved us!\" cheered Kevin. \"That was the best burp I've ever heard!\"", "scene": "Kevin and villagers cheering for proud Burp"},
            {"text": "Burp learned that being different isn't bad—it's just being special in your own way.\n\nThe End", "scene": "Burp and Kevin as friends, Burp proudly burping a small burp, everyone laughing happily"}
        ]
    },
    "The Monster Who Was Scared of Kids": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, sweet gentle mood, soft purples and friendly monster colors",
        "characters": {
            "main": "Mumble, a fluffy purple monster with big scared eyes, tiny horns, who hides under beds but is actually terrified",
            "child": "Tommy, a brave 5-year-old boy with messy brown hair and superhero pajamas"
        },
        "pages": [
            {"text": "The Monster Who Was Scared of Kids\n\nA Not-So-Scary Story", "scene": "Title page: A fluffy monster peeking nervously from under a bed"},
            {"text": "Mumble was a monster who lived under beds. But he had a secret—he was TERRIFIED of children!", "scene": "Mumble the purple monster trembling under a bed, looking scared"},
            {"text": "Every night, Mumble would hear the scary sounds: laughing, singing, and worst of all... GIGGLING!", "scene": "Mumble covering his ears, imaginary scary kid sounds illustrated around him"},
            {"text": "One night, a boy named Tommy looked under his bed. \"AHHH!\" they both screamed at each other!", "scene": "Tommy and Mumble face to face under bed, both screaming in surprise"},
            {"text": "\"Please don't hurt me!\" Mumble whimpered. Tommy was confused. \"You're scared of ME?\"", "scene": "Mumble cowering, Tommy looking puzzled and concerned"},
            {"text": "\"Kids are so loud and bouncy and... and... HAPPY!\" Mumble shivered. \"It's terrifying!\"", "scene": "Mumble explaining while shaking, thought bubble showing scary happy kids"},
            {"text": "Tommy laughed kindly. \"We're not scary! Watch.\" He gave Mumble a gentle hug.", "scene": "Tommy hugging surprised Mumble, Mumble starting to smile"},
            {"text": "\"That was... nice,\" Mumble admitted. \"Can we be friends?\"", "scene": "Tommy and Mumble shaking hands/paw, both smiling"},
            {"text": "From then on, Mumble still lived under Tommy's bed, but now they played together every night.", "scene": "Tommy and Mumble playing board games on the floor at night"},
            {"text": "And Mumble discovered that kids weren't scary at all—they were actually pretty fun!\n\nThe End", "scene": "Tommy and Mumble sleeping, Tommy in bed, Mumble cuddled underneath, both peaceful"}
        ]
    },
    "Kindness Kingdom": {
        "age_range": "3-6",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, warm educational mood, rainbow colors, kingdom setting",
        "characters": {
            "main": "Princess Kira, a young princess with brown skin, curly black hair with a heart-shaped tiara, wearing a dress that changes color based on kind deeds",
            "helper": "Sir Sprout, a tiny talking sunflower knight"
        },
        "pages": [
            {"text": "Kindness Kingdom\n\nWhere Good Deeds Bloom", "scene": "Title page: A magical kingdom where flowers bloom when people are kind"},
            {"text": "In Kindness Kingdom, something magical happened whenever someone did a kind deed—flowers would bloom!", "scene": "Kingdom overview with flowers blooming as people help each other"},
            {"text": "Princess Kira wore a special dress that changed color with each kind act. Today it was plain white.", "scene": "Princess Kira looking at her white dress, wanting to make it colorful"},
            {"text": "\"How do I fill my dress with colors?\" Kira asked Sir Sprout, her sunflower friend.", "scene": "Kira talking to Sir Sprout the tiny sunflower knight"},
            {"text": "\"By being kind!\" said Sir Sprout. \"Let's find ways to help today!\"", "scene": "Sir Sprout pointing toward the village, Kira looking excited"},
            {"text": "Kira helped an old turtle cross the road. PINK! A pink stripe appeared on her dress!", "scene": "Kira helping a turtle, pink stripe magically appearing on her dress"},
            {"text": "She shared her lunch with hungry birds. BLUE! Another stripe appeared!", "scene": "Kira sharing food with birds, blue stripe appearing, birds happy"},
            {"text": "She read stories to younger children. YELLOW! She comforted a sad friend. GREEN!", "scene": "Split scene of Kira reading to kids and comforting friend, stripes appearing"},
            {"text": "By sunset, Kira's dress was a beautiful rainbow! And the whole kingdom was covered in flowers.", "scene": "Kira in full rainbow dress, kingdom blooming with flowers everywhere"},
            {"text": "\"Kindness makes everything more beautiful,\" Kira smiled. \"Even me!\"\n\nThe End", "scene": "Kira and Sir Sprout in blooming garden, rainbow dress glowing, sunset"}
        ]
    }
}

async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
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
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        with open(output_path, 'wb') as f:
                            f.write(image_bytes)
                        images_generated += 1
                        estimated_cost += 0.03
                        return True
        return False
    except Exception as e:
        error_str = str(e).lower()
        if "balance" in error_str or "budget" in error_str or "exceeded" in error_str or "insufficient" in error_str:
            raise Exception("BUDGET_EXHAUSTED")
        print(f"    ERROR: {str(e)[:100]}")
        return False

async def complete_single_book(book_id: str, title: str, template: dict):
    global images_generated, estimated_cost
    
    print(f"\n{'='*60}")
    print(f"COMPLETING: {title}")
    print(f"{'='*60}")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    safe_title = title.lower().replace("'", "").replace(" ", "_")
    output_dir = APP_DIR / f"content/books/completed/{safe_title}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    total_pages = len(template["pages"])
    
    print(f"\n[Cover] Generating...")
    cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}. Engaging scene, space for title at top"
    cover_path = output_dir / "cover.png"
    if await generate_book_image(cover_prompt, template["style_prompt"], cover_path):
        print(f"    ✓ Cover saved")
    
    for i, page_data in enumerate(template["pages"]):
        print(f"[Page {i+1}/{total_pages}] Generating...")
        
        scene_prompt = page_data["scene"]
        for char_key, char_desc in template["characters"].items():
            if char_key == "main":
                scene_prompt = f"{scene_prompt}. Main character: {char_desc}"
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
        
        await asyncio.sleep(0.3)
    
    print(f"[Back Cover] Generating...")
    back_cover_path = output_dir / "back_cover.png"
    await generate_book_image(f"Back cover for '{title}'. Peaceful scene with main character", template["style_prompt"], back_cover_path)
    
    print(f"Updating database...")
    await db.books.update_one(
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
                "updated_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    public_dir = APP_DIR / f"frontend/public/book-assets/{safe_title}"
    public_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    for img_file in output_dir.glob("*.png"):
        shutil.copy(img_file, public_dir / img_file.name)
    
    print(f"\n✓ {title} COMPLETED - Cost: ${estimated_cost:.2f}")
    return True

async def run_batch():
    global images_generated, estimated_cost
    
    print("="*60)
    print("PICTURE BOOK BATCH - PART 2")
    print("="*60)
    
    books_to_complete = [
        ("699adbe6176ebca750087f1b", "The Giant's Gentle Heart"),
        ("699adbe6176ebca750087f28", "The Burping Dragon"),
        ("699adbe6176ebca750087f29", "The Monster Who Was Scared of Kids"),
        ("699adbe6176ebca750087f26", "Kindness Kingdom"),
    ]
    
    completed = 0
    for book_id, title in books_to_complete:
        if title in BOOK_TEMPLATES:
            try:
                await complete_single_book(book_id, title, BOOK_TEMPLATES[title])
                completed += 1
                
                if estimated_cost > 8.5:
                    print("\n⚠️ BUDGET WARNING: Approaching limit")
                    break
                    
            except Exception as e:
                if "BUDGET" in str(e):
                    print("\n🚨 BUDGET EXHAUSTED")
                    break
                print(f"\n✗ Error: {e}")
    
    print("\n" + "="*60)
    print(f"BATCH SUMMARY: {completed} books, {images_generated} images, ${estimated_cost:.2f}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_batch())
