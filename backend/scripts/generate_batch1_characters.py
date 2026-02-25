"""
Batch 1: Character Images Generator
Generates 50 character images for the starter library
"""

import asyncio
import os
import base64
import json
from datetime import datetime, timezone
from dotenv import dotenv_values

env = dotenv_values('/app/backend/.env')
EMERGENT_LLM_KEY = env.get('EMERGENT_LLM_KEY')

from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

# Batch 1: 50 Character Images
# Distribution: 13 Watercolour, 13 Realistic, 12 Comic, 12 Sketch
BATCH_1_CHARACTERS = [
    # === WATERCOLOUR STYLE (13 images) ===
    # Children - Diverse
    {"id": "char_001", "name": "Adventure Girl Maya", "category": "character", 
     "tags": ["child", "girl", "adventure", "diverse", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A cheerful 8-year-old African American girl with curly black hair in pigtails, wearing a bright yellow raincoat and red boots, holding a magnifying glass, curious expression, ready for adventure"},
    
    {"id": "char_002", "name": "Young Explorer Kai", "category": "character",
     "tags": ["child", "boy", "explorer", "diverse", "watercolour"],
     "art_style": "watercolour", 
     "prompt": "A brave 10-year-old Japanese boy with short black hair, wearing a green explorer vest with many pockets, khaki shorts, and hiking boots, holding a compass, determined expression"},
    
    {"id": "char_003", "name": "Princess Amara", "category": "character",
     "tags": ["princess", "girl", "fantasy", "diverse", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful young Indian princess about 12 years old with long flowing black hair adorned with gold jewelry, wearing an elegant turquoise sari with gold embroidery, kind and gentle expression"},
    
    # Fantasy Characters
    {"id": "char_004", "name": "Friendly Garden Gnome", "category": "character",
     "tags": ["gnome", "fantasy", "friendly", "magical", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A jolly little garden gnome with a long white beard, rosy cheeks, wearing a tall red pointed hat and blue coat, sitting on a mushroom, twinkling eyes, holding a small watering can"},
    
    {"id": "char_005", "name": "Ocean Mermaid Coral", "category": "character",
     "tags": ["mermaid", "ocean", "fantasy", "magical", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A friendly young mermaid with flowing turquoise hair decorated with seashells, shimmering pink and purple tail, holding a starfish, surrounded by small fish, peaceful underwater scene"},
    
    # Animals
    {"id": "char_006", "name": "Wise Owl Professor", "category": "character",
     "tags": ["owl", "animal", "wise", "cute", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A distinguished owl wearing tiny round spectacles and a small graduation cap, fluffy brown and white feathers, perched on a stack of books, scholarly expression"},
    
    {"id": "char_007", "name": "Playful Puppy Max", "category": "character",
     "tags": ["dog", "puppy", "pet", "cute", "watercolour"],
     "art_style": "watercolour",
     "prompt": "An adorable golden retriever puppy with floppy ears, big brown eyes, wearing a red bandana around its neck, playful pose with one paw raised, tongue out happily"},
    
    {"id": "char_008", "name": "Curious Kitten Luna", "category": "character",
     "tags": ["cat", "kitten", "pet", "cute", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A fluffy white kitten with bright blue eyes and a pink nose, wearing a tiny purple bow, sitting in a cozy basket, curious tilted head expression"},
    
    # More diverse children
    {"id": "char_009", "name": "Bookworm Emma", "category": "character",
     "tags": ["child", "girl", "reader", "glasses", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A studious 9-year-old girl with red hair in braids, freckles, wearing round glasses and a cozy sweater, sitting cross-legged with an open book, surrounded by stacks of colorful books"},
    
    {"id": "char_010", "name": "Soccer Star Diego", "category": "character",
     "tags": ["child", "boy", "sports", "diverse", "watercolour"],
     "art_style": "watercolour",
     "prompt": "An energetic 11-year-old Latino boy with wavy dark hair, wearing a bright blue soccer jersey and shorts, foot on a soccer ball, confident smile, ready to play"},
    
    {"id": "char_011", "name": "Little Artist Zara", "category": "character",
     "tags": ["child", "girl", "artist", "diverse", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A creative 7-year-old Middle Eastern girl with long dark curly hair, wearing a paint-splattered apron, holding a paintbrush and palette, surrounded by colorful easels"},
    
    {"id": "char_012", "name": "Woodland Fox Felix", "category": "character",
     "tags": ["fox", "animal", "woodland", "cute", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A charming red fox with a white-tipped fluffy tail, bright amber eyes, wearing a tiny green scarf, sitting in autumn leaves, friendly curious expression"},
    
    {"id": "char_013", "name": "Baby Elephant Ella", "category": "character",
     "tags": ["elephant", "baby", "animal", "cute", "watercolour"],
     "art_style": "watercolour",
     "prompt": "An adorable baby elephant with big floppy ears and a tiny trunk, wearing a colorful flower crown, splashing happily in a small puddle, joyful expression"},
    
    # === REALISTIC ILLUSTRATED STYLE (13 images) ===
    {"id": "char_014", "name": "Young Astronaut Stella", "category": "character",
     "tags": ["astronaut", "girl", "space", "hero", "realistic"],
     "art_style": "realistic",
     "prompt": "A determined 12-year-old girl astronaut with short brown hair, wearing an orange NASA-style spacesuit, helmet under her arm, standing proudly with Earth visible through a window behind her"},
    
    {"id": "char_015", "name": "Junior Scientist Chen", "category": "character",
     "tags": ["scientist", "boy", "smart", "diverse", "realistic"],
     "art_style": "realistic",
     "prompt": "A brilliant young Chinese boy about 10 years old wearing a white lab coat and safety goggles pushed up on his forehead, holding a bubbling test tube, excited expression in a colorful laboratory"},
    
    {"id": "char_016", "name": "Brave Knight Roland", "category": "character",
     "tags": ["knight", "boy", "brave", "fantasy", "realistic"],
     "art_style": "realistic",
     "prompt": "A courageous young knight about 14 years old with sandy blonde hair, wearing shining silver armor with a blue cape, holding a shield with a lion emblem, noble expression"},
    
    {"id": "char_017", "name": "Marine Biologist Kai", "category": "character",
     "tags": ["marine", "scientist", "ocean", "diverse", "realistic"],
     "art_style": "realistic",
     "prompt": "A passionate young Hawaiian girl about 13 years old with long dark hair, wearing a wetsuit and snorkel gear, holding a clipboard, standing on a boat with dolphins in the background"},
    
    {"id": "char_018", "name": "Young Chef Pierre", "category": "character",
     "tags": ["chef", "boy", "cooking", "creative", "realistic"],
     "art_style": "realistic",
     "prompt": "A talented young French boy chef about 11 years old with curly brown hair, wearing a white chef hat and apron, holding a wooden spoon, surrounded by colorful ingredients in a bright kitchen"},
    
    {"id": "char_019", "name": "Ballet Dancer Anya", "category": "character",
     "tags": ["ballet", "dancer", "girl", "graceful", "realistic"],
     "art_style": "realistic",
     "prompt": "A graceful young Russian ballerina about 12 years old with blonde hair in a neat bun, wearing a pink tutu and ballet slippers, in an elegant dance pose, soft studio lighting"},
    
    {"id": "char_020", "name": "Park Ranger Sam", "category": "character",
     "tags": ["ranger", "nature", "adventure", "diverse", "realistic"],
     "art_style": "realistic",
     "prompt": "A friendly young Native American park ranger about 14 years old with long black hair in a braid, wearing a ranger uniform and hat, binoculars around neck, standing in a beautiful forest"},
    
    {"id": "char_021", "name": "Gentle Unicorn Spirit", "category": "character",
     "tags": ["unicorn", "magical", "fantasy", "gentle", "realistic"],
     "art_style": "realistic",
     "prompt": "A majestic white unicorn with a spiraling silver horn, flowing rainbow mane, gentle wise eyes, standing in a meadow of wildflowers with soft golden sunlight"},
    
    {"id": "char_022", "name": "Phoenix Rising", "category": "character",
     "tags": ["phoenix", "mythical", "fire", "magical", "realistic"],
     "art_style": "realistic",
     "prompt": "A magnificent phoenix bird with brilliant red, orange and gold feathers, wings spread wide, surrounded by swirling flames, powerful yet benevolent expression, rising against a twilight sky"},
    
    {"id": "char_023", "name": "Loyal Wolf Guardian", "category": "character",
     "tags": ["wolf", "guardian", "loyal", "animal", "realistic"],
     "art_style": "realistic",
     "prompt": "A noble gray wolf with piercing blue eyes, thick silver fur, sitting protectively in a snowy forest, dignified and loyal expression, moonlight illuminating the scene"},
    
    {"id": "char_024", "name": "Young Pilot Amelia", "category": "character",
     "tags": ["pilot", "girl", "adventure", "brave", "realistic"],
     "art_style": "realistic",
     "prompt": "A daring young female pilot about 13 years old with short auburn hair, wearing vintage aviator goggles on her head and a brown leather jacket, standing next to a small colorful airplane"},
    
    {"id": "char_025", "name": "Inventor Thomas", "category": "character",
     "tags": ["inventor", "boy", "creative", "smart", "realistic"],
     "art_style": "realistic",
     "prompt": "A clever young African American inventor about 12 years old with short curly hair, wearing a tool belt and safety glasses, surrounded by gears and gadgets, holding a blueprint"},
    
    {"id": "char_026", "name": "Veterinarian Dr. Rose", "category": "character",
     "tags": ["vet", "doctor", "animals", "caring", "realistic"],
     "art_style": "realistic",
     "prompt": "A kind young veterinarian about 14 years old with long curly red hair, wearing a white coat and stethoscope, gently holding a small puppy, surrounded by various cute animals"},
    
    # === COMIC BOOK STYLE (12 images) ===
    {"id": "char_027", "name": "Super Hero Max", "category": "character",
     "tags": ["superhero", "boy", "hero", "action", "comic"],
     "art_style": "comic",
     "prompt": "A young superhero boy about 12 years old with spiky black hair, wearing a bright red and blue costume with a lightning bolt emblem, heroic flying pose with cape billowing, city skyline behind"},
    
    {"id": "char_028", "name": "Space Captain Zara", "category": "character",
     "tags": ["space", "captain", "girl", "scifi", "comic"],
     "art_style": "comic",
     "prompt": "A fearless young space captain girl with short purple hair, wearing a sleek silver spacesuit with neon blue accents, standing on the bridge of a futuristic spaceship, stars visible through windows"},
    
    {"id": "char_029", "name": "Ninja Warrior Yuki", "category": "character",
     "tags": ["ninja", "warrior", "girl", "action", "comic"],
     "art_style": "comic",
     "prompt": "A skilled young ninja girl about 11 years old with black hair in a ponytail, wearing a dark blue ninja outfit with silver trim, dynamic action pose on a rooftop under moonlight"},
    
    {"id": "char_030", "name": "Robot Helper BEEP", "category": "character",
     "tags": ["robot", "helper", "friendly", "scifi", "comic"],
     "art_style": "comic",
     "prompt": "A cheerful round robot with big expressive screen eyes showing happy emoji, metallic blue body with orange accents, small propeller on top, extending a helpful mechanical arm"},
    
    {"id": "char_031", "name": "Pirate Captain Jack", "category": "character",
     "tags": ["pirate", "captain", "adventure", "boy", "comic"],
     "art_style": "comic",
     "prompt": "A dashing young pirate captain about 13 years old with messy brown hair, wearing a tricorn hat and red coat, eyepatch over one eye, standing at ship wheel with parrot on shoulder"},
    
    {"id": "char_032", "name": "Alien Friend Zorp", "category": "character",
     "tags": ["alien", "friend", "scifi", "cute", "comic"],
     "art_style": "comic",
     "prompt": "A friendly alien creature with green skin, three big purple eyes, small antennae, wearing a colorful space jumpsuit, waving with four arms, floating in a bubble ship"},
    
    {"id": "char_033", "name": "Thunder Lion Leo", "category": "character",
     "tags": ["lion", "mythical", "powerful", "guardian", "comic"],
     "art_style": "comic",
     "prompt": "A powerful mythical lion with a magnificent golden mane crackling with electricity, glowing blue eyes, wearing ancient armor plates, heroic stance on a rocky cliff"},
    
    {"id": "char_034", "name": "Speed Cheetah Chase", "category": "character",
     "tags": ["cheetah", "fast", "hero", "animal", "comic"],
     "art_style": "comic",
     "prompt": "A sleek anthropomorphic cheetah character wearing a red racing suit and goggles, dynamic running pose with motion blur lines, determined expression, savanna background"},
    
    {"id": "char_035", "name": "Ice Princess Freya", "category": "character",
     "tags": ["ice", "princess", "magic", "fantasy", "comic"],
     "art_style": "comic",
     "prompt": "A powerful young ice princess with flowing white hair and icy blue eyes, wearing a glittering silver gown, creating beautiful snowflakes with her hands, northern lights behind her"},
    
    {"id": "char_036", "name": "Dino Rider Rex", "category": "character",
     "tags": ["dinosaur", "rider", "adventure", "boy", "comic"],
     "art_style": "comic",
     "prompt": "An adventurous young boy with goggles on his forehead riding on the back of a friendly green T-Rex, both looking excited, prehistoric jungle background with volcanoes"},
    
    {"id": "char_037", "name": "Magic Girl Sparkle", "category": "character",
     "tags": ["magic", "girl", "sparkle", "hero", "comic"],
     "art_style": "comic",
     "prompt": "A young magical girl with rainbow-streaked hair in twin tails, wearing a sparkly pink and gold costume, wielding a star-shaped staff, surrounded by swirling magical energy"},
    
    {"id": "char_038", "name": "Cyber Detective Zero", "category": "character",
     "tags": ["cyber", "detective", "smart", "scifi", "comic"],
     "art_style": "comic",
     "prompt": "A tech-savvy young detective with neon green hair, wearing a futuristic trench coat with holographic displays, holding a digital magnifying glass, cyberpunk city background"},
    
    # === PENCIL SKETCH STYLE (12 images) ===
    {"id": "char_039", "name": "Wise Old Turtle", "category": "character",
     "tags": ["turtle", "wise", "elder", "animal", "sketch"],
     "art_style": "sketch",
     "prompt": "An ancient wise turtle with a weathered shell covered in moss, kind old eyes, small round spectacles, sitting peacefully on a log, serene pond setting"},
    
    {"id": "char_040", "name": "Gentle Giant Troll", "category": "character",
     "tags": ["troll", "giant", "gentle", "fantasy", "sketch"],
     "art_style": "sketch",
     "prompt": "A friendly large troll with mossy green skin, big gentle eyes, wearing simple clothes made of leaves, sitting under a bridge feeding small woodland creatures"},
    
    {"id": "char_041", "name": "Woodland Deer Spirit", "category": "character",
     "tags": ["deer", "spirit", "magical", "nature", "sketch"],
     "art_style": "sketch",
     "prompt": "A ethereal deer spirit with magnificent antlers decorated with glowing flowers, soft white fur, gentle eyes, standing in a misty forest clearing at dawn"},
    
    {"id": "char_042", "name": "Young Bard Melody", "category": "character",
     "tags": ["bard", "music", "girl", "fantasy", "sketch"],
     "art_style": "sketch",
     "prompt": "A young traveling bard girl about 13 with wavy brown hair, wearing a medieval dress and cloak, playing a beautiful lute, sitting on a stone wall in a village square"},
    
    {"id": "char_043", "name": "Cozy Bear Bernard", "category": "character",
     "tags": ["bear", "cozy", "friendly", "animal", "sketch"],
     "art_style": "sketch",
     "prompt": "A lovable brown bear wearing a knitted sweater and tiny reading glasses, sitting in an armchair with a cup of honey tea, cozy cottage interior background"},
    
    {"id": "char_044", "name": "Garden Rabbit Rose", "category": "character",
     "tags": ["rabbit", "garden", "cute", "animal", "sketch"],
     "art_style": "sketch",
     "prompt": "A sweet white rabbit with long floppy ears, wearing a tiny straw hat with flowers, holding a small basket of carrots, standing in a vegetable garden"},
    
    {"id": "char_045", "name": "Sleepy Dragon Ember", "category": "character",
     "tags": ["dragon", "sleepy", "cute", "fantasy", "sketch"],
     "art_style": "sketch",
     "prompt": "A small sleepy dragon curled up on a pile of treasure coins, tiny smoke puffs from nostrils, one eye half open, wings folded, cozy cave setting with soft lighting"},
    
    {"id": "char_046", "name": "Little Witch Hazel", "category": "character",
     "tags": ["girl", "magical", "fantasy", "young", "sketch"],
     "art_style": "sketch",
     "prompt": "A young apprentice girl about 8 years old with messy auburn hair, wearing an oversized pointy hat and star-covered robe, stirring a bubbling cauldron, friendly black cat nearby"},
    
    {"id": "char_047", "name": "Mountain Goat Guide", "category": "character",
     "tags": ["goat", "mountain", "guide", "animal", "sketch"],
     "art_style": "sketch",
     "prompt": "A sturdy mountain goat with curved horns, wearing a small backpack and tiny hiking boots, standing confidently on a rocky mountain peak, majestic view behind"},
    
    {"id": "char_048", "name": "Friendly Scarecrow Sam", "category": "character",
     "tags": ["scarecrow", "friendly", "farm", "fantasy", "sketch"],
     "art_style": "sketch",
     "prompt": "A cheerful scarecrow with a stitched smile and button eyes, wearing a patched hat and overalls, birds sitting on his arms as friends, autumn harvest field background"},
    
    {"id": "char_049", "name": "River Otter Otto", "category": "character",
     "tags": ["otter", "river", "playful", "animal", "sketch"],
     "art_style": "sketch",
     "prompt": "A playful river otter floating on his back in a stream, holding a small fish, whiskers twitching happily, reeds and lily pads around, peaceful river setting"},
    
    {"id": "char_050", "name": "Stargazer Mouse Pip", "category": "character",
     "tags": ["mouse", "stargazer", "curious", "animal", "sketch"],
     "art_style": "sketch",
     "prompt": "A tiny mouse wearing a miniature astronomer robe, peering through a small telescope on a hilltop, night sky full of stars and constellations above, wonder in his eyes"}
]

# Style suffixes for prompts
STYLE_SUFFIXES = {
    "watercolour": ", painted in soft watercolour style with gentle washes and flowing colors, delicate brushstrokes, professional children's book illustration, vibrant, age-appropriate, safe for children",
    "realistic": ", realistic illustrated style with detailed rendering, professional children's book illustration quality, vibrant colors, age-appropriate, safe for children",
    "comic": ", dynamic comic book style with bold outlines, vibrant colors, expressive features, professional children's book illustration, age-appropriate, safe for children",
    "sketch": ", pencil sketch style with detailed line work, crosshatching for shadows, artistic shading on cream paper, professional children's book illustration, age-appropriate, safe for children"
}


async def generate_batch_1():
    """Generate all 50 character images for Batch 1"""
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
    
    results = []
    failed = []
    
    for i, char in enumerate(BATCH_1_CHARACTERS):
        print(f"\nGenerating {i+1}/50: {char['name']} ({char['art_style']})...")
        
        # Build full prompt with style suffix
        full_prompt = char['prompt'] + STYLE_SUFFIXES[char['art_style']]
        
        try:
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model='gpt-image-1',
                number_of_images=1
            )
            
            if images and len(images) > 0:
                # Save image to file
                filename = f"/tmp/batch1_{char['id']}_{char['art_style']}.png"
                with open(filename, 'wb') as f:
                    f.write(images[0])
                
                # Convert to base64 for storage
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                
                result = {
                    "id": char['id'],
                    "name": char['name'],
                    "category": char['category'],
                    "tags": char['tags'],
                    "art_style": char['art_style'],
                    "filename": filename,
                    "base64_length": len(image_base64)
                }
                results.append(result)
                print(f"  ✓ Saved: {filename}")
            else:
                failed.append(char['name'])
                print(f"  ✗ Failed: No image generated")
                
        except Exception as e:
            failed.append(char['name'])
            print(f"  ✗ Error: {str(e)[:80]}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"BATCH 1 COMPLETE")
    print(f"{'='*60}")
    print(f"Generated: {len(results)}/50")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed items: {failed}")
    
    # Save results to JSON
    with open('/tmp/batch1_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to /tmp/batch1_results.json")
    
    return results, failed


if __name__ == "__main__":
    print("Starting Batch 1: Character Images Generation")
    print("=" * 60)
    results, failed = asyncio.run(generate_batch_1())
